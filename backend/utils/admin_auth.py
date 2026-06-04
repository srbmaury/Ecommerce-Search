import os
import hmac
import logging
from functools import wraps
from flask import request, jsonify, g

from backend.services.db_user_manager import get_user_by_id

logger = logging.getLogger("admin_auth")

ADMIN_USER_IDS = [uid.strip() for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip()]
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")


def require_admin(f):
    """Decorator: require a valid admin user_id + matching X-Admin-Secret header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Let CORS preflight pass through — browser OPTIONS never carries auth headers
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return jsonify({"error": "Missing X-User-ID header"}), 401

        # Second factor: shared secret (required when ADMIN_SECRET is configured)
        if ADMIN_SECRET:
            provided = request.headers.get("X-Admin-Secret", "")
            if not hmac.compare_digest(provided, ADMIN_SECRET):
                logger.warning("Admin request with invalid X-Admin-Secret from user_id=%s", user_id)
                return jsonify({"error": "Admin access required"}), 403

        if user_id not in ADMIN_USER_IDS:
            logger.warning("Unauthorized admin attempt by user_id=%s", user_id)
            return jsonify({"error": "Admin access required"}), 403

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        g.admin_user = user
        return f(*args, **kwargs)
    return decorated
