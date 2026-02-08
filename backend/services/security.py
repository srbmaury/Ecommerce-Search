"""
Security utilities:
- Username validation
- Password validation
- Password hashing & verification
"""

import bcrypt
import re
import string
from typing import Tuple, Optional


# ---------- CONFIG ----------

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,50}$")
MIN_PASSWORD_LENGTH = 8
BCRYPT_ROUNDS = 12  # Explicit cost factor


# ---------- VALIDATION ----------

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Valid usernames:
    - 3 to 50 characters
    - Letters, digits, underscore
    """
    if not username:
        return False, "Username is required."

    if not USERNAME_REGEX.fullmatch(username):
        return False, (
            "Username must be 3–50 characters and contain only "
            "letters, numbers, or underscores."
        )

    return True, None


def validate_password(
    password: str,
    complexity: bool = True,
) -> Tuple[bool, Optional[str]]:
    """
    Validate password strength.
    """
    if not password:
        return False, "Password is required."

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, (
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )

    if not complexity:
        return True, None

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."

    if not any(c in string.punctuation for c in password):
        return False, (
            "Password must contain at least one special character "
            "(e.g. !@#$%)."
        )

    return True, None


# ---------- PASSWORD HASHING ----------

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    Returns UTF-8 encoded hash for DB storage.
    """
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Constant-time password verification.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False
