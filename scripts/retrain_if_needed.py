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
from backend.services.rq_jobs import enqueue_retrain_and_cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def retrain_and_cluster():
    logger.info("Enqueuing retrain+cluster job to RQ...")
    job = enqueue_retrain_and_cluster()
    logger.info(f"Enqueued retrain+cluster job: {job.id}")
    mark_model_retrained()
    mark_clusters_retrained()

def main():
    status = get_status()

    # Only enqueue if either retrain or clustering is needed
    if should_retrain_model() or should_retrain_clusters():
        logger.info("Retrain or clustering needed. Enqueuing combined job...")
        retrain_and_cluster()
    else:
        logger.info("No retrain or clustering needed at this time.")

if __name__ == "__main__":
    main()