import logging

from backend.services.db_product_service import (
    get_products_paginated,
    create_product,
    update_product,
    delete_product,
    serialize_product,
)
from backend.services.cache_invalidation import invalidate_on_product_update

logger = logging.getLogger("product_admin_controller")

EDITABLE_FIELDS = ("title", "description", "category", "price")
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def error_response(message, status=400):
    return {"error": message}, status


def _validate_price(raw_price):
    try:
        price = float(raw_price)
    except (TypeError, ValueError):
        return None, error_response("price must be a number")
    if price <= 0:
        return None, error_response("price must be a positive number")
    return price, None


def _parse_pagination(cursor_raw, limit_raw):
    cursor, limit = 0, DEFAULT_PAGE_SIZE
    if cursor_raw not in (None, ""):
        try:
            cursor = int(cursor_raw)
        except (TypeError, ValueError):
            return None, None, "invalid cursor"
    if limit_raw not in (None, ""):
        try:
            limit = int(limit_raw)
        except (TypeError, ValueError):
            return None, None, "invalid limit"
    if cursor < 0:
        return None, None, "cursor must be >= 0"
    if limit <= 0 or limit > MAX_PAGE_SIZE:
        return None, None, f"limit must be between 1 and {MAX_PAGE_SIZE}"
    return cursor, limit, None


def list_products_controller(search=None, cursor_raw=None, limit_raw=None):
    cursor, limit, error = _parse_pagination(cursor_raw, limit_raw)
    if error:
        return error_response(error)

    products, total = get_products_paginated(search=search or None, cursor=cursor, limit=limit)
    return {
        "products": products,
        "total": total,
        "cursor": cursor,
        "limit": limit,
        "has_more": cursor + len(products) < total,
    }, 200


def create_product_controller(data):
    title = (data.get("title") or "").strip()
    if not title:
        return error_response("title is required")

    price, error = _validate_price(data.get("price"))
    if error:
        return error

    description = data.get("description")
    category = data.get("category")

    try:
        product = create_product(
            title=title,
            description=description,
            category=category,
            price=price,
        )
    except Exception:
        logger.warning("Failed to create product title=%s", title, exc_info=True)
        return error_response("Failed to create product", 500)

    invalidate_on_product_update(product.id)
    return {"status": "product created", "product": serialize_product(product)}, 201


def update_product_controller(product_id, data):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return error_response("product_id must be an integer")

    fields = {}
    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return error_response("title cannot be empty")
        fields["title"] = title
    if "price" in data:
        price, error = _validate_price(data.get("price"))
        if error:
            return error
        fields["price"] = price
    if "description" in data:
        fields["description"] = data.get("description")
    if "category" in data:
        fields["category"] = data.get("category")

    if not fields:
        return error_response("no editable fields provided")

    try:
        product = update_product(product_id, **fields)
    except Exception:
        logger.warning("Failed to update product id=%s", product_id, exc_info=True)
        return error_response("Failed to update product", 500)

    if product is None:
        return error_response("product not found", 404)

    invalidate_on_product_update(product_id)
    return {"status": "product updated", "product": product}, 200


def delete_product_controller(product_id):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return error_response("product_id must be an integer")

    try:
        deleted = delete_product(product_id)
    except Exception:
        logger.warning("Failed to delete product id=%s", product_id, exc_info=True)
        return error_response("Failed to delete product", 500)

    if not deleted:
        return error_response("product not found", 404)

    invalidate_on_product_update(product_id)
    return {"status": "product deleted"}, 200
