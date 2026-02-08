"""
Product utility service.

Responsibilities:
- Provide cached access to product DataFrame
- Time-based cache invalidation
- Thread-safe refresh
- Delegate writes directly to DB service

NOTE:
This is an in-memory cache suitable for a single process.
Can be replaced with Redis without changing public API.
"""

import pandas as pd
import threading
import logging
from datetime import datetime, timezone

from backend.services.db_product_service import (
    get_products_df as _get_products_df,
    update_product_popularity as _update_product_popularity,
)


# ---------- CONFIG ----------

CACHE_DURATION_SECONDS = 300  # 5 minutes


# ---------- STATE ----------

class ProductCache:
    def __init__(self):
        self.df = None
        self.last_refresh = None
        self.lock = threading.Lock()


_state = ProductCache()
logger = logging.getLogger("product_cache")


# ---------- INTERNAL HELPERS ----------

def _is_cache_valid(now: datetime) -> bool:
    if _state.df is None or _state.last_refresh is None:
        return False
    return (
        now - _state.last_refresh
    ).total_seconds() <= CACHE_DURATION_SECONDS


def _load_products() -> pd.DataFrame:
    df = _get_products_df()
    if df is None:
        return pd.DataFrame()

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])

    return df


# ---------- PUBLIC API ----------

def get_products_cached() -> pd.DataFrame:
    """
    Get products DataFrame with in-memory caching.

    Uses double-checked locking:
    - Fast path for cache hits
    - Thread-safe refresh on expiry

    Returns:
        pandas.DataFrame (empty if DB error)
    """
    now = datetime.now(timezone.utc)

    # Fast path (no lock)
    if _is_cache_valid(now):
        return _state.df

    # Slow path (refresh under lock)
    with _state.lock:
        # Double-check after acquiring lock
        if not _is_cache_valid(now):
            logger.info("Refreshing product cache")
            try:
                _state.df = _load_products()
                _state.last_refresh = now
            except Exception:
                logger.exception("Failed to refresh product cache")
                _state.df = pd.DataFrame()
                _state.last_refresh = now

    return _state.df


def refresh_products_cache():
    """
    Force refresh of product cache.
    Useful after bulk updates or admin operations.
    """
    with _state.lock:
        logger.info("Force refreshing product cache")
        _state.df = _load_products()
        _state.last_refresh = datetime.now(timezone.utc)


def get_products_df() -> pd.DataFrame:
    """
    Bypass cache and load products directly from DB.
    Intended for batch jobs / ML pipelines.
    """
    return _load_products()


def update_product_popularity(product_id, points):
    """
    Update product popularity score in DB.

    NOTE:
    Cache is not updated automatically.
    Call refresh_products_cache() if consistency is required.
    """
    return _update_product_popularity(product_id, points)
