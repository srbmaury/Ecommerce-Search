"""
Integration-style tests confirming each route blueprint actually enforces
the auth level it's supposed to (require_auth / optional_auth / require_admin).

Controller functions are patched out so no real DB/Redis is touched — this
is purely about whether the *route* rejects/accepts requests correctly,
which is exactly the kind of thing that silently breaks if a decorator is
dropped during a refactor.
"""
import os
from unittest.mock import patch, MagicMock

import flask
import pytest

from backend.utils.auth_token import create_token
from backend.utils import admin_auth
from backend.utils.rate_limit import limiter


SECRET = "test-secret-key"


def _token_for(user_id):
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        return create_token(user_id)


def _fresh_user(user_id):
    """A user who has never changed their password — no token is stale."""
    return MagicMock(user_id=user_id, username="user", email=None, password_changed_at=None)


def _app_with_blueprint(bp):
    app = flask.Flask(__name__)
    limiter.init_app(app)
    app.register_blueprint(bp)
    return app


@pytest.fixture(autouse=True)
def secret_key_env():
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        yield


class TestCartRoutesRequireAuth:
    def _client(self):
        from backend.routes.cart_routes import bp
        return _app_with_blueprint(bp).test_client()

    def test_get_cart_without_token_401(self):
        resp = self._client().get("/api/cart")
        assert resp.status_code == 401

    def test_get_cart_with_token_reaches_controller(self):
        token = _token_for("u_owner")
        with patch("backend.routes.cart_routes.get_cart_controller", return_value=({"items": []}, 200)) as mock_ctrl, \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_owner")):
            resp = self._client().get("/api/cart", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        # Controller must be called with the token-derived id, not a client one
        mock_ctrl.assert_called_once_with("u_owner")

    def test_update_cart_ignores_spoofed_user_id_in_body(self):
        token = _token_for("u_real")
        with patch("backend.routes.cart_routes.update_cart_controller", return_value=({"status": "ok"}, 200)) as mock_ctrl, \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_real")):
            resp = self._client().post(
                "/api/cart/update",
                json={"user_id": "u_spoofed", "product_id": 1, "quantity": 1},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        called_data = mock_ctrl.call_args[0][0]
        assert called_data["user_id"] == "u_real"

    def test_update_cart_without_token_401(self):
        resp = self._client().post("/api/cart/update", json={"product_id": 1, "quantity": 1})
        assert resp.status_code == 401

    def test_clear_cart_without_token_401(self):
        resp = self._client().post("/api/cart/clear")
        assert resp.status_code == 401


class TestSearchRouteOptionalAuth:
    def _client(self):
        from backend.routes.search_routes import bp
        return _app_with_blueprint(bp).test_client()

    def test_anonymous_search_succeeds(self):
        with patch("backend.routes.search_routes.search_controller", return_value=({"products": []}, 200)) as mock_ctrl:
            resp = self._client().get("/api/search?q=phone")
        assert resp.status_code == 200
        # Called with user_id=None for an unauthenticated request
        assert mock_ctrl.call_args[0][1] is None

    def test_authenticated_search_passes_real_user_id(self):
        token = _token_for("u_owner")
        with patch("backend.routes.search_routes.search_controller", return_value=({"products": []}, 200)) as mock_ctrl, \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_owner")):
            resp = self._client().get("/api/search?q=phone", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert mock_ctrl.call_args[0][1] == "u_owner"


class TestRecommendationsRouteRequireAuth:
    def _client(self):
        from backend.routes.recommendations_routes import bp
        return _app_with_blueprint(bp).test_client()

    def test_without_token_401(self):
        resp = self._client().get("/api/recommendations")
        assert resp.status_code == 401

    def test_with_token_reaches_controller_with_real_id(self):
        token = _token_for("u_owner")
        with patch("backend.routes.recommendations_routes.recommendations_controller", return_value=({"recent": []}, 200)) as mock_ctrl, \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_owner")):
            resp = self._client().get("/api/recommendations", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        mock_ctrl.assert_called_once_with("u_owner")


class TestEventsRouteOptionalAuth:
    def _client(self):
        from backend.routes.events_routes import bp
        return _app_with_blueprint(bp).test_client()

    def test_anonymous_event_allowed(self):
        with patch("backend.routes.events_routes.log_event_controller", return_value=({"status": "logged"}, 200)) as mock_ctrl:
            resp = self._client().post("/api/event", json={"event": "click", "product_id": 1})
        assert resp.status_code == 200
        assert mock_ctrl.call_args[0][0]["user_id"] == ""

    def test_authenticated_event_cannot_spoof_user_id(self):
        token = _token_for("u_real")
        with patch("backend.routes.events_routes.log_event_controller", return_value=({"status": "logged"}, 200)) as mock_ctrl, \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_real")):
            resp = self._client().post(
                "/api/event",
                json={"event": "click", "product_id": 1, "user_id": "u_spoofed"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert mock_ctrl.call_args[0][0]["user_id"] == "u_real"


class TestCacheRoutesRequireAdmin:
    def _client(self):
        from backend.routes.cache_routes import bp
        return _app_with_blueprint(bp).test_client()

    def test_without_token_401(self):
        resp = self._client().get("/api/admin/cache/dashboard")
        assert resp.status_code == 401

    def test_spoofed_x_user_id_header_alone_is_ignored(self):
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]):
            resp = self._client().get("/api/admin/cache/dashboard", headers={"X-User-ID": "u_admin"})
        assert resp.status_code == 401

    def test_valid_non_admin_token_403(self):
        token = _token_for("u_regular")
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]):
            resp = self._client().get("/api/admin/cache/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_valid_admin_token_succeeds(self):
        token = _token_for("u_admin")
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]), \
             patch.object(admin_auth, "get_user_by_id", return_value=_fresh_user("u_admin")), \
             patch("backend.routes.cache_routes.get_cache_stats", return_value={"hits": 0, "misses": 0, "hit_rate": 0}):
            resp = self._client().get("/api/admin/cache/dashboard", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


class TestAnalyticsRouteRequireAuthNotAdmin:
    """Regression test for the "Analytics visible to all logged-in users"
    fix — any authenticated user should reach it, not just admins."""

    def _client(self):
        from backend.routes.analytics_routes import bp
        return _app_with_blueprint(bp).test_client()

    def test_without_token_401(self):
        resp = self._client().get("/api/analytics")
        assert resp.status_code == 401

    def test_non_admin_authenticated_user_succeeds(self):
        token = _token_for("u_regular")
        with patch("backend.routes.analytics_routes.get_analytics_json", return_value=({"summary": {}}, 200)), \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_regular")):
            resp = self._client().get("/api/analytics", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
