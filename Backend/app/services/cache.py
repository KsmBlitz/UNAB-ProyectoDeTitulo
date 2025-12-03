# app/services/cache.py
import json
import logging
from typing import Any, Optional
from datetime import timedelta
from functools import wraps
import hashlib

try:
    import redis.asyncio as redis  # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore

logger = logging.getLogger(__name__)

class CacheService:
    """
    Redis cache service for optimizing frequent queries.
    
    Cache strategy:
    - Dashboard metrics: TTL 30 seconds
    - ML Predictions: TTL 5 minutes
    - User permissions: TTL 15 minutes
    - Analytics data: TTL 2 minutes
    """
    
    def __init__(self):
        self.redis_client: Optional[Any] = None
        self.enabled = True
        
        # Configurable TTLs
        self.TTL_DASHBOARD = 30  # 30 seconds
        self.TTL_PREDICTIONS = 300  # 5 minutes
        self.TTL_PERMISSIONS = 900  # 15 minutes
        self.TTL_ANALYTICS = 120  # 2 minutes
        self.TTL_SENSOR_DATA = 60  # 1 minute
    
    async def connect(self, redis_url: str = "redis://localhost:6379"):
        """Connect to Redis server"""
        try:
            self.redis_client = await redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache connected successfully")
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis connection failed, cache disabled: {str(e)}")
            self.enabled = False
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate unique cache key based on parameters"""
        # Create string from all parameters
        params_str = f"{args}{sorted(kwargs.items())}"
        # Hash for unique, fixed-length keys
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
        return f"{prefix}:{params_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache GET error: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int):
        """Store value in cache with TTL"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache SET error: {str(e)}")
            return False
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error: {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.debug(f"Cache DELETE PATTERN: {pattern} ({len(keys)} keys)")
            return True
        except Exception as e:
            logger.error(f"Cache DELETE PATTERN error: {str(e)}")
            return False
    
    async def clear_all(self):
        """Clear entire cache"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            logger.info("Cache cleared (FLUSHDB)")
            return True
        except Exception as e:
            logger.error(f"Cache CLEAR error: {str(e)}")
            return False
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = await self.redis_client.info("stats")
            memory_info = await self.redis_client.info("memory")
            
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "memory_used_mb": round(memory_info.get("used_memory", 0) / (1024 * 1024), 2),
                "total_keys": await self.redis_client.dbsize()
            }
        except Exception as e:
            logger.error(f"Cache STATS error: {str(e)}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def cached(self, ttl: int, key_prefix: str):
        """
        Decorator for caching function results.
        
        Usage:
        @cache_service.cached(ttl=60, key_prefix="sensor_data")
        async def get_sensor_data(reservoir_id: str):
            # ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(key_prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # If not cached, execute function
                result = await func(*args, **kwargs)
                
                # Save to cache
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

# Global cache service instance
cache_service = CacheService()
