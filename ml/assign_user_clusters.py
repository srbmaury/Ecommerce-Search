import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml.user_clustering import cluster_users
from backend.db_user_manager import get_db_session
from backend.models import User

def assign_clusters_to_users(n_clusters=3):
    """Assign clusters to users using database data."""
    print("🧠 Clustering users from database...")
    clusters = cluster_users(n_clusters)
    
    if not clusters:
        print("⚠️  No users to cluster. Generate some events first.")
        return
    
    print(f"✓ Clustered {len(clusters)} users")
    print("💾 Updating cluster assignments in database...")
    
    session = get_db_session()
    try:
        updated = 0
        for user_id, cluster_id in clusters.items():
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.cluster = int(cluster_id)
                updated += 1
        
        session.commit()
        print(f"✅ Updated {updated} user clusters in database")
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating clusters: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    assign_clusters_to_users()
