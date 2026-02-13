from backend.utils.database import get_db_session
from backend.models import User

def create_user(user_id, username, password_hash, group="A", email=None):
    session = get_db_session()
    try:
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            group=group,
            email_verified=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.expunge(user)
        return user
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
