"""
Flask application factory.

Responsibilities:
- Load environment configuration
- Initialize database
- Configure middleware (CORS, logging)
- Register blueprints
- Expose WSGI-compatible app
"""
import os
import logging
import threading
from dotenv import load_dotenv

# Load .env before any other backend imports so module-level os.getenv() calls
# in services (e.g. email_service, database) see the correct values.
load_dotenv()

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from backend.utils.response_time_logger import setup_response_time_logging
from backend.utils.config import configure_cors
from backend.utils.database import init_db, create_tables
from backend.utils.rate_limit import limiter

from backend.routes.auth_routes import bp as auth_bp
from backend.routes.search_routes import bp as search_bp
from backend.routes.events_routes import bp as events_bp
from backend.routes.cart_routes import bp as cart_bp
from backend.routes.analytics_routes import bp as analytics_bp
from backend.routes.recommendations_routes import bp as rec_bp
from backend.routes.cache_routes import bp as cache_bp
from backend.routes.reviews_routes import bp as reviews_bp
from backend.routes.products_admin_routes import bp as products_admin_bp


# ---------- LOGGING ----------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("app")


# ---------- ENV VAR VALIDATION ----------

_REQUIRED_ENV_VARS = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY"]
_OPTIONAL_ENV_VARS = {
    "ADMIN_USER_IDS": "admin features disabled",
    "SMTP_HOST":      "email sending disabled",
    "SMTP_PORT":      "email sending disabled",
    "SMTP_USER":      "email sending disabled",
    "SMTP_PASSWORD":  "email sending disabled",
}


def _validate_env():
    missing = [v for v in _REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        raise EnvironmentError(
            f"Required environment variables not set: {', '.join(missing)}. "
            "Check your .env file."
        )
    for var, impact in _OPTIONAL_ENV_VARS.items():
        if not os.getenv(var):
            logger.warning("Optional env var %s not set — %s", var, impact)


_validate_env()


# ---------- APP FACTORY ----------

def create_app() -> Flask:
    """
    Create and configure Flask application.
    """
    app = Flask(
        __name__,
        static_folder="../frontend",
        static_url_path="/static",
    )

    _init_database()
    _configure_app(app)
    _register_routes(app)
    _warmup_ml_state()

    return app


# ---------- INITIALIZATION HELPERS ----------

def _init_database():
    """
    Initialize database engine and schema.
    """
    try:
        logger.info("Initializing database connection")
        init_db()

        logger.info("Creating database tables (if not exist)")
        create_tables()

        logger.info("Database ready")

    except SQLAlchemyError:
        logger.exception("Database initialization failed")
        raise
    except Exception:
        logger.exception("Unexpected error during database initialization")
        raise

def _configure_app(app: Flask):
    """
    Configure middleware and app-level settings.
    """
    # Response-time logging
    setup_response_time_logging(
        app,
        log_file="api_response_times.log",
    )

    # CORS
    configure_cors(app)

    # Rate limiting (backed by Redis so limits hold across worker processes)
    app.config["RATELIMIT_STORAGE_URI"] = os.getenv("REDIS_URL")
    limiter.init_app(app)

    # Root route for frontend
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

def _register_routes(app: Flask):
    """
    Register all API blueprints.
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(rec_bp)
    app.register_blueprint(cache_bp)  # NEW: Cache management endpoints
    app.register_blueprint(reviews_bp)
    app.register_blueprint(products_admin_bp)


def _warmup_ml_state():
    """
    Load the ranking model and build the user-profile cache in a background
    thread at startup, instead of on the first incoming request. Previously
    the first search after a fresh boot paid this cost inline (10-18s in
    testing) with only a bare spinner shown to the user.
    """
    def _run():
        try:
            from ml.model import get_model
            from backend.services.user_profile_service import get_profiles
            logger.info("Warming up ranking model and user profile cache")
            get_model()
            get_profiles()
            logger.info("Warmup complete")
        except Exception:
            logger.exception("Warmup failed (non-fatal — will load lazily on first request)")

    threading.Thread(target=_run, daemon=True, name="MLWarmup").start()


# ---------- WSGI ENTRYPOINT ----------

app = create_app()


# ---------- DEV SERVER ----------

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=debug_mode,
    )
