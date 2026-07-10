"""
Request authentication middleware.

Reads the `Authorization: Bearer <token>` header, verifies it, and exposes
the authenticated user_id as `g.user_id`. Routes must not trust a user_id
supplied via query params / JSON body — that value is client-controlled
and trivially spoofable.
"""
import logging
from functools import wraps
from flask import request, jsonify, g

from backend.utils.auth_token import decode_token, is_token_stale
from backend.services.db_user_manager import get_user_by_id

logger = logging.getLogger("auth_middleware")


def _extract_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[len("Bearer "):].strip()
    return None


def _resolve_user_id(token):
    """
    Verify the token's signature/expiry, then check it hasn't been revoked
    by a password change (a valid signature alone doesn't capture that).
    """
    user_id, issued_at = decode_token(token)
    if not user_id:
        return None
    user = get_user_by_id(user_id)
    if not user or is_token_stale(user, issued_at):
        return None
    return user_id


def optional_auth(f):
    """Populate g.user_id from a valid bearer token if present; else None.

    Use for endpoints that support both anonymous and authenticated access
    (e.g. search, event logging).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)
        g.user_id = _resolve_user_id(_extract_token())
        return f(*args, **kwargs)
    return decorated


def require_auth(f):
    """Require a valid, non-revoked bearer token; 401s otherwise."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)
        user_id = _resolve_user_id(_extract_token())
        if not user_id:
            return jsonify({"error": "authentication required"}), 401
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated
