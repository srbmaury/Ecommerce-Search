import os
from flask_cors import CORS

def configure_cors(app):
    origins = os.getenv("ALLOWED_ORIGINS")
    if origins:
        origins = [o.strip() for o in origins.split(",")]
    else:
        origins = [
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]

    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        supports_credentials=True
    )


def get_database_url():
    """Get database URL from environment or use default SQLite."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Default to SQLite for development
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ecommerce.db")
        database_url = f"sqlite:///{db_path}"
    
    # Handle postgres:// URLs (convert to postgresql:// for SQLAlchemy)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url
