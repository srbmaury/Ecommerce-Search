"""
Retrain trigger service - manages when to retrain model and clusters.

Strategies:
- Event-based: Retrain after N new events
- Time-based: Retrain after max interval (fallback)
- Separate intervals for clusters vs model
"""
import threading
import time
from datetime import datetime, timezone

# Thresholds
EVENT_THRESHOLD_MODEL = 500      # Retrain model after 500 new events
EVENT_THRESHOLD_CLUSTERS = 200   # Re-cluster after 200 new events
MAX_INTERVAL_MODEL = 24 * 60 * 60      # Max 24h between model retrains
MAX_INTERVAL_CLUSTERS = 6 * 60 * 60    # Max 6h between cluster updates

# State
_lock = threading.Lock()
_events_since_model_retrain = 0
_events_since_cluster_retrain = 0
_last_model_retrain = None
_last_cluster_retrain = None


def record_event():
    """Call this when a new event (click/add_to_cart) is logged."""
    global _events_since_model_retrain, _events_since_cluster_retrain
    with _lock:
        _events_since_model_retrain += 1
        _events_since_cluster_retrain += 1


def should_retrain_model():
    """Check if model should be retrained based on events or time."""
    global _events_since_model_retrain, _last_model_retrain
    with _lock:
        now = datetime.now(timezone.utc)

        # Event threshold reached
        if _events_since_model_retrain >= EVENT_THRESHOLD_MODEL:
            return True

        # Max time interval reached
        if _last_model_retrain is None:
            return True
        if (now - _last_model_retrain).total_seconds() >= MAX_INTERVAL_MODEL:
            return True

        return False


def should_retrain_clusters():
    """Check if clusters should be updated based on events or time."""
    global _events_since_cluster_retrain, _last_cluster_retrain
    with _lock:
        now = datetime.now(timezone.utc)

        # Event threshold reached
        if _events_since_cluster_retrain >= EVENT_THRESHOLD_CLUSTERS:
            return True

        # Max time interval reached
        if _last_cluster_retrain is None:
            return True
        if (now - _last_cluster_retrain).total_seconds() >= MAX_INTERVAL_CLUSTERS:
            return True

        return False


def mark_model_retrained():
    """Call after successful model retrain."""
    global _events_since_model_retrain, _last_model_retrain
    with _lock:
        _events_since_model_retrain = 0
        _last_model_retrain = datetime.now(timezone.utc)


def mark_clusters_retrained():
    """Call after successful cluster update."""
    global _events_since_cluster_retrain, _last_cluster_retrain
    with _lock:
        _events_since_cluster_retrain = 0
        _last_cluster_retrain = datetime.now(timezone.utc)


def get_status():
    """Get current retrain status for monitoring."""
    with _lock:
        return {
            "events_since_model_retrain": _events_since_model_retrain,
            "events_since_cluster_retrain": _events_since_cluster_retrain,
            "last_model_retrain": _last_model_retrain.isoformat() if _last_model_retrain else None,
            "last_cluster_retrain": _last_cluster_retrain.isoformat() if _last_cluster_retrain else None,
            "model_threshold": EVENT_THRESHOLD_MODEL,
            "cluster_threshold": EVENT_THRESHOLD_CLUSTERS,
        }
