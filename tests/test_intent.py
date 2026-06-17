"""Tests for backend/utils/intent.py — search intent detection."""

import pytest

from backend.utils.intent import (
    detect_intent,
    detect_category,
    detect_price,
    detect_sort,
    clean_query_text,
    normalize,
    word_match,
)


class TestNormalize:
    def test_lowercases(self):
        assert normalize("LAPTOP") == "laptop"

    def test_collapses_whitespace(self):
        assert normalize("  gaming   laptop  ") == "gaming laptop"

    def test_strips_edges(self):
        assert normalize("  headphones  ") == "headphones"


class TestWordMatch:
    def test_exact_word(self):
        assert word_match("laptop", "buy a laptop today") is True

    def test_no_partial_match(self):
        # "ssd" must not match "ssds" as a substring without word boundary
        assert word_match("storage", "restore my files") is False

    def test_word_at_start(self):
        assert word_match("camera", "camera tripod") is True

    def test_word_at_end(self):
        assert word_match("gaming", "best gaming") is True

    def test_not_present(self):
        assert word_match("router", "laptop stand") is False


class TestDetectCategory:
    @pytest.mark.parametrize("query,expected", [
        ("buy laptops", "Computers"),
        ("macbook pro", "Computers"),
        ("wireless headphones", "Audio"),
        ("bluetooth speaker", "Audio"),
        ("dslr camera", "Photography"),
        ("gaming console", "Gaming"),
        ("wifi router", "Networking"),
        ("external ssd", "Storage"),
        ("usb keyboard", "Accessories"),
        ("smart bulb for home", "Smart Home"),
        ("iphone android", "Electronics"),
    ])
    def test_category_detected(self, query, expected):
        result = detect_category(normalize(query))
        assert result == expected

    def test_unknown_query_returns_none(self):
        assert detect_category(normalize("buy something nice")) is None

    def test_case_insensitive(self):
        assert detect_category(normalize("LAPTOP")) == "Computers"


class TestDetectPrice:
    def test_under(self):
        min_p, max_p = detect_price("laptop under $500")
        assert min_p is None
        assert max_p == 500.0

    def test_over(self):
        min_p, max_p = detect_price("monitor over $1,000")
        assert min_p == 1000.0
        assert max_p is None

    def test_range_with_to(self):
        min_p, max_p = detect_price("headphones $100 to $300")
        assert min_p == 100.0
        assert max_p == 300.0

    def test_range_with_between(self):
        min_p, max_p = detect_price("between 200 and 600")
        assert min_p == 200.0
        assert max_p == 600.0

    def test_below_keyword(self):
        _, max_p = detect_price("camera below 800")
        assert max_p == 800.0

    def test_upto_keyword(self):
        _, max_p = detect_price("keyboard upto $150")
        assert max_p == 150.0

    def test_no_price(self):
        min_p, max_p = detect_price("best wireless headphones")
        assert min_p is None
        assert max_p is None

    def test_comma_separated_number(self):
        _, max_p = detect_price("laptop less than $1,500")
        assert max_p == 1500.0


class TestDetectSort:
    @pytest.mark.parametrize("query,expected", [
        ("cheap laptop", "price_asc"),
        ("budget headphones", "price_asc"),
        ("affordable mouse", "price_asc"),
        ("premium camera", "price_desc"),
        ("luxury keyboard", "price_desc"),
        ("best router", "rating"),
        ("top rated ssd", "rating"),
        ("recommended monitor", "rating"),
    ])
    def test_sort_detected(self, query, expected):
        assert detect_sort(normalize(query)) == expected

    def test_no_sort_intent(self):
        assert detect_sort(normalize("wireless headphones")) is None


class TestCleanQueryText:
    def test_removes_price_phrase(self):
        cleaned = clean_query_text(normalize("laptop under $500"))
        assert "500" not in cleaned
        assert "under" not in cleaned

    def test_removes_negation(self):
        cleaned = clean_query_text(normalize("headphones without cable"))
        assert "without" not in cleaned

    def test_removes_modifier_keywords(self):
        cleaned = clean_query_text(normalize("gaming laptop"))
        assert "gaming" not in cleaned

    def test_removes_quality_keywords(self):
        cleaned = clean_query_text(normalize("best laptop"))
        assert "best" not in cleaned

    def test_preserves_product_noun(self):
        cleaned = clean_query_text(normalize("gaming laptop under $800"))
        assert "laptop" in cleaned

    def test_all_removed_falls_back_in_detect_intent(self):
        # "cheap gaming" removes all words; detect_intent should fall back to original
        result = detect_intent("cheap gaming")
        assert result["clean_query"] != ""


class TestDetectIntent:
    def test_full_query(self):
        result = detect_intent("best wireless headphones under $200")
        assert result["suggested_category"] == "Audio"
        assert result["suggested_sort"] == "rating"
        assert result["suggested_max_price"] == 200.0
        assert "wireless" not in result["clean_query"]
        assert "best" not in result["clean_query"]

    def test_returns_all_keys(self):
        result = detect_intent("laptop")
        expected_keys = {
            "original_query", "clean_query", "suggested_category",
            "modifiers", "suggested_sort", "suggested_min_price", "suggested_max_price",
        }
        assert set(result.keys()) == expected_keys

    def test_negation_stripped_before_category_detection(self):
        # "not gaming" should not trigger Gaming category
        result = detect_intent("laptop not gaming")
        assert result["suggested_category"] == "Computers"

    def test_empty_query(self):
        result = detect_intent("")
        assert result["suggested_category"] is None
        assert result["suggested_sort"] is None
        assert result["suggested_min_price"] is None

    def test_price_range_extracted(self):
        result = detect_intent("camera between $300 and $700")
        assert result["suggested_min_price"] == 300.0
        assert result["suggested_max_price"] == 700.0
