import os
import json
import collections
import pandas as pd
from flask import jsonify
from utils.data_paths import get_data_path
from backend.user_manager import USERS_FILE
from backend.services.analytics_html import build_html


def get_analytics_data():
    analytics_path = get_data_path("search_events.csv")

    if not os.path.exists(analytics_path):
        return jsonify({"error": "Analytics data not available"}), 404

    try:
        events = pd.read_csv(analytics_path)
    except Exception:
        return jsonify({"error": "Failed to read analytics data"}), 500

    summary = {}
    for group in events["group"].unique():
        gdf = events[events["group"] == group]
        searches = gdf["query"].notnull().sum()
        clicks = (gdf["event"] == "click").sum()
        carts = (gdf["event"] == "add_to_cart").sum()
        users = gdf["user_id"].nunique()

        summary[group] = {
            "users": users,
            "searches": searches,
            "clicks": clicks,
            "add_to_cart": carts,
            "CTR": round(clicks / searches, 3) if searches else 0,
            "Conversion": round(carts / searches, 3) if searches else 0,
        }

    cluster_counts = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            users = json.load(f)
            cluster_counts = collections.Counter(
                u.get("cluster", -1) for u in users
            )

    top_queries = events["query"].value_counts().head(10)

    return build_html(summary, cluster_counts, top_queries)
