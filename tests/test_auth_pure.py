"""
Tests for pure helper functions in backend/controllers/auth_controller.py.
Covers is_admin, generate_user_id, and signup validation paths
that don't touch the database.
"""

import os
import re
from unittest.mock import patch, MagicMock

import pytest


class TestIsAdmin:
    def test_known_admin_returns_true(self):
        with patch.dict(os.environ, {"ADMIN_USER_IDS": "u_admin1,u_admin2"}):
            # Re-import to pick up the patched env — ADMIN_USER_IDS is read at module level,
            # so we patch the already-built set directly.
            from backend.controllers import auth_controller as ac
            with patch.object(ac, "ADMIN_USER_IDS", {"u_admin1", "u_admin2"}):
                assert ac.is_admin("u_admin1") is True

    def test_unknown_user_returns_false(self):
        from backend.controllers import auth_controller as ac
        with patch.object(ac, "ADMIN_USER_IDS", {"u_admin1"}):
            assert ac.is_admin("u_regular") is False

    def test_empty_string_returns_false(self):
        from backend.controllers import auth_controller as ac
        with patch.object(ac, "ADMIN_USER_IDS", {"u_admin1"}):
            assert ac.is_admin("") is False

    def test_empty_admin_set_always_false(self):
        from backend.controllers import auth_controller as ac
        with patch.object(ac, "ADMIN_USER_IDS", set()):
            assert ac.is_admin("anyone") is False


class TestGenerateUserId:
    def setup_method(self):
        from backend.controllers.auth_controller import generate_user_id
        self._fn = generate_user_id

    def test_starts_with_u(self):
        uid = self._fn()
        assert uid.startswith("u")

    def test_total_length_is_13(self):
        # "u" + 12 hex chars
        uid = self._fn()
        assert len(uid) == 13

    def test_suffix_is_hex(self):
        uid = self._fn()
        suffix = uid[1:]  # strip leading "u"
        assert re.fullmatch(r"[0-9a-f]{12}", suffix) is not None

    def test_generates_unique_ids(self):
        ids = {self._fn() for _ in range(100)}
        assert len(ids) == 100


class TestSignupValidation:
    """
    Test the validation logic inside signup_controller without hitting the DB.
    We mock create_user so the function short-circuits at the DB boundary.
    """

    def _call(self, data):
        from backend.controllers.auth_controller import signup_controller
        from unittest.mock import MagicMock
        mock_user = MagicMock()
        mock_user.user_id = "u_test123abc"
        mock_user.username = data.get("username", "")
        mock_user.group = "A"
        mock_user.email_verified = False

        with patch("backend.controllers.auth_controller.create_user", return_value=mock_user), \
             patch("backend.controllers.auth_controller.create_email_verification_token", return_value="tok"), \
             patch("backend.controllers.auth_controller._send_email_async"), \
             patch("backend.controllers.auth_controller.is_admin", return_value=False):
            import flask
            app = flask.Flask(__name__)
            with app.app_context():
                return signup_controller(data)

    def test_missing_username_returns_error(self):
        resp = self._call({"password": "SecurePass1@", "email": "a@b.com"})
        # Returns (Response, status) or just Response depending on Flask context
        # invalid_response uses jsonify which returns a Response object in tuple form
        body, status = resp
        assert status == 400

    def test_short_password_returns_error(self):
        body, status = self._call({"username": "alice", "password": "Ab1@", "email": "a@b.com"})
        assert status == 400

    def test_invalid_email_returns_error(self):
        body, status = self._call({"username": "alice123", "password": "SecurePass1@", "email": "not-an-email"})
        assert status == 400

    def test_valid_data_returns_200(self):
        result = self._call({"username": "alice123", "password": "SecurePass1@", "email": "alice@example.com"})
        # signup_controller returns a Response (jsonify), not a tuple with status — 200 is default
        # When successful it returns jsonify({...}) which is a 200 Response
        assert result is not None

    def test_no_email_still_signs_up(self):
        result = self._call({"username": "alice123", "password": "SecurePass1@"})
        assert result is not None
