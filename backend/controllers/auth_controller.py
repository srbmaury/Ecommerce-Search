import random
import uuid
import bcrypt
from flask import jsonify

from backend.services.security import (
    validate_username,
    validate_password,
    hash_password,
)
from backend.services.db_user_manager import (
    get_user_by_username,
    create_user,
)


EXPERIMENT_GROUPS = ("A", "B")


# ---------- Helpers ----------

def generate_user_id():
    # Short, collision-resistant, non-sequential ID
    return f"u{uuid.uuid4().hex[:12]}"


def invalid_response(message, status=400):
    return jsonify({"error": message}), status


def constant_time_password_check(password: str, password_hash: str | None):
    """
    Prevents timing attacks by always running bcrypt.
    """
    password_bytes = password.encode("utf-8")

    if password_hash:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))

    # Dummy check to match bcrypt cost
    bcrypt.checkpw(password_bytes, bcrypt.hashpw(b"dummy", bcrypt.gensalt()))
    return False


# ---------- Controllers ----------

def signup_controller(data):
    username = data.get("username")
    password = data.get("password")

    ok, error = validate_username(username)
    if not ok:
        return invalid_response(error)

    ok, error = validate_password(password)
    if not ok:
        return invalid_response(error)

    user_id = generate_user_id()
    group = random.choice(EXPERIMENT_GROUPS)

    try:
        user = create_user(
            user_id=user_id,
            username=username,
            password_hash=hash_password(password),
            group=group,
        )
    except Exception as e:
        # Handle unique constraint violations safely
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return invalid_response("username already exists")
        raise

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "group": user.group,
    })


def login_controller(data):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return invalid_response("username and password required")

    user = get_user_by_username(username)

    password_valid = constant_time_password_check(
        password,
        user.password_hash if user else None
    )

    if not user or not password_valid:
        return invalid_response("invalid credentials", status=401)

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "group": user.group,
    })
