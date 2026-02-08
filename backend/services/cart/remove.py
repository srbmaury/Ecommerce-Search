from backend.utils.database import get_db_session
from backend.models import CartItem

def remove_from_cart(user_id, product_id, quantity=1):
    session = get_db_session()
    try:
        item = session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()
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
