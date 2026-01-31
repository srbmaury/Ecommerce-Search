import datetime
import logging
from backend.database import get_db_session
from backend.models import SearchEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    session = get_db_session()
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=180)

    deleted = (
        session.query(SearchEvent)
        .filter(SearchEvent.timestamp < cutoff)
        .delete(synchronize_session=False)
    )

    session.commit()
    session.close()

    logger.info(f"Deleted {deleted} search events older than 6 months")

if __name__ == "__main__":
    main()