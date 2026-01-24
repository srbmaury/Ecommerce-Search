from datetime import datetime, timezone
from ml.user_profile import build_user_profiles

# Profile refresh interval - profiles update more frequently than model
PROFILE_REFRESH_SECONDS = 300  # 5 minutes

_profiles_cache = None
_profiles_last_refresh = None


def get_profiles():
    """
    Get user profiles with automatic time-based refresh.
    Profiles refresh every 5 minutes to capture recent user behavior.
    """
    global _profiles_cache, _profiles_last_refresh

    now = datetime.now(timezone.utc)

    if (
        _profiles_cache is None
        or _profiles_last_refresh is None
        or (now - _profiles_last_refresh).total_seconds() > PROFILE_REFRESH_SECONDS
    ):
        _profiles_cache = build_user_profiles()
        _profiles_last_refresh = now

    return _profiles_cache


def refresh_profiles():
    """Force refresh profiles immediately."""
    global _profiles_cache, _profiles_last_refresh
    _profiles_cache = build_user_profiles()
    _profiles_last_refresh = datetime.now(timezone.utc)
