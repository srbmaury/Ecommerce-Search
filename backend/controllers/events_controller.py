import logging
import time

from backend.utils.sanitize import sanitize_user_id
from backend.services.db_user_manager import get_user_by_id
from backend.services.db_event_service import create_search_event
from backend.services.db_product_service import update_product_popularity, get_product_by_id
from backend.services.retrain_trigger import record_event
from backend.services.cache_invalidation import invalidate_on_user_event

logger = logging.getLogger("event_logger")

DEFAULT_GROUP = "A"
ALLOWED_EVENTS = {"click", "add_to_cart"}
MAX_QUERY_LENGTH = 512
POPULARITY_EVENTS = {"click"}
RETRAIN_EVENTS = {"click", "add_to_cart"}
CACHE_INVALIDATION_EVENTS = { "click", "add_to_cart"}


# ---------- Helpers ----------

def error_response(message, status=400):
    return {"error": message}, status


def normalize_event_type(event_type):
    if event_type is None:
        return ""
    return str(event_type).strip().lower()


def normalize_product_id(product_id):
    if product_id in (None, ""):
        return None
    try:
        normalized = int(product_id)
        return normalized if normalized > 0 else None
    except Exception:
        return None


def resolve_user_context(raw_user_id):
    """
    Returns (user_id, group)
    Anonymous users are allowed.
    """
    if not raw_user_id:
        return "", DEFAULT_GROUP

    user_id = sanitize_user_id(raw_user_id)
    if not user_id:
        return None, None

    try:
        user = get_user_by_id(user_id)
        group = user.group if user and user.group else DEFAULT_GROUP
    except Exception:
        group = DEFAULT_GROUP

    return user_id, group


# ---------- Controller ----------

def log_event_controller(data):
    t0 = time.perf_counter()
    raw_user_id = data.get("user_id", "")
    event_type = normalize_event_type(data.get("event", ""))
    product_id = normalize_product_id(data.get("product_id", ""))
    query = str(data.get("query", "") or "").strip()[:MAX_QUERY_LENGTH]

    if event_type not in ALLOWED_EVENTS:
        return error_response("invalid event type")

    if product_id is None:
        return error_response("valid product_id required")

    # Validate product exists before logging to prevent orphaned events
    try:
        if not get_product_by_id(product_id):
            return error_response("product not found", 404)
    except Exception:
        pass  # DB unavailable — allow through rather than drop events

    user_id, group = resolve_user_context(raw_user_id)
    if user_id is None:
        logger.warning(f"Invalid user_id received: {raw_user_id}")
        return error_response("invalid user_id")

    # Best-effort analytics logging
    try:
        create_search_event(
            user_id=user_id,
            query=query,
            product_id=product_id,
            event_type=event_type,
            group=group,
        )
        logger.info("Event created successfully.")
    except Exception as e:
        logger.error(f"Event logging failed: {e}")

    # Popularity update
    if event_type in POPULARITY_EVENTS and product_id:
        update_product_popularity(product_id, 1)

    # Retrain trigger
    if event_type in RETRAIN_EVENTS:
        record_event()

    # NEW: Cache invalidation on user events
    if user_id and event_type in CACHE_INVALIDATION_EVENTS:
        try:
            user = get_user_by_id(user_id)
            cluster_id = getattr(user, "cluster", None) if user else None
            invalidate_on_user_event(user_id, event_type, cluster_id)
        except Exception as e:
            logger.error(f"Cache invalidation failed (non-blocking): {e}")

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("log_event type=%s product=%s user=%s %.1fms", event_type, product_id, user_id, elapsed)
    return {"status": "logged"}, 200
