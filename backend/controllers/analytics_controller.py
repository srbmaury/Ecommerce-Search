import logging
import collections
import pandas as pd
from flask import jsonify
from sqlalchemy import func

from backend.services.db_event_service import get_events_df
from backend.utils.database import get_db_session
from backend.services.redis_client import redis_get_json, redis_setex_json
from backend.models import User


logger = logging.getLogger("analytics_debug")

EVENT_CLICK = "click"
EVENT_CART = "add_to_cart"
ANALYTICS_CACHE_KEY = "analytics:summary"
ANALYTICS_CACHE_TTL = 60  # seconds


# ---------- CORE COMPUTATION ----------

def _compute_analytics():
    events = get_events_df()
    if events.empty:
        logger.warning("No events found in database.")
        return None, None, None

    summary = {}
    try:
        grouped = events.groupby("group")
        for group, gdf in grouped:
            searches = gdf["query"].notna().sum()
            clicks = (gdf["event"] == EVENT_CLICK).sum()
            carts = (gdf["event"] == EVENT_CART).sum()
            summary[group] = {
                "users": int(gdf["user_id"].nunique()),
                "searches": int(searches),
                "clicks": int(clicks),
                "add_to_cart": int(carts),
                "CTR": round(clicks / searches, 3) if searches else 0.0,
                "Conversion": round(carts / searches, 3) if searches else 0.0,
            }
    except Exception as e:
        logger.exception(f"Error during analytics computation: {e}")
        raise

    try:
        cluster_counts = get_cluster_counts()
    except Exception as e:
        logger.exception(f"Error in get_cluster_counts: {e}")
        raise

    try:
        top_queries = events["query"].value_counts().head(10)
    except Exception as e:
        logger.exception(f"Error in top_queries: {e}")
        raise

    return summary, cluster_counts, top_queries


def get_cluster_counts():
    with get_db_session() as session:
        rows = (
            session.query(
                func.coalesce(User.cluster, -1),
                func.count(),
            )
            .group_by(User.cluster)
            .all()
        )
        return collections.Counter({int(cluster): int(count) for cluster, count in rows})


# ---------- API Endpoint ----------

def get_analytics_json():
    cached = redis_get_json(ANALYTICS_CACHE_KEY)
    if cached:
        return jsonify(cached)

    try:
        summary, cluster_counts, top_queries = _compute_analytics()
        if summary is None:
            return jsonify({"error": "Analytics data not available"}), 404
    except Exception:
        return jsonify({"error": "Failed to read analytics data"}), 500

    result = {
        "summary": summary,
        "cluster_counts": {str(k): int(v) for k, v in cluster_counts.items()},
        "top_queries": {str(k): int(v) for k, v in top_queries.items()},
    }
    redis_setex_json(ANALYTICS_CACHE_KEY, result, ANALYTICS_CACHE_TTL)
    return jsonify(result)
