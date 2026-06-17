"""Tests for backend/services/cache_keys.py — query normalization and hashing."""

import pytest

from backend.services.cache_keys import normalize_query, query_hash


class TestNormalizeQuery:
    def test_lowercases(self):
        assert normalize_query("Wireless HEADPHONES") == "wireless headphones"

    def test_strips_whitespace(self):
        assert normalize_query("  laptop  ") == "laptop"

    def test_collapses_inner_whitespace(self):
        assert normalize_query("gaming  laptop   stand") == "gaming laptop stand"

    def test_empty_string(self):
        assert normalize_query("") == ""

    def test_none_returns_empty(self):
        assert normalize_query(None) == ""

    def test_whitespace_only(self):
        assert normalize_query("   ") == ""


class TestQueryHash:
    def test_returns_string(self):
        h = query_hash("laptop")
        assert isinstance(h, str)

    def test_deterministic(self):
        assert query_hash("headphones") == query_hash("headphones")

    def test_different_queries_different_hashes(self):
        assert query_hash("laptop") != query_hash("headphones")

    def test_length_is_16(self):
        assert len(query_hash("any query here")) == 16

    def test_case_insensitive(self):
        # "Laptop" and "laptop" should produce the same hash (normalized first)
        assert query_hash("Laptop") == query_hash("laptop")

    def test_whitespace_normalized(self):
        # Extra whitespace should not change the hash
        assert query_hash("gaming laptop") == query_hash("  gaming  laptop  ")

    def test_empty_query(self):
        h = query_hash("")
        assert isinstance(h, str)
        assert len(h) == 16

    def test_hex_characters_only(self):
        h = query_hash("some query")
        assert all(c in "0123456789abcdef" for c in h)
