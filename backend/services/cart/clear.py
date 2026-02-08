from backend.utils.database import get_db_session
from backend.models import CartItem

def clear_cart(user_id):
    session = get_db_session()
    try:
        session.query(CartItem).filter_by(user_id=user_id).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
