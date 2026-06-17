"""
Tests for pure helper functions in search_controller and search utils.
No DB, no Redis — all functions are stateless and fully deterministic.
"""

import pytest

from backend.controllers.search_controller import (
    parse_pagination,
    apply_price_filter,
    apply_sort,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from backend.utils.search import (
    user_category_score,
    user_price_affinity,
    _fuzzy_match,
    _get_cluster_category_boost,
    RECENT_BOOST_MAX,
    RECENT_BOOST_DECAY,
)


# ---- parse_pagination ----

class TestParsePagination:
    def test_defaults_when_both_none(self):
        cursor, limit, err = parse_pagination(None, None)
        assert cursor == 0
        assert limit == DEFAULT_PAGE_SIZE
        assert err is None

    def test_explicit_cursor_and_limit(self):
        cursor, limit, err = parse_pagination("24", "12")
        assert cursor == 24
        assert limit == 12
        assert err is None

    def test_zero_cursor_is_valid(self):
        cursor, limit, err = parse_pagination("0", None)
        assert cursor == 0
        assert err is None

    def test_negative_cursor_is_error(self):
        cursor, limit, err = parse_pagination("-1", None)
        assert err is not None

    def test_limit_zero_is_error(self):
        _, _, err = parse_pagination(None, "0")
        assert err is not None

    def test_limit_above_max_is_error(self):
        _, _, err = parse_pagination(None, str(MAX_PAGE_SIZE + 1))
        assert err is not None

    def test_limit_at_max_is_valid(self):
        _, limit, err = parse_pagination(None, str(MAX_PAGE_SIZE))
        assert limit == MAX_PAGE_SIZE
        assert err is None

    def test_non_integer_cursor_is_error(self):
        _, _, err = parse_pagination("abc", None)
        assert err is not None

    def test_non_integer_limit_is_error(self):
        _, _, err = parse_pagination(None, "twelve")
        assert err is not None

    def test_empty_string_treated_as_default(self):
        cursor, limit, err = parse_pagination("", "")
        assert cursor == 0
        assert limit == DEFAULT_PAGE_SIZE
        assert err is None


# ---- apply_price_filter ----

class TestApplyPriceFilter:
    _PRODUCTS = [
        {"title": "Cheap Keyboard", "price": 29.99},
        {"title": "Mid Laptop",     "price": 799.00},
        {"title": "Pricey Camera",  "price": 1499.00},
    ]

    def test_no_filter_returns_all(self):
        result = apply_price_filter(self._PRODUCTS, None, None)
        assert len(result) == 3

    def test_max_price_filter(self):
        result = apply_price_filter(self._PRODUCTS, None, 800)
        assert all(p["price"] <= 800 for p in result)
        assert len(result) == 2

    def test_min_price_filter(self):
        result = apply_price_filter(self._PRODUCTS, 100, None)
        assert all(p["price"] >= 100 for p in result)
        assert len(result) == 2

    def test_price_range_filter(self):
        result = apply_price_filter(self._PRODUCTS, 50, 1000)
        assert len(result) == 1
        assert result[0]["title"] == "Mid Laptop"

    def test_boundary_inclusive(self):
        # 799.00 exactly at max boundary should be included
        result = apply_price_filter(self._PRODUCTS, None, 799.00)
        assert any(p["title"] == "Mid Laptop" for p in result)

    def test_empty_list_returns_empty(self):
        assert apply_price_filter([], 0, 1000) == []

    def test_no_matches_returns_empty(self):
        result = apply_price_filter(self._PRODUCTS, 2000, 5000)
        assert result == []


# ---- apply_sort ----

class TestApplySort:
    def _products(self):
        return [
            {"title": "A", "price": 500, "rating": 3.5},
            {"title": "B", "price": 100, "rating": 4.8},
            {"title": "C", "price": 999, "rating": 2.1},
        ]

    def test_sort_price_asc(self):
        prods = self._products()
        apply_sort(prods, "price_asc")
        prices = [p["price"] for p in prods]
        assert prices == sorted(prices)

    def test_sort_price_desc(self):
        prods = self._products()
        apply_sort(prods, "price_desc")
        prices = [p["price"] for p in prods]
        assert prices == sorted(prices, reverse=True)

    def test_sort_rating(self):
        prods = self._products()
        apply_sort(prods, "rating")
        ratings = [p["rating"] for p in prods]
        assert ratings == sorted(ratings, reverse=True)

    def test_unknown_sort_key_is_noop(self):
        prods = self._products()
        original_order = [p["title"] for p in prods]
        apply_sort(prods, "nonsense")
        assert [p["title"] for p in prods] == original_order

    def test_none_sort_key_is_noop(self):
        prods = self._products()
        original_order = [p["title"] for p in prods]
        apply_sort(prods, None)
        assert [p["title"] for p in prods] == original_order


# ---- user_category_score ----

class TestUserCategoryScore:
    def test_known_category(self):
        profile = {"category_pref": {"Audio": 0.6, "Computers": 0.2}}
        assert user_category_score(profile, "Audio") == pytest.approx(0.6)

    def test_unknown_category_returns_zero(self):
        profile = {"category_pref": {"Audio": 0.6}}
        assert user_category_score(profile, "Gaming") == pytest.approx(0.0)

    def test_empty_profile_returns_zero(self):
        assert user_category_score({}, "Audio") == pytest.approx(0.0)

    def test_none_profile_returns_zero(self):
        assert user_category_score(None, "Audio") == pytest.approx(0.0)


# ---- user_price_affinity ----

class TestUserPriceAffinity:
    def test_exact_match_returns_one(self):
        profile = {"avg_price": 500.0}
        assert user_price_affinity(profile, 500.0) == pytest.approx(1.0)

    def test_far_from_avg_returns_low(self):
        profile = {"avg_price": 100.0}
        # price=300 → |300-100|/100 = 2.0 → clamped to 0
        assert user_price_affinity(profile, 300.0) == pytest.approx(0.0)

    def test_moderate_deviation(self):
        profile = {"avg_price": 200.0}
        # price=300 → |300-200|/200 = 0.5 → affinity = 0.5
        assert user_price_affinity(profile, 300.0) == pytest.approx(0.5)

    def test_no_avg_price_returns_zero(self):
        assert user_price_affinity({"avg_price": None}, 100.0) == pytest.approx(0.0)

    def test_empty_profile_returns_zero(self):
        assert user_price_affinity({}, 100.0) == pytest.approx(0.0)

    def test_none_profile_returns_zero(self):
        assert user_price_affinity(None, 100.0) == pytest.approx(0.0)

    def test_result_never_negative(self):
        profile = {"avg_price": 50.0}
        # price=1000 is extremely far away
        assert user_price_affinity(profile, 1000.0) >= 0.0


# ---- _fuzzy_match ----

class TestFuzzyMatch:
    def test_exact_substring_match(self):
        assert _fuzzy_match("Sony Wireless Headphones", ["wireless"]) is True

    def test_fuzzy_typo_match(self):
        # "labtop" should fuzzy-match "laptop" with threshold 0.7
        assert _fuzzy_match("Laptop stand for desk", ["labtop"]) is True

    def test_no_match(self):
        assert _fuzzy_match("USB-C Charging Cable", ["headphone"]) is False

    def test_empty_query_words(self):
        # No words to match against → False
        assert _fuzzy_match("Some product title", []) is False

    def test_case_insensitive(self):
        assert _fuzzy_match("Gaming Laptop", ["gaming"]) is True


# ---- _get_cluster_category_boost ----

class TestGetClusterCategoryBoost:
    def _profiles(self):
        return {
            "u1": {"cluster": 0, "category_pref": {"Audio": 0.8, "Computers": 0.2}},
            "u2": {"cluster": 0, "category_pref": {"Audio": 0.4, "Gaming": 0.6}},
            "u3": {"cluster": 1, "category_pref": {"Photography": 1.0}},
        }

    def test_known_cluster_sums_preferences(self):
        boost = _get_cluster_category_boost(0, self._profiles())
        assert "Audio" in boost
        assert boost["Audio"] > 0

    def test_boost_values_sum_to_one(self):
        boost = _get_cluster_category_boost(0, self._profiles())
        assert sum(boost.values()) == pytest.approx(1.0, abs=1e-5)

    def test_other_cluster_excluded(self):
        boost = _get_cluster_category_boost(0, self._profiles())
        assert "Photography" not in boost

    def test_none_cluster_returns_empty(self):
        assert _get_cluster_category_boost(None, self._profiles()) == {}

    def test_cluster_with_no_members_returns_empty(self):
        assert _get_cluster_category_boost(99, self._profiles()) == {}

    def test_empty_profiles_returns_empty(self):
        assert _get_cluster_category_boost(0, {}) == {}
