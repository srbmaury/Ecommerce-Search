import os
import json
import requests
from sqlalchemy import desc

from backend.services.db_event_service import get_events_df
from backend.services.user_profile_service import get_profiles
from backend.services.db_product_service import get_products_by_ids
from backend.models import Product
from backend.services.db_user_manager import get_user_by_id
from backend.utils.database import get_db_session

from ml.features import build_features
from ml.model import predict_score


# ---------- CONFIG ----------

CACHE_DURATION_SECONDS = 300
CANDIDATE_LIMIT = 200
FINAL_LIMIT = 10
MAX_PER_CATEGORY = 3

EVENT_TYPES = ("click", "add_to_cart")

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")


# ---------- REDIS HELPERS ----------

def redis_enabled():
    return bool(UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)


def redis_get(key):
    if not redis_enabled():
        return None
    try:
        resp = requests.get(
            f"{UPSTASH_REDIS_REST_URL}/get/{key}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"},
            timeout=2,
        )
        if resp.status_code == 200:
            return resp.json().get("result")
    except Exception:
        pass
    return None


def redis_setex(key, seconds, value):
    if not redis_enabled():
        return
    try:
        requests.post(
            f"{UPSTASH_REDIS_REST_URL}/setex/{key}/{seconds}",
            headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"},
            data=value,
            timeout=2,
        )
    except Exception:
        pass


# ---------- HELPERS ----------

def serialize_product_dates(products):
    for p in products:
        for field in ("created_at", "updated_at"):
            if field in p and hasattr(p[field], "isoformat"):
                p[field] = p[field].isoformat()


def get_recent_product_ids(user_id, limit=5):
    try:
        print(f"DEBUG get_recent_product_ids: user_id={user_id}, event_types={EVENT_TYPES}")
        df = get_events_df(
            user_id=user_id,
            event_types=EVENT_TYPES,
            limit=20,
        )
        print(f"DEBUG get_recent_product_ids: df.empty={df.empty}, df.shape={df.shape if not df.empty else 'N/A'}")
        if not df.empty:
            print(f"DEBUG get_recent_product_ids: df.columns={list(df.columns)}")
            print(f"DEBUG get_recent_product_ids: df.head()=\n{df.head()}")
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
        print(f"DEBUG get_recent_product_ids: EXCEPTION {e}")
        return []


def get_cluster_category_boost(cluster, profiles):
    if cluster is None:
        return {}

    boost_key = f"cluster_boost:{cluster}"
    cached = redis_get(boost_key)
    if cached:
        return json.loads(cached)

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
    redis_setex(boost_key, 3600, json.dumps(boost))
    return boost


# ---------- CONTROLLER ----------

def recommendations_controller(user_id):
    if not user_id:
        return {"error": "user_id required"}, 400

    cache_key = f"recommendations:{user_id}"
    cached = redis_get(cache_key)
    if cached:
        return json.loads(cached), 200

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
    session = get_db_session()
    try:
        candidates = (
            session.query(Product)
            .filter(~Product.id.in_(recent_ids))
            .order_by(desc(Product.popularity))
            .limit(CANDIDATE_LIMIT)
            .all()
        )

        scored = []
        avg_price = profile.get("avg_price")

        for p in candidates:
            cat_pref = profile.get("category_pref", {}).get(p.category, 0)
            cluster_pref = cluster_boost.get(p.category, 0)

            price_affinity = 0.0
            if avg_price:
                denom = max(abs(avg_price), 1.0)
                price_affinity = max(
                    0.0, 1.0 - abs(p.price - avg_price) / denom
                )

            features = build_features(
                popularity=p.popularity,
                rating=p.rating,
                created_at=p.created_at,
                category_score=cat_pref + 0.5 * cluster_pref,
                price_affinity=price_affinity,
            )

            scored.append((p, predict_score(features)))
    finally:
        session.close()

    # ---- rank + diversify ----
    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    per_category = {}

    for product, _ in scored:
        if len(results) >= FINAL_LIMIT:
            break

        if per_category.get(product.category, 0) >= MAX_PER_CATEGORY:
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

    print(f"DEBUG: user_id={user_id}, recent_ids={recent_ids}, recent_products_count={len(recent_products)}")
    result = {
        "recent": recent_products,
        "similar": results,
    }

    redis_setex(cache_key, CACHE_DURATION_SECONDS, json.dumps(result))
    return result, 200
