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
    Servicio de caché con Redis para optimizar consultas frecuentes.
    
    Estrategia de caché:
    - Dashboard metrics: TTL 30 segundos
    - ML Predictions: TTL 5 minutos
    - User permissions: TTL 15 minutos
    - Analytics data: TTL 2 minutos
    """
    
    def __init__(self):
        self.redis_client: Optional[Any] = None
        self.enabled = True
        
        # TTLs configurables
        self.TTL_DASHBOARD = 30  # 30 segundos
        self.TTL_PREDICTIONS = 300  # 5 minutos
        self.TTL_PERMISSIONS = 900  # 15 minutos
        self.TTL_ANALYTICS = 120  # 2 minutos
        self.TTL_SENSOR_DATA = 60  # 1 minuto
    
    async def connect(self, redis_url: str = "redis://localhost:6379"):
        """Conecta al servidor Redis"""
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
        """Cierra la conexión con Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Genera una clave de caché única basada en los parámetros"""
        # Crear un string con todos los parámetros
        params_str = f"{args}{sorted(kwargs.items())}"
        # Hash para claves únicas y de longitud fija
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
        return f"{prefix}:{params_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché"""
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
        """Almacena un valor en el caché con TTL"""
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
        """Elimina una clave del caché"""
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
        """Elimina todas las claves que coinciden con un patrón"""
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
        """Limpia todo el caché"""
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
        """Obtiene estadísticas del caché"""
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
        """Calcula la tasa de aciertos del caché"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def cached(self, ttl: int, key_prefix: str):
        """
        Decorador para cachear resultados de funciones.
        
        Uso:
        @cache_service.cached(ttl=60, key_prefix="sensor_data")
        async def get_sensor_data(reservoir_id: str):
            # ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generar clave de caché
                cache_key = self._generate_cache_key(key_prefix, *args, **kwargs)
                
                # Intentar obtener del caché
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Si no está en caché, ejecutar función
                result = await func(*args, **kwargs)
                
                # Guardar en caché
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

# Instancia global del servicio de caché
cache_service = CacheService()
