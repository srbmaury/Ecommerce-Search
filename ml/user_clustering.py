import logging
from typing import Dict, Tuple, List

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from backend.services.db_event_service import get_events_df
from backend.services.db_product_service import get_products_df


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------

def extract_user_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Extract per-user behavioral features for clustering.

    Features:
    - Normalized category click distribution
    - Average clicked product price

    Returns:
        user_ids: array of user IDs
        X: feature matrix (n_users, n_features)
        categories: category ordering used for features
    """
    # Batch job — needs the full catalog/history, not the 1000-row default
    # cap meant for interactive API calls (see ml/user_profile.py).
    events = get_events_df(limit=None)
    products = get_products_df(limit=None)

    if events.empty or products.empty:
        logger.warning("Events or products table is empty")
        return np.array([]), np.array([]), []

    events = events.copy()
    products = products.copy()

    # events.product_id is float64 vs products.product_id int64 — casting
    # straight to str gives "16923.0" vs "16923", which never match (see
    # ml/user_profile.py for the same fix). Go through nullable Int64 first.
    events["product_id"] = events["product_id"].astype("Int64").astype(str)
    products["product_id"] = products["product_id"].astype("Int64").astype(str)

    merged = events.merge(products, on="product_id", how="left")

    clicks = merged[merged["event"] == "click"]
    if clicks.empty:
        logger.warning("No click events found")
        return np.array([]), np.array([]), []

    categories = sorted(products["category"].dropna().unique())

    # --- Category distribution (vectorized) ---
    category_dist = (
        clicks.groupby(["user_id", "category"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=categories, fill_value=0)
    )

    # Normalize per user
    category_dist = category_dist.div(category_dist.sum(axis=1), axis=0)

    # --- Average price feature ---
    avg_price = clicks.groupby("user_id")["price"].mean()

    # --- Combine features ---
    feature_df = category_dist.copy()
    feature_df["avg_price"] = avg_price

    feature_df = feature_df.fillna(0)

    user_ids = feature_df.index.to_numpy()
    X = feature_df.to_numpy(dtype=np.float32)

    logger.info(
        "Extracted features for %d users (%d features)",
        len(user_ids),
        X.shape[1],
    )

    return user_ids, X, categories


# ---------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------

_OPTIMAL_K_REDIS_KEY = "ml:optimal_k"
_OPTIMAL_K_CACHE_TTL = 24 * 60 * 60  # re-evaluate once per day at most


def _pick_n_clusters(X_scaled: np.ndarray, max_k: int = 8) -> int:
    """
    Choose the number of clusters that maximises silhouette score.
    Falls back to 3 if there are too few users to evaluate.
    Result is cached in Redis for 24 hours to avoid expensive re-evaluation on every retrain.
    """
    try:
        from backend.services.redis_client import _redis
        cached = _redis.get(_OPTIMAL_K_REDIS_KEY)
        if cached:
            k = int(cached)
            logger.info("Using cached optimal k=%d", k)
            return k
    except Exception:
        pass

    n_users = len(X_scaled)
    # Need at least 2 samples per cluster to compute silhouette
    upper = min(max_k, n_users // 2)
    if upper < 2:
        return min(3, n_users)

    best_k, best_score = 2, -1.0
    for k in range(2, upper + 1):
        labels = KMeans(n_clusters=k, random_state=42, n_init=5).fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        logger.debug("Silhouette score for k=%d: %.4f", k, score)
        if score > best_score:
            best_k, best_score = k, score

    logger.info("Selected n_clusters=%d (silhouette=%.4f)", best_k, best_score)

    try:
        from backend.services.redis_client import _redis
        _redis.setex(_OPTIMAL_K_REDIS_KEY, _OPTIMAL_K_CACHE_TTL, best_k)
    except Exception:
        pass

    return best_k


def cluster_users(n_clusters: int = 0) -> Dict[str, int]:
    """
    Cluster users based on behavioral features.

    Args:
        n_clusters: Target cluster count. Pass 0 (default) to auto-select
                    using silhouette score, or pass an explicit value to
                    override (useful for testing).

    Returns:
        Dict[user_id -> cluster_id]
    """
    user_ids, X, _ = extract_user_features()

    if len(user_ids) == 0:
        logger.warning("No users available for clustering")
        return {}

    if len(user_ids) < 2:
        return {str(user_ids[0]): 0}

    # Scale features for KMeans
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if n_clusters <= 0:
        n_clusters = _pick_n_clusters(X_scaled)
    else:
        n_clusters = min(n_clusters, len(user_ids))

    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
    )

    labels = kmeans.fit_predict(X_scaled)

    clusters = {
        str(user_ids[i]): int(labels[i])
        for i in range(len(user_ids))
    }

    logger.info(
        "Clustered %d users into %d clusters",
        len(user_ids),
        n_clusters,
    )

    return clusters


# ---------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------

def run_user_clustering(n_clusters: int = 3) -> Dict[str, int]:
    """Alias kept for backward compatibility."""
    return cluster_users(n_clusters)
