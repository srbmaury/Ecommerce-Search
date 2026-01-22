
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from utils.data_paths import get_data_path

def extract_user_features(events_path=None, products_path=None):
    if events_path is None:
        events_path = get_data_path("search_events.csv")
    if products_path is None:
        products_path = get_data_path("products.csv")
    events = pd.read_csv(events_path, dtype={"product_id": str})
    products = pd.read_csv(products_path, dtype={"product_id": str})
    merged = events.merge(products, on="product_id", how="left")
    clicks = merged[merged.event == "click"]
    user_ids = clicks["user_id"].unique()
    categories = products["category"].unique()
    features = []
    for user_id in user_ids:
        user_clicks = clicks[clicks["user_id"] == user_id]
        cat_counts = user_clicks["category"].value_counts(normalize=True).reindex(categories, fill_value=0).values
        avg_price = user_clicks["price"].mean() if not user_clicks.empty else 0
        features.append(np.concatenate([cat_counts, [avg_price]]))
    return user_ids, np.array(features), categories

def cluster_users(n_clusters=3, events_path=None, products_path=None):
    user_ids, X, categories = extract_user_features(events_path, products_path)
    if len(user_ids) < n_clusters:
        n_clusters = max(1, len(user_ids))
    if n_clusters < 2:
        return {user_ids[i]: 0 for i in range(len(user_ids))}
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    return {user_ids[i]: int(labels[i]) for i in range(len(user_ids))}
