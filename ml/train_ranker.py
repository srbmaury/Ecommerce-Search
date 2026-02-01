# -*- coding: utf-8 -*-
from ml.user_profile import build_user_profiles
from ml.features import build_features
from lightgbm import LGBMRanker
import pandas as pd
import joblib
import os
from backend.utils.search import user_category_score, user_price_affinity
from backend.services.db_product_service import get_products_df
from backend.services.db_event_service import get_events_df

def validate_dataframe(df, name, required_columns):
    """
    Validate that a DataFrame is non-empty and contains all required columns.
    Exits the program with a clear message if validation fails.
    """
    if df.empty:
        print(f"{name} data is empty. Please ensure the database contains data.")
        exit(1)
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(
            f"{name} data is missing required columns: {', '.join(missing_columns)}. "
            f"Please check the database schema."
        )
        exit(1)

def main():
    print("📦 Loading data from database...")
    try:
        products = get_products_df()
        if products.empty:
            print("❌ No products found in database!")
            exit(1)
    except Exception as e:
        print(f"❌ Failed to load products: {e}")
        exit(1)

    validate_dataframe(
        products,
        name="Products",
        required_columns=[
            "product_id",
            "created_at",
            "popularity",
            "rating",
            "category",
            "price",
        ],
    )
    products["created_at"] = pd.to_datetime(products["created_at"])

    try:
        events = get_events_df()
        if events.empty:
            print("❌ No events found in database!")
            print("   Generate some events using: python scripts.generate_fake_data.py")
            exit(1)
    except Exception as e:
        print(f"❌ Failed to load events: {e}")
        exit(1)

    validate_dataframe(
        events,
        name="Events",
        required_columns=[
            "product_id",
            "user_id",
            "event",
        ],
    )

    print(f"✓ Loaded {len(products)} products and {len(events)} events")
    print("🧠 Building user profiles...")
    user_profiles = build_user_profiles()

    # Create product index for O(1) lookup
    product_index = products.set_index('product_id').to_dict('index')

    # Group by user_id for ranking
    X, y, group = [], [], []
    total_events = len(events)
    filtered_events = 0

    for user_id, user_events in events.groupby('user_id'):
        user_X, user_y = [], []
        for _, e in user_events.iterrows():
            product = product_index.get(e.product_id)
            if product is None:
                filtered_events += 1
                continue
            profile = user_profiles.get(e.user_id)

            features = build_features(
                popularity=product['popularity'],
                rating=product['rating'],
                created_at=product['created_at'],
                category_score=user_category_score(profile, product['category']),
                price_affinity=user_price_affinity(profile, product['price'])
            )

            # Event weights: click=1, add_to_cart=2
            event_weights = {"click": 1, "add_to_cart": 2}
            weight = event_weights.get(e.event, 0)

            user_X.append(features)
            user_y.append(weight)
        if user_X:
            X.extend(user_X)
            y.extend(user_y)
            group.append(len(user_X))

    # Check for empty training data
    if not X or not y or not group:
        if total_events == 0:
            print("No training data available. The events table contains no data.")
            print("Please log some search events first by using the search functionality.")
        elif filtered_events == total_events:
            print(f"No training data available. All {total_events} events were filtered out.")
            print(f"None of the product IDs in the events match products in the product table.")
            print("This may indicate a data consistency issue between products and events tables.")
        else:
            print(f"No training data available. {filtered_events}/{total_events} events were filtered out.")
            print("Please ensure events are being logged correctly.")
        exit(1)

    print(f"📊 Training ranking model with {len(X)} samples and {len(group)} groups (users)...")
    model = LGBMRanker(n_estimators=100, random_state=42)
    model.fit(X, y, group=group)

    joblib.dump(model, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking_model.pkl"))
    print("✅ Personalized ranking model trained with LightGBM Ranker (grouped by user)")

if __name__ == "__main__":
    main()