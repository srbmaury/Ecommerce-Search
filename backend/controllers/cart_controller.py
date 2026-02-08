from backend.utils.sanitize import sanitize_user_id
from backend.services.db_user_manager import (
    get_user_by_id
)
from backend.services.db_cart_manager import (
    add_to_cart,
    get_cart,
    remove_from_cart,
    clear_cart
)
from backend.services.db_event_service import create_search_event
from backend.services.db_product_service import (
    update_product_popularity,
    get_products_by_ids,
)
from backend.services.retrain_trigger import record_event


DEFAULT_GROUP = "A"


# ---------- Helpers ----------

def error_response(message, status=400):
    return {"error": message}, status


def get_valid_user(raw_user_id):
    if not raw_user_id:
        return None, error_response("user_id required")

    user_id = sanitize_user_id(raw_user_id)
    if not user_id:
        return None, error_response("invalid user_id")

    user = get_user_by_id(user_id)
    if not user:
        return None, error_response("user not found. Please login again.", 404)

    return user, None


# ---------- Controllers ----------

def batch_cart_controller(data):
    """
    Accepts a list of cart actions: [{action: 'add'|'remove', product_id, query}]
    { user_id: str, actions: [ ... ] }
    """
    raw_user_id = data.get("user_id")
    actions = data.get("actions", [])
    if not actions or not isinstance(actions, list):
        return error_response("actions (list) required")
    user, error = get_valid_user(raw_user_id)
    if error:
        return error
    user_id = user.user_id
    group = getattr(user, "group", None) or DEFAULT_GROUP
    results = []
    for act in actions:
        product_id = act.get("product_id")
        query = act.get("query", "")
        if not product_id:
            results.append({"error": "product_id required"})
            continue
        try:
            if act.get("action") == "add":
                add_to_cart(user_id, int(product_id), 1)
                create_search_event(
                    user_id=user_id,
                    query=query,
                    product_id=product_id,
                    event_type="add_to_cart",
                    group=group,
                )
                update_product_popularity(product_id, 3)
                record_event()
                results.append({"status": "added", "product_id": product_id})
            elif act.get("action") == "remove":
                remove_from_cart(user_id, int(product_id), 1)
                results.append({"status": "removed", "product_id": product_id})
            else:
                results.append({"error": "invalid action", "product_id": product_id})
        except Exception as e:
            results.append({"error": str(e), "product_id": product_id})
    return {"results": results}, 200

def add_to_cart_controller(data):
    raw_user_id = data.get("user_id")
    product_id = data.get("product_id")
    query = data.get("query", "")

    if not product_id:
        return error_response("user_id and product_id required")

    user, error = get_valid_user(raw_user_id)
    if error:
        return error

    user_id = user.user_id
    group = getattr(user, "group", None) or DEFAULT_GROUP

    try:
        add_to_cart(user_id, int(product_id), 1)
    except Exception as e:
        return error_response(f"Failed to update cart: {str(e)}", 500)

    # Non-critical analytics logging
    try:
        create_search_event(
            user_id=user_id,
            query=query,
            product_id=product_id,
            event_type="add_to_cart",
            group=group,
        )
    except Exception:
        pass

    update_product_popularity(product_id, 3)
    record_event()

    return {"status": "added to cart"}, 200


def get_cart_controller(raw_user_id):
    user, error = get_valid_user(raw_user_id)
    if error:
        return error

    user_id = user.user_id

    try:
        cart_data = get_cart(user_id) or {}
    except Exception:
        cart_data = {}

    if not cart_data:
        return {
            "items": [],
            "total": 0,
            "total_items": 0,
            "count": 0,
        }, 200

    product_ids = list(cart_data.keys())
    products = get_products_by_ids(product_ids)
    products_by_id = {
        str(p["product_id"]): p for p in products
    }

    items = []
    for pid, quantity in cart_data.items():
        product = products_by_id.get(str(pid))
        if not product:
            continue

        item = product.copy()
        item["quantity"] = quantity
        items.append(item)

    total = sum(
        item.get("price", 0) * item.get("quantity", 1)
        for item in items
    )
    total_items = sum(item.get("quantity", 1) for item in items)

    return {
        "items": items,
        "total": total,
        "total_items": total_items,
        "count": total_items,
    }, 200


def remove_from_cart_controller(data):
    raw_user_id = data.get("user_id")
    product_id = data.get("product_id")

    if not product_id:
        return error_response("user_id and product_id required")

    user, error = get_valid_user(raw_user_id)
    if error:
        return error

    try:
        remove_from_cart(user["user_id"], int(product_id), 1)
    except Exception:
        pass

    return {"status": "removed from cart"}, 200


def clear_cart_controller(data):
    raw_user_id = data.get("user_id")

    user, error = get_valid_user(raw_user_id)
    if error:
        return error


    try:
        clear_cart(user.user_id)
    except Exception:
        pass

    return {"status": "cart cleared"}, 200
