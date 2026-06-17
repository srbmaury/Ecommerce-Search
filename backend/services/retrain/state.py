import threading
from datetime import datetime


_KEY_LAST_MODEL = "retrain:last_model"
_KEY_LAST_CLUSTER = "retrain:last_cluster"
_KEY_EVENTS_MODEL = "retrain:events_model"
_KEY_EVENTS_CLUSTER = "retrain:events_cluster"


def _load_int(r, key: str) -> int:
    try:
        val = r.get(key)
        return int(val) if val else 0
    except Exception:
        return 0


def _load_datetime(r, key: str):
    try:
        val = r.get(key)
        return datetime.fromisoformat(val) if val else None
    except Exception:
        return None


class RetrainState:
    def __init__(self):
        self.lock = threading.Lock()
        try:
            from backend.services.redis_client import _redis
            self._r = _redis
        except Exception:
            self._r = None

        self._events_since_model = _load_int(self._r, _KEY_EVENTS_MODEL) if self._r else 0
        self._events_since_cluster = _load_int(self._r, _KEY_EVENTS_CLUSTER) if self._r else 0
        self._last_model_retrain = _load_datetime(self._r, _KEY_LAST_MODEL) if self._r else None
        self._last_cluster_retrain = _load_datetime(self._r, _KEY_LAST_CLUSTER) if self._r else None

    def _rset(self, key: str, value) -> None:
        if self._r:
            try:
                self._r.set(key, value)
            except Exception:
                pass

    @property
    def events_since_model(self) -> int:
        return self._events_since_model

    @events_since_model.setter
    def events_since_model(self, value: int) -> None:
        self._events_since_model = value
        self._rset(_KEY_EVENTS_MODEL, value)

    @property
    def events_since_cluster(self) -> int:
        return self._events_since_cluster

    @events_since_cluster.setter
    def events_since_cluster(self, value: int) -> None:
        self._events_since_cluster = value
        self._rset(_KEY_EVENTS_CLUSTER, value)

    @property
    def last_model_retrain(self):
        return self._last_model_retrain

    @last_model_retrain.setter
    def last_model_retrain(self, value) -> None:
        self._last_model_retrain = value
        if value is not None:
            self._rset(_KEY_LAST_MODEL, value.isoformat())

    @property
    def last_cluster_retrain(self):
        return self._last_cluster_retrain

    @last_cluster_retrain.setter
    def last_cluster_retrain(self, value) -> None:
        self._last_cluster_retrain = value
        if value is not None:
            self._rset(_KEY_LAST_CLUSTER, value.isoformat())


_state = RetrainState()
