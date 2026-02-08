from backend.utils.database import get_db_session
from backend.models import CartItem

def add_to_cart(user_id, product_id, quantity=1):
    session = get_db_session()
    try:
        item = session.query(CartItem).filter_by(user_id=user_id, product_id=product_id).first()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            session.add(item)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
