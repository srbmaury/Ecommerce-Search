from flask import Blueprint, request, jsonify
from backend.controllers.events_controller import log_event_controller

bp = Blueprint("events", __name__, url_prefix="/api")


@bp.route("/event", methods=["POST"])
def log_event():
    resp, status = log_event_controller(request.json or {})
    return jsonify(resp), status
