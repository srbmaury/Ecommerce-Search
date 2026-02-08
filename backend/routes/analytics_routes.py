from flask import Blueprint, request
from backend.controllers.analytics_controller import get_analytics_json

bp = Blueprint("analytics", __name__, url_prefix="/api")

@bp.route("/analytics", methods=["GET", "OPTIONS"])
def analytics_json():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    return get_analytics_json()
