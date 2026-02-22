"""
Cache invalidation service.

Responsibilities:
- Provide unified cache invalidation API
- Track cache usage and hit rates
- Support event-triggered invalidation
- Graceful handling of Redis failures
"""

import logging
from typing import List, Optional
from backend.services.redis_client import _redis
from backend.services.cache_keys import query_hash

logger = logging.getLogger("cache_invalidation")

# Redis-backed counter keys
_HITS_KEY = "cache:hits"
_MISSES_KEY = "cache:misses"
_INVALIDATIONS_KEY = "cache:invalidations"


def _delete_by_pattern(pattern: str) -> int:
    deleted_total = 0
    try:
        for key in _redis.scan_iter(match=pattern, count=500):
            try:
                deleted_total += int(_redis.delete(key) or 0)
            except Exception:
                continue
        return deleted_total
    except Exception as e:
        logger.error(f"Failed pattern delete for {pattern}: {e}")
        return 0


# ---------- CORE INVALIDATION ----------

def invalidate_user_recommendations(user_id: str) -> bool:
    """Invalidate recommendation cache for specific user."""
    key = f"recommendations:{user_id}"
    return _delete_cache_key(key)


def invalidate_user_search_caches(user_id: str) -> bool:
    """Invalidate all search caches for specific user."""
    # Note: Search cache is now query-level only
    # This is a placeholder for potential future user-specific caching
    return True


def invalidate_cluster_boost(cluster_id: Optional[int]) -> bool:
    """Invalidate cluster category boost cache."""
    if cluster_id is None:
        return False
    key = f"cluster_boost:{cluster_id}"
    return _delete_cache_key(key)


def invalidate_product_search_cache(query: str) -> bool:
    """Invalidate search results for specific query."""
    try:
        key_hash = query_hash(query)
        deleted = 0
        deleted += _delete_by_pattern(f"search_products:{key_hash}:*")
        deleted += _delete_by_pattern(f"search_ranked:{key_hash}:*")
        if deleted:
            try:
                _redis.incrby(_INVALIDATIONS_KEY, deleted)
            except Exception:
                pass
        return deleted > 0
    except Exception as e:
        logger.error(f"Failed to invalidate search cache for query '{query}': {e}")
        return False


def invalidate_all_search_caches() -> int:
    """
    Invalidate ALL search caches.
    Use sparingly - expensive operation.
    
    Returns: Number of keys deleted
    """
    try:
        deleted = 0
        deleted += _delete_by_pattern("search_products:*")
        deleted += _delete_by_pattern("search_ranked:*")
        if deleted:
            try:
                _redis.incrby(_INVALIDATIONS_KEY, deleted)
            except Exception:
                pass
        logger.info(f"Invalidated {deleted} search cache keys")
        return deleted
    except Exception as e:
        logger.error(f"Failed to invalidate all search caches: {e}")
        return 0


def invalidate_all_recommendation_caches() -> int:
    """
    Invalidate ALL recommendation caches.
    Use when user preferences change globally.
    
    Returns: Number of keys deleted
    """
    try:
        pattern = "recommendations:*"
        deleted = _delete_by_pattern(pattern)
        if deleted:
            try:
                _redis.incrby(_INVALIDATIONS_KEY, deleted)
            except Exception:
                pass
        logger.info(f"Invalidated {deleted} recommendation cache keys")
        return deleted
    except Exception as e:
        logger.error(f"Failed to invalidate all recommendation caches: {e}")
        return 0


def invalidate_on_product_update(product_id: int) -> bool:
    """
    Invalidate caches when a product is updated.
    
    Clears:
    - All search caches (product could be in many results)
    - All recommendation caches (product could be recommended)
    """
    results = []
    
    # Invalidate all search caches (conservative approach)
    # In production, could implement query-product index to target specific queries
    results.append(invalidate_all_search_caches() > 0)
    results.append(invalidate_all_recommendation_caches() > 0)
    
    logger.info(f"Invalidated caches for product {product_id} update")
    return any(results)


def invalidate_on_user_event(user_id: str, event_type: str, cluster_id: Optional[int] = None) -> bool:
    """
    Invalidate caches when user event occurs.
    
    Events that trigger invalidation:
    - add_to_cart: User preferences might change
    - purchase: User preferences definitely changed
    - click: User interest signal (could update cluster)
    """
    results = []
    
    if event_type in ["add_to_cart", "purchase", "click"]:
        # Always invalidate user's recommendations
        results.append(invalidate_user_recommendations(user_id))
        
        # Invalidate cluster boost if user is in a cluster
        if cluster_id is not None:
            results.append(invalidate_cluster_boost(cluster_id))
        
        logger.info(f"Invalidated caches for user {user_id} event: {event_type}")
    
    return any(results)


# ---------- INTERNAL HELPERS ----------

def _delete_cache_key(key: str) -> bool:
    """Delete single cache key from Redis."""
    try:
        deleted = _redis.delete(key)
        if deleted:
            try:
                _redis.incr(_INVALIDATIONS_KEY)
            except Exception:
                pass
            logger.debug(f"Invalidated cache key: {key}")
        return deleted > 0
    except Exception as e:
        logger.error(f"Failed to delete cache key {key}: {e}")
        return False


# ---------- STATISTICS ----------

def get_cache_stats():
    """Get cache invalidation statistics."""
    try:
        hits = int(_redis.get(_HITS_KEY) or 0)
        misses = int(_redis.get(_MISSES_KEY) or 0)
        invalidations = int(_redis.get(_INVALIDATIONS_KEY) or 0)
    except Exception:
        # Fallback to zeros on Redis failure
        hits = misses = invalidations = 0

    total = hits + misses
    hit_rate = (hits / total) if total > 0 else 0.0
    return {
        "hits": hits,
        "misses": misses,
        "invalidations": invalidations,
        "hit_rate": hit_rate,
    }


# Note: cache counters are incremented directly in Redis by `redis_client`.


def get_cache_hit_rate() -> float:
    """Calculate cache hit rate (0.0-1.0)."""
    stats = get_cache_stats()
    return stats["hit_rate"]


def reset_cache_stats():
    """Reset statistics counters."""
    try:
        _redis.set(_HITS_KEY, 0)
        _redis.set(_MISSES_KEY, 0)
        _redis.set(_INVALIDATIONS_KEY, 0)
    except Exception:
        pass
