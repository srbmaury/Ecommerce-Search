"""
User profile service.

Responsibilities:
- Cache user profiles in memory
- Refresh profiles on a fixed interval (async to prevent blocking)
- Allow forced refresh
- Provide thread-safe access
"""

from datetime import datetime, timezone
import threading
import logging

from ml.user_profile import build_user_profiles


# ---------- CONFIG ----------

PROFILE_REFRESH_SECONDS = 300  # 5 minutes


# ---------- STATE ----------

class ProfileCache:
    def __init__(self):
        self.profiles = None
        self.last_refresh = None
        self.lock = threading.Lock()
        self.refresh_in_progress = False


_state = ProfileCache()

logger = logging.getLogger("profile_service")


# ---------- HELPERS ----------

def _is_stale(now: datetime) -> bool:
    if _state.last_refresh is None:
        return True
    return (
        now - _state.last_refresh
    ).total_seconds() > PROFILE_REFRESH_SECONDS


# ---------- PUBLIC API ----------

def get_profiles():
    """
    Get cached user profiles.

    Profiles are refreshed automatically if stale (async, non-blocking).
    Returns stale cache immediately while background refresh happens.
    Thread-safe.
    """
    now = datetime.now(timezone.utc)

    # Fast path: cache is fresh
    if _state.profiles is not None and not _is_stale(now):
        return _state.profiles

    # Return stale cache while background refresh happens
    if _state.profiles is not None:
        # Trigger async refresh in background (don't block)
        with _state.lock:
            if not _state.refresh_in_progress:
                _state.refresh_in_progress = True
                _trigger_async_refresh()
        return _state.profiles  # Return stale, not empty ✓
    
    # First load: must block to get initial data
    with _state.lock:
        if _state.profiles is None or _is_stale(now):
            logger.info("Refreshing user profiles cache (blocking initial load)")
            _state.profiles = build_user_profiles()
            _state.last_refresh = now

    return _state.profiles


def refresh_profiles():
    """
    Force immediate refresh of user profiles.
    Blocks until refresh completes.
    Thread-safe.
    """
    with _state.lock:
        logger.info("Force refreshing user profiles cache")
        _state.profiles = build_user_profiles()
        _state.last_refresh = datetime.now(timezone.utc)
        _state.refresh_in_progress = False


def _trigger_async_refresh():
    """
    Trigger background refresh without blocking.
    Multiple simultaneous refreshes are prevented by flag (set by caller under lock).
    """
    thread = threading.Thread(
        target=_background_refresh,
        daemon=True,
        name="ProfileCacheRefresh"
    )
    thread.start()


def _background_refresh():
    """
    Background thread that refreshes profiles.
    Doesn't block main requests.
    """
    try:
        logger.info("Starting background profile refresh")
        new_profiles = build_user_profiles()
        
        # Acquire lock only to swap the cache (fast operation)
        with _state.lock:
            _state.profiles = new_profiles
            _state.last_refresh = datetime.now(timezone.utc)
            _state.refresh_in_progress = False
        
        logger.info("Background profile refresh completed")
    
    except Exception as e:
        logger.exception(f"Background profile refresh failed: {e}")
        _state.refresh_in_progress = False

