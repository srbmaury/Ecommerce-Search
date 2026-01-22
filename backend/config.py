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
        ]

    CORS(
        app,
        resources={r"/*": {"origins": origins}},
        supports_credentials=True
    )
