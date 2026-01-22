import threading
import subprocess
import time
import logging
import sys
import os

logger = logging.getLogger(__name__)

# Compute project root directory (parent of backend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def retrain_job():
    while True:
        try:
            logger.info("Auto retrain started")
            # Use sys.executable to ensure we use the same Python interpreter as the Flask app
            subprocess.run([sys.executable, os.path.join(PROJECT_ROOT, "ml/train_ranker.py")], check=True, cwd=PROJECT_ROOT)
            subprocess.run([sys.executable, os.path.join(PROJECT_ROOT, "ml/assign_user_clusters.py")], check=True, cwd=PROJECT_ROOT)
            logger.info("Auto retrain finished")
        except Exception:
            logger.exception("Auto retrain failed")

        time.sleep(60 * 60 * 24)

def start_scheduler():
    threading.Thread(target=retrain_job, daemon=True).start()
