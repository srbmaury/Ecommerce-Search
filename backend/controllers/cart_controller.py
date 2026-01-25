from datetime import datetime
import csv

from backend.utils.csv_lock import csv_lock
from backend.utils.sanitize import sanitize_user_id, sanitize_csv_field
from backend.user_manager import load_users, save_users
from backend.services.retrain_trigger import record_event
from backend.services.utils import get_products_df, update_product_popularity
from utils.data_paths import get_data_path

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
        users = load_users()
        user = next((u for u in users if u["user_id"] == user_id), None)
        if user:
            group = user.get("group", "A")
            cart = user.get("cart", {})
            # Convert old list format to dict format if needed
            if isinstance(cart, list):
                cart = {str(pid): 1 for pid in cart}
            # Add or increment quantity
            product_id_str = str(product_id)
            cart[product_id_str] = cart.get(product_id_str, 0) + 1
            user["cart"] = cart
            save_users(users)
    except Exception:
        pass

    with csv_lock:
        with open(get_data_path("search_events.csv"), "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                user_id,
                sanitize_csv_field(query),
                sanitize_csv_field(product_id),
                "add_to_cart",
                datetime.now().isoformat(),
                group
            ])

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
        users = load_users()
        user = next((u for u in users if u["user_id"] == user_id), None)
        if user:
            cart_data = user.get("cart", {})
            # Convert old list format to dict format if needed
            if isinstance(cart_data, list):
                cart_data = {str(pid): 1 for pid in cart_data}
    except Exception:
        pass

    products_df = get_products_df()
    cart_items = []

    if not products_df.empty:
        for pid, quantity in cart_data.items():
            try:
                product = products_df[products_df["product_id"] == int(pid)]
                if not product.empty:
                    item = product.iloc[0].to_dict()
                    item["quantity"] = quantity
                    cart_items.append(item)
            except Exception:
                continue

    total = sum(item.get("price", 0) * item.get("quantity", 1) for item in cart_items)
    total_items = sum(item.get("quantity", 1) for item in cart_items)

    return {
        "items": cart_items,
        "count": total_items,
        "total": total
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
        users = load_users()
        user = next((u for u in users if u["user_id"] == user_id), None)
        if user:
            cart = user.get("cart", {})
            # Convert old list format to dict format if needed
            if isinstance(cart, list):
                cart = {str(pid): 1 for pid in cart}
            # Remove product or decrement quantity
            if product_id in cart:
                if cart[product_id] > 1:
                    cart[product_id] -= 1
                else:
                    del cart[product_id]
                user["cart"] = cart
                save_users(users)
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
        users = load_users()
        user = next((u for u in users if u["user_id"] == user_id), None)
        if user:
            user["cart"] = {}
            save_users(users)
    except Exception:
        pass

    return {"status": "cart cleared"}, 200
