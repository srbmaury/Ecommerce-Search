"""
Tests for backend/utils/admin_auth.py — require_admin.

Covers the exact regression this decorator was rewritten to prevent: an
unsigned X-User-ID header must never grant admin access, only a verified
token whose user_id is in ADMIN_USER_IDS.
"""
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import flask
import pytest

from backend.utils import admin_auth
from backend.utils.auth_token import create_token


SECRET = "test-secret-key"


def make_app():
    app = flask.Flask(__name__)

    @app.route("/admin-only")
    @admin_auth.require_admin
    def admin_only():
        return {"user_id": flask.g.admin_user.user_id}

    return app


@pytest.fixture
def client():
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        app = make_app()
        yield app.test_client()


def _token_for(user_id):
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        return create_token(user_id)


class TestRequireAdmin:
    def test_no_header_returns_401(self, client):
        resp = client.get("/admin-only")
        assert resp.status_code == 401

    def test_old_vuln_spoofed_x_user_id_header_alone_is_ignored(self, client):
        # This is the exact hole that was closed: X-User-ID used to be
        # trusted at face value with no signature check.
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]):
            resp = client.get("/admin-only", headers={"X-User-ID": "u_admin"})
        assert resp.status_code == 401

    def test_valid_token_but_not_admin_returns_403(self, client):
        token = _token_for("u_regular")
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]):
            resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_valid_admin_token_succeeds(self, client):
        token = _token_for("u_admin")
        mock_user = MagicMock(user_id="u_admin", password_changed_at=None)
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]), \
             patch.object(admin_auth, "get_user_by_id", return_value=mock_user):
            resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.get_json()["user_id"] == "u_admin"

    def test_admin_id_but_user_deleted_returns_401(self, client):
        token = _token_for("u_admin")
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]), \
             patch.object(admin_auth, "get_user_by_id", return_value=None):
            resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_empty_admin_list_always_403(self, client):
        token = _token_for("u_anyone")
        with patch.object(admin_auth, "ADMIN_USER_IDS", []):
            resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_admin_token_issued_before_password_change_returns_401(self, client):
        # Same protection as require_auth: a reset must revoke old tokens,
        # including ones that would otherwise carry admin access.
        token = _token_for("u_admin")
        stale_user = MagicMock(
            user_id="u_admin",
            password_changed_at=datetime.now(timezone.utc) + timedelta(minutes=1),
        )
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]), \
             patch.object(admin_auth, "get_user_by_id", return_value=stale_user):
            resp = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
