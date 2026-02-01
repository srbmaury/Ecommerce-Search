import os
import json
import collections
import pandas as pd
import numpy as np
from flask import jsonify
from backend.services.db_event_service import get_events_df
from backend.services.db_user_manager import get_db_session
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


# New: API endpoint for JSON analytics data
def get_analytics_json():
    try:
        events = get_events_df()
        if events.empty:
            return jsonify({"error": "Analytics data not available"}), 404
    except Exception:
        return jsonify({"error": "Failed to read analytics data"}), 500

    summary = {}
    for group in events["group"].unique():
        gdf = events[events["group"] == group]
        searches = int(gdf["query"].notnull().sum())
        clicks = int((gdf["event"] == "click").sum())
        carts = int((gdf["event"] == "add_to_cart").sum())
        users = int(gdf["user_id"].nunique())

        summary[group] = {
            "users": users,
            "searches": searches,
            "clicks": clicks,
            "add_to_cart": carts,
            "CTR": float(round(clicks / searches, 3)) if searches else 0.0,
            "Conversion": float(round(carts / searches, 3)) if searches else 0.0,
        }

    session = get_db_session()
    try:
        users = session.query(User).all()
        cluster_counts = collections.Counter(
            int(u.cluster) if u.cluster is not None else -1 for u in users
        )
    finally:
        session.close()

    # Convert top_queries index and values to native Python types
    top_queries_series = events["query"].value_counts().head(10)
    top_queries = {str(k): int(v) for k, v in top_queries_series.items()}

    # Convert cluster_counts keys to str for JSON
    cluster_counts_json = {str(k): int(v) for k, v in dict(cluster_counts).items()}

    return jsonify({
        "summary": summary,
        "cluster_counts": cluster_counts_json,
        "top_queries": top_queries,
    })
