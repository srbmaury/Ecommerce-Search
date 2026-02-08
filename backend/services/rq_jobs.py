"""
RQ worker for model retraining and user clustering.

Responsibilities:
- Enqueue retrain jobs
- Prevent concurrent retraining via distributed lock
- Run model retrain followed by cluster assignment
- Provide retries, timeouts, and observability
"""

import os
import logging
import redis
from rq import Queue, Retry
from datetime import timedelta

from ml.train_ranker import main as train_ranker_main
from ml.assign_user_clusters import assign_clusters_to_users
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIG ----------

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

QUEUE_NAME = "ml-retrain"
JOB_TIMEOUT_SECONDS = 60 * 60          # 1 hour hard timeout
RESULT_TTL_SECONDS = 24 * 60 * 60      # Keep job result for 24h

RETRAIN_LOCK_KEY = "lock:retrain_and_cluster"
RETRAIN_LOCK_TTL = 60 * 60              # Lock auto-expires after 1h


# ---------- SETUP ----------

logger = logging.getLogger("retrain_worker")

redis_conn = redis.from_url(
    REDIS_URL,
    decode_responses=True,
)

queue = Queue(
    name=QUEUE_NAME,
    connection=redis_conn,
    default_timeout=JOB_TIMEOUT_SECONDS,
)


# ---------- WORKER JOB ----------

def retrain_and_cluster():
    """
    RQ job:
    - Retrains ranking model
    - Reassigns user clusters
    Uses a Redis lock to prevent concurrent execution.
    """
    lock = redis_conn.lock(
        RETRAIN_LOCK_KEY,
        timeout=RETRAIN_LOCK_TTL,
        blocking=False,
    )

    if not lock.acquire(blocking=False):
        logger.warning(
            "Retrain job already running. Skipping duplicate execution."
        )
        return

    try:
        logger.info("[RQ] Starting model retraining")
        train_ranker_main()
        logger.info("[RQ] Model retraining completed")

        logger.info("[RQ] Starting user clustering")
        assign_clusters_to_users()
        logger.info("[RQ] User clustering completed")

    except Exception:
        logger.exception("Retrain + cluster job failed")
        raise

    finally:
        try:
            lock.release()
        except Exception:
            pass


# ---------- ENQUEUE API ----------

def enqueue_retrain_and_cluster():
    """
    Enqueue retrain + clustering job with retries and backoff.
    Safe to call multiple times due to distributed locking.
    """
    return queue.enqueue(
        retrain_and_cluster,
        retry=Retry(
            max=3,
            interval=[60, 300, 900],  # 1m, 5m, 15m
        ),
        job_timeout=JOB_TIMEOUT_SECONDS,
        result_ttl=RESULT_TTL_SECONDS,
    )


# ---------- CLI ----------

def main():
    """CLI entry point - run training directly without RQ."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--enqueue":
        # Enqueue job to RQ (requires worker to be running)
        # Note: This must be called from a separate script, not as __main__
        print("To enqueue jobs, use: python -c \"from backend.services.rq_jobs import enqueue_retrain_and_cluster; enqueue_retrain_and_cluster()\"")
        return
    
    # Run training directly (no RQ)
    print("Running retrain + cluster directly (no RQ)...")
    retrain_and_cluster()
    print("Done!")


if __name__ == "__main__":
    main()
