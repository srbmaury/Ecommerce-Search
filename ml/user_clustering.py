import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from backend.services.db_event_service import get_events_df
from backend.services.db_product_service import get_products_df

def extract_user_features():
    """Extract user features from database."""
    events = get_events_df()
    products = get_products_df()
    
    if events.empty or products.empty:
        return np.array([]), np.array([]), np.array([])
    
    # Ensure product_id is string for merging
    events['product_id'] = events['product_id'].astype(str)
    products['product_id'] = products['product_id'].astype(str)
    
    merged = events.merge(products, on="product_id", how="left")
    clicks = merged[merged.event == "click"]
    
    if clicks.empty:
        return np.array([]), np.array([]), np.array([])
    
    user_ids = clicks["user_id"].unique()
    categories = products["category"].unique()
    features = []
    
    for user_id in user_ids:
        user_clicks = clicks[clicks["user_id"] == user_id]
        cat_counts = user_clicks["category"].value_counts(normalize=True).reindex(categories, fill_value=0).values
        avg_price = user_clicks["price"].mean() if not user_clicks.empty else 0
        features.append(np.concatenate([cat_counts, [avg_price]]))
    
    return user_ids, np.array(features), categories

def cluster_users(n_clusters=3):
    """Cluster users based on their behavior from database."""
    user_ids, X, categories = extract_user_features()
    
    if len(user_ids) == 0:
        return {}
    
    if len(user_ids) < n_clusters:
        n_clusters = max(1, len(user_ids))
    if n_clusters < 2:
        return {user_ids[i]: 0 for i in range(len(user_ids))}
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    return {user_ids[i]: int(labels[i]) for i in range(len(user_ids))}

def run_user_clustering(n_clusters=3):
    """Run user clustering (alias for backward compatibility)."""
    return cluster_users(n_clusters)
