from flask import Blueprint, request
from backend.controllers.auth_controller import (
    signup_controller,
    login_controller
)

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.route("/signup", methods=["POST", "OPTIONS"])
def signup():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    return signup_controller(request.json)


@bp.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    return login_controller(request.json)
