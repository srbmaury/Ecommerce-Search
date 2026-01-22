import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml.user_clustering import cluster_users
from backend.user_manager import load_users, save_users

def assign_clusters_to_users(events_path=None, products_path=None, n_clusters=3):
    clusters = cluster_users(n_clusters, events_path, products_path)
    users = load_users()
    for user in users:
        user_id = user.get("user_id")
        user["cluster"] = int(clusters.get(user_id, -1))
    save_users(users)
    print(f"Assigned clusters to {len(users)} users.")

if __name__ == "__main__":
    assign_clusters_to_users()
