"""
Tests for backend/utils/auth_middleware.py — require_auth/optional_auth.

These decorators are the actual security boundary: they decide whether a
route trusts g.user_id (server-derived from a verified token) versus a
client-supplied user_id. A regression here (e.g. a route losing its
@require_auth) should show up as a failing test, not just in manual curl
checks.
"""
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import flask
import pytest

from backend.utils.auth_token import create_token
from backend.utils.auth_middleware import require_auth, optional_auth


SECRET = "test-secret-key"


def make_app():
    app = flask.Flask(__name__)

    @app.route("/protected")
    @require_auth
    def protected():
        return {"user_id": flask.g.user_id}

    @app.route("/maybe-protected")
    @optional_auth
    def maybe_protected():
        return {"user_id": flask.g.user_id}

    return app


@pytest.fixture
def client():
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        app = make_app()
        yield app.test_client()


def _token_for(user_id):
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        return create_token(user_id)


def _fresh_user(user_id):
    """A user who has never changed their password — no token is stale."""
    return MagicMock(user_id=user_id, password_changed_at=None)


class TestRequireAuth:
    def test_no_header_returns_401(self, client):
        resp = client.get("/protected")
        assert resp.status_code == 401

    def test_malformed_header_returns_401(self, client):
        resp = client.get("/protected", headers={"Authorization": "garbage"})
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/protected", headers={"Authorization": "Bearer not-a-real-token"})
        assert resp.status_code == 401

    def test_valid_token_sets_user_id_and_succeeds(self, client):
        token = _token_for("u123abc")
        with patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u123abc")):
            resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] == "u123abc"

    def test_client_cannot_spoof_user_id_via_body(self, client):
        # A spoofed user_id in the body/query must never override the
        # token-derived identity — the route only ever sees flask.g.user_id.
        token = _token_for("u_real_owner")
        with patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_real_owner")):
            resp = client.get(
                "/protected?user_id=u_someone_else",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.get_json()["user_id"] == "u_real_owner"

    def test_deleted_user_returns_401(self, client):
        token = _token_for("u_ghost")
        with patch("backend.utils.auth_middleware.get_user_by_id", return_value=None):
            resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_token_issued_before_password_change_returns_401(self):
        # Simulates a leaked/old token: the user reset their password after
        # this token was issued, so it must no longer work.
        with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
            app = make_app()
        client = app.test_client()
        token = _token_for("u123abc")
        stale_user = MagicMock(
            user_id="u123abc",
            password_changed_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        with patch("backend.utils.auth_middleware.get_user_by_id", return_value=stale_user):
            resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


class TestOptionalAuth:
    def test_no_header_succeeds_with_none_user_id(self, client):
        resp = client.get("/maybe-protected")
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] is None

    def test_invalid_token_succeeds_with_none_user_id(self, client):
        # Anonymous access must degrade gracefully, not 401 — same
        # contract as the /api/search route.
        resp = client.get("/maybe-protected", headers={"Authorization": "Bearer garbage"})
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] is None

    def test_valid_token_sets_user_id(self, client):
        token = _token_for("u123abc")
        with patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u123abc")):
            resp = client.get("/maybe-protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.get_json()["user_id"] == "u123abc"

    def test_revoked_token_degrades_to_anonymous_not_error(self, client):
        token = _token_for("u123abc")
        stale_user = MagicMock(
            user_id="u123abc",
            password_changed_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        with patch("backend.utils.auth_middleware.get_user_by_id", return_value=stale_user):
            resp = client.get("/maybe-protected", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] is None
