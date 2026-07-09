from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from backend.utils.database import get_db_session
from backend.models import Review, utcnow
from backend.services.review.aggregate import recompute_product_aggregate


def submit_review(product_id, user_id, rating, comment):
    """Upsert a user's review for a product, then recompute the product's
    aggregate rating/review_count from the reviews table — all in one
    transaction, so the aggregate is always consistent with what's stored.
    """
    session = get_db_session()
    try:
        insert_fn = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
        stmt = insert_fn(Review).values(
            product_id=product_id, user_id=user_id, rating=rating, comment=comment,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["product_id", "user_id"],
            set_={
                "rating": stmt.excluded.rating,
                "comment": stmt.excluded.comment,
                "updated_at": utcnow(),
            },
        )
        session.execute(stmt)
        recompute_product_aggregate(session, product_id)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
