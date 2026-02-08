import os
import json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_redis = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)

def redis_get_json(key):
    value = _redis.get(key)
    if value is not None:
        try:
            return json.loads(value)
        except Exception:
            return None
    return None

def redis_setex_json(key, value, ttl):
    try:
        _redis.setex(key, ttl, json.dumps(value))
        return True
    except Exception:
        return False
