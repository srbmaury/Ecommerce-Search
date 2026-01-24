import pandas as pd
from utils.data_paths import get_data_path

def build_user_profiles(events_path=None,
                        products_path=None):
    if events_path is None:
        events_path = get_data_path("search_events.csv")
    if products_path is None:
        products_path = get_data_path("products.csv")
    events = pd.read_csv(events_path, dtype={"product_id": str})
    products = pd.read_csv(products_path, dtype={"product_id": str})

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
