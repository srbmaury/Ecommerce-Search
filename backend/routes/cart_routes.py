from flask import Blueprint, request, jsonify
from backend.controllers.cart_controller import (
    get_cart_controller,
    clear_cart_controller,
    update_cart_controller
)

bp = Blueprint("cart", __name__, url_prefix="/api")


@bp.route("/cart/update", methods=["POST"])
def update_cart():
    resp, status = update_cart_controller(request.json or {})
    return jsonify(resp), status


@bp.route("/cart", methods=["GET"])
def get_cart():
    resp, status = get_cart_controller(request.args.get("user_id"))
    return jsonify(resp), status


@bp.route("/cart/clear", methods=["POST"])
def clear_cart():
    resp, status = clear_cart_controller(request.json or {})
    return jsonify(resp), status
