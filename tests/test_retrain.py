"""Tests for backend/services/retrain/ — event counting, thresholds, and marking."""

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state_with_mock_redis():
    """Return a fresh RetrainState backed by a mock Redis client."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None  # cold start — no persisted values
    with patch("backend.services.redis_client._redis", mock_redis):
        from backend.services.retrain import state as state_mod
        import importlib
        importlib.reload(state_mod)
        return state_mod._state, mock_redis


# ---------------------------------------------------------------------------
# record_event
# ---------------------------------------------------------------------------

class TestRecordEvent:
    def test_increments_both_counters(self):
        from backend.services.retrain.state import _state
        before_model = _state.events_since_model
        before_cluster = _state.events_since_cluster

        from backend.services.retrain.record import record_event
        record_event()

        assert _state.events_since_model == before_model + 1
        assert _state.events_since_cluster == before_cluster + 1

    def test_multiple_events_accumulate(self):
        from backend.services.retrain.state import _state
        from backend.services.retrain.record import record_event

        before = _state.events_since_model
        for _ in range(5):
            record_event()

        assert _state.events_since_model == before + 5


# ---------------------------------------------------------------------------
# should_retrain_model / should_retrain_clusters
# ---------------------------------------------------------------------------

class TestShouldRetrainModel:
    def setup_method(self):
        from backend.services.retrain.state import _state
        self.state = _state
        # Reset to clean slate
        self.state._events_since_model = 0
        self.state._last_model_retrain = datetime.now(timezone.utc)

    def test_below_threshold_no_retrain(self):
        from backend.services.retrain.decision import should_retrain_model
        from backend.services.retrain.constants import EVENT_THRESHOLD_MODEL
        self.state._events_since_model = EVENT_THRESHOLD_MODEL - 1

        should, reason = should_retrain_model()
        assert should is False
        assert reason is None

    def test_at_threshold_triggers_retrain(self):
        from backend.services.retrain.decision import should_retrain_model
        from backend.services.retrain.constants import EVENT_THRESHOLD_MODEL
        self.state._events_since_model = EVENT_THRESHOLD_MODEL

        should, reason = should_retrain_model()
        assert should is True
        assert reason == "event_threshold"

    def test_time_threshold_fires_when_last_retrain_is_old(self):
        from backend.services.retrain.decision import should_retrain_model
        from backend.services.retrain.constants import MAX_INTERVAL_MODEL
        self.state._events_since_model = 0
        self.state._last_model_retrain = (
            datetime.now(timezone.utc) - timedelta(seconds=MAX_INTERVAL_MODEL + 1)
        )

        should, reason = should_retrain_model()
        assert should is True
        assert reason == "time_threshold"

    def test_none_last_retrain_fires_time_threshold(self):
        from backend.services.retrain.decision import should_retrain_model
        self.state._events_since_model = 0
        self.state._last_model_retrain = None

        should, reason = should_retrain_model()
        assert should is True
        assert reason == "time_threshold"

    def test_recent_retrain_within_interval_no_trigger(self):
        from backend.services.retrain.decision import should_retrain_model
        self.state._events_since_model = 0
        self.state._last_model_retrain = datetime.now(timezone.utc) - timedelta(hours=1)

        should, _ = should_retrain_model()
        assert should is False


class TestShouldRetrainClusters:
    def setup_method(self):
        from backend.services.retrain.state import _state
        self.state = _state
        self.state._events_since_cluster = 0
        self.state._last_cluster_retrain = datetime.now(timezone.utc)

    def test_below_threshold_no_retrain(self):
        from backend.services.retrain.decision import should_retrain_clusters
        from backend.services.retrain.constants import EVENT_THRESHOLD_CLUSTERS
        self.state._events_since_cluster = EVENT_THRESHOLD_CLUSTERS - 1

        should, reason = should_retrain_clusters()
        assert should is False

    def test_at_threshold_triggers(self):
        from backend.services.retrain.decision import should_retrain_clusters
        from backend.services.retrain.constants import EVENT_THRESHOLD_CLUSTERS
        self.state._events_since_cluster = EVENT_THRESHOLD_CLUSTERS

        should, reason = should_retrain_clusters()
        assert should is True
        assert reason == "event_threshold"


# ---------------------------------------------------------------------------
# mark_model_retrained / mark_clusters_retrained
# ---------------------------------------------------------------------------

class TestMarkRetrained:
    def setup_method(self):
        from backend.services.retrain.state import _state
        self.state = _state
        self.state._events_since_model = 999
        self.state._events_since_cluster = 888
        self.state._last_model_retrain = None
        self.state._last_cluster_retrain = None

    def test_mark_model_resets_counter(self):
        from backend.services.retrain.mark import mark_model_retrained
        mark_model_retrained()
        assert self.state.events_since_model == 0

    def test_mark_model_sets_timestamp(self):
        from backend.services.retrain.mark import mark_model_retrained
        before = datetime.now(timezone.utc)
        mark_model_retrained()
        assert self.state.last_model_retrain is not None
        assert self.state.last_model_retrain >= before

    def test_mark_clusters_resets_counter(self):
        from backend.services.retrain.mark import mark_clusters_retrained
        mark_clusters_retrained()
        assert self.state.events_since_cluster == 0

    def test_mark_clusters_sets_timestamp(self):
        from backend.services.retrain.mark import mark_clusters_retrained
        before = datetime.now(timezone.utc)
        mark_clusters_retrained()
        assert self.state.last_cluster_retrain is not None
        assert self.state.last_cluster_retrain >= before

    def test_after_mark_model_no_immediate_retrain(self):
        from backend.services.retrain.mark import mark_model_retrained
        from backend.services.retrain.decision import should_retrain_model

        self.state._events_since_model = 999
        mark_model_retrained()

        should, _ = should_retrain_model()
        assert should is False


# ---------------------------------------------------------------------------
# RetrainState — Redis persistence
# ---------------------------------------------------------------------------

class TestRetrainStateRedisPersistence:
    def test_setter_writes_to_redis(self):
        """Setting events_since_model should call redis.set."""
        mock_r = MagicMock()
        from backend.services.retrain.state import _state
        original_r = _state._r
        try:
            _state._r = mock_r
            _state.events_since_model = 42
            mock_r.set.assert_called()
        finally:
            _state._r = original_r

    def test_setter_handles_redis_failure_gracefully(self):
        """Redis write failure must not propagate."""
        mock_r = MagicMock()
        mock_r.set.side_effect = ConnectionError("Redis down")
        from backend.services.retrain.state import _state
        original_r = _state._r
        try:
            _state._r = mock_r
            # Should not raise
            _state.events_since_model = 10
            assert _state._events_since_model == 10
        finally:
            _state._r = original_r

    def test_timestamp_setter_persists_isoformat(self):
        mock_r = MagicMock()
        from backend.services.retrain.state import _state
        original_r = _state._r
        try:
            _state._r = mock_r
            ts = datetime.now(timezone.utc)
            _state.last_model_retrain = ts
            mock_r.set.assert_called_with(
                "retrain:last_model", ts.isoformat()
            )
        finally:
            _state._r = original_r
