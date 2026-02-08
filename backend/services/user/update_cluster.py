from backend.utils.database import get_db_session
from backend.models import User

def update_user_cluster(user_id, cluster):
    session = get_db_session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.cluster = cluster
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
