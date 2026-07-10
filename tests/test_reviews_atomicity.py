"""
Regression tests for the reviews aggregate-recompute race
(backend/services/review/aggregate.py, create.py, delete.py).

Exercise a real (temp, on-disk) SQLite database rather than mocks: the bug
was a lost-update race where two different users reviewing the same
product concurrently could each compute Product.rating/review_count from a
snapshot missing the other's not-yet-committed review, so the later commit
silently overwrote the earlier one's contribution. A mocked session can't
catch that — only a real concurrent write path can.
"""
import os
import tempfile
import concurrent.futures

import pytest
from sqlalchemy import Text


@pytest.fixture
def reviews_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")

    import backend.utils.database as database
    database._engine = None
    database._SessionLocal = None
    engine, _ = database.init_db()

    from backend.models import User, Product, Review
    User.__table__.create(bind=engine)
    # products.search_vector is PostgreSQL-only TSVECTOR (see models.py) —
    # SQLite can't render it in DDL. Swap in a plain type just for CREATE
    # TABLE; it's never written to in these tests so the real type doesn't
    # matter, and restoring it immediately avoids leaking the swap into
    # other test files sharing this process.
    original_type = Product.__table__.c.search_vector.type
    Product.__table__.c.search_vector.type = Text()
    try:
        Product.__table__.create(bind=engine)
    finally:
        Product.__table__.c.search_vector.type = original_type
    Review.__table__.create(bind=engine)

    from backend.utils.database import get_db_session
    session = get_db_session()
    session.add(Product(id=1, title="Widget", price=9.99, rating=0, review_count=0))
    for i in range(10):
        session.add(User(user_id=f"u{i}", username=f"u{i}", password_hash="x"))
    session.commit()
    session.close()

    yield

    database._engine = None
    database._SessionLocal = None
    os.remove(path)


def test_concurrent_reviews_from_different_users_all_counted(reviews_db):
    """10 different users submit a review for the same product at once.
    Under the pre-fix code, concurrent recomputes could each work from a
    stale snapshot and the aggregate would end up reflecting fewer than 10
    reviews. review_count must equal exactly 10, and since every review is
    5 stars, rating must be exactly 5.0."""
    from backend.services.review.create import submit_review
    from backend.utils.database import get_db_session
    from backend.models import Product

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(submit_review, 1, f"u{i}", 5, None) for i in range(10)]
        for f in futures:
            f.result()

    session = get_db_session()
    product = session.query(Product).filter_by(id=1).first()
    session.close()
    assert product.review_count == 10
    assert product.rating == 5.0


def test_concurrent_mixed_ratings_average_correctly(reviews_db):
    """Same as above but with varied ratings (avg of 1..5 twice = 3.0) —
    catches a fix that happens to get the count right but the average
    wrong (e.g. only locking around the count query)."""
    from backend.services.review.create import submit_review
    from backend.utils.database import get_db_session
    from backend.models import Product

    ratings = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(submit_review, 1, f"u{i}", r, None) for i, r in enumerate(ratings)]
        for f in futures:
            f.result()

    session = get_db_session()
    product = session.query(Product).filter_by(id=1).first()
    session.close()
    assert product.review_count == 10
    assert product.rating == 3.0


def test_resubmit_upserts_and_recomputes(reviews_db):
    from backend.services.review.create import submit_review
    from backend.utils.database import get_db_session
    from backend.models import Product, Review

    submit_review(1, "u0", 5, "first")
    submit_review(1, "u0", 2, "changed my mind")

    session = get_db_session()
    reviews = session.query(Review).filter_by(product_id=1, user_id="u0").all()
    product = session.query(Product).filter_by(id=1).first()
    session.close()

    assert len(reviews) == 1
    assert reviews[0].rating == 2
    assert product.review_count == 1
    assert product.rating == 2.0


def test_delete_recomputes_aggregate(reviews_db):
    from backend.services.review.create import submit_review
    from backend.services.review.delete import delete_review
    from backend.utils.database import get_db_session
    from backend.models import Product

    submit_review(1, "u0", 5, None)
    submit_review(1, "u1", 1, None)
    assert delete_review(1, "u0") is True

    session = get_db_session()
    product = session.query(Product).filter_by(id=1).first()
    session.close()
    assert product.review_count == 1
    assert product.rating == 1.0
