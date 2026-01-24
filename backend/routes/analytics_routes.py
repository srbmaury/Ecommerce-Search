from flask import Blueprint
from backend.controllers.analytics_controller import get_analytics_data

bp = Blueprint("analytics", __name__)

@bp.route("/analytics", methods=["GET"])
def analytics():
    return get_analytics_data()
