from flask import Blueprint, request
from backend.controllers.auth_controller import (
    signup_controller,
    login_controller,
    verify_email_controller,
    resend_verification_controller,
    forgot_password_controller,
    reset_password_controller,
)
from backend.utils.rate_limit import limiter

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.route("/signup", methods=["POST"])
@limiter.limit("10 per hour")
def signup():
    return signup_controller(request.json or {})


@bp.route("/login", methods=["POST"])
@limiter.limit("20 per minute")
def login():
    return login_controller(request.json or {})


@bp.route("/verify-email", methods=["POST"])
def verify_email():
    return verify_email_controller(request.json or {})


@bp.route("/resend-verification", methods=["POST"])
@limiter.limit("5 per hour")
def resend_verification():
    return resend_verification_controller(request.json or {})


@bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    return forgot_password_controller(request.json or {})


@bp.route("/reset-password", methods=["POST"])
@limiter.limit("10 per hour")
def reset_password():
    return reset_password_controller(request.json or {})
