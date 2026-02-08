"""
Application configuration utilities.

Responsibilities:
- Configure CORS safely
- Resolve database URL with sane defaults
- Normalize database URLs for SQLAlchemy compatibility
"""

import os
import logging
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from flask_cors import CORS


# ---------- LOGGING ----------

logger = logging.getLogger("app_config")


# ---------- CORS ----------

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def configure_cors(app):
    """
    Configure CORS for the Flask app.

    Reads ALLOWED_ORIGINS from environment (comma-separated).
    Falls back to sensible local-dev defaults.
    """
    origins_env = os.getenv("ALLOWED_ORIGINS")

    if origins_env:
        origins = [o.strip() for o in origins_env.split(",") if o.strip()]
        logger.info("CORS enabled for configured origins: %s", origins)
    else:
        origins = DEFAULT_CORS_ORIGINS
        logger.info("CORS enabled for default dev origins")

    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        supports_credentials=True,
    )


# ---------- DATABASE URL ----------

def get_database_url():
    """
    Resolve database URL.

    Priority:
    1. DATABASE_URL environment variable
    2. Local SQLite database (development)

    Also normalizes postgres:// URLs to postgresql://
    for SQLAlchemy compatibility.
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        db_path = (
            Path(__file__)
            .resolve()
            .parent.parent
            / "data"
            / "ecommerce.db"
        )
        database_url = f"sqlite:///{db_path}"
        logger.info("Using local SQLite database: %s", db_path)

    database_url = _normalize_database_url(database_url)
    return database_url


def _normalize_database_url(database_url: str) -> str:
    """
    Normalize database URLs for SQLAlchemy.

    Converts:
        postgres:// -> postgresql://
    while preserving all URL components.
    """
    if database_url.startswith("postgres://"):
        logger.info(
            "Normalizing postgres:// URL to postgresql:// for SQLAlchemy"
        )
        parsed = urlparse(database_url)
        return urlunparse((
            "postgresql",
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ))

    return database_url
