from flask import Blueprint, request, jsonify, g
from backend.controllers.events_controller import log_event_controller
from backend.utils.auth_middleware import optional_auth

bp = Blueprint("events", __name__, url_prefix="/api")


@bp.route("/event", methods=["POST"])
@optional_auth
def log_event():
    data = dict(request.json or {})
    # Anonymous events are allowed, but if the caller IS authenticated,
    # the event must be attributed to them — never to a client-chosen id.
    data["user_id"] = g.user_id or ""
    resp, status = log_event_controller(data)
    return jsonify(resp), status
