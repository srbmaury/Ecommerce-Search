from flask import Blueprint, jsonify
import os
import json
import html
import collections
import pandas as pd
from utils.data_paths import get_data_path
from backend.user_manager import USERS_FILE
import logging

bp = Blueprint("analytics", __name__)
logger = logging.getLogger(__name__)

@bp.route("/analytics")
def analytics():
    if not os.path.exists(get_data_path("search_events.csv")):
        return jsonify({"error": "Analytics data not available"}), 404

    try:
        events = pd.read_csv(get_data_path("search_events.csv"))
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
            "Conversion": round(carts / searches, 3) if searches else 0
        }

    cluster_counts = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            users = json.load(f)
            cluster_counts = collections.Counter(
                u.get("cluster", -1) for u in users
            )

    top_queries = events["query"].value_counts().head(10)

    html_out = "<h2>A/B Group Analytics</h2><table border=1>"
    html_out += "<tr><th>Group</th><th>Users</th><th>Searches</th><th>Clicks</th><th>Add to Cart</th><th>CTR</th><th>Conversion</th></tr>"
    for g, s in summary.items():
        html_out += f"<tr><td>{g}</td><td>{s['users']}</td><td>{s['searches']}</td><td>{s['clicks']}</td><td>{s['add_to_cart']}</td><td>{s['CTR']}</td><td>{s['Conversion']}</td></tr>"
    html_out += "</table>"

    if cluster_counts:
        html_out += "<h2>Cluster Sizes</h2><table border=1>"
        for c, n in cluster_counts.items():
            html_out += f"<tr><td>{c}</td><td>{n}</td></tr>"
        html_out += "</table>"

    html_out += "<h2>Top Queries</h2><table border=1>"
    for q, c in top_queries.items():
        html_out += f"<tr><td>{html.escape(str(q))}</td><td>{c}</td></tr>"
    html_out += "</table>"

    return html_out
