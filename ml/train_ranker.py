# -*- coding: utf-8 -*-
import sys
import os
# Add parent directory to path to allow imports from backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from user_profile import build_user_profiles
from features import build_features
from sklearn.linear_model import LogisticRegression
import pandas as pd
from utils.data_paths import get_data_path
import joblib
from backend.search import user_category_score, user_price_affinity
def validate_dataframe(df, name, required_columns):
    """
    Validate that a DataFrame is non-empty and contains all required columns.
    Exits the program with a clear message if validation fails.
    """
    if df.empty:
        print(f"{name} data is empty. Please ensure the CSV file contains data.")
        exit(1)

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(
            f"{name} data is missing required columns: {', '.join(missing_columns)}. "
            f"Please check the CSV schema."
        )
        exit(1)


try:
    products = pd.read_csv(get_data_path("products.csv"))
except FileNotFoundError:
    print("Products data file not found. Please provide the products CSV.")
    exit(1)
except pd.errors.EmptyDataError:
    print("Products data file is empty. Please ensure it contains data.")
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
    events = pd.read_csv(get_data_path("search_events.csv"))
except FileNotFoundError:
    print("Events data file not found. Please provide the events CSV.")
    exit(1)
except pd.errors.EmptyDataError:
    print("Events data file is empty. Please ensure it contains data.")
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
        print("No training data available. The events file contains no data.")
        print("Please log some search events first by using the search functionality.")
    elif filtered_events == total_events:
        print(f"No training data available. All {total_events} events were filtered out.")
        print(f"None of the product IDs in the events match products in the product index.")
        print("This may indicate a data consistency issue between products.csv and search_events.csv.")
    else:
        print(f"No training data available. {filtered_events}/{total_events} events were filtered out.")
        print("Please ensure events are being logged correctly.")
    exit(1)

model = LogisticRegression(max_iter=1000)
model.fit(X, y)

joblib.dump(model, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ranking_model.pkl"))
print("✅ Personalized model trained")
