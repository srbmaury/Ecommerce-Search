import threading
import subprocess
import time
import logging
import sys
import os

from backend.services.retrain_trigger import (
    should_retrain_model,
    should_retrain_clusters,
    mark_model_retrained,
    mark_clusters_retrained,
    get_status
)

logger = logging.getLogger(__name__)

# Compute project root directory (parent of backend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Check interval - how often to check if retrain is needed
CHECK_INTERVAL = 60  # Check every 60 seconds


def retrain_model():
    """Retrain the ML ranking model."""
    try:
        logger.info("Retraining ML model...")
        subprocess.run(
            [sys.executable, "-m", "ml.train_ranker"],
            check=True,
            cwd=PROJECT_ROOT
        )
        mark_model_retrained()
        logger.info("ML model retrained successfully")
        return True
    except Exception:
        logger.exception("ML model retrain failed")
        return False


def retrain_clusters():
    """Re-assign user clusters."""
    try:
        logger.info("Updating user clusters...")
        subprocess.run(
            [sys.executable, "-m", "ml.assign_user_clusters"],
            check=True,
            cwd=PROJECT_ROOT
        )
        mark_clusters_retrained()
        logger.info("User clusters updated successfully")
        return True
    except Exception:
        logger.exception("Cluster update failed")
        return False


def retrain_job():
    """Main scheduler loop - checks triggers and runs retrains as needed."""
    # Initial retrain on startup
    logger.info("Initial retrain on startup")
    retrain_model()
    retrain_clusters()

    while True:
        time.sleep(CHECK_INTERVAL)

        try:
            # Check if model needs retraining
            if should_retrain_model():
                status = get_status()
                logger.info(
                    f"Model retrain triggered: {status['events_since_model_retrain']} events"
                )
                retrain_model()

            # Check if clusters need updating (independent of model)
            if should_retrain_clusters():
                status = get_status()
                logger.info(
                    f"Cluster update triggered: {status['events_since_cluster_retrain']} events"
                )
                retrain_clusters()

        except Exception:
            logger.exception("Scheduler check failed")


def start_scheduler():
    threading.Thread(target=retrain_job, daemon=True).start()
