"""
Session token issuing/verification.

Login and signup issue a signed, expiring token binding the response to a
user_id. Protected routes verify this token instead of trusting a client-
supplied user_id, so knowing/guessing a user_id alone is no longer enough
to act as that user.
"""
import os
from datetime import datetime, timezone
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

TOKEN_MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 days
_SALT = "user-session"


def _serializer():
    secret_key = os.getenv("SECRET_KEY")
    return URLSafeTimedSerializer(secret_key, salt=_SALT)


def create_token(user_id: str) -> str:
    return _serializer().dumps({"user_id": user_id})


def decode_token(token: str) -> tuple[str | None, datetime | None]:
    """
    Verify a token and return (user_id, issued_at), or (None, None) if the
    token is missing, malformed, tampered with, or expired.

    issued_at lets callers reject tokens minted before a password change
    (see is_token_stale) — the signature alone can't express that, since a
    correctly-signed old token is still cryptographically valid.
    """
    if not token:
        return None, None
    try:
        data, issued_at = _serializer().loads(
            token, max_age=TOKEN_MAX_AGE_SECONDS, return_timestamp=True
        )
    except (BadSignature, SignatureExpired):
        return None, None
    except Exception:
        return None, None
    if not isinstance(data, dict):
        return None, None
    return data.get("user_id"), issued_at


def is_token_stale(user, issued_at: datetime | None) -> bool:
    """
    True if `user`'s password was changed after this token was issued —
    i.e. the token should be treated as revoked even though its signature
    and expiry are still valid.
    """
    changed_at = getattr(user, "password_changed_at", None)
    if changed_at is None or issued_at is None:
        return False
    if changed_at.tzinfo is None:
        changed_at = changed_at.replace(tzinfo=timezone.utc)
    return issued_at < changed_at
