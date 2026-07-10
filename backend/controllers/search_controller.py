import time

from backend.utils.search import search_products
from backend.services.db_user_manager import get_user_by_id
from backend.utils.sanitize import sanitize_user_id
from backend.utils.intent import detect_intent


DEFAULT_GROUP = "A"
MIN_RESULTS_THRESHOLD = 5
DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


# ---------- Helpers ----------

def error_response(message, status=400):
    return {"error": message}, status


def parse_pagination(cursor_raw, limit_raw):
    cursor = 0
    limit = DEFAULT_PAGE_SIZE

    if cursor_raw not in (None, ""):
        try:
            cursor = int(cursor_raw)
        except Exception:
            return None, None, "invalid cursor"

    if limit_raw not in (None, ""):
        try:
            limit = int(limit_raw)
        except Exception:
            return None, None, "invalid limit"

    if cursor < 0:
        return None, None, "cursor must be >= 0"
    if limit <= 0 or limit > MAX_PAGE_SIZE:
        return None, None, f"limit must be between 1 and {MAX_PAGE_SIZE}"

    return cursor, limit, None


def resolve_user_context(raw_user_id):
    if not raw_user_id:
        return None, None, DEFAULT_GROUP

    user_id = sanitize_user_id(raw_user_id)
    if not user_id:
        return None, None, None

    try:
        user = get_user_by_id(user_id)
        if user:
            return user_id, user.cluster, user.group or DEFAULT_GROUP
    except Exception:
        pass

    return user_id, None, DEFAULT_GROUP


def apply_price_filter(products, min_price, max_price):
    if min_price is None and max_price is None:
        return products

    filtered = []
    for p in products:
        price = p.get("price", 0)
        if min_price is not None and price < min_price:
            continue
        if max_price is not None and price > max_price:
            continue
        filtered.append(p)
    return filtered


def apply_sort(products, sort_key):
    if sort_key == "price_asc":
        products.sort(key=lambda x: x.get("price", 0))
    elif sort_key == "price_desc":
        products.sort(key=lambda x: x.get("price", 0), reverse=True)
    elif sort_key == "rating":
        products.sort(key=lambda x: x.get("rating", 0), reverse=True)
    return products


# ---------- Controller ----------

def search_controller(query, raw_user_id, cursor_raw=None, limit_raw=None):
    timings = {}
    t0 = time.perf_counter()

    if not query:
        return error_response("query required")

    cursor, page_size, pagination_error = parse_pagination(cursor_raw, limit_raw)
    if pagination_error:
        return error_response(pagination_error)

    # -------- user context --------
    t_user = time.perf_counter()
    user_id, cluster, group = resolve_user_context(raw_user_id)
    if raw_user_id and group is None:
        return error_response("invalid user_id")
    timings["user_context"] = (time.perf_counter() - t_user) * 1000

    # -------- intent detection --------
    t_intent = time.perf_counter()
    intent = detect_intent(query)
    timings["intent"] = (time.perf_counter() - t_intent) * 1000
    search_query = intent["clean_query"]

    # -------- primary search (with category expansion) --------
    t_search = time.perf_counter()
    products = search_products(
        search_query,
        user_id,
        cluster=cluster,
        ab_group=group,
        limit=None,
        category=intent["suggested_category"],
    )
    timings["search_products"] = (time.perf_counter() - t_search) * 1000

    # -------- price filtering --------
    t_price = time.perf_counter()
    products = apply_price_filter(
        products,
        intent["suggested_min_price"],
        intent["suggested_max_price"],
    )
    timings["price_filter"] = (time.perf_counter() - t_price) * 1000

    # -------- sorting --------
    t_sort = time.perf_counter()
    products = apply_sort(products, intent["suggested_sort"])
    timings["sort"] = (time.perf_counter() - t_sort) * 1000

    # -------- response --------
    detected_intents = []
    if intent["suggested_category"]:
        detected_intents.append("category")
    if intent["suggested_sort"]:
        detected_intents.append(intent["suggested_sort"])
    if (
        intent["suggested_min_price"] is not None
        or intent["suggested_max_price"] is not None
    ):
        detected_intents.append("price_filter")

    timings["total"] = (time.perf_counter() - t0) * 1000

    total_results = len(products)
    paginated_products = products[cursor : cursor + page_size]
    next_cursor = cursor + page_size if cursor + page_size < total_results else None
    has_more = next_cursor is not None

    return {
        "products": paginated_products,
        "pagination": {
            "cursor": cursor,
            "next_cursor": next_cursor,
            "limit": page_size,
            "has_more": has_more,
            "total": total_results,
        },
        "intent": {
            "detected": detected_intents,
            "suggested_category": intent["suggested_category"],
            "suggested_sort": intent["suggested_sort"],
            "suggested_min_price": intent["suggested_min_price"],
            "suggested_max_price": intent["suggested_max_price"],
        },
    }, 200
