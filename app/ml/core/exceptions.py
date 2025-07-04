"""
🔥 Excepciones Personalizadas para Sistema ML - huntRED®

Manejo de errores específico y contextual para todo el sistema de ML.
"""

from typing import Optional, Dict, Any


class MLBaseException(Exception):
    """Excepción base para todo el sistema ML"""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.error_code = error_code or self.__class__.__name__
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context
        }


class ConfigurationError(MLBaseException):
    """Error en configuración del sistema"""
    pass


class ModelNotFoundError(MLBaseException):
    """Modelo ML no encontrado"""
    pass


class InvalidInputError(MLBaseException):
    """Datos de entrada inválidos"""
    pass


class AnalysisError(MLBaseException):
    """Error durante análisis ML"""
    pass


class DependencyError(MLBaseException):
    """Error de dependencia externa"""
    pass


class CacheError(MLBaseException):
    """Error de cache"""
    pass


class ValidationError(MLBaseException):
    """Error de validación"""
    pass


class PerformanceError(MLBaseException):
    """Error de performance (timeout, etc.)"""
    pass


def handle_ml_exception(func):
    """Decorator para manejo consistente de excepciones ML"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MLBaseException:
            raise  # Re-raise ML exceptions as-is
        except Exception as e:
            # Convert generic exceptions to ML exceptions
            raise AnalysisError(
                message=f"Error inesperado en {func.__name__}: {str(e)}",
                context={'function': func.__name__, 'args': str(args)[:100]}
            ) from e
    return wrapper