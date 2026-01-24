import csv
from datetime import datetime

from backend.utils.csv_lock import csv_lock
from backend.utils.sanitize import sanitize_user_id, sanitize_csv_field
from backend.user_manager import load_users
from backend.services.retrain_trigger import record_event
from backend.services.utils import update_product_popularity
from utils.data_paths import get_data_path


def log_event_controller(data):
    timestamp = datetime.now().isoformat()

    raw_user_id = data.get("user_id", "")
    user_id = sanitize_user_id(raw_user_id)

    if raw_user_id and user_id is None:
        return {"error": "invalid user_id"}, 400

    if user_id is None:
        user_id = ""

    group = "A"
    try:
        users = load_users()
        user = next((u for u in users if u["user_id"] == user_id), None)
        if user:
            group = user.get("group", "A")
    except Exception:
        pass

    event_type = data.get("event", "")
    product_id = data.get("product_id", "")
    query = data.get("query", "")

    with csv_lock:
        with open(get_data_path("search_events.csv"), "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                user_id,
                sanitize_csv_field(query),
                sanitize_csv_field(product_id),
                sanitize_csv_field(event_type),
                timestamp,
                group
            ])

    # Popularity rule
    if event_type == "click" and product_id:
        update_product_popularity(product_id, 1)

    # Track event for retrain triggers
    if event_type in ("click", "add_to_cart"):
        record_event()

    return {"status": "logged"}, 200
