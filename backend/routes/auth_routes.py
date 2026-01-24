from flask import Blueprint, request
from backend.controllers.auth_controller import (
    signup_controller,
    login_controller
)

bp = Blueprint("auth", __name__)


@bp.route("/signup", methods=["POST"])
def signup():
    return signup_controller(request.json)


@bp.route("/login", methods=["POST"])
def login():
    return login_controller(request.json)
