"""Tests for backend/utils/sanitize.py — user ID sanitization."""

import pytest

from backend.utils.sanitize import sanitize_user_id


class TestSanitizeUserId:
    def test_valid_id_returned_as_is(self):
        assert sanitize_user_id("u1a2b3c4d5e6") == "u1a2b3c4d5e6"

    def test_none_returns_none(self):
        assert sanitize_user_id(None) is None

    def test_empty_string_returns_none(self):
        assert sanitize_user_id("") is None

    def test_whitespace_only_returns_none(self):
        assert sanitize_user_id("   ") is None

    def test_strips_leading_trailing_whitespace(self):
        assert sanitize_user_id("  user123  ") == "user123"

    def test_literal_undefined_returns_none(self):
        assert sanitize_user_id("undefined") is None

    def test_literal_null_returns_none(self):
        assert sanitize_user_id("null") is None

    def test_literal_none_string_returns_none(self):
        assert sanitize_user_id("none") is None

    def test_case_insensitive_sentinel_check(self):
        assert sanitize_user_id("UNDEFINED") is None
        assert sanitize_user_id("NULL") is None
        assert sanitize_user_id("None") is None

    def test_too_long_id_returns_none(self):
        assert sanitize_user_id("a" * 129) is None

    def test_exactly_max_length_is_valid(self):
        assert sanitize_user_id("a" * 128) == "a" * 128

    def test_newline_character_returns_none(self):
        assert sanitize_user_id("user\nid") is None

    def test_carriage_return_returns_none(self):
        assert sanitize_user_id("user\rid") is None

    def test_comma_returns_none(self):
        assert sanitize_user_id("user,id") is None

    def test_integer_input_coerced_to_string(self):
        result = sanitize_user_id(42)
        assert result == "42"

    def test_numeric_id_string_accepted(self):
        assert sanitize_user_id("1234567890") == "1234567890"
