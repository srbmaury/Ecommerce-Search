from backend.utils.database import get_db_session
from backend.models import CartItem

def get_cart(user_id):
    session = get_db_session()
    try:
        items = session.query(CartItem).filter_by(user_id=user_id).limit(100).all()
        return {str(item.product_id): item.quantity for item in items}
    finally:
        session.close()
