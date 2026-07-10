from flask import Blueprint
from backend.controllers.analytics_controller import get_analytics_json
from backend.utils.auth_middleware import require_auth

bp = Blueprint("analytics", __name__, url_prefix="/api")

# Aggregate-only (group summaries, cluster counts, top queries — no per-user
# data), so any logged-in user can view it, matching the "Analytics" nav
# button which is shown unconditionally rather than gated on is_admin.
@bp.route("/analytics", methods=["GET"])
@require_auth
def analytics_json():
    return get_analytics_json()
