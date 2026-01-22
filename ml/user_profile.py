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

    # Only clicks matter for preference
    clicks = merged[merged.event == "click"]

    profiles = {}

    for user_id, group in clicks.groupby("user_id"):
        category_pref = group["category"].value_counts(normalize=True).to_dict()
        price_pref = group["price"].mean()

        profiles[user_id] = {
            "category_pref": category_pref,
            "avg_price": price_pref
        }

    return profiles
