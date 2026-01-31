import pandas as pd
from backend.services.db_event_service import get_events_df
from backend.services.db_product_service import get_products_df

def build_user_profiles():
    """Build user profiles from database data."""
    events = get_events_df()
    products = get_products_df()
    
    if events.empty or products.empty:
        return {}
    
    # Ensure product_id is string for merging
    events['product_id'] = events['product_id'].astype(str)
    products['product_id'] = products['product_id'].astype(str)

    merged = events.merge(products, on="product_id")

    # Include clicks and add_to_cart for preferences (weighted)
    # add_to_cart has higher weight than click
    interactions = merged[merged.event.isin(["click", "add_to_cart"])]

    profiles = {}

    for user_id, group in interactions.groupby("user_id"):
        # Weight: click=1, add_to_cart=2 for category preference
        weights = group["event"].map({"click": 1, "add_to_cart": 2}).fillna(0)

        # Weighted category preferences
        category_counts = {}
        for cat, weight in zip(group["category"], weights):
            category_counts[cat] = category_counts.get(cat, 0) + weight
        total_weight = sum(category_counts.values())
        category_pref = {k: v / total_weight for k, v in category_counts.items()} if total_weight > 0 else {}

        # Weighted average price (add_to_cart counts more)
        price_pref = (group["price"] * weights).sum() / weights.sum() if weights.sum() > 0 else group["price"].mean()

        profiles[user_id] = {
            "category_pref": category_pref,
            "avg_price": price_pref
        }

    return profiles
