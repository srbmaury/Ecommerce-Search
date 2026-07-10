import json
from sqlalchemy import desc

from backend.services.db_event_service import get_events_df
from backend.services.user_profile_service import get_profiles
from backend.services.db_product_service import get_products_by_ids
from backend.models import Product
from backend.services.db_user_manager import get_user_by_id
from backend.services.redis_client import redis_get_json, redis_setex_json
from backend.utils.database import get_db_session

from ml.features import build_features
from ml.model import predict_score


# ---------- CONFIG ----------

CACHE_DURATION_SECONDS = 300
FINAL_LIMIT = 10
DEFAULT_RECS_LIMIT = 10
MAX_RECS_LIMIT = 50
# Candidate pool: up to 500 products ranked; never exceeds actual catalogue size.
_CANDIDATE_MAX = 500

EVENT_TYPES = ("click", "add_to_cart")


# ---------- HELPERS ----------

def serialize_product_dates(products):
    for p in products:
        for field in ("created_at", "updated_at"):
            if field in p and hasattr(p[field], "isoformat"):
                p[field] = p[field].isoformat()


def get_recent_product_ids(user_id, limit=5):
    try:
        df = get_events_df(
            user_id=user_id,
            event_types=EVENT_TYPES,
            limit=20,
        )
        if df.empty:
            return []

        return (
            df.sort_values("timestamp", ascending=False)
            .product_id.dropna()
            .astype(int)
            .drop_duplicates()
            .tolist()[:limit]
        )
    except Exception as e:
        return []


def get_cluster_category_boost(cluster, profiles):
    if cluster is None:
        return {}

    boost_key = f"cluster_boost:{cluster}"
    cached = redis_get_json(boost_key, count_stats=False)
    if cached:
        return cached

    cat_counts = {}
    for profile in profiles.values():
        if profile.get("cluster") != cluster:
            continue
        for cat, weight in profile.get("category_pref", {}).items():
            cat_counts[cat] = cat_counts.get(cat, 0) + weight

    if not cat_counts:
        return {}

    total = sum(cat_counts.values())
    boost = {k: v / total for k, v in cat_counts.items()}
    redis_setex_json(boost_key, boost, 3600)
    return boost


# ---------- CONTROLLER ----------

def recommendations_controller(user_id, limit=None):
    if not user_id:
        return {"error": "user_id required"}, 400

    try:
        limit = int(limit) if limit is not None else DEFAULT_RECS_LIMIT
        limit = max(1, min(limit, MAX_RECS_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_RECS_LIMIT

    cache_key = f"recommendations:{user_id}"
    cached = redis_get_json(cache_key)
    if cached:
        return cached, 200

    # ---- user context ----
    user = get_user_by_id(user_id)
    cluster = getattr(user, "cluster", None) if user else None

    profiles = get_profiles()
    profile = profiles.get(user_id, {})

    # ---- recent products ----
    recent_ids = get_recent_product_ids(user_id)
    recent_products = get_products_by_ids(recent_ids) if recent_ids else []
    serialize_product_dates(recent_products)

    # ---- cluster boost ----
    cluster_boost = get_cluster_category_boost(cluster, profiles)

    # ---- candidate generation ----
    avg_price = profile.get("avg_price")
    cat_pref_map = profile.get("category_pref", {})
    recent_set = set(recent_ids)
    scored = []

    with get_db_session() as session:
        total_products = session.query(Product.id).count()
        candidate_limit = min(_CANDIDATE_MAX, total_products)

        candidates = (
            session.query(Product)
            .order_by(desc(Product.popularity))
            .limit(candidate_limit)
            .all()
        )

        for p in candidates:
            cat_pref = cat_pref_map.get(p.category, 0)
            cluster_pref = cluster_boost.get(p.category, 0)
            category_score = min(1.0, cat_pref + 0.5 * cluster_pref)

            price_affinity = 0.0
            if avg_price:
                denom = max(abs(avg_price), 1.0)
                price_affinity = max(0.0, 1.0 - abs(p.price - avg_price) / denom)

            features = build_features(
                popularity=p.popularity,
                rating=p.rating,
                created_at=p.created_at,
                category_score=category_score,
                price_affinity=price_affinity,
            )

            base_score = predict_score(features)
            if p.id in recent_set:
                base_score *= 0.5

            scored.append((p, base_score))

    # ---- rank + diversify ----
    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    per_category: dict[str, int] = {}

    for product, _ in scored:
        if len(results) >= limit:
            break

        # Per-category quota scales with user's stated preference:
        # strong preference (>30%) → up to 5 slots; moderate → 3; cold-start → 2.
        pref_weight = cat_pref_map.get(product.category, 0)
        if pref_weight > 0.3:
            quota = min(5, FINAL_LIMIT // 2)
        elif pref_weight > 0.1:
            quota = 3
        else:
            quota = 2

        if per_category.get(product.category, 0) >= quota:
            continue

        results.append({
            "product_id": product.id,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "price": product.price,
            "rating": product.rating,
            "review_count": product.review_count,
            "popularity": product.popularity,
            "created_at": product.created_at.isoformat(),
        })
        per_category[product.category] = per_category.get(product.category, 0) + 1

    result = {
        "recent": recent_products,
        "similar": results,
    }

    redis_setex_json(cache_key, result, CACHE_DURATION_SECONDS)
    return result, 200
