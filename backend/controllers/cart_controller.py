from datetime import datetime

from backend.utils.sanitize import sanitize_user_id
from backend.services.db_user_manager import get_user_by_id, add_to_cart, remove_from_cart, clear_cart, get_cart
from backend.services.db_event_service import create_search_event
from backend.services.db_product_service import update_product_popularity, get_products_by_ids
from backend.services.retrain_trigger import record_event

def add_to_cart_controller(data):
    raw_user_id = data.get("user_id")
    product_id = data.get("product_id")
    query = data.get("query", "")

    if not raw_user_id or not product_id:
        return {"error": "user_id and product_id required"}, 400

    user_id = sanitize_user_id(raw_user_id)
    if user_id is None:
        return {"error": "invalid user_id"}, 400

    group = "A"

    try:
        user = get_user_by_id(user_id)
        if not user:
            return {"error": "user not found. Please login again."}, 404
        group = user.get('group') or "A"
        add_to_cart(user_id, int(product_id), 1)
    except Exception as e:
        return {"error": f"Failed to update cart: {str(e)}"}, 500

    # Log the event to database
    try:
        create_search_event(user_id, query, product_id, 'add_to_cart', group)
    except Exception:
        # If event logging fails, continue processing (non-critical)
        pass

    update_product_popularity(product_id, 3)

    # Track event for retrain triggers
    record_event()

    return {"status": "added to cart"}, 200


def get_cart_controller(raw_user_id):
    if not raw_user_id:
        return {"error": "user_id required"}, 400

    user_id = sanitize_user_id(raw_user_id)
    if user_id is None:
        return {"error": "invalid user_id"}, 400

    try:
        user = get_user_by_id(user_id)
        if not user:
            return {"error": "user not found. Please login again."}, 404
        cart_data = get_cart(user_id)
    except Exception:
        cart_data = {}

    cart_items = []
    if cart_data:
        product_ids = list(cart_data.keys())
        products_list = get_products_by_ids(product_ids)
        products_dict = {str(p['product_id']): p for p in products_list}
        for pid, quantity in cart_data.items():
            try:
                if pid in products_dict:
                    item = products_dict[pid].copy()
                    item["quantity"] = quantity
                    cart_items.append(item)
            except Exception:
                continue
    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)
    total_items = sum(item.get("quantity", 1) for item in cart_items)
    return {
        "items": cart_items,
        "total": total,
        "total_items": total_items,
        "count": total_items
    }, 200


def remove_from_cart_controller(data):
    raw_user_id = data.get("user_id")
    product_id = str(data.get("product_id", ""))

    if not raw_user_id or not product_id:
        return {"error": "user_id and product_id required"}, 400

    user_id = sanitize_user_id(raw_user_id)
    if user_id is None:
        return {"error": "invalid user_id"}, 400

    try:
        user = get_user_by_id(user_id)
        if not user:
            return {"error": "user not found. Please login again."}, 404
        remove_from_cart(user_id, int(product_id), 1)
    except Exception:
        pass
    return {"status": "removed from cart"}, 200


def clear_cart_controller(data):
    raw_user_id = data.get("user_id")

    if not raw_user_id:
        return {"error": "user_id required"}, 400

    user_id = sanitize_user_id(raw_user_id)
    if user_id is None:
        return {"error": "invalid user_id"}, 400

    try:
        user = get_user_by_id(user_id)
        if not user:
            return {"error": "user not found. Please login again."}, 404
        clear_cart(user_id)
    except Exception:
        pass
    return {"status": "cart cleared"}, 200
