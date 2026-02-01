import redis
import json
from sqlalchemy import desc

from backend.services.db_user_manager import load_users
from backend.services.db_event_service import get_events_df
from backend.services.user_profile_service import get_profiles
from backend.services.db_product_service import (
    get_products_by_ids,
    Product,
    get_db_session,
)
from ml.features import build_features
from ml.model import predict_score

# ---------------- CONFIG ----------------
CACHE_DURATION_SECONDS = 300
CANDIDATE_LIMIT = 200
FINAL_LIMIT = 10
MAX_PER_CATEGORY = 3

redis_client = redis.Redis(
    host="localhost", port=6379, db=0, decode_responses=True
)

# ---------------------------------------


def recommendations_controller(user_id):
    if not user_id:
        return {"error": "user_id required"}, 400

    cache_key = f"recommendations:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached), 200

    # -------- user cluster (existing API) --------
    cluster = None
    users = load_users()
    for u in users:
        if u.get("user_id") == user_id:
            cluster = u.get("cluster")
            break

    # -------- recent interactions (existing API) --------
    recent_ids = []
    try:
        events_df = get_events_df(
            user_id=user_id,
            event_types=["click", "add_to_cart"],
            limit=20,
        )
        if not events_df.empty:
            recent_ids = (
                events_df.sort_values("timestamp", ascending=False)
                .product_id.astype(int)
                .drop_duplicates()
                .tolist()[:5]
            )
    except Exception:
        recent_ids = []

    recent_products = (
        get_products_by_ids(recent_ids) if recent_ids else []
    )
    # Convert datetimes to ISO format for recent products
    for p in recent_products:
        if 'created_at' in p and hasattr(p['created_at'], 'isoformat'):
            p['created_at'] = p['created_at'].isoformat()
        if 'updated_at' in p and hasattr(p['updated_at'], 'isoformat'):
            p['updated_at'] = p['updated_at'].isoformat()

    # -------- user profile --------
    profiles = get_profiles()
    profile = profiles.get(user_id, {})

    # -------- cluster category boost (cached) --------
    cluster_category_boost = {}
    if cluster is not None:
        boost_key = f"cluster_boost:{cluster}"
        cached_boost = redis_client.get(boost_key)
        if cached_boost:
            cluster_category_boost = json.loads(cached_boost)
        else:
            cat_counts = {}
            for u in users:
                if u.get("cluster") != cluster:
                    continue
                p = profiles.get(u["user_id"])
                if not p:
                    continue
                for cat, v in p.get("category_pref", {}).items():
                    cat_counts[cat] = cat_counts.get(cat, 0) + v

            if cat_counts:
                total = sum(cat_counts.values())
                cluster_category_boost = {
                    k: v / total for k, v in cat_counts.items()
                }
                redis_client.setex(
                    boost_key, 3600, json.dumps(cluster_category_boost)
                )

    # -------- candidate generation (CRITICAL FIX) --------
    session = get_db_session()
    try:
        products = (
            session.query(Product)
            .filter(~Product.id.in_(recent_ids))
            .order_by(desc(Product.popularity))
            .limit(CANDIDATE_LIMIT)
            .all()
        )

        scored = []
        for p in products:
            cat_pref = profile.get("category_pref", {}).get(
                p.category, 0
            )
            cluster_pref = cluster_category_boost.get(p.category, 0)

            avg_price = profile.get("avg_price")
            if avg_price:
                denom = max(abs(avg_price), 1.0)
                price_affinity = max(
                    0, 1 - abs(p.price - avg_price) / denom
                )
            else:
                price_affinity = 0

            features = build_features(
                popularity=p.popularity,
                rating=p.rating,
                created_at=p.created_at,
                category_score=cat_pref + 0.5 * cluster_pref,
                price_affinity=price_affinity,
            )

            score = predict_score(features)
            scored.append((p, score))
    finally:
        session.close()

    # -------- rank + diversify --------
    scored.sort(key=lambda x: x[1], reverse=True)

    similar = []
    per_category = {}


    for product, _ in scored:
        if len(similar) >= FINAL_LIMIT:
            break

        count = per_category.get(product.category, 0)
        if count >= MAX_PER_CATEGORY:
            continue

        prod_dict = {
            "product_id": product.id,
            "title": product.title,
            "description": product.description,
            "category": product.category,
            "price": product.price,
            "rating": product.rating,
            "review_count": product.review_count,
            "popularity": product.popularity,
            "created_at": product.created_at.isoformat() if hasattr(product.created_at, 'isoformat') else product.created_at,
        }
        similar.append(prod_dict)
        per_category[product.category] = count + 1

    result = {"recent": recent_products, "similar": similar}
    redis_client.setex(cache_key, CACHE_DURATION_SECONDS, json.dumps(result))
    return result, 200