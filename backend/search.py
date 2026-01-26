
import pandas as pd
from datetime import datetime, timezone
from ml.user_profile import build_user_profiles
from ml.features import build_features
from ml.model import predict_score
from ml.vectorizer import build_vectorizer
from backend.db_user_manager import load_users
from backend.db_product_service import get_products_df
from backend.db_event_service import get_events_df
import difflib
import json

# Fuzzy matching threshold for search queries
# A value of 0.7 means tokens must be at least 70% similar to match.
# This balances between being too strict (missing relevant results) and 
# too lenient (including irrelevant results). Empirically, 0.7 provides
# good results for common typos while filtering out unrelated terms.
FUZZY_MATCH_THRESHOLD = 0.7

# Recent product interaction boost constants
# These control the decay formula for boosting products the user recently interacted with.
# The boost is calculated as: RECENT_BOOST_BASE - RECENT_BOOST_DECAY * position
# where position is 0 for the most recent interaction, 1 for second most recent, etc.
# This creates a linear decay: most recent gets 1.0, second gets 0.85, third gets 0.70, etc.
# The decay rate of 0.15 ensures older interactions still provide meaningful boost while
# prioritizing the most recent user behavior in search rankings.
RECENT_BOOST_BASE = 1.0
RECENT_BOOST_DECAY = 0.15
CLUSTER_BOOST_WEIGHT = 0.5

# Global cache for products and vectorizer
products = None
vectorizer = None
tfidf_matrix = None
products_cache_time = None
CACHE_DURATION_SECONDS = 300  # 5 minutes


def _load_products():
    """Lazy load products and build vectorizer with time-based cache invalidation."""
    global products, vectorizer, tfidf_matrix, products_cache_time
    current_time = datetime.now(timezone.utc)
    
    # Reload if:
    # 1. Products have never been loaded
    # 2. Cache has expired (more than CACHE_DURATION_SECONDS old)
    needs_reload = (
        products is None or 
        products_cache_time is None or
        (current_time - products_cache_time).total_seconds() > CACHE_DURATION_SECONDS
    )
    
    if needs_reload:
        products = get_products_df()
        products_cache_time = current_time
        if not products.empty:
            products["created_at"] = pd.to_datetime(products["created_at"])
            texts = (products["title"] + " " + products["description"]).tolist()
            vectorizer, tfidf_matrix = build_vectorizer(texts)
    return products, vectorizer, tfidf_matrix

def user_category_score(profile, category):
    if profile and "category_pref" in profile:
        return profile["category_pref"].get(category, 0)
    return 0

def user_price_affinity(profile, price):
    if profile and "avg_price" in profile:
        # Score is higher if price is close to user's avg_price
        avg_price = profile["avg_price"]
        # Use a robust denominator to avoid division by (near) zero and huge values
        safe_denominator = max(abs(avg_price), 1.0)
        relative_diff = abs(price - avg_price) / safe_denominator
        score = 1.0 - relative_diff
        # Clamp to [0.0, 1.0] to avoid distortions
        return max(0.0, min(1.0, score))
    return 0

PROFILE_REFRESH_SECONDS = 300  # how often to refresh user profiles from source data
_user_profiles = None
_user_profiles_last_refresh = None

def get_user_profile(user_id):
    """
    Return the profile for the given user, refreshing the cached profiles
    periodically so that new behavior is reflected in search rankings.
    """
    global _user_profiles, _user_profiles_last_refresh

    now = datetime.now(timezone.utc)
    if (
        _user_profiles is None
        or _user_profiles_last_refresh is None
        or (now - _user_profiles_last_refresh).total_seconds() > PROFILE_REFRESH_SECONDS
    ):
        _user_profiles = build_user_profiles()
        _user_profiles_last_refresh = now

    if _user_profiles is None:
        return None

    return _user_profiles.get(user_id)

def search_by_category(category, user_id, cluster=None, ab_group="A", limit=50):
    """Search products by category when fuzzy search returns no results"""
    products_df, _, _ = _load_products()
    if products_df is None or products_df.empty:
        return []
    
    profile = get_user_profile(user_id)

    filtered_products = [row for _, row in products_df.iterrows() if row.category == category]

    if ab_group == "B":
        return sorted([
            {
                "product_id": int(row.product_id),
                "title": row.title,
                "price": row.price,
                "category": row.category,
                "rating": float(row.rating),
                "popularity": int(row.popularity),
                "description": row.description,
                "score": float(row.popularity)
            }
            for row in filtered_products
        ], key=lambda x: x["score"], reverse=True)[:limit]

    results = []
    for row in filtered_products:
        base_cat_score = user_category_score(profile, row.category)
        features = build_features(
            popularity=row.popularity,
            rating=row.rating,
            created_at=row.created_at,
            category_score=base_cat_score,
            price_affinity=user_price_affinity(profile, row.price)
        )
        score = predict_score(features)
        results.append({
            "product_id": int(row.product_id),
            "title": row.title,
            "price": row.price,
            "category": row.category,
            "rating": float(row.rating),
            "popularity": int(row.popularity),
            "description": row.description,
            "score": round(score, 3)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]


def search_products(query, user_id, cluster=None, ab_group="A", limit=10):
    products_df, _, _ = _load_products()
    if products_df is None or products_df.empty:
        return []
    
    profile = get_user_profile(user_id)

    # --- Filter products by fuzzy query match ---
    query_words = [w.lower() for w in query.strip().split() if w]
    def fuzzy_match(text, words, threshold=FUZZY_MATCH_THRESHOLD):
        text = text.lower()
        for w in words:
            if w in text:
                return True
            for token in text.split():
                if difflib.SequenceMatcher(None, w, token).ratio() >= threshold:
                    return True
        return False

    filtered_products = [row for _, row in products_df.iterrows()
        if fuzzy_match(str(row.title) + ' ' + str(row.description), query_words)]

    # --- A/B testing logic ---
    if ab_group == "B":
        # Group B: default sort (by popularity), no ML, no cluster, no recent boost
        return sorted([
            {
                "product_id": int(row.product_id),
                "title": row.title,
                "price": row.price,
                "category": row.category,
                "rating": float(row.rating),
                "score": float(row.popularity)
            }
            for row in filtered_products
        ], key=lambda x: x["score"], reverse=True)[:limit]

    # Group A: ML ranking + cluster + recent boost
    # Optionally: load cluster preferences (e.g., top categories for the cluster)
    cluster_category_boost = {}
    if cluster is not None:
        try:
            users = load_users()
            cluster_users = [u["user_id"] for u in users if u.get("cluster") == cluster]
            cat_counts = {}
            for uid in cluster_users:
                p = _user_profiles.get(uid) if _user_profiles else None
                if p and "category_pref" in p:
                    for cat, v in p["category_pref"].items():
                        cat_counts[cat] = cat_counts.get(cat, 0) + v
            if cat_counts:
                total = sum(cat_counts.values())
                cluster_category_boost = {cat: v/total for cat, v in cat_counts.items()}
        except (FileNotFoundError, IOError, json.JSONDecodeError, ValueError, KeyError):
            # Silently ignore errors when loading cluster preferences - cluster boost is optional
            # and search should continue with default behavior if unavailable
            pass

    # --- Get user's most recent product interactions ---
    recent_boost = {}
    try:
        events = get_events_df()
        if not events.empty:
            user_events = events[events.user_id == user_id]
            user_events = user_events[user_events.event.isin(["click", "add_to_cart"])]
            user_events = user_events.sort_values("timestamp", ascending=False)
            for i, row in enumerate(user_events.head(5).itertuples()):
                pid = int(row.product_id)
                recent_boost[pid] = RECENT_BOOST_BASE - RECENT_BOOST_DECAY * i
    except Exception:
        # Silently ignore errors when loading recent user interactions - recent boost is optional
        # and search should continue with default ranking if user history is unavailable
        pass

    results = []
    for row in filtered_products:
        base_cat_score = user_category_score(profile, row.category)
        # Add cluster boost
        cluster_boost = cluster_category_boost.get(row.category, 0)
        features = build_features(
            popularity=row.popularity,
            rating=row.rating,
            created_at=row.created_at,
            category_score=base_cat_score + CLUSTER_BOOST_WEIGHT * cluster_boost,
            price_affinity=user_price_affinity(profile, row.price)
        )

        score = predict_score(features)
        # Boost for recent usage
        boost = recent_boost.get(int(row.product_id), 0)
        final_score = score + boost

        results.append({
            "product_id": int(row.product_id),
            "title": row.title,
            "price": row.price,
            "category": row.category,
            "rating": float(row.rating),
            "score": round(final_score, 3)
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
