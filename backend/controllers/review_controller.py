import logging

from backend.services.db_product_service import get_product_by_id
from backend.services.db_review_service import submit_review, get_reviews_for_product, delete_review

logger = logging.getLogger("review_controller")

MAX_COMMENT_LENGTH = 2000


def error_response(message, status=400):
    return {"error": message}, status


def submit_review_controller(data):
    product_id = data.get("product_id")
    user_id = data.get("user_id")

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return error_response("product_id must be an integer")

    if not get_product_by_id(product_id):
        return error_response("product not found", 404)

    rating = data.get("rating")
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return error_response("rating must be an integer between 1 and 5")

    if rating < 1 or rating > 5:
        return error_response("rating must be between 1 and 5")

    comment = data.get("comment")
    if comment is not None:
        comment = str(comment).strip()
        if len(comment) > MAX_COMMENT_LENGTH:
            return error_response(f"comment cannot exceed {MAX_COMMENT_LENGTH} characters")
        comment = comment or None

    try:
        submit_review(product_id, user_id, rating, comment)
    except Exception:
        logger.warning("Failed to submit review product=%s user=%s", product_id, user_id, exc_info=True)
        return error_response("Failed to submit review", 500)

    return {"status": "review submitted"}, 200


def get_reviews_controller(product_id):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return error_response("product_id must be an integer")

    if not get_product_by_id(product_id):
        return error_response("product not found", 404)

    reviews = get_reviews_for_product(product_id)
    return {"reviews": reviews, "count": len(reviews)}, 200


def delete_review_controller(product_id, user_id):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return error_response("product_id must be an integer")

    try:
        deleted = delete_review(product_id, user_id)
    except Exception:
        logger.warning("Failed to delete review product=%s user=%s", product_id, user_id, exc_info=True)
        return error_response("Failed to delete review", 500)

    if not deleted:
        return error_response("review not found", 404)

    return {"status": "review deleted"}, 200
