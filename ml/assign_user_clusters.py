import logging
from typing import Dict

from ml.user_clustering import cluster_users
from backend.utils.database import get_db_session
from backend.models import User


logger = logging.getLogger(__name__)


def update_user_clusters(
    clusters: Dict[str, int],
    session
) -> int:
    """
    Update user cluster assignments in the database.

    Returns:
        Number of users updated
    """
    updated = 0

    for user_id, cluster_id in clusters.items():
        user = session.query(User).filter_by(user_id=user_id).first()
        if user:
            user.cluster = int(cluster_id)
            updated += 1

    return updated


def assign_clusters_to_users(n_clusters: int = 3) -> int:
    """
    Run user clustering and persist cluster assignments.

    Returns:
        Number of users updated
    """
    logger.info("Clustering users from database (n_clusters=%d)", n_clusters)

    clusters = cluster_users(n_clusters)

    if not clusters:
        logger.warning("No users to cluster. Generate some events first.")
        return 0

    logger.info("Clustered %d users", len(clusters))
    logger.info("Updating cluster assignments in database")

    session = get_db_session()
    try:
        updated = update_user_clusters(clusters, session)
        session.commit()

        logger.info("Updated %d user clusters in database", updated)
        return updated

    except Exception:
        session.rollback()
        logger.exception("Error updating user clusters")
        raise

    finally:
        session.close()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    assign_clusters_to_users()


if __name__ == "__main__":
    main()
