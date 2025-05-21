import asyncio
from redis.asyncio import Redis
import json
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DistributedCache:
    """
    Sistema de caché distribuido para el ATS AI.
    
    Este caché utiliza Redis para almacenar datos de manera distribuida,
    mejorando el rendimiento y la consistencia del sistema.
    """
    
    def __init__(self, max_size: int = 10000, ttl: int = 86400):
        """
        Inicializa el caché distribuido.
        
        Args:
            max_size: Tamaño máximo del caché
            ttl: Tiempo de vida de los elementos en segundos
        """
        self.max_size = max_size
        self.ttl = ttl
        self._hits = 0
        self._misses = 0
        self._redis = None
        self._lock = asyncio.Lock()
        
        # Configuración de Redis
        self.redis_config = {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'decode_responses': True
        }

    async def initialize(self) -> None:
        """
        Inicializa la conexión con Redis.
        """
        async with self._lock:
            if self._redis is None:
                try:
                    self._redis = await aioredis.create_redis_pool(
                        (self.redis_config['host'], self.redis_config['port']),
                        db=self.redis_config['db'],
                        encoding='utf-8'
                    )
                    logger.info("Conexión con Redis establecida")
                except Exception as e:
                    logger.error(f"Error conectando con Redis: {e}")
                    raise

    async def get(self, key: str) -> Optional[Dict]:
        """
        Obtiene un valor del caché distribuido.
        
        Args:
            key: Clave del valor a obtener
            
        Returns:
            Optional[Dict]: Valor almacenado o None si no existe
        """
        try:
            async with self._lock:
                value = await self._redis.get(key)
                
                if value:
                    self._hits += 1
                    return json.loads(value)
                else:
                    self._misses += 1
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo valor del caché: {e}")
            self._misses += 1
            return None

    async def set(self, key: str, value: Dict) -> None:
        """
        Almacena un valor en el caché distribuido.
        
        Args:
            key: Clave para almacenar el valor
            value: Valor a almacenar
        """
        try:
            async with self._lock:
                # Verificar tamaño del caché
                current_size = await self._redis.dbsize()
                if current_size >= self.max_size:
                    # Eliminar el menos reciente
                    oldest_key = await self._redis.scan(match='*', count=1)
                    if oldest_key:
                        await self._redis.delete(oldest_key[0])
                
                # Almacenar valor con TTL
                await self._redis.setex(
                    key,
                    self.ttl,
                    json.dumps(value)
                )
                
        except Exception as e:
            logger.error(f"Error almacenando en caché: {e}")

    async def clear(self) -> None:
        """
        Limpia el caché distribuido.
        """
        try:
            async with self._lock:
                await self._redis.flushdb()
                self._hits = 0
                self._misses = 0
                
        except Exception as e:
            logger.error(f"Error limpiando caché: {e}")

    async def size(self) -> int:
        """
        Obtiene el tamaño actual del caché.
        
        Returns:
            int: Número de elementos en el caché
        """
        try:
            async with self._lock:
                return await self._redis.dbsize()
                
        except Exception as e:
            logger.error(f"Error obteniendo tamaño del caché: {e}")
            return 0

    async def hit_rate(self) -> float:
        """
        Calcula la tasa de hits del caché.
        
        Returns:
            float: Tasa de hits (0-1)
        """
        try:
            total = self._hits + self._misses
            return self._hits / total if total > 0 else 0.0
            
        except ZeroDivisionError:
            return 0.0

    async def close(self) -> None:
        """
        Cierra la conexión con Redis.
        """
        try:
            async with self._lock:
                self._redis.close()
                await self._redis.wait_closed()
                
        except Exception as e:
            logger.error(f"Error cerrando conexión con Redis: {e}")
