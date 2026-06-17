"""Tests for backend/services/security.py — validation and password hashing."""

import pytest

from backend.services.security import (
    validate_username,
    validate_password,
    validate_email,
    hash_password,
    verify_password,
    MIN_PASSWORD_LENGTH,
)


class TestValidateUsername:
    def test_valid_username(self):
        ok, err = validate_username("alice123")
        assert ok is True
        assert err is None

    def test_valid_with_underscore(self):
        ok, err = validate_username("user_name_42")
        assert ok is True

    def test_minimum_length(self):
        ok, _ = validate_username("abc")
        assert ok is True

    def test_too_short(self):
        ok, err = validate_username("ab")
        assert ok is False
        assert err is not None

    def test_too_long(self):
        ok, err = validate_username("a" * 51)
        assert ok is False

    def test_empty_string(self):
        ok, err = validate_username("")
        assert ok is False

    def test_none_value(self):
        ok, err = validate_username(None)
        assert ok is False

    def test_disallows_spaces(self):
        ok, err = validate_username("user name")
        assert ok is False

    def test_disallows_special_chars(self):
        ok, err = validate_username("user@name!")
        assert ok is False

    def test_disallows_hyphen(self):
        ok, err = validate_username("user-name")
        assert ok is False


class TestValidatePassword:
    _VALID = "Secure1@"

    def test_valid_password(self):
        ok, err = validate_password(self._VALID)
        assert ok is True
        assert err is None

    def test_too_short(self):
        ok, err = validate_password("Ab1@")
        assert ok is False
        assert err is not None

    def test_minimum_length_boundary(self):
        # Exactly MIN_PASSWORD_LENGTH chars with all complexity
        pw = "Aa1@" + "x" * (MIN_PASSWORD_LENGTH - 4)
        ok, _ = validate_password(pw)
        assert ok is True

    def test_missing_uppercase(self):
        ok, err = validate_password("secure1@pass")
        assert ok is False

    def test_missing_lowercase(self):
        ok, err = validate_password("SECURE1@PASS")
        assert ok is False

    def test_missing_digit(self):
        ok, err = validate_password("SecurePass@")
        assert ok is False

    def test_missing_special_char(self):
        ok, err = validate_password("SecurePass1")
        assert ok is False

    def test_empty_password(self):
        ok, err = validate_password("")
        assert ok is False

    def test_none_password(self):
        ok, err = validate_password(None)
        assert ok is False

    def test_complexity_off_skips_char_checks(self):
        # With complexity=False only length is checked
        ok, _ = validate_password("alllowercase", complexity=False)
        assert ok is True


class TestValidateEmail:
    def test_valid_email(self):
        ok, err = validate_email("user@example.com")
        assert ok is True
        assert err is None

    def test_valid_subdomain(self):
        ok, _ = validate_email("user@mail.example.co.uk")
        assert ok is True

    def test_missing_at(self):
        ok, err = validate_email("userexample.com")
        assert ok is False

    def test_missing_domain(self):
        ok, err = validate_email("user@")
        assert ok is False

    def test_empty(self):
        ok, err = validate_email("")
        assert ok is False

    def test_none(self):
        ok, err = validate_email(None)
        assert ok is False

    def test_too_long(self):
        ok, err = validate_email("a" * 250 + "@x.com")
        assert ok is False

    def test_strips_whitespace(self):
        # Leading/trailing whitespace should not cause failure
        ok, err = validate_email("  user@example.com  ")
        assert ok is True


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        pw = "SecurePass1@"
        h = hash_password(pw)
        assert h != pw

    def test_hash_starts_with_bcrypt_prefix(self):
        h = hash_password("SecurePass1@")
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_verify_correct_password(self):
        pw = "SecurePass1@"
        h = hash_password(pw)
        assert verify_password(pw, h) is True

    def test_verify_wrong_password(self):
        h = hash_password("SecurePass1@")
        assert verify_password("WrongPass1@", h) is False

    def test_hashes_are_salted(self):
        pw = "SecurePass1@"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2  # Different salts → different hashes

    def test_verify_returns_false_for_bad_hash(self):
        # Should not raise; returns False for malformed hash
        assert verify_password("anything", "not-a-valid-hash") is False
