from flask import Blueprint
from backend.controllers.analytics_controller import get_analytics_json
from backend.utils.admin_auth import require_admin

bp = Blueprint("analytics", __name__, url_prefix="/api")

@bp.route("/analytics", methods=["GET"])
@require_admin
def analytics_json():
    return get_analytics_json()
