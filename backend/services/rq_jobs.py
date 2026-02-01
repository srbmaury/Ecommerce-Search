import os
import sys
import redis
from rq import Queue
from ml.train_ranker import main as train_ranker_main
from ml.assign_user_clusters import assign_clusters_to_users

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)
q = Queue(connection=redis_conn)


def retrain_and_cluster():
    print("[RQ] Starting model retraining...")
    train_ranker_main()
    print("[RQ] Model retraining complete. Starting user clustering...")
    assign_clusters_to_users()
    print("[RQ] User clustering complete.")

def enqueue_retrain_and_cluster():
    return q.enqueue(retrain_and_cluster)

if __name__ == "__main__":
    job = enqueue_retrain_and_cluster()
    print(f"Enqueued retrain+cluster job: {job.id}")
