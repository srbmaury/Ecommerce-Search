from flask import Blueprint, jsonify, g
from backend.controllers.recommendations_controller import recommendations_controller
from backend.utils.auth_middleware import require_auth

bp = Blueprint("recommendations", __name__, url_prefix="/api")


@bp.route("/recommendations", methods=["GET"])
@require_auth
def recommendations():
    resp, status = recommendations_controller(g.user_id)
    return jsonify(resp), status
