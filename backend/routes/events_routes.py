from flask import Blueprint, request, jsonify
from backend.controllers.events_controller import log_event_controller

bp = Blueprint("events", __name__, url_prefix="/api")


@bp.route("/event", methods=["POST", "OPTIONS"])
def log_event():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200
    resp, status = log_event_controller(request.json or {})
    return jsonify(resp), status
