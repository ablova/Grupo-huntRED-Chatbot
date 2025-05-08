"""
Implementación de LRUCache para optimizar el rendimiento del sistema.
"""

from collections import OrderedDict
from typing import Any, Dict, Optional

class LRUCache:
    def __init__(self, max_size: int = 1000):
        """
        Inicializa el cache LRU.
        
        Args:
            max_size: Tamaño máximo del cache
        """
        self.max_size = max_size
        self.cache = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Dict]:
        """
        Obtiene un valor del cache.
        
        Args:
            key: Clave del valor a obtener
            
        Returns:
            Optional[Dict]: Valor almacenado o None si no existe
        """
        try:
            value = self.cache.pop(key)
            self.cache[key] = value  # Mover a la posición más reciente
            self._hits += 1
            return value
            
        except KeyError:
            self._misses += 1
            return None

    def set(self, key: str, value: Dict) -> None:
        """
        Almacena un valor en el cache.
        
        Args:
            key: Clave para almacenar el valor
            value: Valor a almacenar
        """
        try:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)  # Eliminar el menos reciente
            
            self.cache[key] = value
            
        except Exception as e:
            print(f"Error almacenando en cache: {e}")

    def clear(self) -> None:
        """Limpia el cache."""
        self.cache.clear()
        self._hits = 0
        self._misses = 0

    def size(self) -> int:
        """Obtiene el tamaño actual del cache."""
        return len(self.cache)

    def hit_rate(self) -> float:
        """Calcula la tasa de hits del cache."""
        try:
            total = self._hits + self._misses
            return self._hits / total if total > 0 else 0.0
            
        except ZeroDivisionError:
            return 0.0
