# -*- coding: utf-8 -*-
import sys
import os
# Add parent directory to path to allow imports from backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_profile import build_user_profiles
from features import build_features
from sklearn.linear_model import LogisticRegression
import pandas as pd
import joblib
from backend.search import user_category_score, user_price_affinity
from backend.db_product_service import get_products_df
from backend.db_event_service import get_events_df


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


print("📦 Loading data from database...")
try:
    products = get_products_df()
    if products.empty:
        print("❌ No products found in database!")
        print("   Run 'python migrate_to_db.py' first to load products.")
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
        print("   Generate some events using: python ml/generate_fake_data.py")
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

X, y = [], []
total_events = len(events)
filtered_events = 0

for _, e in events.iterrows():
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

    X.append(features)
    y.append(weight)


# Check for empty training data
if not X or not y:
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

print(f"📊 Training model with {len(X)} samples...")
model = LogisticRegression(max_iter=1000)
model.fit(X, y)

joblib.dump(model, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking_model.pkl"))
print("✅ Personalized model trained")
