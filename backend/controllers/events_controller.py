from datetime import datetime

from backend.utils.sanitize import sanitize_user_id
from backend.services.db_user_manager import get_user_by_id
from backend.services.db_event_service import create_search_event
from backend.services.db_product_service import update_product_popularity
from backend.services.retrain_trigger import record_event


def log_event_controller(data):
    raw_user_id = data.get("user_id", "")
    user_id = sanitize_user_id(raw_user_id)

    if raw_user_id and user_id is None:
        return {"error": "invalid user_id"}, 400

    if user_id is None:
        user_id = ""

    group = "A"
    try:
        user = get_user_by_id(user_id)
        if user:
            group = user.group or "A"
    except Exception:
        # If user lookup fails, continue with default group A
        pass

    event_type = data.get("event", "")
    product_id = data.get("product_id", "")
    query = data.get("query", "")

    # Log the event to database
    try:
        create_search_event(user_id, query, product_id, event_type, group)
    except Exception:
        # If event logging fails, continue processing (non-critical)
        pass

    # Popularity rule
    if event_type == "click" and product_id:
        update_product_popularity(product_id, 1)

    # Track event for retrain triggers
    if event_type in ("click", "add_to_cart"):
        record_event()

    return {"status": "logged"}, 200
