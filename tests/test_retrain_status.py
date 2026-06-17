"""Tests for backend/services/retrain/status.py — status dict structure and values."""

from datetime import datetime, timezone, timedelta
import pytest

from backend.services.retrain.state import _state
from backend.services.retrain.status import get_status
from backend.services.retrain.constants import (
    EVENT_THRESHOLD_MODEL,
    EVENT_THRESHOLD_CLUSTERS,
    MAX_INTERVAL_MODEL,
    MAX_INTERVAL_CLUSTERS,
)


class TestGetStatus:
    def test_returns_all_required_keys(self):
        status = get_status()
        required = {
            "events_since_model_retrain",
            "events_since_cluster_retrain",
            "last_model_retrain",
            "last_cluster_retrain",
            "model_threshold",
            "cluster_threshold",
            "max_interval_model",
            "max_interval_clusters",
        }
        assert required.issubset(set(status.keys()))

    def test_thresholds_match_constants(self):
        status = get_status()
        assert status["model_threshold"] == EVENT_THRESHOLD_MODEL
        assert status["cluster_threshold"] == EVENT_THRESHOLD_CLUSTERS
        assert status["max_interval_model"] == MAX_INTERVAL_MODEL
        assert status["max_interval_clusters"] == MAX_INTERVAL_CLUSTERS

    def test_event_counts_are_integers(self):
        status = get_status()
        assert isinstance(status["events_since_model_retrain"], int)
        assert isinstance(status["events_since_cluster_retrain"], int)

    def test_last_retrain_none_when_not_yet_run(self):
        # Set to None, check status reflects that
        _state._last_model_retrain = None
        status = get_status()
        assert status["last_model_retrain"] is None

    def test_last_retrain_iso_format_when_set(self):
        ts = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        _state._last_model_retrain = ts
        status = get_status()
        # Should be an ISO-formatted string
        assert status["last_model_retrain"] == ts.isoformat()

    def test_event_counts_reflect_state(self):
        _state._events_since_model = 42
        _state._events_since_cluster = 17
        status = get_status()
        assert status["events_since_model_retrain"] == 42
        assert status["events_since_cluster_retrain"] == 17

    def test_thresholds_are_positive(self):
        status = get_status()
        assert status["model_threshold"] > 0
        assert status["cluster_threshold"] > 0
        assert status["max_interval_model"] > 0
        assert status["max_interval_clusters"] > 0
