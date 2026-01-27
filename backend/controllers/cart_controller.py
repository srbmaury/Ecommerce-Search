from datetime import datetime

from backend.utils.sanitize import sanitize_user_id
from backend.db_user_manager import get_user_by_id, update_user_cart
from backend.db_event_service import create_search_event
from backend.db_product_service import update_product_popularity, get_products_by_ids
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
        if user:
            group = user.group or "A"
            cart = user.cart or {}
            # Convert old list format to dict format if needed
            if isinstance(cart, list):
                cart = {str(pid): 1 for pid in cart}
            # Add or increment quantity
            product_id_str = str(product_id)
            cart[product_id_str] = cart.get(product_id_str, 0) + 1
            update_user_cart(user_id, cart)
    except Exception:
        # If cart update fails, continue to log event (cart operation is non-critical)
        pass

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

    cart_data = {}

    try:
        user = get_user_by_id(user_id)
        if user:
            cart_data = user.cart or {}
            # Convert old list format to dict format if needed
            if isinstance(cart_data, list):
                cart_data = {str(pid): 1 for pid in cart_data}
    except Exception:
        # If user lookup fails, return empty cart
        pass

    cart_items = []

    if cart_data:
        # Only fetch products that are in the cart (more efficient than loading all products)
        product_ids = list(cart_data.keys())
        products_list = get_products_by_ids(product_ids)
        
        # Create a lookup dict for quick access
        products_dict = {str(p['product_id']): p for p in products_list}
        
        for pid, quantity in cart_data.items():
            try:
                if pid in products_dict:
                    item = products_dict[pid].copy()
                    item["quantity"] = quantity
                    cart_items.append(item)
            except Exception:
                # Skip products that can't be loaded
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
        if user:
            cart = user.cart or {}
            # Convert old list format to dict format if needed
            if isinstance(cart, list):
                cart = {str(pid): 1 for pid in cart}
            # Remove product or decrement quantity
            if product_id in cart:
                if cart[product_id] > 1:
                    cart[product_id] -= 1
                else:
                    del cart[product_id]
                update_user_cart(user_id, cart)
    except Exception:
        # If cart update fails, silently ignore (non-critical operation)
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
        if user:
            update_user_cart(user_id, {})
    except Exception:
        # If cart clear fails, silently ignore (non-critical operation)
        pass

    return {"status": "cart cleared"}, 200
