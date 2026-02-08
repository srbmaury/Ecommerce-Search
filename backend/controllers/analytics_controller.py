import logging
import collections
import pandas as pd
from flask import jsonify
from sqlalchemy import func

from backend.services.db_event_service import get_events_df
from backend.utils.database import get_db_session
from backend.models import User

logger = logging.getLogger("analytics_debug")

EVENT_CLICK = "click"
EVENT_CART = "add_to_cart"

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
        logger.info(f"Cluster counts: {cluster_counts}")
    except Exception as e:
        logger.exception(f"Error in get_cluster_counts: {e}")
        raise

    try:
        top_queries = events["query"].value_counts().head(10)
        logger.info(f"Top queries: {top_queries}")
    except Exception as e:
        logger.exception(f"Error in top_queries: {e}")
        raise

    return summary, cluster_counts, top_queries
    
def get_cluster_counts():
    session = get_db_session()
    try:
        rows = (
            session.query(
                func.coalesce(User.cluster, -1),
                func.count(),
            )
            .group_by(User.cluster)
            .all()
        )
        return collections.Counter({int(cluster): int(count) for cluster, count in rows})
    finally:
        session.close()


# ---------- Analytics Computation ----------

    summary = {}
    grouped = events.groupby("group")
    for group, gdf in grouped:
        try:
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
            logger.exception(f"Error processing group {group}: {e}")
            raise

    try:
        cluster_counts = get_cluster_counts()
        logger.info(f"Cluster counts: {cluster_counts}")
    except Exception as e:
        logger.exception(f"Error in get_cluster_counts: {e}")
        raise

    try:
        top_queries = events["query"].value_counts().head(10)
        logger.info(f"Top queries: {top_queries}")
    except Exception as e:
        logger.exception(f"Error in top_queries: {e}")
        raise

    return summary, cluster_counts, top_queries


# ---------- HTML ENDPOINT ----------

def get_analytics_data():
    try:
        summary, cluster_counts, top_queries = _compute_analytics()
        if summary is None:
            return jsonify({"error": "Analytics data not available"}), 404
    except Exception:
        return jsonify({"error": "Failed to read analytics data"}), 500

    return build_html(summary, cluster_counts, top_queries)

    return summary


def get_top_queries(events, limit=10):
    return {
        str(query): int(count)
        for query, count in events["query"].value_counts().head(limit).items()
    }


# ---------- API Endpoints ----------

def get_analytics_json():
    try:
        summary, cluster_counts, top_queries = _compute_analytics()
        if summary is None:
            return jsonify({"error": "Analytics data not available"}), 404
    except Exception:
        return jsonify({"error": "Failed to read analytics data"}), 500

    return jsonify({
        "summary": summary,
        "cluster_counts": {
            str(k): int(v) for k, v in cluster_counts.items()
        },
        "top_queries": {
            str(k): int(v) for k, v in top_queries.items()
        },
    })
