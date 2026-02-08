from flask import request, jsonify
from backend.controllers.cart_controller import batch_cart_controller

# Add this to cart_routes.py
@bp.route("/cart/batch", methods=["POST", "OPTIONS"])
def batch_cart():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = batch_cart_controller(request.json or {})
    return jsonify(resp), status
