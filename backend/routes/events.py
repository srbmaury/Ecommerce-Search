from flask import Blueprint, request, jsonify
import csv
from datetime import datetime

from backend.utils.csv_lock import csv_lock
from backend.utils.sanitize import sanitize_user_id, sanitize_csv_field
from backend.user_manager import load_users
from utils.data_paths import get_data_path

bp = Blueprint("events", __name__)

@bp.route("/event", methods=["POST"])
def log_event():
    data = request.json or {}
    timestamp = datetime.now().isoformat()

    raw_user_id = data.get("user_id", "")
    user_id = sanitize_user_id(raw_user_id)

    if raw_user_id and user_id is None:
        return jsonify({"error": "invalid user_id"}), 400

    if user_id is None:
        user_id = ""

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
                sanitize_csv_field(data.get("query", "")),
                sanitize_csv_field(data.get("product_id", "")),
                sanitize_csv_field(data.get("event", "")),
                timestamp,
                group
            ])

    return jsonify({"status": "logged"})
