from flask import Blueprint
from backend.controllers.analytics_controller import get_analytics_data, get_analytics_json

bp = Blueprint("analytics", __name__)

@bp.route("/analytics", methods=["GET"])
def analytics():
    return get_analytics_data()

# New API endpoint for dashboard
@bp.route("/api/analytics", methods=["GET"])
def analytics_json():
    return get_analytics_json()
