import pandas as pd
from backend.services.db_user_manager import load_users
from backend.services.db_event_service import get_events_df
from backend.services.utils import get_products_cached
from backend.services.user_profile_service import get_profiles
from ml.features import build_features
from ml.model import predict_score


def recommendations_controller(user_id):
    if not user_id:
        return {"error": "user_id required"}, 400

    # Get products
    products_df = get_products_cached()
    if products_df is None or products_df.empty:
        return {"recent": [], "similar": []}, 200

    # ---- user cluster ----
    cluster = None
    users = []
    try:
        users = load_users()
        u = next((u for u in users if u["user_id"] == user_id), None)
        if u:
            cluster = u.get("cluster")
    except Exception:
        pass

    # ---- recent interactions ----
    try:
        events = get_events_df()

        user_events = events[
            (events.user_id == str(user_id)) &
            (events.event.isin(["click", "add_to_cart"]))
        ].sort_values("timestamp", ascending=False)

        recent_ids = (
            user_events.product_id.astype(int).unique()[:5].tolist()
            if not user_events.empty else []
        )
    except Exception:
        recent_ids = []

    if not recent_ids:
        return {"recent": [], "similar": []}, 200

    recent = products_df[products_df.product_id.isin(recent_ids)].to_dict("records")

    # ---- profiles ----
    profiles = get_profiles()
    profile = profiles.get(user_id, {})

    # ---- cluster category boost ----
    cluster_category_boost = {}
    if cluster is not None:
        try:
            cat_counts = {}
            cluster_users = [u["user_id"] for u in users if u.get("cluster") == cluster]
            for uid in cluster_users:
                p = profiles.get(uid)
                if p and "category_pref" in p:
                    for cat, v in p["category_pref"].items():
                        cat_counts[cat] = cat_counts.get(cat, 0) + v

            if cat_counts:
                total = sum(cat_counts.values())
                cluster_category_boost = {
                    cat: v / total for cat, v in cat_counts.items()
                }
        except Exception:
            pass

    # ---- scoring ----
    seen = set(recent_ids)
    candidates = []

    for _, row in products_df.iterrows():
        pid = int(row.product_id)
        if pid in seen:
            continue

        cat_score = profile.get("category_pref", {}).get(row.category, 0)
        cluster_boost = cluster_category_boost.get(row.category, 0)

        price_affinity = 0
        if profile.get("avg_price"):
            avg_price = profile["avg_price"]
            safe_denom = max(abs(avg_price), 1.0)
            price_affinity = max(0, 1 - abs(row.price - avg_price) / safe_denom)

        features = build_features(
            popularity=row.popularity,
            rating=row.rating,
            created_at=row.created_at,
            category_score=cat_score + 0.5 * cluster_boost,
            price_affinity=price_affinity
        )

        score = predict_score(features)

        candidates.append({
            "product": row.to_dict(),
            "score": score,
            "category": row.category
        })

    # ---- rank + diversify (interleave categories) ----
    candidates.sort(key=lambda x: x["score"], reverse=True)

    similar = []
    seen_categories = {}  # total count per category

    # Group candidates by category, maintaining score order within each
    by_category = {}
    for c in candidates:
        cat = c["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    # Interleave: pick one from each category in rounds
    while len(similar) < 10 and by_category:
        cats_to_remove = []
        for cat in list(by_category.keys()):
            if len(similar) >= 10:
                break
            if seen_categories.get(cat, 0) >= 3:
                cats_to_remove.append(cat)
                continue
            if by_category[cat]:
                c = by_category[cat].pop(0)
                similar.append(c["product"])
                seen_categories[cat] = seen_categories.get(cat, 0) + 1
            if not by_category[cat]:
                cats_to_remove.append(cat)
        for cat in cats_to_remove:
            by_category.pop(cat, None)

    return {"recent": recent, "similar": similar}, 200
