"""
RQ worker entrypoint.

Listens to one or more queues and executes background jobs.
"""

import os
import redis
from rq import Worker, Queue
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIG ----------

QUEUE_NAMES = os.getenv("RQ_QUEUES", "default").split(",")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


# ---------- WORKER ----------

def main():
    redis_conn = redis.from_url(REDIS_URL)

    queues = [Queue(name.strip(), connection=redis_conn) for name in QUEUE_NAMES]

    worker = Worker(queues, connection=redis_conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
