from sqlalchemy import func
from backend.models import Review, Product


def lock_product_for_review_write(session, product_id):
    """Lock the product row before touching its reviews.

    Must be called before any INSERT/UPDATE/DELETE on `reviews` for this
    product, not after: locking afterward (e.g. from inside the aggregate
    recompute) still fixes the lost-update race, but it makes the lock
    acquisition order "reviews row, then product row" — which under real
    concurrent writers can deadlock against PostgreSQL's internal locking
    for concurrent `ON CONFLICT` upserts (observed directly: 10 concurrent
    submit_review calls for the same product raised `DeadlockDetected`).
    Locking the product row first gives every transaction touching this
    product's reviews the same acquisition order, so they simply queue
    instead of forming a cycle.
    """
    session.query(Product).filter(Product.id == product_id).with_for_update().first()


def recompute_product_aggregate(session, product_id):
    """Recompute Product.rating/review_count from the reviews table.

    Caller is responsible for the transaction (commit/rollback) and for
    calling lock_product_for_review_write() first — this only reads the
    aggregate and queues the UPDATE, it doesn't lock anything itself.
    """
    avg_rating, count = session.query(
        func.avg(Review.rating), func.count(Review.id)
    ).filter(Review.product_id == product_id).one()

    session.query(Product).filter(Product.id == product_id).update({
        "rating": round(float(avg_rating or 0), 2),
        "review_count": count,
    })
