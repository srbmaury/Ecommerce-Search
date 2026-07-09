from sqlalchemy import func
from backend.models import Review, Product


def recompute_product_aggregate(session, product_id):
    """Recompute Product.rating/review_count from the reviews table.

    Caller is responsible for the transaction (commit/rollback) — this just
    queues the UPDATE on the given session so it lands in the same
    transaction as whatever review write triggered it.
    """
    avg_rating, count = session.query(
        func.avg(Review.rating), func.count(Review.id)
    ).filter(Review.product_id == product_id).one()

    session.query(Product).filter(Product.id == product_id).update({
        "rating": round(float(avg_rating or 0), 2),
        "review_count": count,
    })
