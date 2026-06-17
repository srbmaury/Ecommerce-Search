"""
Cache management routes.

Provides admin endpoints for:
- Viewing cache statistics
- Manual cache invalidation
- Cache maintenance operations

All endpoints require X-User-ID (must be in ADMIN_USER_IDS).
"""

from flask import Blueprint, jsonify, g

from backend.services.cache_invalidation import (
    get_cache_stats,
    reset_cache_stats,
    invalidate_all_search_caches,
    invalidate_all_recommendation_caches,
    invalidate_user_recommendations,
)
from backend.utils.admin_auth import require_admin

bp = Blueprint("cache", __name__, url_prefix="/api/admin/cache")


@bp.route("/dashboard", methods=["GET"])
@require_admin
def cache_dashboard():
    """Get admin dashboard data (user info + cache stats)."""
    user = g.admin_user
    stats = get_cache_stats()
    stats["hit_rate"] = round(stats["hit_rate"], 4)

    return jsonify({
        "admin": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
        },
        "cache": stats
    }), 200


@bp.route("/stats", methods=["GET"])
@require_admin
def cache_stats():
    """Get cache statistics."""
    stats = get_cache_stats()
    stats["hit_rate"] = round(stats["hit_rate"], 4)
    return jsonify(stats), 200


@bp.route("/reset-stats", methods=["POST"])
@require_admin
def reset_stats():
    """Reset cache statistics counters."""
    reset_cache_stats()
    return jsonify({"status": "stats reset"}), 200


@bp.route("/invalidate/user/<user_id>", methods=["POST"])
@require_admin
def invalidate_user(user_id):
    """Invalidate cache for specific user."""
    invalidate_user_recommendations(user_id)
    return jsonify({"status": f"invalidated user {user_id}"}), 200


@bp.route("/invalidate/all-search", methods=["POST"])
@require_admin
def invalidate_search():
    """Invalidate all search caches."""
    deleted = invalidate_all_search_caches()
    return jsonify({"status": f"invalidated {deleted} search keys"}), 200


@bp.route("/invalidate/all-recommendations", methods=["POST"])
@require_admin
def invalidate_recommendations():
    """Invalidate all recommendation caches."""
    deleted = invalidate_all_recommendation_caches()
    return jsonify({"status": f"invalidated {deleted} recommendation keys"}), 200


@bp.route("/invalidate/all", methods=["POST"])
@require_admin
def invalidate_all():
    """Invalidate ALL caches (use sparingly)."""
    search_deleted = invalidate_all_search_caches()
    recs_deleted = invalidate_all_recommendation_caches()
    total = search_deleted + recs_deleted
    return jsonify({"status": f"invalidated {total} total keys"}), 200
