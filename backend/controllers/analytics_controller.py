import os
import json
import collections
import pandas as pd
from flask import jsonify
from backend.db_event_service import get_events_df
from backend.db_user_manager import get_db_session
from backend.models import User
from backend.services.analytics_html import build_html


def get_analytics_data():
    try:
        events = get_events_df()
        if events.empty:
            return jsonify({"error": "Analytics data not available"}), 404
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

    # Get cluster counts from database
    session = get_db_session()
    try:
        users = session.query(User).all()
        cluster_counts = collections.Counter(
            u.cluster if u.cluster is not None else -1 for u in users
        )
    finally:
        session.close()

    top_queries = events["query"].value_counts().head(10)

    return build_html(summary, cluster_counts, top_queries)
