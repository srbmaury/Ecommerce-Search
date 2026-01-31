import logging
import subprocess
import sys
import os
from backend.services.retrain_trigger import (
    should_retrain_model,
    should_retrain_clusters,
    mark_model_retrained,
    mark_clusters_retrained,
    get_status
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def retrain_model():
    logger.info("Retraining ML model")
    subprocess.run(
        [sys.executable, "-m", "ml.train_ranker"],
        check=True,
        cwd=PROJECT_ROOT
    )
    mark_model_retrained()

def retrain_clusters():
    logger.info("Updating user clusters")
    subprocess.run(
        [sys.executable, "-m", "ml.assign_user_clusters"],
        check=True,
        cwd=PROJECT_ROOT
    )
    mark_clusters_retrained()

def main():
    status = get_status()

    if should_retrain_model():
        logger.info(
            f"Model retrain triggered after {status['events_since_model_retrain']} events"
        )
        retrain_model()

    if should_retrain_clusters():
        logger.info(
            f"Cluster update triggered after {status['events_since_cluster_retrain']} events"
        )
        retrain_clusters()

if __name__ == "__main__":
    main()