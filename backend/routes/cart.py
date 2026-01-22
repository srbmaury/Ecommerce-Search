from flask import Blueprint, request, jsonify
from datetime import datetime
import csv
import threading

from backend.utils.csv_lock import csv_lock
from backend.utils.sanitize import sanitize_user_id, sanitize_csv_field
from backend.user_manager import load_users
from utils.data_paths import get_data_path

bp = Blueprint("cart", __name__)

user_carts = {}
user_carts_lock = threading.Lock()

@bp.route("/cart", methods=["POST", "OPTIONS"])
def add_to_cart():
    if request.method == "OPTIONS":
        return "", 200

    data = request.json or {}
    raw_user_id = data.get("user_id")
    product_id = data.get("product_id")

    if not raw_user_id or not product_id:
        return jsonify({"error": "user_id and product_id required"}), 400

    user_id = sanitize_user_id(raw_user_id)
    if user_id is None:
        return jsonify({"error": "invalid user_id"}), 400

    with user_carts_lock:
        user_carts.setdefault(user_id, []).append(product_id)

    group = "A"
    try:
        users = load_users()
        user = next((u for u in users if u["user_id"] == user_id), None)
        if user:
            group = user.get("group", "A")
    except Exception:
        # If user lookup fails, default to group A (already set above)
        pass

    with csv_lock:
        with open(get_data_path("search_events.csv"), "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                user_id,
                "",
                sanitize_csv_field(product_id),
                "add_to_cart",
                datetime.now().isoformat(),
                group
            ])

    return jsonify({"status": "added to cart"})
