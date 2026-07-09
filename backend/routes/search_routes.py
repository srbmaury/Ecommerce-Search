from flask import Blueprint, request, jsonify, g
from backend.controllers.search_controller import search_controller
from backend.utils.auth_middleware import optional_auth
from backend.utils.rate_limit import limiter

bp = Blueprint("search", __name__, url_prefix="/api")


@bp.route("/search", methods=["GET"])
@limiter.limit("60 per minute")
@optional_auth
def search():
    resp, status = search_controller(
        request.args.get("q"),
        g.user_id,  # server-derived; anonymous search stays anonymous
        request.args.get("cursor"),
        request.args.get("limit"),
    )
    return jsonify(resp), status
