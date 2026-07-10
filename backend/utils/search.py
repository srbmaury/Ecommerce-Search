"""
Search and ranking service.

Responsibilities:
- Product search (text + category fallback)
- A/B ranking logic
- ML-based scoring
- Recent interaction boosting
"""

import json
import difflib
from datetime import datetime, timezone
from typing import List

from backend.services.db_product_service import get_products_df
from backend.services.db_event_service import get_events_df
from backend.services.user_profile_service import get_profiles
from backend.services.db_user_manager import get_user_by_id
from backend.services.redis_client import redis_get_json, redis_setex_json
from backend.services.cache_keys import query_hash

from ml.features import build_features
from ml.model import predict_score


# ---------- CONFIG ----------

CACHE_SECONDS = 300
RANKED_CACHE_SECONDS = 120
RECENT_BOOST_CACHE_SECONDS = 30
FUZZY_MATCH_THRESHOLD = 0.7

# Recent boost: multiplicative, max 20% for most-recently-viewed item,
# decaying by 2% per position. Additive boosts can dominate ML scores when
# score magnitudes are small; a percentage multiplier is scale-invariant.
RECENT_BOOST_MAX = 0.20
RECENT_BOOST_DECAY = 0.02
CLUSTER_BOOST_WEIGHT = 0.5


# ---------- HELPERS ----------

def user_category_score(profile: dict, category: str) -> float:
    """Get user's preference score for a category (case-insensitive)."""
    if not profile:
        return 0.0
    cat_pref = profile.get("category_pref", {})
    # Strip + case-insensitive match guards against DB/intent casing drift
    target = (category or "").strip().lower()
    for k, v in cat_pref.items():
        if k.strip().lower() == target:
            return v
    return 0.0


def user_price_affinity(profile: dict, price: float) -> float:
    """Calculate price affinity based on user's average price preference."""
    if not profile:
        return 0.0
    avg_price = profile.get("avg_price")
    if avg_price is None:
        return 0.0
    denom = max(abs(avg_price), 1.0)
    return max(0.0, 1.0 - abs(price - avg_price) / denom)


def _fuzzy_match(text: str, query_words: List[str]) -> bool:
    text = text.lower()
    for w in query_words:
        if w in text:
            return True
        for token in text.split():
            if difflib.SequenceMatcher(None, w, token).ratio() >= FUZZY_MATCH_THRESHOLD:
                return True
    return False


def _get_recent_boost(user_id: str) -> dict[int, float]:
    if not user_id:
        return {}

    cache_key = f"recent_boost:{user_id}"
    cached = redis_get_json(cache_key, count_stats=False)
    if isinstance(cached, dict):
        return {int(k): v for k, v in cached.items()}

    boosts = {}
    try:
        df = get_events_df(
            user_id=user_id,
            event_types=["click", "add_to_cart"],
            limit=10,
        )
        if not df.empty:
            for i, row in enumerate(df.itertuples()):
                # Multiplicative percentage boost: 20% for rank-0, decays by 2% per rank
                boosts[int(row.product_id)] = max(0.0, RECENT_BOOST_MAX - RECENT_BOOST_DECAY * i)
    except Exception:
        pass

    # Cache with short TTL — invalidated by cache_invalidation.py on new events
    redis_setex_json(cache_key, {str(k): v for k, v in boosts.items()}, RECENT_BOOST_CACHE_SECONDS)
    return boosts


def _get_cluster_category_boost(cluster: int, profiles: dict) -> dict:
    if cluster is None:
        return {}

    counts = {}
    for profile in profiles.values():
        if profile.get("cluster") != cluster:
            continue
        for cat, v in profile.get("category_pref", {}).items():
            counts[cat] = counts.get(cat, 0) + v

    if not counts:
        return {}

    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}


def _ranked_cache_key(query: str, user_id: str, cluster, ab_group: str) -> str:
    user_key = user_id or "anon"
    cluster_key = "none" if cluster is None else str(cluster)
    return f"search_ranked:{query_hash(query)}:{ab_group}:{cluster_key}:{user_key}"


# ---------- MAIN API ----------

def search_products(
    query: str,
    user_id: str,
    cluster=None,
    ab_group="A",
    limit=None,
    category: str = None,
):
    # Cache base query candidates (non-personalized).
    # Key includes category so category-expanded results cache separately.
    cat_key = category.lower() if category else "none"
    base_cache_key = f"search_products:{query_hash(query)}:{cat_key}:base"
    ranked_cache_key = _ranked_cache_key(query, user_id, cluster, ab_group)

    cached_ranked = redis_get_json(ranked_cache_key)
    if isinstance(cached_ranked, list):
        return cached_ranked[:limit] if limit is not None else cached_ranked

    cached_products = redis_get_json(base_cache_key, count_stats=False)

    if cached_products:
        products = cached_products
    else:
        # Text search
        products_df = get_products_df(search_query=query)
        seen_ids: set[int] = set()
        products = []

        def _df_to_rows(df):
            rows = []
            for _, r in df.iterrows():
                pid = int(r.product_id)
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                rows.append({
                    "product_id": pid,
                    "title": r.title,
                    "description": r.description,
                    "price": r.price,
                    "category": r.category,
                    "rating": float(r.rating),
                    "popularity": float(r.popularity),
                    "created_at": r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
                })
            return rows

        if products_df is not None and not products_df.empty:
            products.extend(_df_to_rows(products_df))

        # Category expansion: when intent detected a category (e.g. "laptops" →
        # "Computers"), fetch ALL products in that category so results aren't
        # limited to those that literally contain the word "laptop".
        if category:
            cat_df = get_products_df(category_filter=category)
            if cat_df is not None and not cat_df.empty:
                products.extend(_df_to_rows(cat_df))

        if not products:
            return []

        redis_setex_json(base_cache_key, products, CACHE_SECONDS)

    # Get user context for personalization (happens after cache hit)
    profiles = get_profiles()
    profile = profiles.get(user_id, {})

    # --- Fuzzy text filtering ---
    # Products whose category exactly matches the intent-detected category are
    # automatically included — they are semantically relevant even if their
    # title doesn't contain the query word (e.g. "MacBook Pro" for "laptops").
    category_lower = category.lower() if category else None
    query_words = [w for w in query.lower().split() if w]
    filtered = [
        row for row in products
        if (category_lower and (row.get("category") or "").lower() == category_lower)
        or _fuzzy_match(f"{row['title']} {row['description']} {row.get('category') or ''}", query_words)
    ]

    # --- Group B: simple popularity ---
    if ab_group == "B":
        results = sorted(
            (
                {
                    "product_id": row["product_id"],
                    "title": row["title"],
                    "description": row["description"],
                    "price": row["price"],
                    "category": row["category"],
                    "rating": row["rating"],
                    "popularity": row["popularity"],
                    "score": float(row["popularity"]),
                }
                for row in filtered
            ),
            key=lambda x: x["score"],
            reverse=True,
        )

        redis_setex_json(ranked_cache_key, results, RANKED_CACHE_SECONDS)

        return results[:limit] if limit is not None else results

    # --- Group A: ML ranking ---
    recent_boost = _get_recent_boost(user_id)
    cluster_boost = _get_cluster_category_boost(cluster, profiles)

    results = []
    for r in filtered:
        cat_pref = profile.get("category_pref", {}).get(r["category"], 0)
        cl_boost = cluster_boost.get(r["category"], 0)
        # Cap combined category signal to [0, 1] — the two components share the same scale
        category_score = min(1.0, cat_pref + CLUSTER_BOOST_WEIGHT * cl_boost)

        # Convert created_at string to datetime if needed for features
        created_at = r.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        features = build_features(
            popularity=r["popularity"],
            rating=r["rating"],
            created_at=created_at,
            category_score=category_score,
            price_affinity=user_price_affinity(profile, r["price"]),
        )

        score = predict_score(features)
        # Multiplicative recent boost: scale-invariant regardless of model score magnitude
        boost_pct = recent_boost.get(int(r["product_id"]), 0)
        score *= (1.0 + boost_pct)

        results.append({
            "product_id": int(r["product_id"]),
            "title": r["title"],
            "description": r["description"],
            "price": r["price"],
            "category": r["category"],
            "rating": float(r["rating"]),
            "popularity": float(r["popularity"]),
            "score": round(score, 3),
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)
    redis_setex_json(ranked_cache_key, results, RANKED_CACHE_SECONDS)
    return results[:limit] if limit is not None else results
