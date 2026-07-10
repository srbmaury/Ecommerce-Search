from backend.utils.database import get_db_session
from backend.models import Review, User

DEFAULT_LIMIT = 50


def get_reviews_for_product(product_id, limit=DEFAULT_LIMIT, cursor=0):
    """Most recent reviews first, with the reviewer's username attached."""
    session = get_db_session()
    try:
        rows = (
            session.query(Review, User.username)
            .join(User, User.user_id == Review.user_id)
            .filter(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
            .offset(cursor)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": review.id,
                "product_id": review.product_id,
                "user_id": review.user_id,
                "username": username,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
            }
            for review, username in rows
        ]
    finally:
        session.close()
