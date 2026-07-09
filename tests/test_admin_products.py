"""
Tests for admin product management: require_admin route wiring and
controller validation for create/update/delete.
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
    return MagicMock(user_id=user_id, username="admin", email=None, password_changed_at=None)


def _app_with_blueprint(bp):
    app = flask.Flask(__name__)
    limiter.init_app(app)
    app.register_blueprint(bp)
    return app


@pytest.fixture(autouse=True)
def secret_key_env():
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        yield


# ---------- Route auth wiring ----------

class TestAdminProductRoutesRequireAdmin:
    def _client(self):
        from backend.routes.products_admin_routes import bp
        return _app_with_blueprint(bp).test_client()

    @pytest.mark.parametrize("method,path", [
        ("GET", "/api/admin/products"),
        ("POST", "/api/admin/products"),
        ("PUT", "/api/admin/products/1"),
        ("DELETE", "/api/admin/products/1"),
    ])
    def test_without_token_401(self, method, path):
        resp = self._client().open(path, method=method)
        assert resp.status_code == 401

    @pytest.mark.parametrize("method,path", [
        ("GET", "/api/admin/products"),
        ("POST", "/api/admin/products"),
        ("PUT", "/api/admin/products/1"),
        ("DELETE", "/api/admin/products/1"),
    ])
    def test_non_admin_token_403(self, method, path):
        token = _token_for("u_regular")
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]):
            resp = self._client().open(path, method=method, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_admin_list_products_succeeds(self):
        token = _token_for("u_admin")
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]), \
             patch.object(admin_auth, "get_user_by_id", return_value=_fresh_user("u_admin")), \
             patch("backend.routes.products_admin_routes.list_products_controller", return_value=({"products": []}, 200)):
            resp = self._client().get("/api/admin/products", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_admin_create_product_succeeds(self):
        token = _token_for("u_admin")
        with patch.object(admin_auth, "ADMIN_USER_IDS", ["u_admin"]), \
             patch.object(admin_auth, "get_user_by_id", return_value=_fresh_user("u_admin")), \
             patch("backend.routes.products_admin_routes.create_product_controller", return_value=({"status": "created"}, 201)) as mock_ctrl:
            resp = self._client().post(
                "/api/admin/products",
                json={"title": "Widget", "price": 9.99},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 201
        mock_ctrl.assert_called_once_with({"title": "Widget", "price": 9.99})


# ---------- Controller validation ----------

class TestCreateProductController:
    def test_missing_title_rejected(self):
        from backend.controllers.product_admin_controller import create_product_controller
        resp, status = create_product_controller({"title": "", "price": 10})
        assert status == 400

    def test_non_numeric_price_rejected(self):
        from backend.controllers.product_admin_controller import create_product_controller
        resp, status = create_product_controller({"title": "Widget", "price": "abc"})
        assert status == 400

    def test_zero_or_negative_price_rejected(self):
        from backend.controllers.product_admin_controller import create_product_controller
        resp, status = create_product_controller({"title": "Widget", "price": 0})
        assert status == 400
        resp, status = create_product_controller({"title": "Widget", "price": -5})
        assert status == 400

    def test_valid_product_created(self):
        from backend.controllers.product_admin_controller import create_product_controller
        fake_product = MagicMock(id=1)
        with patch("backend.controllers.product_admin_controller.create_product", return_value=fake_product) as mock_create, \
             patch("backend.controllers.product_admin_controller.serialize_product", return_value={"product_id": 1}), \
             patch("backend.controllers.product_admin_controller.invalidate_on_product_update") as mock_invalidate:
            resp, status = create_product_controller({
                "title": "Widget", "price": 9.99, "category": "Gadgets", "description": "A widget",
            })
        assert status == 201
        mock_create.assert_called_once_with(
            title="Widget", description="A widget", category="Gadgets", price=9.99,
        )
        mock_invalidate.assert_called_once_with(1)


class TestUpdateProductController:
    def test_no_fields_rejected(self):
        from backend.controllers.product_admin_controller import update_product_controller
        resp, status = update_product_controller(1, {})
        assert status == 400

    def test_invalid_price_rejected(self):
        from backend.controllers.product_admin_controller import update_product_controller
        resp, status = update_product_controller(1, {"price": -1})
        assert status == 400

    def test_nonexistent_product_404(self):
        from backend.controllers.product_admin_controller import update_product_controller
        with patch("backend.controllers.product_admin_controller.update_product", return_value=None):
            resp, status = update_product_controller(999, {"title": "New Title"})
        assert status == 404

    def test_valid_update_succeeds(self):
        from backend.controllers.product_admin_controller import update_product_controller
        with patch("backend.controllers.product_admin_controller.update_product", return_value={"product_id": 1, "title": "New Title"}) as mock_update, \
             patch("backend.controllers.product_admin_controller.invalidate_on_product_update") as mock_invalidate:
            resp, status = update_product_controller(1, {"title": "New Title"})
        assert status == 200
        mock_update.assert_called_once_with(1, title="New Title")
        mock_invalidate.assert_called_once_with(1)


class TestDeleteProductController:
    def test_nonexistent_product_404(self):
        from backend.controllers.product_admin_controller import delete_product_controller
        with patch("backend.controllers.product_admin_controller.delete_product", return_value=False):
            resp, status = delete_product_controller(999)
        assert status == 404

    def test_existing_product_deleted(self):
        from backend.controllers.product_admin_controller import delete_product_controller
        with patch("backend.controllers.product_admin_controller.delete_product", return_value=True) as mock_delete, \
             patch("backend.controllers.product_admin_controller.invalidate_on_product_update") as mock_invalidate:
            resp, status = delete_product_controller(1)
        assert status == 200
        mock_delete.assert_called_once_with(1)
        mock_invalidate.assert_called_once_with(1)


class TestListProductsController:
    def test_default_pagination(self):
        from backend.controllers.product_admin_controller import list_products_controller
        with patch("backend.controllers.product_admin_controller.get_products_paginated", return_value=([{"product_id": 1}], 1)) as mock_list:
            resp, status = list_products_controller()
        assert status == 200
        assert resp == {"products": [{"product_id": 1}], "total": 1, "cursor": 0, "limit": 50, "has_more": False}
        mock_list.assert_called_once_with(search=None, cursor=0, limit=50)

    def test_search_and_pagination_params_forwarded(self):
        from backend.controllers.product_admin_controller import list_products_controller
        with patch("backend.controllers.product_admin_controller.get_products_paginated", return_value=([], 0)) as mock_list:
            list_products_controller(search="phone", cursor_raw="10", limit_raw="5")
        mock_list.assert_called_once_with(search="phone", cursor=10, limit=5)

    def test_has_more_true_when_results_remain(self):
        from backend.controllers.product_admin_controller import list_products_controller
        with patch("backend.controllers.product_admin_controller.get_products_paginated", return_value=([{"product_id": 1}], 5)):
            resp, status = list_products_controller(cursor_raw="0", limit_raw="1")
        assert resp["has_more"] is True

    def test_invalid_cursor_rejected(self):
        from backend.controllers.product_admin_controller import list_products_controller
        resp, status = list_products_controller(cursor_raw="-1")
        assert status == 400

    def test_invalid_limit_rejected(self):
        from backend.controllers.product_admin_controller import list_products_controller
        resp, status = list_products_controller(limit_raw="0")
        assert status == 400
