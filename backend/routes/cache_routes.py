"""
Cache management routes.

Provides admin endpoints for:
- Viewing cache statistics
- Manual cache invalidation
- Cache maintenance operations

All endpoints require admin user email (from ADMIN_EMAILS env var).
Users authenticate by passing X-User-ID header with their user_id.
"""

import os
from functools import wraps
from flask import Blueprint, jsonify, request, g

from backend.services.cache_invalidation import (
    get_cache_stats,
    get_cache_hit_rate,
    reset_cache_stats,
    invalidate_all_search_caches,
    invalidate_all_recommendation_caches,
    invalidate_user_recommendations,
)
from backend.services.db_user_manager import get_user_by_id

bp = Blueprint("cache", __name__, url_prefix="/api/admin/cache")

# Admin email whitelist (comma-separated env var)
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").lower().split(",")
ADMIN_EMAILS = [email.strip() for email in ADMIN_EMAILS if email.strip()]

# Shared secret API key required for all admin cache routes
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


def require_admin(f):
    """Decorator: Require authenticated admin user (email in ADMIN_EMAILS)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Require a non-spoofable admin API key in addition to user ID
        if not ADMIN_API_KEY:
            return jsonify({"error": "Admin API key not configured"}), 500
        api_key = request.headers.get("X-Admin-API-Key")
        if api_key != ADMIN_API_KEY:
            return jsonify({"error": "Invalid or missing admin API key"}), 401

        user_id = request.headers.get("X-User-ID")

        if not user_id:
            return jsonify({"error": "Missing X-User-ID header"}), 401

        # Fetch user from database
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        # Check if user's email is in admin list
        user_email = (user.email or "").lower()
        if user_email not in ADMIN_EMAILS:
            return jsonify({"error": "Admin access required"}), 403

        # Store user in flask.g for the request context
        g.admin_user = user
        return f(*args, **kwargs)
    return decorated_function


@bp.route("/dashboard", methods=["GET"])
@require_admin
def cache_dashboard():
    """Get admin dashboard data (user info + cache stats)."""
    user = g.admin_user
    stats = get_cache_stats()
    stats["hit_rate"] = round(get_cache_hit_rate(), 4)
    
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
    stats["hit_rate"] = round(get_cache_hit_rate(), 4)
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
