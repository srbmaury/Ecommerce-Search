import threading

class RetrainState:
    def __init__(self):
        self.events_since_model = 0
        self.events_since_cluster = 0
        self.last_model_retrain = None
        self.last_cluster_retrain = None
        self.lock = threading.Lock()

_state = RetrainState()
