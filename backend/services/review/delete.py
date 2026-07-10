from backend.utils.database import get_db_session
from backend.models import Review
from backend.services.review.aggregate import lock_product_for_review_write, recompute_product_aggregate


def delete_review(product_id, user_id):
    """Delete a user's review for a product and recompute the product's
    aggregate rating/review_count in the same transaction.

    Returns True if a row was deleted, False if the user had no review.
    """
    session = get_db_session()
    try:
        lock_product_for_review_write(session, product_id)
        deleted = (
            session.query(Review)
            .filter_by(product_id=product_id, user_id=user_id)
            .delete()
        )
        if not deleted:
            session.rollback()
            return False

        recompute_product_aggregate(session, product_id)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
