from backend.utils.database import get_db_session
from backend.models import CartItem

def remove_from_cart(user_id, product_id, quantity=1):
    """Decrement (or delete, if it would hit zero) a cart row.

    Locks the row with SELECT ... FOR UPDATE first so a concurrent remove
    (or an add racing this decrement) on the same row serializes instead
    of both operating on a stale quantity. SQLite ignores the clause,
    which is fine — it already serializes writers at the file level.
    """
    session = get_db_session()
    try:
        item = (
            session.query(CartItem)
            .filter_by(user_id=user_id, product_id=product_id)
            .with_for_update()
            .first()
        )
        if item:
            if item.quantity > quantity:
                item.quantity -= quantity
            else:
                session.delete(item)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
