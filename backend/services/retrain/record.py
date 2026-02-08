from .state import _state

def record_event():
    """Call when a user interaction occurs."""
    with _state.lock:
        _state.events_since_model += 1
        _state.events_since_cluster += 1
