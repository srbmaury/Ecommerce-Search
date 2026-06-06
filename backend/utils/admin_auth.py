import os
import logging
from functools import wraps
from flask import request, jsonify, g

from backend.services.db_user_manager import get_user_by_id

logger = logging.getLogger("admin_auth")

ADMIN_USER_IDS = [uid.strip() for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip()]


def require_admin(f):
    """Decorator: require the requesting user_id to be in ADMIN_USER_IDS."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return jsonify({"error": "Missing X-User-ID header"}), 401

        if user_id not in ADMIN_USER_IDS:
            logger.warning("Unauthorized admin attempt by user_id=%s", user_id)
            return jsonify({"error": "Admin access required"}), 403

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        g.admin_user = user
        return f(*args, **kwargs)
    return decorated
