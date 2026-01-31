"""
Utility functions for services - use database instead.
"""
import pandas as pd
import threading
from datetime import datetime, timezone
from backend.services.db_product_service import get_products_df as _get_products_df, update_product_popularity as _update_product_popularity


# Global cache for products with thread-safe access
_products_cache = None
_products_cache_time = None
_products_cache_lock = threading.Lock()
CACHE_DURATION_SECONDS = 300  # 5 minutes


def get_products_cached():
    """
    Thread-safe lazy load products from database with time-based cache invalidation.
    
    Uses double-checked locking pattern to avoid race conditions while maintaining performance:
    1. Quick check without lock (fast path for cache hits)
    2. Acquire lock only when reload is needed
    3. Double-check after acquiring lock (another thread may have reloaded)
    
    Returns:
        DataFrame: Products data from database, or None if error occurs
    """
    global _products_cache, _products_cache_time
    
    # Quick check without lock (fast path)
    current_time = datetime.now(timezone.utc)
    if (_products_cache is not None and 
        not getattr(_products_cache, "empty", False) and
        _products_cache_time is not None and
        (current_time - _products_cache_time).total_seconds() <= CACHE_DURATION_SECONDS):
        return _products_cache
    
    # Reload with lock (slow path)
    with _products_cache_lock:
        # Double-check after acquiring lock
        current_time = datetime.now(timezone.utc)
        needs_reload = (
            _products_cache is None or 
            getattr(_products_cache, "empty", False) or
            _products_cache_time is None or
            (current_time - _products_cache_time).total_seconds() > CACHE_DURATION_SECONDS
        )
        
        if needs_reload:
            _products_cache = _get_products_df()
            _products_cache_time = current_time
            if _products_cache is not None and not _products_cache.empty and "created_at" in _products_cache.columns:
                _products_cache["created_at"] = pd.to_datetime(_products_cache["created_at"])
    
    return _products_cache


def get_products_df():
    """Load products DataFrame from database, returns empty DataFrame on error."""
    return _get_products_df()


def update_product_popularity(product_id, points):
    """Update product popularity score by given points in database."""
    return _update_product_popularity(product_id, points)
