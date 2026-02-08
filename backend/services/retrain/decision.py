from datetime import datetime, timezone
from .constants import EVENT_THRESHOLD_MODEL, EVENT_THRESHOLD_CLUSTERS, MAX_INTERVAL_MODEL, MAX_INTERVAL_CLUSTERS
from .state import _state

def _time_elapsed(last_time, max_interval):
    if last_time is None:
        return True
    return (
        datetime.now(timezone.utc) - last_time
    ).total_seconds() >= max_interval

def should_retrain_model():
    with _state.lock:
        if _state.events_since_model >= EVENT_THRESHOLD_MODEL:
            return True, "event_threshold"
        if _time_elapsed(_state.last_model_retrain, MAX_INTERVAL_MODEL):
            return True, "time_threshold"
        return False, None

def should_retrain_clusters():
    with _state.lock:
        if _state.events_since_cluster >= EVENT_THRESHOLD_CLUSTERS:
            return True, "event_threshold"
        if _time_elapsed(_state.last_cluster_retrain, MAX_INTERVAL_CLUSTERS):
            return True, "time_threshold"
        return False, None
