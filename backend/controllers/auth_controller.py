import random
import uuid
import bcrypt
from flask import jsonify

from backend.services.security import (
    validate_username,
    validate_password,
    hash_password
)
from backend.db_user_manager import (
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

    # Check if username exists
    existing_user = get_user_by_username(username)
    if existing_user:
        return jsonify({"error": "username exists"}), 400

    # Generate unique user_id using UUID to avoid race conditions
    user_id = f"u{uuid.uuid4().hex[:12]}"
    group = random.choice(["A", "B"])
    
    user = create_user(user_id, username, hash_password(password), group)
    
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
    if not user:
        return jsonify({"error": "invalid credentials"}), 401

    # Verify password
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "group": user.group
    })
