from backend.services.event.shared import normalize_user_id
from backend.services.event.creation import create_search_event
from backend.services.event.query import _build_event_query
from backend.services.event.convert import _events_to_dataframe
from backend.utils.database import get_db_session
from backend.models import SearchEvent
from sqlalchemy import and_

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

def get_user_interactions(user_id, product_ids):
    user_id = normalize_user_id(user_id)
    if not user_id or not product_ids:
        return []
    with get_db_session() as session:
        return (
            session.query(SearchEvent)
            .filter(
                SearchEvent.user_id == user_id,
                SearchEvent.product_id.in_(product_ids),
            )
            .order_by(SearchEvent.timestamp.desc())
            .all()
        )

def count_events_since(since_timestamp):
    with get_db_session() as session:
        return (
            session.query(SearchEvent)
            .filter(SearchEvent.timestamp >= since_timestamp)
            .count()
        )
