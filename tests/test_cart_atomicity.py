"""
Regression tests for cart write atomicity (backend/services/cart/add.py,
remove.py). These exercise a real (temp, on-disk) SQLite database rather
than mocks, because the whole point is verifying the SQL the upsert/
row-locking code actually emits behaves correctly — a mocked session
can't catch a lost-update race.
"""
import os
import tempfile
import concurrent.futures

import pytest


@pytest.fixture
def cart_db(monkeypatch):
    """A fresh on-disk SQLite DB with just the users/cart_items tables,
    wired up as backend.utils.database's active engine/session factory."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")

    import backend.utils.database as database
    database._engine = None
    database._SessionLocal = None
    engine, _ = database.init_db()

    from backend.models import User, CartItem
    User.__table__.create(bind=engine)
    CartItem.__table__.create(bind=engine)

    from backend.utils.database import get_db_session
    session = get_db_session()
    session.add(User(user_id="u1", username="u1", password_hash="x"))
    session.commit()
    session.close()

    yield

    database._engine = None
    database._SessionLocal = None
    os.remove(path)


def test_concurrent_adds_sum_correctly(cart_db):
    """20 threads each add quantity=1 for the same (user, product) — the
    final quantity must be exactly 20. Under the old SELECT-then-INSERT/
    UPDATE code this is a lost-update race; the upsert makes the increment
    atomic inside the database."""
    from backend.services.cart.add import add_to_cart
    from backend.services.cart.get import get_cart

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(add_to_cart, "u1", 1, 1) for _ in range(20)]
        for f in futures:
            f.result()

    assert get_cart("u1") == {"1": 20}


def test_add_creates_row_when_absent(cart_db):
    from backend.services.cart.add import add_to_cart
    from backend.services.cart.get import get_cart

    add_to_cart("u1", 5, 3)
    assert get_cart("u1") == {"5": 3}


def test_add_increments_existing_row(cart_db):
    from backend.services.cart.add import add_to_cart
    from backend.services.cart.get import get_cart

    add_to_cart("u1", 5, 3)
    add_to_cart("u1", 5, 2)
    assert get_cart("u1") == {"5": 5}


def test_remove_decrements_without_deleting(cart_db):
    from backend.services.cart.add import add_to_cart
    from backend.services.cart.remove import remove_from_cart
    from backend.services.cart.get import get_cart

    add_to_cart("u1", 5, 10)
    assert remove_from_cart("u1", 5, 4) is True
    assert get_cart("u1") == {"5": 6}


def test_remove_deletes_row_when_quantity_hits_zero(cart_db):
    from backend.services.cart.add import add_to_cart
    from backend.services.cart.remove import remove_from_cart
    from backend.services.cart.get import get_cart

    add_to_cart("u1", 5, 3)
    assert remove_from_cart("u1", 5, 3) is True
    assert get_cart("u1") == {}


def test_remove_deletes_row_when_quantity_exceeds_removal(cart_db):
    from backend.services.cart.add import add_to_cart
    from backend.services.cart.remove import remove_from_cart
    from backend.services.cart.get import get_cart

    add_to_cart("u1", 5, 3)
    assert remove_from_cart("u1", 5, 100) is True
    assert get_cart("u1") == {}


def test_remove_nonexistent_row_returns_false(cart_db):
    from backend.services.cart.remove import remove_from_cart

    assert remove_from_cart("u1", 999, 1) is False
