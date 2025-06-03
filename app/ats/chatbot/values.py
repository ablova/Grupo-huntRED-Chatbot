"""
Módulo para manejar valores y middlewares relacionados con valores en el chatbot.
"""
from typing import Dict, Any, Callable, Awaitable
from functools import wraps


def values_middleware(func: Callable[..., Awaitable[Dict[str, Any]]]) -> Callable[..., Awaitable[Dict[str, Any]]]:
    """
    Middleware para manejar valores en el flujo del chatbot.
    
    Args:
        func: Función a decorar que maneja mensajes del chatbot.
        
    Returns:
        Función decorada que procesa los valores.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Dict[str, Any]:
        # Lógica del middleware de valores
        # Por ahora, simplemente llamamos a la función original
        return await func(*args, **kwargs)
    
    return wrapper
