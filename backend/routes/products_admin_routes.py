"""
Admin product management routes.

All endpoints require a valid session token whose user_id is in
ADMIN_USER_IDS (see backend/utils/admin_auth.py).
"""

from flask import Blueprint, request, jsonify

from backend.controllers.product_admin_controller import (
    list_products_controller,
    create_product_controller,
    update_product_controller,
    delete_product_controller,
)
from backend.utils.admin_auth import require_admin

bp = Blueprint("products_admin", __name__, url_prefix="/api/admin/products")


@bp.route("", methods=["GET"])
@require_admin
def list_products():
    resp, status = list_products_controller(
        search=request.args.get("q"),
        cursor_raw=request.args.get("cursor"),
        limit_raw=request.args.get("limit"),
    )
    return jsonify(resp), status


@bp.route("", methods=["POST"])
@require_admin
def create_product_route():
    resp, status = create_product_controller(dict(request.json or {}))
    return jsonify(resp), status


@bp.route("/<int:product_id>", methods=["PUT"])
@require_admin
def update_product_route(product_id):
    resp, status = update_product_controller(product_id, dict(request.json or {}))
    return jsonify(resp), status


@bp.route("/<int:product_id>", methods=["DELETE"])
@require_admin
def delete_product_route(product_id):
    resp, status = delete_product_controller(product_id)
    return jsonify(resp), status
