import random
import bcrypt
import hashlib
from flask import jsonify

from backend.services.security import (
    validate_username,
    validate_password,
    hash_password
)
from backend.user_manager import load_users, save_users


def signup_controller(data):
    username = data.get("username")
    password = data.get("password")

    ok, err = validate_username(username)
    if not ok:
        return jsonify({"error": err}), 400

    ok, err = validate_password(password)
    if not ok:
        return jsonify({"error": err}), 400

    users = load_users()
    if any(u["username"] == username for u in users):
        return jsonify({"error": "username exists"}), 400

    user_id = f"u{len(users) + 1}"
    group = random.choice(["A", "B"])

    users.append({
        "user_id": user_id,
        "username": username,
        "password": hash_password(password),
        "group": group
    })

    save_users(users)

    return jsonify({
        "user_id": user_id,
        "username": username,
        "group": group
    })


def login_controller(data):
    username = data.get("username")
    password = data.get("password")

    ok, _ = validate_username(username)
    if not ok:
        return jsonify({"error": "invalid credentials"}), 401

    ok, _ = validate_password(password, complexity=False)
    if not ok:
        return jsonify({"error": "invalid credentials"}), 401

    users = load_users()
    user = next((u for u in users if u["username"] == username), None)
    if not user:
        return jsonify({"error": "invalid credentials"}), 401

    stored = user["password"]
    valid = False

    if stored.startswith("$2"):  # bcrypt
        valid = bcrypt.checkpw(password.encode(), stored.encode())
    else:  # legacy sha256
        valid = hashlib.sha256(password.encode()).hexdigest() == stored
        if valid:
            user["password"] = hash_password(password)
            save_users(users)

    if not valid:
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({
        "user_id": user["user_id"],
        "username": user["username"],
        "group": user["group"]
    })
