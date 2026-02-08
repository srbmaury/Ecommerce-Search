"""
User profile service.

Responsibilities:
- Cache user profiles in memory
- Refresh profiles on a fixed interval
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

    Profiles are refreshed automatically if stale.
    Thread-safe.
    """
    now = datetime.now(timezone.utc)

    # Fast path: cache is fresh
    if _state.profiles is not None and not _is_stale(now):
        return _state.profiles

    # Slow path: refresh under lock
    with _state.lock:
        # Double-check after acquiring lock
        if _state.profiles is None or _is_stale(now):
            logger.info("Refreshing user profiles cache")
            _state.profiles = build_user_profiles()
            _state.last_refresh = now

    return _state.profiles


def refresh_profiles():
    """
    Force immediate refresh of user profiles.
    Thread-safe.
    """
    with _state.lock:
        logger.info("Force refreshing user profiles cache")
        _state.profiles = build_user_profiles()
        _state.last_refresh = datetime.now(timezone.utc)
