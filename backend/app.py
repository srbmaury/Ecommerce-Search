import os
import logging
from flask import Flask
from dotenv import load_dotenv

from backend.config import configure_cors
from backend.scheduler import start_scheduler

from backend.routes.auth import bp as auth_bp
from backend.routes.search import bp as search_bp
from backend.routes.events import bp as events_bp
from backend.routes.cart import bp as cart_bp
from backend.routes.analytics import bp as analytics_bp
from backend.routes.recommendations import bp as rec_bp

load_dotenv()
logging.basicConfig(level=logging.INFO)

def create_app():

    # Serve static files from the frontend directory
    app = Flask(__name__, static_folder="../frontend", static_url_path="/static")
    # Route for root URL to serve index.html
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    configure_cors(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(rec_bp)

    # Only start the scheduler if RUN_SCHEDULER is not set to '0' or 'false'
    run_scheduler = os.getenv("RUN_SCHEDULER", "1").lower() in ("1", "true", "yes")
    if run_scheduler:
        start_scheduler()
    return app


# Expose 'app' at module level for WSGI servers (e.g., PythonAnywhere)
app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.getenv("FLASK_DEBUG", "0") in ("1", "true")
    )
