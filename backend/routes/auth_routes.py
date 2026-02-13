from flask import Blueprint, request
from backend.controllers.auth_controller import (
    signup_controller,
    login_controller,
    verify_email_controller,
    resend_verification_controller,
    forgot_password_controller,
    reset_password_controller,
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


@bp.route("/verify-email", methods=["POST", "OPTIONS"])
def verify_email():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    return verify_email_controller(request.json)


@bp.route("/resend-verification", methods=["POST", "OPTIONS"])
def resend_verification():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    return resend_verification_controller(request.json)


@bp.route("/forgot-password", methods=["POST", "OPTIONS"])
def forgot_password():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    return forgot_password_controller(request.json)


@bp.route("/reset-password", methods=["POST", "OPTIONS"])
def reset_password():
    if request.method == "OPTIONS":
        return {"message": "CORS preflight successful"}, 200
    return reset_password_controller(request.json)
