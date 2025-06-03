"""
Middleware para la gestión de valores en el chatbot.

Este módulo proporciona middlewares para enriquecer las respuestas del chatbot
con los valores y principios fundamentales de la organización.
"""
from functools import wraps
from typing import Callable, Awaitable, Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def values_middleware(func: Callable[..., Awaitable[Dict[str, Any]]]) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """
    Middleware para enriquecer las respuestas con los valores fundamentales.
    
    Args:
        func: La función del manejador que será envuelta por el middleware.
        
    Returns:
        Una función envuelta que enriquece la respuesta con los valores.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            # Ejecutar la función original
            response = await func(*args, **kwargs)
            
            # Asegurarse de que la respuesta sea un diccionario
            if not isinstance(response, dict):
                logger.warning("La respuesta no es un diccionario, no se puede enriquecer con valores")
                return response
                
            # Aquí podríamos añadir lógica para enriquecer la respuesta
            # con los valores fundamentales si fuera necesario
            
            return response
            
        except Exception as e:
            logger.error(f"Error en el values_middleware: {str(e)}", exc_info=True)
            # En caso de error, devolver la respuesta sin modificar
            return await func(*args, **kwargs)
    
    return wrapper
