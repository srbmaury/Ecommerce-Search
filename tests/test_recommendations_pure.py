"""
Tests for pure helpers in backend/controllers/recommendations_controller.py
and the _ranked_cache_key helper in backend/utils/search.py.
"""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest


# ---- serialize_product_dates ----

class TestSerializeProductDates:
    def test_datetime_converted_to_iso_string(self):
        from backend.controllers.recommendations_controller import serialize_product_dates
        ts = datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        products = [{"product_id": 1, "created_at": ts}]
        serialize_product_dates(products)
        assert products[0]["created_at"] == ts.isoformat()

    def test_updated_at_also_converted(self):
        from backend.controllers.recommendations_controller import serialize_product_dates
        ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
        products = [{"product_id": 2, "created_at": ts, "updated_at": ts}]
        serialize_product_dates(products)
        assert isinstance(products[0]["updated_at"], str)

    def test_string_dates_left_untouched(self):
        from backend.controllers.recommendations_controller import serialize_product_dates
        products = [{"product_id": 3, "created_at": "2024-01-01T00:00:00+00:00"}]
        serialize_product_dates(products)
        assert products[0]["created_at"] == "2024-01-01T00:00:00+00:00"

    def test_missing_date_fields_skipped(self):
        from backend.controllers.recommendations_controller import serialize_product_dates
        products = [{"product_id": 4, "title": "Gadget"}]
        serialize_product_dates(products)  # must not raise
        assert "created_at" not in products[0]

    def test_mutates_list_in_place(self):
        from backend.controllers.recommendations_controller import serialize_product_dates
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        products = [{"product_id": 5, "created_at": ts}]
        original_list = products
        serialize_product_dates(products)
        assert products is original_list  # same object

    def test_empty_list_is_noop(self):
        from backend.controllers.recommendations_controller import serialize_product_dates
        serialize_product_dates([])  # must not raise

    def test_multiple_products(self):
        from backend.controllers.recommendations_controller import serialize_product_dates
        ts = datetime(2024, 5, 10, tzinfo=timezone.utc)
        products = [
            {"product_id": i, "created_at": ts}
            for i in range(5)
        ]
        serialize_product_dates(products)
        for p in products:
            assert isinstance(p["created_at"], str)


# ---- get_cluster_category_boost (recommendations_controller) ----

class TestRecoGetClusterCategoryBoost:
    def _profiles(self):
        return {
            "u1": {"cluster": 0, "category_pref": {"Audio": 0.8, "Gaming": 0.2}},
            "u2": {"cluster": 0, "category_pref": {"Audio": 0.6, "Computers": 0.4}},
            "u3": {"cluster": 1, "category_pref": {"Photography": 1.0}},
        }

    def test_none_cluster_returns_empty(self):
        from backend.controllers.recommendations_controller import get_cluster_category_boost
        with patch("backend.controllers.recommendations_controller.redis_get_json", return_value=None), \
             patch("backend.controllers.recommendations_controller.redis_setex_json"):
            result = get_cluster_category_boost(None, self._profiles())
        assert result == {}

    def test_returns_cached_value_from_redis(self):
        from backend.controllers.recommendations_controller import get_cluster_category_boost
        cached = {"Audio": 0.7, "Gaming": 0.3}
        with patch("backend.controllers.recommendations_controller.redis_get_json", return_value=cached):
            result = get_cluster_category_boost(0, self._profiles())
        assert result == cached

    def test_boost_values_sum_to_one_when_computed(self):
        from backend.controllers.recommendations_controller import get_cluster_category_boost
        with patch("backend.controllers.recommendations_controller.redis_get_json", return_value=None), \
             patch("backend.controllers.recommendations_controller.redis_setex_json"):
            result = get_cluster_category_boost(0, self._profiles())
        assert sum(result.values()) == pytest.approx(1.0, abs=1e-5)

    def test_other_cluster_excluded(self):
        from backend.controllers.recommendations_controller import get_cluster_category_boost
        with patch("backend.controllers.recommendations_controller.redis_get_json", return_value=None), \
             patch("backend.controllers.recommendations_controller.redis_setex_json"):
            result = get_cluster_category_boost(0, self._profiles())
        assert "Photography" not in result

    def test_unknown_cluster_returns_empty(self):
        from backend.controllers.recommendations_controller import get_cluster_category_boost
        with patch("backend.controllers.recommendations_controller.redis_get_json", return_value=None), \
             patch("backend.controllers.recommendations_controller.redis_setex_json"):
            result = get_cluster_category_boost(99, self._profiles())
        assert result == {}

    def test_result_cached_in_redis(self):
        from backend.controllers.recommendations_controller import get_cluster_category_boost
        mock_setex = MagicMock()
        with patch("backend.controllers.recommendations_controller.redis_get_json", return_value=None), \
             patch("backend.controllers.recommendations_controller.redis_setex_json", mock_setex):
            get_cluster_category_boost(0, self._profiles())
        mock_setex.assert_called_once()
        # First arg should be the cache key for cluster 0
        call_key = mock_setex.call_args[0][0]
        assert "cluster_boost:0" in call_key


# ---- _ranked_cache_key ----

class TestRankedCacheKey:
    def test_returns_string(self):
        from backend.utils.search import _ranked_cache_key
        key = _ranked_cache_key("laptop", "u123", 0, "A")
        assert isinstance(key, str)

    def test_contains_ab_group(self):
        from backend.utils.search import _ranked_cache_key
        key_a = _ranked_cache_key("laptop", "u123", 0, "A")
        key_b = _ranked_cache_key("laptop", "u123", 0, "B")
        assert ":A:" in key_a
        assert ":B:" in key_b

    def test_different_users_different_keys(self):
        from backend.utils.search import _ranked_cache_key
        key1 = _ranked_cache_key("laptop", "u111", 0, "A")
        key2 = _ranked_cache_key("laptop", "u222", 0, "A")
        assert key1 != key2

    def test_different_queries_different_keys(self):
        from backend.utils.search import _ranked_cache_key
        key1 = _ranked_cache_key("laptop", "u111", 0, "A")
        key2 = _ranked_cache_key("headphones", "u111", 0, "A")
        assert key1 != key2

    def test_different_clusters_different_keys(self):
        from backend.utils.search import _ranked_cache_key
        key1 = _ranked_cache_key("laptop", "u111", 0, "A")
        key2 = _ranked_cache_key("laptop", "u111", 1, "A")
        assert key1 != key2

    def test_none_cluster_uses_none_literal(self):
        from backend.utils.search import _ranked_cache_key
        key = _ranked_cache_key("laptop", "u111", None, "A")
        assert ":none:" in key

    def test_anonymous_user_uses_anon(self):
        from backend.utils.search import _ranked_cache_key
        key = _ranked_cache_key("laptop", None, 0, "A")
        assert ":anon" in key

    def test_same_inputs_same_key(self):
        from backend.utils.search import _ranked_cache_key
        key1 = _ranked_cache_key("wireless headphones", "u999", 2, "B")
        key2 = _ranked_cache_key("wireless headphones", "u999", 2, "B")
        assert key1 == key2

    def test_starts_with_search_ranked_prefix(self):
        from backend.utils.search import _ranked_cache_key
        key = _ranked_cache_key("laptop", "u1", 0, "A")
        assert key.startswith("search_ranked:")
