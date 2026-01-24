from flask import Blueprint, request, jsonify
from backend.controllers.search_controller import search_controller

bp = Blueprint("search", __name__)


@bp.route("/search", methods=["GET"])
def search():
    resp, status = search_controller(
        request.args.get("q"),
        request.args.get("user_id")
    )
    return jsonify(resp), status
