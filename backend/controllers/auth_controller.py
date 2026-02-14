import random
import uuid
import bcrypt
from flask import jsonify

from backend.services.security import (
    validate_username,
    validate_password,
    validate_email,
    hash_password,
)
from backend.services.db_user_manager import (
    get_user_by_username,
    create_user,
)
from backend.services.email_service import (
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    use_password_reset_token,
    send_verification_email,
    send_password_reset_email,
    get_user_by_email,
    update_user_password,
)


EXPERIMENT_GROUPS = ("A", "B")


# ---------- Helpers ----------

def generate_user_id():
    # Short, collision-resistant, non-sequential ID
    return f"u{uuid.uuid4().hex[:12]}"


def invalid_response(message, status=400):
    return jsonify({"error": message}), status


def success_response(message, **kwargs):
    return jsonify({"message": message, **kwargs})


def constant_time_password_check(password: str, password_hash: str | None):
    """
    Prevents timing attacks by always running bcrypt.
    """
    password_bytes = password.encode("utf-8")

    if password_hash:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))

    # Dummy check to match bcrypt cost
    bcrypt.checkpw(password_bytes, bcrypt.hashpw(b"dummy", bcrypt.gensalt()))
    return False


# ---------- Controllers ----------

def signup_controller(data):
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    ok, error = validate_username(username)
    if not ok:
        return invalid_response(error)

    ok, error = validate_password(password)
    if not ok:
        return invalid_response(error)

    # Email is optional but validated if provided
    if email:
        email = email.strip().lower()
        ok, error = validate_email(email)
        if not ok:
            return invalid_response(error)

    user_id = generate_user_id()
    group = random.choice(EXPERIMENT_GROUPS)

    try:
        user = create_user(
            user_id=user_id,
            username=username,
            password_hash=hash_password(password),
            group=group,
            email=email,
        )
    except Exception as e:
        # Handle unique constraint violations safely
        error_str = str(e).lower()
        if "unique" in error_str or "duplicate" in error_str:
            if "email" in error_str:
                return invalid_response("email already exists")
            return invalid_response("username already exists")
        raise

    # Send verification email if email provided
    if email:
        token = create_email_verification_token(user.user_id)
        send_verification_email(email, username, token)

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "group": user.group,
        "email_verified": user.email_verified,
    })


def login_controller(data):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return invalid_response("username and password required")

    user = get_user_by_username(username)

    password_valid = constant_time_password_check(
        password,
        user.password_hash if user else None
    )

    if not user or not password_valid:
        return invalid_response("invalid credentials", status=401)

    return jsonify({
        "user_id": user.user_id,
        "username": user.username,
        "group": user.group,
        "email_verified": user.email_verified,
    })


# ---------- Email Verification ----------

def verify_email_controller(data):
    """Verify user's email with token."""
    token = data.get("token")
    
    if not token:
        return invalid_response("Verification token is required.")
    
    user = verify_email_token(token)
    
    if not user:
        return invalid_response("Invalid or expired verification link.", status=400)
    
    return success_response(
        "Email verified successfully!",
        user_id=user.user_id,
        email_verified=True,
    )


def resend_verification_controller(data):
    """Resend verification email."""
    email = data.get("email")
    
    if not email:
        return invalid_response("Email is required.")
    
    email = email.strip().lower()
    user = get_user_by_email(email)
    
    # Always return success to prevent email enumeration
    if not user:
        return success_response(
            "If an account exists with this email, a verification link has been sent."
        )
    
    if user.email_verified:
        return success_response("Email is already verified.")
    
    token = create_email_verification_token(user.user_id)
    send_verification_email(email, user.username, token)
    
    return success_response(
        "If an account exists with this email, a verification link has been sent."
    )


# ---------- Password Reset ----------

def forgot_password_controller(data):
    """Request password reset link."""
    email = data.get("email")
    
    if not email:
        return invalid_response("Email is required.")
    
    email = email.strip().lower()
    user = get_user_by_email(email)
    
    # Always return success to prevent email enumeration
    if not user:
        return success_response(
            "If an account exists with this email, a password reset link has been sent."
        )
    
    token = create_password_reset_token(user.user_id)
    send_password_reset_email(email, user.username, token)
    
    return success_response(
        "If an account exists with this email, a password reset link has been sent."
    )


def reset_password_controller(data):
    """Reset password with token."""
    token = data.get("token")
    new_password = data.get("password")
    
    if not token:
        return invalid_response("Reset token is required.")
    
    if not new_password:
        return invalid_response("New password is required.")
    
    # Validate new password
    ok, error = validate_password(new_password)
    if not ok:
        return invalid_response(error)
    
    user = verify_password_reset_token(token)
    
    if not user:
        return invalid_response("Invalid or expired reset link.", status=400)
    
    # Update password
    password_hash = hash_password(new_password)
    update_user_password(user.user_id, password_hash)
    
    # Mark token as used
    use_password_reset_token(token)
    
    return success_response("Password reset successfully! You can now log in.")
