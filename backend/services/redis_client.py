import os
import json
import random
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis = redis.StrictRedis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    health_check_interval=30,
    retry_on_timeout=True,
)
_TTL_JITTER_SECONDS = 30


def redis_get_json(key):
    try:
        value = _redis.get(key)
    except Exception:
        return None

    if value is not None:
        try:
            parsed = json.loads(value)
            try:
                _redis.incr("cache:hits")
            except Exception:
                pass
            return parsed
        except Exception:
            try:
                _redis.incr("cache:misses")
            except Exception:
                pass
            return None

    # Cache miss: increment Redis-stored miss counter
    try:
        _redis.incr("cache:misses")
    except Exception:
        pass
    return None


def redis_setex_json(key, value, ttl):
    try:
        effective_ttl = max(1, int(ttl) + random.randint(0, _TTL_JITTER_SECONDS))
        _redis.setex(key, effective_ttl, json.dumps(value))
        return True
    except Exception:
        return False
