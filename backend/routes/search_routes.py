from flask import Blueprint, request, jsonify
from backend.controllers.search_controller import search_controller

bp = Blueprint("search", __name__, url_prefix="/api")


@bp.route("/search", methods=["GET", "OPTIONS"])
def search():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    resp, status = search_controller(
        request.args.get("q"),
        request.args.get("user_id")
    )
    return jsonify(resp), status
