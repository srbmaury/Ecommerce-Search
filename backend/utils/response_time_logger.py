"""
API response time logging middleware.

Responsibilities:
- Measure request latency
- Log method, path, status, and duration
- Use rotating log files
- Avoid polluting request namespace
"""

import time
import logging
import os
from logging.handlers import RotatingFileHandler
from flask import request, g
# ---------- CONFIG ----------

DEFAULT_LOG_FILE = "api_response_times.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 2

LOGGER_NAME = "api_response_time"

# ---------- SETUP ----------

def setup_response_time_logging(app, log_file: str = DEFAULT_LOG_FILE):
    """
    Attach request timing middleware to Flask app.
    """
    logger = _get_logger(log_file)

    @app.before_request
    def _start_timer():
        # Use flask.g instead of mutating request object
        g._request_start_time = time.perf_counter()

    @app.after_request
    def _log_response_time(response):
        start = getattr(g, "_request_start_time", None)
        api_logging_enabled = os.getenv("API_LOGGING_ENABLED", "False").lower() in ("1", "true", "yes")
        if start is not None and api_logging_enabled:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s %s %.2fms",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
            )
        return response


def _get_logger(log_file: str) -> logging.Logger:
    """
    Get or create the response-time logger.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
    )
    formatter = logging.Formatter(
        "%(asctime)s %(message)s"
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    logger.addHandler(handler)
    logger.propagate = False  # Prevent double logging

    return logger
