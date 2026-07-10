"""
Tests for backend/services/cache_invalidation.py.
All Redis calls are mocked — no live Redis required.
"""

from unittest.mock import MagicMock, patch, call
import pytest

import backend.services.cache_invalidation as ci


def _mock_redis():
    m = MagicMock()
    m.scan_iter.return_value = []
    m.delete.return_value = 0
    m.get.return_value = None
    return m


# ---- get_cache_stats ----

class TestGetCacheStats:
    def test_returns_zeros_when_redis_has_none(self):
        mock_r = _mock_redis()
        with patch.object(ci, "_redis", mock_r):
            stats = ci.get_cache_stats()
        assert stats == {"hits": 0, "misses": 0, "invalidations": 0, "hit_rate": 0.0}

    def test_computes_hit_rate_correctly(self):
        mock_r = _mock_redis()
        mock_r.get.side_effect = lambda key: {
            "cache:hits": "80",
            "cache:misses": "20",
            "cache:invalidations": "3",
        }.get(key)
        with patch.object(ci, "_redis", mock_r):
            stats = ci.get_cache_stats()
        assert stats["hit_rate"] == pytest.approx(0.8)
        assert stats["hits"] == 80
        assert stats["misses"] == 20
        assert stats["invalidations"] == 3

    def test_returns_zeros_on_redis_failure(self):
        mock_r = _mock_redis()
        mock_r.get.side_effect = ConnectionError("Redis down")
        with patch.object(ci, "_redis", mock_r):
            stats = ci.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_hit_rate_zero_when_no_requests(self):
        mock_r = _mock_redis()
        mock_r.get.return_value = "0"
        with patch.object(ci, "_redis", mock_r):
            stats = ci.get_cache_stats()
        assert stats["hit_rate"] == 0.0


# ---- reset_cache_stats ----

class TestResetCacheStats:
    def test_sets_all_three_keys_to_zero(self):
        mock_r = _mock_redis()
        with patch.object(ci, "_redis", mock_r):
            ci.reset_cache_stats()
        calls = mock_r.set.call_args_list
        keys_set = {c[0][0] for c in calls}
        assert "cache:hits" in keys_set
        assert "cache:misses" in keys_set
        assert "cache:invalidations" in keys_set
        values_set = {c[0][1] for c in calls}
        assert values_set == {0}

    def test_redis_failure_does_not_raise(self):
        mock_r = _mock_redis()
        mock_r.set.side_effect = ConnectionError
        with patch.object(ci, "_redis", mock_r):
            ci.reset_cache_stats()  # must not raise


# ---- invalidate_cluster_boost ----

class TestInvalidateClusterBoost:
    def test_calls_delete_with_correct_key(self):
        mock_r = _mock_redis()
        mock_r.delete.return_value = 1
        with patch.object(ci, "_redis", mock_r):
            result = ci.invalidate_cluster_boost(3)
        mock_r.delete.assert_called_with("cluster_boost:3")
        assert result is True

    def test_none_cluster_returns_false(self):
        mock_r = _mock_redis()
        with patch.object(ci, "_redis", mock_r):
            result = ci.invalidate_cluster_boost(None)
        assert result is False
        mock_r.delete.assert_not_called()

    def test_returns_false_when_key_not_found(self):
        mock_r = _mock_redis()
        mock_r.delete.return_value = 0
        with patch.object(ci, "_redis", mock_r):
            result = ci.invalidate_cluster_boost(5)
        assert result is False


# ---- invalidate_on_user_event ----

class TestInvalidateOnUserEvent:
    def test_click_event_deletes_recommendations_and_recent_boost(self):
        mock_r = _mock_redis()
        mock_r.delete.return_value = 1
        with patch.object(ci, "_redis", mock_r):
            result = ci.invalidate_on_user_event("u123", "click")
        # Must delete recommendations:u123 and recent_boost:u123
        deleted_keys = {c[0][0] for c in mock_r.delete.call_args_list}
        assert "recommendations:u123" in deleted_keys
        assert "recent_boost:u123" in deleted_keys

    def test_add_to_cart_triggers_invalidation(self):
        mock_r = _mock_redis()
        mock_r.delete.return_value = 1
        with patch.object(ci, "_redis", mock_r):
            result = ci.invalidate_on_user_event("u456", "add_to_cart")
        assert mock_r.delete.called

    def test_unknown_event_type_does_nothing(self):
        mock_r = _mock_redis()
        with patch.object(ci, "_redis", mock_r):
            ci.invalidate_on_user_event("u789", "page_view")
        mock_r.delete.assert_not_called()

    def test_cluster_boost_invalidated_when_cluster_provided(self):
        mock_r = _mock_redis()
        mock_r.delete.return_value = 1
        with patch.object(ci, "_redis", mock_r):
            ci.invalidate_on_user_event("u123", "purchase", cluster_id=2)
        deleted_keys = {c[0][0] for c in mock_r.delete.call_args_list}
        assert "cluster_boost:2" in deleted_keys

    def test_cluster_boost_not_invalidated_without_cluster(self):
        mock_r = _mock_redis()
        mock_r.delete.return_value = 1
        with patch.object(ci, "_redis", mock_r):
            ci.invalidate_on_user_event("u123", "click")
        deleted_keys = {c[0][0] for c in mock_r.delete.call_args_list}
        assert not any("cluster_boost" in k for k in deleted_keys)

    def test_redis_failure_does_not_raise(self):
        mock_r = _mock_redis()
        mock_r.delete.side_effect = ConnectionError("Redis down")
        with patch.object(ci, "_redis", mock_r):
            # Should not raise — failures are silently absorbed
            ci.invalidate_on_user_event("u123", "click")


# ---- invalidate_user_recommendations ----

class TestInvalidateUserRecommendations:
    def test_deletes_correct_key(self):
        mock_r = _mock_redis()
        mock_r.delete.return_value = 1
        with patch.object(ci, "_redis", mock_r):
            result = ci.invalidate_user_recommendations("u999")
        mock_r.delete.assert_called_with("recommendations:u999")
        assert result is True


# ---- get_cache_hit_rate ----

class TestGetCacheHitRate:
    def test_returns_float_between_zero_and_one(self):
        mock_r = _mock_redis()
        mock_r.get.side_effect = lambda key: {"cache:hits": "3", "cache:misses": "1"}.get(key, "0")
        with patch.object(ci, "_redis", mock_r):
            rate = ci.get_cache_hit_rate()
        assert 0.0 <= rate <= 1.0
        assert rate == pytest.approx(0.75)
