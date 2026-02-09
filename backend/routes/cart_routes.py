from flask import Blueprint, request, jsonify
from backend.controllers.cart_controller import (
    get_cart_controller,
    clear_cart_controller,
    update_cart_controller
)


bp = Blueprint("cart", __name__, url_prefix="/api")


@bp.route("/cart/update", methods=["POST", "OPTIONS"])
def update_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = update_cart_controller(request.json or {})
    return jsonify(resp), status


@bp.route("/cart", methods=["GET", "OPTIONS"])
def get_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = get_cart_controller(request.args.get("user_id"))
    return jsonify(resp), status


@bp.route("/cart/clear", methods=["POST", "OPTIONS"])
def clear_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = clear_cart_controller(request.json or {})
    return jsonify(resp), status
