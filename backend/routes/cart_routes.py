from flask import Blueprint, request, jsonify
from backend.controllers.cart_controller import (
    add_to_cart_controller,
    get_cart_controller,
    remove_from_cart_controller,
    clear_cart_controller
)


bp = Blueprint("cart", __name__, url_prefix="/api")

# Batch cart actions endpoint (moved inline to avoid NameError)
from backend.controllers.cart_controller import batch_cart_controller
@bp.route("/cart/batch", methods=["POST", "OPTIONS"])
def batch_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = batch_cart_controller(request.json or {})
    return jsonify(resp), status


@bp.route("/cart", methods=["POST", "OPTIONS"])
def add_to_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = add_to_cart_controller(request.json or {})
    return jsonify(resp), status


@bp.route("/cart", methods=["GET", "OPTIONS"])
def get_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = get_cart_controller(request.args.get("user_id"))
    return jsonify(resp), status


@bp.route("/cart/remove", methods=["POST", "OPTIONS"])
def remove_from_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = remove_from_cart_controller(request.json or {})
    return jsonify(resp), status


@bp.route("/cart/clear", methods=["POST", "OPTIONS"])
def clear_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = clear_cart_controller(request.json or {})
    return jsonify(resp), status
