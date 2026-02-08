from datetime import datetime, timezone
from .state import _state

def mark_model_retrained():
    with _state.lock:
        _state.events_since_model = 0
        _state.last_model_retrain = datetime.now(timezone.utc)

def mark_clusters_retrained():
    with _state.lock:
        _state.events_since_cluster = 0
        _state.last_cluster_retrain = datetime.now(timezone.utc)
