import os
import json
import random
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis = redis.StrictRedis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
    socket_connect_timeout=1,
    socket_timeout=1,
    health_check_interval=30,
    retry_on_timeout=True,
)
_TTL_JITTER_SECONDS = 30


def redis_get_json(key, *, count_stats=True):
    """
    Fetch and JSON-decode a Redis key.

    count_stats=True  → record hit/miss in cache:hits / cache:misses.
    count_stats=False → internal/sub-caches that shouldn't skew dashboard stats.
    """
    def _incr(counter):
        if not count_stats:
            return
        try:
            _redis.incr(counter)
        except Exception:
            pass

    try:
        value = _redis.get(key)
    except Exception:
        # Redis error: caller gets None, same outcome as a miss
        _incr("cache:misses")
        return None

    if value is None:
        _incr("cache:misses")
        return None

    try:
        parsed = json.loads(value)
        _incr("cache:hits")
        return parsed
    except Exception:
        # Corrupt cached value — treat as miss so caller re-fetches
        _incr("cache:misses")
        return None


def redis_setex_json(key, value, ttl):
    try:
        effective_ttl = max(1, int(ttl) + random.randint(0, _TTL_JITTER_SECONDS))
        _redis.setex(key, effective_ttl, json.dumps(value))
        return True
    except Exception:
        return False
