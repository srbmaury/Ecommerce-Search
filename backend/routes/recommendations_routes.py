from flask import Blueprint, request, jsonify
from backend.controllers.recommendations_controller import recommendations_controller

bp = Blueprint("recommendations", __name__, url_prefix="/api")


@bp.route("/recommendations", methods=["GET"])
def recommendations():
    resp, status = recommendations_controller(
        request.args.get("user_id")
    )
    return jsonify(resp), status
