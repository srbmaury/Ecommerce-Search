from backend.utils.database import get_db_session
from backend.models import User

def get_user_by_id(user_id):
    session = get_db_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        return user
    finally:
        session.close()
