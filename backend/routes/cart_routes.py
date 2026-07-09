from flask import Blueprint, request, jsonify, g
from backend.controllers.cart_controller import (
    get_cart_controller,
    clear_cart_controller,
    update_cart_controller
)
from backend.utils.auth_middleware import require_auth
from backend.utils.rate_limit import limiter

bp = Blueprint("cart", __name__, url_prefix="/api")


@bp.route("/cart/update", methods=["POST"])
@limiter.limit("60 per minute")
@require_auth
def update_cart():
    data = dict(request.json or {})
    data["user_id"] = g.user_id  # server-derived identity, not client-supplied
    resp, status = update_cart_controller(data)
    return jsonify(resp), status


@bp.route("/cart", methods=["GET"])
@limiter.limit("120 per minute")
@require_auth
def get_cart():
    resp, status = get_cart_controller(g.user_id)
    return jsonify(resp), status


@bp.route("/cart/clear", methods=["POST"])
@limiter.limit("20 per minute")
@require_auth
def clear_cart():
    resp, status = clear_cart_controller({"user_id": g.user_id})
    return jsonify(resp), status
