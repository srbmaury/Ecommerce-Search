"""
Email service for sending verification and password reset emails.

Supports SMTP or can be extended for services like SendGrid, Mailgun, etc.
"""

import os
import logging
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.utils.database import get_db_session
from backend.models import (
    User,
    EmailVerificationToken,
    PasswordResetToken,
)


logger = logging.getLogger("email_service")


# ---------- CONFIG ----------

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@example.com")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Ecommerce Search")

# Frontend URL for links in emails
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Token expiry times
EMAIL_VERIFICATION_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_HOURS = 1


# ---------- TOKEN GENERATION ----------

def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def utcnow():
    return datetime.now(timezone.utc)


# ---------- EMAIL VERIFICATION ----------

def create_email_verification_token(user_id: str) -> str:
    """
    Create an email verification token for a user.
    Invalidates any existing tokens for the user.
    """
    session = get_db_session()
    try:
        # Delete existing tokens for this user
        session.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id
        ).delete()
        
        token = generate_token()
        expires_at = utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS)
        
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        session.add(verification_token)
        session.commit()
        
        return token
    except Exception as e:
        session.rollback()
        logger.exception("Failed to create email verification token")
        raise
    finally:
        session.close()


def verify_email_token(token: str) -> Optional[User]:
    """
    Verify an email token and mark user's email as verified.
    Returns the user if successful, None otherwise.
    """
    session = get_db_session()
    try:
        verification = session.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token
        ).first()
        
        if not verification:
            return None
        
        if verification.expires_at < utcnow():
            # Token expired, delete it
            session.delete(verification)
            session.commit()
            return None
        
        # Mark user as verified
        user = session.query(User).filter(
            User.user_id == verification.user_id
        ).first()
        
        if user:
            user.email_verified = True
            session.delete(verification)
            session.commit()
            session.refresh(user)
            session.expunge(user)
            return user
        
        return None
    except Exception as e:
        session.rollback()
        logger.exception("Failed to verify email token")
        raise
    finally:
        session.close()


# ---------- PASSWORD RESET ----------

def create_password_reset_token(user_id: str) -> str:
    """
    Create a password reset token for a user.
    Invalidates any existing unused tokens for the user.
    """
    session = get_db_session()
    try:
        # Invalidate existing unused tokens
        session.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used == False
        ).update({"used": True})
        
        token = generate_token()
        expires_at = utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)
        
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        session.add(reset_token)
        session.commit()
        
        return token
    except Exception as e:
        session.rollback()
        logger.exception("Failed to create password reset token")
        raise
    finally:
        session.close()


def verify_password_reset_token(token: str) -> Optional[User]:
    """
    Verify a password reset token.
    Returns the user if valid, None otherwise.
    Does NOT mark as used - call use_password_reset_token after password change.
    """
    session = get_db_session()
    try:
        reset = session.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used == False
        ).first()
        
        if not reset:
            return None
        
        if reset.expires_at < utcnow():
            # Token expired
            reset.used = True
            session.commit()
            return None
        
        user = session.query(User).filter(
            User.user_id == reset.user_id
        ).first()
        
        if user:
            session.expunge(user)
            return user
        
        return None
    except Exception as e:
        session.rollback()
        logger.exception("Failed to verify password reset token")
        raise
    finally:
        session.close()


def use_password_reset_token(token: str) -> bool:
    """Mark a password reset token as used."""
    session = get_db_session()
    try:
        result = session.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).update({"used": True})
        session.commit()
        return result > 0
    except Exception as e:
        session.rollback()
        logger.exception("Failed to use password reset token")
        raise
    finally:
        session.close()


# ---------- EMAIL SENDING ----------

def _send_email(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """
    Send an email via SMTP.
    Returns True if successful, False otherwise.
    """
    # If SMTP is not configured, log the email instead
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning(
            "SMTP not configured. Email would have been sent:\n"
            f"To: {to_email}\n"
            f"Subject: {subject}\n"
            f"Body: {text_body}"
        )
        # Return True in dev mode to allow testing
        return True
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
        
        logger.info(f"Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to send email to {to_email}")
        return False


def send_verification_email(email: str, username: str, token: str) -> bool:
    """Send email verification link."""
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    
    subject = "Verify your email address"
    
    html_body = f"""
    <html>
    <body>
        <h2>Welcome to Ecommerce Search, {username}!</h2>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verify_url}" style="display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px;">Verify Email</a></p>
        <p>Or copy and paste this link into your browser:</p>
        <p>{verify_url}</p>
        <p>This link will expire in {EMAIL_VERIFICATION_EXPIRY_HOURS} hours.</p>
        <p>If you didn't create an account, you can safely ignore this email.</p>
    </body>
    </html>
    """
    
    text_body = f"""
Welcome to Ecommerce Search, {username}!

Please verify your email address by visiting this link:
{verify_url}

This link will expire in {EMAIL_VERIFICATION_EXPIRY_HOURS} hours.

If you didn't create an account, you can safely ignore this email.
    """
    
    return _send_email(email, subject, html_body, text_body)


def send_password_reset_email(email: str, username: str, token: str) -> bool:
    """Send password reset link."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    
    subject = "Reset your password"
    
    html_body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hi {username},</p>
        <p>We received a request to reset your password. Click the button below to create a new password:</p>
        <p><a href="{reset_url}" style="display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px;">Reset Password</a></p>
        <p>Or copy and paste this link into your browser:</p>
        <p>{reset_url}</p>
        <p>This link will expire in {PASSWORD_RESET_EXPIRY_HOURS} hour(s).</p>
        <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
    </body>
    </html>
    """
    
    text_body = f"""
Password Reset Request

Hi {username},

We received a request to reset your password. Visit this link to create a new password:
{reset_url}

This link will expire in {PASSWORD_RESET_EXPIRY_HOURS} hour(s).

If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
    """
    
    return _send_email(email, subject, html_body, text_body)


# ---------- USER HELPERS ----------

def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by their email address."""
    session = get_db_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if user:
            session.expunge(user)
        return user
    finally:
        session.close()


def update_user_password(user_id: str, password_hash: str) -> bool:
    """Update a user's password."""
    session = get_db_session()
    try:
        result = session.query(User).filter(
            User.user_id == user_id
        ).update({"password_hash": password_hash})
        session.commit()
        return result > 0
    except Exception as e:
        session.rollback()
        logger.exception("Failed to update user password")
        raise
    finally:
        session.close()
