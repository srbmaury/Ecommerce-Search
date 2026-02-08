from .constants import EVENT_THRESHOLD_MODEL, EVENT_THRESHOLD_CLUSTERS, MAX_INTERVAL_MODEL, MAX_INTERVAL_CLUSTERS
from .state import _state

def get_status():
    with _state.lock:
        return {
            "events_since_model_retrain": _state.events_since_model,
            "events_since_cluster_retrain": _state.events_since_cluster,
            "last_model_retrain": (
                _state.last_model_retrain.isoformat()
                if _state.last_model_retrain else None
            ),
            "last_cluster_retrain": (
                _state.last_cluster_retrain.isoformat()
                if _state.last_cluster_retrain else None
            ),
            "model_threshold": EVENT_THRESHOLD_MODEL,
            "cluster_threshold": EVENT_THRESHOLD_CLUSTERS,
            "max_interval_model": MAX_INTERVAL_MODEL,
            "max_interval_clusters": MAX_INTERVAL_CLUSTERS,
        }
