from datetime import datetime, timezone
from .shared import session_scope, normalize_user_id, logger
from backend.models import SearchEvent

def create_search_event(
    user_id,
    query,
    product_id,
    event_type,
    group="A",
    position=None,
):
    normalized_user_id = normalize_user_id(user_id) or ""
    logger.info(f"create_search_event called: user_id={user_id}, normalized={normalized_user_id}, product_id={product_id}, event_type={event_type}")
    with session_scope() as session:
        event = SearchEvent(
            user_id=normalized_user_id,
            query=query,
            product_id=int(product_id) if product_id else None,
            event_type=event_type,
            group=group,
            position=position,
            timestamp=datetime.now(timezone.utc),
        )
        logger.info(f"Adding SearchEvent: {event}")
        session.add(event)
        return event
