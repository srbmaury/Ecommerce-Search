from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import pandas as pd
from sqlalchemy import desc, and_
import logging

from backend.utils.database import get_db_session
from backend.models import SearchEvent

logger = logging.getLogger("event_logger")

@contextmanager
def session_scope():
    session = get_db_session()
    try:
        yield session
        session.commit()
        logger.info("session_scope: commit successful")
    except Exception as e:
        logger.error(f"session_scope: rollback due to {e}")
        session.rollback()
        raise
    finally:
        session.close()

def normalize_user_id(user_id):
    """
    Normalize user_id for consistent querying.
    Empty / None represents anonymous users.
    """
    if user_id is None:
        return None
    user_id = str(user_id).strip()
    return user_id if user_id else None
