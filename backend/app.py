"""
Flask application factory.

Responsibilities:
- Load environment configuration
- Initialize database
- Configure middleware (CORS, logging)
- Register blueprints
- Expose WSGI-compatible app
"""
from backend.utils.response_time_logger import setup_response_time_logging
import os
import logging
from flask import Flask
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

from backend.utils.response_time_logger import setup_response_time_logging
from backend.utils.config import configure_cors
from backend.utils.database import init_db, create_tables

from backend.routes.auth_routes import bp as auth_bp
from backend.routes.search_routes import bp as search_bp
from backend.routes.events_routes import bp as events_bp
from backend.routes.cart_routes import bp as cart_bp
from backend.routes.analytics_routes import bp as analytics_bp
from backend.routes.recommendations_routes import bp as rec_bp


# ---------- ENV & LOGGING ----------

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("app")


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
