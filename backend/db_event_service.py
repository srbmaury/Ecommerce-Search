"""
Database service for search event operations.
"""
import pandas as pd
from datetime import datetime, timezone, timedelta
from sqlalchemy import desc, and_
from backend.database import get_db_session
from backend.models import SearchEvent


def create_search_event(user_id, query, product_id, event_type, group='A', position=None):
    """Create a new search event."""
    session = get_db_session()
    try:
        event = SearchEvent(
            user_id=user_id,
            query=query,
            product_id=int(product_id) if product_id else None,
            event_type=event_type,
            group=group,
            position=position,
            timestamp=datetime.now(timezone.utc)
        )
        session.add(event)
        session.commit()
        return event
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_events_df(since_hours=None, limit=None):
    """Get search events as a pandas DataFrame (for ML compatibility)."""
    session = get_db_session()
    try:
        query = session.query(SearchEvent)
        
        if since_hours:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
            query = query.filter(SearchEvent.timestamp >= cutoff)
        
        query = query.order_by(desc(SearchEvent.timestamp))
        
        # Apply limit if specified to prevent loading too much data
        if limit:
            query = query.limit(limit)
        
        events = query.all()
        
        if not events:
            return pd.DataFrame()
        
        events_data = [{
            'user_id': e.user_id,
            'query': e.query,
            'product_id': e.product_id,
            'event': e.event_type,  # Use 'event' for backwards compatibility
            'timestamp': e.timestamp,
            'group': e.group,
            'position': e.position
        } for e in events]
        
        df = pd.DataFrame(events_data)
        return df
    finally:
        session.close()


def get_user_recent_events(user_id, event_types=None, limit=20):
    """Get recent events for a specific user."""
    session = get_db_session()
    try:
        query = session.query(SearchEvent).filter_by(user_id=user_id)
        
        if event_types:
            query = query.filter(SearchEvent.event_type.in_(event_types))
        
        events = query.order_by(desc(SearchEvent.timestamp)).limit(limit).all()
        return events
    finally:
        session.close()


def get_user_interactions(user_id, product_ids):
    """Get user interactions with specific products."""
    session = get_db_session()
    try:
        events = session.query(SearchEvent).filter(
            and_(
                SearchEvent.user_id == user_id,
                SearchEvent.product_id.in_([str(pid) for pid in product_ids])
            )
        ).order_by(desc(SearchEvent.timestamp)).all()
        return events
    finally:
        session.close()


def _escape_ilike_pattern(value):
    """
    Escape special characters used in SQL ILIKE patterns.

    Escapes %, _ and \\ so that user input cannot change the pattern
    semantics. Use together with escape='\\' in ilike().
    """
    if value is None:
        return ""
    # First escape backslash itself, then % and _
    value = str(value)
    value = value.replace("\\", "\\\\")
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    return value


def get_events_by_query(query_text, limit=100):
    """Get events matching a query."""
    session = get_db_session()
    try:
        escaped_query = _escape_ilike_pattern(query_text)
        pattern = f'%{escaped_query}%'
        events = session.query(SearchEvent).filter(
            SearchEvent.query.ilike(pattern, escape='\\')
        ).order_by(desc(SearchEvent.timestamp)).limit(limit).all()
        return events
    finally:
        session.close()


def count_events_since(since_timestamp):
    """Count events since a specific timestamp."""
    session = get_db_session()
    try:
        count = session.query(SearchEvent).filter(
            SearchEvent.timestamp >= since_timestamp
        ).count()
        return count
    finally:
        session.close()
