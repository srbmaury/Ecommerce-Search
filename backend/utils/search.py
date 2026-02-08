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

from ml.features import build_features
from ml.model import predict_score


# ---------- CONFIG ----------

CACHE_SECONDS = 300
FUZZY_MATCH_THRESHOLD = 0.7

RECENT_BOOST_BASE = 1.0
RECENT_BOOST_DECAY = 0.15
CLUSTER_BOOST_WEIGHT = 0.5


# ---------- HELPERS ----------

def user_category_score(profile: dict, category: str) -> float:
    """Get user's preference score for a category."""
    if not profile:
        return 0.0
    return profile.get("category_pref", {}).get(category, 0.0)


def user_price_affinity(profile: dict, price: float) -> float:
    """Calculate price affinity based on user's average price preference."""
    if not profile:
        return 0.0
    avg_price = profile.get("avg_price")
    if not avg_price:
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
    boosts = {}
    try:
        df = get_events_df(
            user_id=user_id,
            event_types=["click", "add_to_cart"],
            limit=10,
        )
        if df.empty:
            return boosts

        for i, row in enumerate(df.itertuples()):
            boosts[int(row.product_id)] = (
                RECENT_BOOST_BASE - RECENT_BOOST_DECAY * i
            )
    except Exception:
        pass

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


# ---------- MAIN API ----------

def search_products(
    query: str,
    user_id: str,
    cluster=None,
    ab_group="A",
    limit=10,
):
    cache_key = f"search:{query}:{user_id}:{cluster}:{ab_group}:{limit}"
    cached = redis_get_json(cache_key)
    if cached:
        return cached

    products_df = get_products_df(search_query=query)
    if products_df is None or products_df.empty:
        return []

    profiles = get_profiles()
    profile = profiles.get(user_id, {})

    # --- Text filtering (includes category) ---
    query_words = [w for w in query.lower().split() if w]
    filtered = [
        row for _, row in products_df.iterrows()
        if _fuzzy_match(f"{row.title} {row.description} {row.category}", query_words)
    ]

    # --- Group B: simple popularity ---
    if ab_group == "B":
        results = sorted(
            (
                {
                    "product_id": int(r.product_id),
                    "title": r.title,
                    "description": r.description,
                    "price": r.price,
                    "category": r.category,
                    "rating": float(r.rating),
                    "popularity": float(r.popularity),
                    "score": float(r.popularity),
                }
                for r in filtered
            ),
            key=lambda x: x["score"],
            reverse=True,
        )[:limit]

        redis_setex_json(cache_key, CACHE_SECONDS, results)
        return results

    # --- Group A: ML ranking ---
    recent_boost = _get_recent_boost(user_id)
    cluster_boost = _get_cluster_category_boost(cluster, profiles)

    results = []
    for r in filtered:
        cat_pref = profile.get("category_pref", {}).get(r.category, 0)
        cl_boost = cluster_boost.get(r.category, 0)

        avg_price = profile.get("avg_price")
        price_affinity = 0
        if avg_price:
            denom = max(abs(avg_price), 1.0)
            price_affinity = max(0, 1 - abs(r.price - avg_price) / denom)

        features = build_features(
            popularity=r.popularity,
            rating=r.rating,
            created_at=r.created_at,
            category_score=cat_pref + CLUSTER_BOOST_WEIGHT * cl_boost,
            price_affinity=price_affinity,
        )

        score = predict_score(features)
        score += recent_boost.get(int(r.product_id), 0)

        results.append({
            "product_id": int(r.product_id),
            "title": r.title,
            "description": r.description,
            "price": r.price,
            "category": r.category,
            "rating": float(r.rating),
            "popularity": float(r.popularity),
            "score": round(score, 3),
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
    redis_setex_json(cache_key, CACHE_SECONDS, results)
    return results
