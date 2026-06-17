from flask import Blueprint, request, jsonify
from backend.controllers.search_controller import search_controller

bp = Blueprint("search", __name__, url_prefix="/api")


@bp.route("/search", methods=["GET"])
def search():
    resp, status = search_controller(
        request.args.get("q"),
        request.args.get("user_id"),
        request.args.get("cursor"),
        request.args.get("limit"),
    )
    return jsonify(resp), status
