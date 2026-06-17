import logging
from datetime import datetime, timezone, timedelta

from backend.services.event.creation import create_search_event
from backend.services.event.query import _build_event_query
from backend.services.event.convert import _events_to_dataframe
from backend.utils.database import get_db_session
from backend.models import SearchEvent

logger = logging.getLogger("event_logger")

def get_events_df(
    since_hours=None,
    limit=1000,
    user_id=None,
    event_types=None,
):
    with get_db_session() as session:
        query = _build_event_query(
            session,
            user_id=user_id,
            event_types=event_types,
            since_hours=since_hours,
        )
        events = query.limit(limit).all()
        return _events_to_dataframe(events)

def get_user_recent_events(user_id, event_types=None, limit=20):
    with get_db_session() as session:
        query = _build_event_query(
            session,
            user_id=user_id,
            event_types=event_types,
        )
        return query.limit(limit).all()

def count_events_since(since_timestamp):
    with get_db_session() as session:
        return (
            session.query(SearchEvent)
            .filter(SearchEvent.timestamp >= since_timestamp)
            .count()
        )


def purge_old_events(retention_days: int = 90) -> int:
    """Delete search events older than retention_days. Returns count deleted."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    try:
        with get_db_session() as session:
            deleted = (
                session.query(SearchEvent)
                .filter(SearchEvent.timestamp < cutoff)
                .delete(synchronize_session=False)
            )
            session.commit()
            logger.info("Purged %d events older than %d days", deleted, retention_days)
            return deleted
    except Exception:
        logger.exception("Failed to purge old events")
        return 0
