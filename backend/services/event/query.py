from datetime import datetime, timezone, timedelta
from sqlalchemy import desc
from .shared import normalize_user_id
from backend.models import SearchEvent

def _build_event_query(
    session,
    user_id=None,
    event_types=None,
    since_hours=None,
):
    query = session.query(SearchEvent)

    user_id = normalize_user_id(user_id)
    if user_id is not None:
        query = query.filter(SearchEvent.user_id == user_id)

    if event_types:
        query = query.filter(SearchEvent.event_type.in_(event_types))

    if since_hours:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        query = query.filter(SearchEvent.timestamp >= cutoff)

    return query.order_by(desc(SearchEvent.timestamp))
