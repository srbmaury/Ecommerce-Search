from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from backend.utils.database import get_db_session
from backend.models import CartItem, utcnow

def add_to_cart(user_id, product_id, quantity=1):
    """Atomically upsert a cart row: insert if absent, otherwise increment
    quantity in a single statement. Two concurrent adds for the same
    (user_id, product_id) can no longer race on a separate SELECT-then-
    INSERT/UPDATE — the increment happens inside the database.
    """
    session = get_db_session()
    try:
        insert_fn = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
        stmt = insert_fn(CartItem).values(
            user_id=user_id, product_id=product_id, quantity=quantity
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "product_id"],
            set_={
                "quantity": CartItem.__table__.c.quantity + stmt.excluded.quantity,
                "updated_at": utcnow(),
            },
        )
        session.execute(stmt)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
