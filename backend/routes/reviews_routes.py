from flask import Blueprint, request, jsonify, g
from backend.controllers.review_controller import (
    submit_review_controller,
    get_reviews_controller,
    delete_review_controller,
)
from backend.utils.auth_middleware import require_auth, optional_auth
from backend.utils.rate_limit import limiter

bp = Blueprint("reviews", __name__, url_prefix="/api")


@bp.route("/products/<int:product_id>/reviews", methods=["GET"])
@limiter.limit("60 per minute")
@optional_auth
def list_reviews(product_id):
    resp, status = get_reviews_controller(product_id)
    return jsonify(resp), status


@bp.route("/products/<int:product_id>/reviews", methods=["POST"])
@limiter.limit("20 per minute")
@require_auth
def create_review(product_id):
    data = dict(request.json or {})
    data["product_id"] = product_id
    data["user_id"] = g.user_id  # server-derived identity, not client-supplied
    resp, status = submit_review_controller(data)
    return jsonify(resp), status


@bp.route("/products/<int:product_id>/reviews", methods=["DELETE"])
@limiter.limit("20 per minute")
@require_auth
def delete_review_route(product_id):
    resp, status = delete_review_controller(product_id, g.user_id)
    return jsonify(resp), status
