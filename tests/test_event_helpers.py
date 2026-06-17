"""Tests for pure helper functions in backend/controllers/events_controller.py."""

import pytest

from backend.controllers.events_controller import (
    normalize_event_type,
    normalize_product_id,
    error_response,
    ALLOWED_EVENTS,
    MAX_QUERY_LENGTH,
)


class TestNormalizeEventType:
    def test_click_passes_through(self):
        assert normalize_event_type("click") == "click"

    def test_add_to_cart_passes_through(self):
        assert normalize_event_type("add_to_cart") == "add_to_cart"

    def test_uppercased_is_lowercased(self):
        assert normalize_event_type("CLICK") == "click"

    def test_strips_leading_trailing_whitespace(self):
        assert normalize_event_type("  click  ") == "click"

    def test_none_returns_empty_string(self):
        assert normalize_event_type(None) == ""

    def test_empty_string_returned_as_is(self):
        assert normalize_event_type("") == ""

    def test_unknown_event_normalized_but_not_blocked_here(self):
        # Gate is in log_event_controller; normalize just lowercases
        assert normalize_event_type("PageView") == "pageview"

    def test_allowed_events_are_valid_after_normalize(self):
        for evt in ALLOWED_EVENTS:
            assert normalize_event_type(evt) == evt


class TestNormalizeProductId:
    def test_positive_integer_returned(self):
        assert normalize_product_id(42) == 42

    def test_string_integer_coerced(self):
        assert normalize_product_id("7") == 7

    def test_none_returns_none(self):
        assert normalize_product_id(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_product_id("") is None

    def test_zero_returns_none(self):
        assert normalize_product_id(0) is None

    def test_negative_returns_none(self):
        assert normalize_product_id(-5) is None

    def test_negative_string_returns_none(self):
        assert normalize_product_id("-1") is None

    def test_non_numeric_string_returns_none(self):
        assert normalize_product_id("abc") is None

    def test_float_string_truncates_to_int(self):
        # int("3.5") raises ValueError → None
        assert normalize_product_id("3.5") is None

    def test_large_valid_id(self):
        assert normalize_product_id(999999) == 999999

    def test_string_zero_returns_none(self):
        assert normalize_product_id("0") is None


class TestEventErrorResponse:
    def test_returns_tuple(self):
        result = error_response("oops")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_body_has_error_key(self):
        body, _ = error_response("something went wrong")
        assert body["error"] == "something went wrong"

    def test_default_status_is_400(self):
        _, status = error_response("bad request")
        assert status == 400

    def test_custom_status_code(self):
        _, status = error_response("not found", 404)
        assert status == 404

    def test_body_is_plain_dict(self):
        # Unlike auth_controller.invalid_response, this must NOT use jsonify
        body, _ = error_response("msg")
        assert isinstance(body, dict)


class TestAllowedEventsAndConstants:
    def test_click_is_allowed(self):
        assert "click" in ALLOWED_EVENTS

    def test_add_to_cart_is_allowed(self):
        assert "add_to_cart" in ALLOWED_EVENTS

    def test_max_query_length_is_positive(self):
        assert MAX_QUERY_LENGTH > 0
