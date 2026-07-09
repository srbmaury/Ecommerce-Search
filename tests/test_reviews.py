"""
Tests for the product reviews feature: route auth wiring, controller
validation, and the upsert + aggregate-recompute service behavior.
"""
import os
from unittest.mock import patch, MagicMock

import flask
import pytest

from backend.utils.auth_token import create_token
from backend.utils.rate_limit import limiter


SECRET = "test-secret-key"


def _token_for(user_id):
    with patch.dict(os.environ, {"SECRET_KEY": SECRET}):
        return create_token(user_id)


def _fresh_user(user_id):
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


# ---------- Route auth wiring ----------

class TestReviewsRouteWiring:
    def _client(self):
        from backend.routes.reviews_routes import bp
        return _app_with_blueprint(bp).test_client()

    def test_list_reviews_is_public(self):
        with patch("backend.routes.reviews_routes.get_reviews_controller", return_value=({"reviews": []}, 200)) as mock_ctrl:
            resp = self._client().get("/api/products/1/reviews")
        assert resp.status_code == 200
        mock_ctrl.assert_called_once_with(1)

    def test_submit_review_without_token_401(self):
        resp = self._client().post("/api/products/1/reviews", json={"rating": 5})
        assert resp.status_code == 401

    def test_submit_review_ignores_spoofed_user_id_in_body(self):
        token = _token_for("u_real")
        with patch("backend.routes.reviews_routes.submit_review_controller", return_value=({"status": "ok"}, 200)) as mock_ctrl, \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_real")):
            resp = self._client().post(
                "/api/products/1/reviews",
                json={"rating": 5, "user_id": "u_spoofed"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        called_data = mock_ctrl.call_args[0][0]
        assert called_data["user_id"] == "u_real"
        assert called_data["product_id"] == 1

    def test_delete_review_without_token_401(self):
        resp = self._client().delete("/api/products/1/reviews")
        assert resp.status_code == 401

    def test_delete_review_uses_token_derived_user_id(self):
        token = _token_for("u_real")
        with patch("backend.routes.reviews_routes.delete_review_controller", return_value=({"status": "ok"}, 200)) as mock_ctrl, \
             patch("backend.utils.auth_middleware.get_user_by_id", return_value=_fresh_user("u_real")):
            resp = self._client().delete(
                "/api/products/1/reviews",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        mock_ctrl.assert_called_once_with(1, "u_real")


# ---------- Controller validation ----------

class TestSubmitReviewController:
    def _product(self):
        return {"product_id": 1, "title": "Widget"}

    def test_missing_product_returns_404(self):
        from backend.controllers.review_controller import submit_review_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=None):
            resp, status = submit_review_controller({"product_id": 1, "user_id": "u1", "rating": 5})
        assert status == 404

    def test_rating_out_of_range_rejected(self):
        from backend.controllers.review_controller import submit_review_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=self._product()):
            resp, status = submit_review_controller({"product_id": 1, "user_id": "u1", "rating": 6})
        assert status == 400

    def test_rating_zero_rejected(self):
        from backend.controllers.review_controller import submit_review_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=self._product()):
            resp, status = submit_review_controller({"product_id": 1, "user_id": "u1", "rating": 0})
        assert status == 400

    def test_non_integer_rating_rejected(self):
        from backend.controllers.review_controller import submit_review_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=self._product()):
            resp, status = submit_review_controller({"product_id": 1, "user_id": "u1", "rating": "not-a-number"})
        assert status == 400

    def test_comment_too_long_rejected(self):
        from backend.controllers.review_controller import submit_review_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=self._product()):
            resp, status = submit_review_controller({
                "product_id": 1, "user_id": "u1", "rating": 5, "comment": "x" * 2001,
            })
        assert status == 400

    def test_valid_review_calls_submit_review(self):
        from backend.controllers.review_controller import submit_review_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=self._product()), \
             patch("backend.controllers.review_controller.submit_review", return_value=True) as mock_submit:
            resp, status = submit_review_controller({
                "product_id": 1, "user_id": "u1", "rating": 4, "comment": "Pretty good",
            })
        assert status == 200
        mock_submit.assert_called_once_with(1, "u1", 4, "Pretty good")

    def test_blank_comment_normalized_to_none(self):
        from backend.controllers.review_controller import submit_review_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=self._product()), \
             patch("backend.controllers.review_controller.submit_review", return_value=True) as mock_submit:
            submit_review_controller({"product_id": 1, "user_id": "u1", "rating": 4, "comment": "   "})
        assert mock_submit.call_args[0][3] is None


class TestDeleteReviewController:
    def test_nonexistent_review_returns_404(self):
        from backend.controllers.review_controller import delete_review_controller
        with patch("backend.controllers.review_controller.delete_review", return_value=False):
            resp, status = delete_review_controller(1, "u1")
        assert status == 404

    def test_existing_review_deleted(self):
        from backend.controllers.review_controller import delete_review_controller
        with patch("backend.controllers.review_controller.delete_review", return_value=True) as mock_delete:
            resp, status = delete_review_controller(1, "u1")
        assert status == 200
        mock_delete.assert_called_once_with(1, "u1")

    def test_invalid_product_id_rejected(self):
        from backend.controllers.review_controller import delete_review_controller
        resp, status = delete_review_controller("not-an-id", "u1")
        assert status == 400


class TestGetReviewsController:
    def test_missing_product_returns_404(self):
        from backend.controllers.review_controller import get_reviews_controller
        with patch("backend.controllers.review_controller.get_product_by_id", return_value=None):
            resp, status = get_reviews_controller(1)
        assert status == 404

    def test_returns_reviews_and_count(self):
        from backend.controllers.review_controller import get_reviews_controller
        reviews = [{"id": 1, "rating": 5}, {"id": 2, "rating": 3}]
        with patch("backend.controllers.review_controller.get_product_by_id", return_value={"product_id": 1}), \
             patch("backend.controllers.review_controller.get_reviews_for_product", return_value=reviews):
            resp, status = get_reviews_controller(1)
        assert status == 200
        assert resp["count"] == 2
        assert resp["reviews"] == reviews


# ---------- Service: upsert + aggregate recompute ----------

class TestSubmitReviewService:
    def _mock_session(self):
        session = MagicMock()
        session.bind.dialect.name = "sqlite"
        session.query.return_value.filter.return_value.one.return_value = (4.5, 2)
        return session

    def test_resubmitting_upserts_not_duplicates(self):
        """Calling submit_review twice for the same (product, user) must
        hit on_conflict_do_update, not create two rows — this is what makes
        'one review per user per product' actually hold under the hood."""
        from backend.services.review.create import submit_review
        session = self._mock_session()
        with patch("backend.services.review.create.get_db_session", return_value=session):
            submit_review(1, "u1", 5, "Great")
        executed_stmt = session.execute.call_args[0][0]
        assert executed_stmt is not None
        # on_conflict_do_update compiles into an INSERT ... ON CONFLICT statement
        assert "ON CONFLICT" in str(executed_stmt)

    def test_recomputes_product_aggregate_after_upsert(self):
        from backend.services.review.create import submit_review
        session = self._mock_session()
        with patch("backend.services.review.create.get_db_session", return_value=session):
            submit_review(1, "u1", 5, None)
        # Product.rating/review_count update should reflect the aggregate query result
        update_call = session.query.return_value.filter.return_value.update
        update_call.assert_called_once_with({"rating": 4.5, "review_count": 2})
        session.commit.assert_called_once()

    def test_rolls_back_on_error(self):
        from backend.services.review.create import submit_review
        session = self._mock_session()
        session.execute.side_effect = RuntimeError("db error")
        with patch("backend.services.review.create.get_db_session", return_value=session):
            with pytest.raises(RuntimeError):
                submit_review(1, "u1", 5, None)
        session.rollback.assert_called_once()


class TestDeleteReviewService:
    def _mock_session(self, delete_count=1):
        session = MagicMock()
        session.query.return_value.filter_by.return_value.delete.return_value = delete_count
        session.query.return_value.filter.return_value.one.return_value = (4.0, 1)
        return session

    def test_deletes_and_recomputes_aggregate(self):
        from backend.services.review.delete import delete_review
        session = self._mock_session(delete_count=1)
        with patch("backend.services.review.delete.get_db_session", return_value=session):
            result = delete_review(1, "u1")
        assert result is True
        session.query.return_value.filter_by.assert_called_once_with(product_id=1, user_id="u1")
        update_call = session.query.return_value.filter.return_value.update
        update_call.assert_called_once_with({"rating": 4.0, "review_count": 1})
        session.commit.assert_called_once()

    def test_no_matching_review_returns_false_without_commit(self):
        from backend.services.review.delete import delete_review
        session = self._mock_session(delete_count=0)
        with patch("backend.services.review.delete.get_db_session", return_value=session):
            result = delete_review(1, "u1")
        assert result is False
        session.commit.assert_not_called()
        session.rollback.assert_called_once()

    def test_rolls_back_on_error(self):
        from backend.services.review.delete import delete_review
        session = self._mock_session()
        session.query.return_value.filter_by.return_value.delete.side_effect = RuntimeError("db error")
        with patch("backend.services.review.delete.get_db_session", return_value=session):
            with pytest.raises(RuntimeError):
                delete_review(1, "u1")
        session.rollback.assert_called_once()
