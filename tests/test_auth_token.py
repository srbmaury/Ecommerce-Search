"""Tests for backend/utils/auth_token.py — session token creation/verification."""

import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest

from backend.utils.auth_token import create_token, decode_token, is_token_stale


SECRET = "test-secret-key"


class TestTokenRoundTrip:
    def test_valid_token_decodes_to_same_user_id(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            token = create_token("u123abc")
            user_id, issued_at = decode_token(token)
        assert user_id == "u123abc"

    def test_valid_token_returns_issued_at_timestamp(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            token = create_token("u123abc")
            _, issued_at = decode_token(token)
        assert isinstance(issued_at, datetime)
        assert issued_at.tzinfo is not None

    def test_different_user_ids_produce_different_tokens(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            t1 = create_token("u111")
            t2 = create_token("u222")
        assert t1 != t2

    def test_token_is_a_string(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            token = create_token("u123abc")
        assert isinstance(token, str)
        assert len(token) > 0


class TestDecodeTokenRejectsInvalid:
    def test_none_returns_none(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            assert decode_token(None) == (None, None)

    def test_empty_string_returns_none(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            assert decode_token("") == (None, None)

    def test_garbage_string_returns_none(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            assert decode_token("not-a-real-token") == (None, None)

    def test_tampered_token_returns_none(self):
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            token = create_token("u123abc")
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            assert decode_token(tampered) == (None, None)

    def test_token_signed_with_different_secret_is_rejected(self):
        with patch.dict(os.environ, {"SECRET_KEY": "secret-one"}):
            token = create_token("u123abc")
        with patch.dict(os.environ, {"SECRET_KEY": "secret-two"}):
            assert decode_token(token) == (None, None)

    def test_expired_token_returns_none(self):
        # itsdangerous timestamps at whole-second granularity, so max_age=0
        # needs >=1s of real elapsed time to reliably tip into "expired".
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            token = create_token("u123abc")
            time.sleep(1.1)
            with patch("backend.utils.auth_token.TOKEN_MAX_AGE_SECONDS", 0):
                assert decode_token(token) == (None, None)

    def test_non_dict_payload_returns_none(self):
        # Defensive: decode_token should reject a validly-signed token whose
        # payload isn't the expected {"user_id": ...} shape.
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            from backend.utils.auth_token import _serializer
            token = _serializer().dumps("just-a-string")
            assert decode_token(token) == (None, None)


class TestIsTokenStale:
    def test_no_password_changed_at_is_never_stale(self):
        user = MagicMock(password_changed_at=None)
        issued_at = datetime.now(timezone.utc)
        assert is_token_stale(user, issued_at) is False

    def test_none_issued_at_is_never_stale(self):
        user = MagicMock(password_changed_at=datetime.now(timezone.utc))
        assert is_token_stale(user, None) is False

    def test_token_issued_before_password_change_is_stale(self):
        now = datetime.now(timezone.utc)
        user = MagicMock(password_changed_at=now)
        issued_at = now - timedelta(minutes=5)
        assert is_token_stale(user, issued_at) is True

    def test_token_issued_after_password_change_is_fresh(self):
        now = datetime.now(timezone.utc)
        user = MagicMock(password_changed_at=now)
        issued_at = now + timedelta(minutes=5)
        assert is_token_stale(user, issued_at) is False

    def test_naive_password_changed_at_treated_as_utc(self):
        # DB drivers can return naive datetimes for TIMESTAMP columns;
        # comparing against a tz-aware issued_at must not raise.
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        user = MagicMock(password_changed_at=now_naive)
        issued_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert is_token_stale(user, issued_at) is True
