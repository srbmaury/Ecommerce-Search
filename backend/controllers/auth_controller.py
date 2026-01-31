import random
import uuid
import bcrypt
from flask import jsonify

from backend.services.security import (
    validate_username,
    validate_password,
    hash_password
)
from backend.services.db_user_manager import (
    get_user_by_username, 
    create_user
)


def signup_controller(data):
    username = data.get("username")
    password = data.get("password")

    ok, err = validate_username(username)
    if not ok:
        return jsonify({"error": err}), 400

    ok, err = validate_password(password)
    if not ok:
        return jsonify({"error": err}), 400

    # Generate unique user_id using UUID to avoid race conditions
    user_id = f"u{uuid.uuid4().hex[:12]}"
    group = random.choice(["A", "B"])
    
    try:
        user = create_user(user_id, username, hash_password(password), group)
    except Exception as e:
        # Handle unique constraint violations
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return jsonify({"error": "username exists"}), 400
        raise
    
    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "group": user.group
    })


def login_controller(data):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    user = get_user_by_username(username)
    # Always perform bcrypt to prevent timing attacks
    if user:
        password_valid = bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
    else:
        # Dummy hash check to maintain constant time
        bcrypt.checkpw(password.encode("utf-8"), bcrypt.hashpw(b"dummy", bcrypt.gensalt()))
        password_valid = False

    if not user or not password_valid:
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "group": user.group
    })
