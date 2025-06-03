from typing import Dict, Any, Optional
import logging
from django.core.cache import cache

logger = logging.getLogger('ml')

class BaseAnalyzer:
    """
    Clase base para todos los analizadores del sistema.
    """
    
    def __init__(self):
        """Inicializa el analizador base."""
        self.cache_timeout = 3600  # 1 hora por defecto
        self.cache_prefix = "analyzer_"
        
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal de análisis que debe ser implementado por las clases hijas.
        
        Args:
            data: Diccionario con los datos a analizar
            
        Returns:
            Dict con los resultados del análisis
        """
        raise NotImplementedError("Las clases hijas deben implementar este método")
        
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un resultado de la caché.
        
        Args:
            cache_key: Clave de caché
            
        Returns:
            Dict con el resultado en caché o None si no existe
        """
        try:
            return cache.get(f"{self.cache_prefix}{cache_key}")
        except Exception as e:
            logger.error(f"Error obteniendo resultado de caché: {str(e)}")
            return None
            
    def _set_cached_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Almacena un resultado en la caché.
        
        Args:
            cache_key: Clave de caché
            result: Resultado a almacenar
        """
        try:
            cache.set(
                f"{self.cache_prefix}{cache_key}",
                result,
                timeout=self.cache_timeout
            )
        except Exception as e:
            logger.error(f"Error almacenando resultado en caché: {str(e)}")
            
    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """
        Genera una clave de caché única para los datos.
        
        Args:
            data: Datos para generar la clave
            
        Returns:
            str: Clave de caché generada
        """
        # Implementación básica que puede ser sobrescrita
        import hashlib
        import json
        
        # Convertir datos a string y generar hash
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
        
    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Valida los datos de entrada.
        
        Args:
            data: Datos a validar
            
        Returns:
            bool: True si los datos son válidos, False en caso contrario
        """
        # Implementación básica que puede ser sobrescrita
        return isinstance(data, dict) and len(data) > 0
        
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """
        Maneja errores durante el análisis.
        
        Args:
            error: Excepción ocurrida
            
        Returns:
            Dict con información del error
        """
        logger.error(f"Error en análisis: {str(error)}")
        return {
            'error': str(error),
            'status': 'error'
        } 