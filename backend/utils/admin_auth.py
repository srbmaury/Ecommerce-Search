import os
import logging
from functools import wraps
from flask import request, jsonify, g

from backend.services.db_user_manager import get_user_by_id
from backend.utils.auth_token import decode_token, is_token_stale

logger = logging.getLogger("admin_auth")

ADMIN_USER_IDS = [uid.strip() for uid in os.getenv("ADMIN_USER_IDS", "").split(",") if uid.strip()]


def _extract_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):].strip()
    return None


def require_admin(f):
    """Decorator: require a valid session token whose user_id is in ADMIN_USER_IDS.

    Admin identity is derived from the signed token, not a client-supplied
    header — an unsigned X-User-ID would let anyone claim to be an admin.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        user_id, issued_at = decode_token(_extract_token())
        if not user_id:
            return jsonify({"error": "authentication required"}), 401

        if user_id not in ADMIN_USER_IDS:
            logger.warning("Unauthorized admin attempt by user_id=%s", user_id)
            return jsonify({"error": "Admin access required"}), 403

        user = get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        if is_token_stale(user, issued_at):
            return jsonify({"error": "authentication required"}), 401

        g.user_id = user_id
        g.admin_user = user
        return f(*args, **kwargs)
    return decorated
