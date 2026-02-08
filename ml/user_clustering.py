import logging
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
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
    events = get_events_df()
    products = get_products_df()

    if events.empty or products.empty:
        logger.warning("Events or products table is empty")
        return np.array([]), np.array([]), []

    events = events.copy()
    products = products.copy()

    events["product_id"] = events["product_id"].astype(str)
    products["product_id"] = products["product_id"].astype(str)

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

def cluster_users(n_clusters: int = 3) -> Dict[str, int]:
    """
    Cluster users based on behavioral features.

    Returns:
        Dict[user_id -> cluster_id]
    """
    user_ids, X, _ = extract_user_features()

    if len(user_ids) == 0:
        logger.warning("No users available for clustering")
        return {}

    if len(user_ids) < 2:
        return {str(user_ids[0]): 0}

    n_clusters = min(n_clusters, len(user_ids))
    if n_clusters < 2:
        return {str(uid): 0 for uid in user_ids}

    # Scale features for KMeans
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

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
