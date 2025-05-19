"""
Módulo de base para tareas de Celery en Grupo huntRED.
Contiene decoradores, funciones y utilidades comunes para todas las tareas.
"""

import logging
from celery import shared_task
from functools import wraps
from celery.exceptions import MaxRetriesExceededError

# Configuración de logging
logger = logging.getLogger(__name__)

# Decorador para manejo de errores y reintentos
def with_retry(task_function):
    """
    Decorador que implementa reintentos para tareas fallidas con backoff exponencial.
    
    Args:
        task_function: La función de tarea a ejecutar
        
    Returns:
        wrapper: Función envuelta con lógica de reintento
    """
    @wraps(task_function)
    def wrapper(self, *args, **kwargs):
        try:
            return task_function(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en {task_function.__name__}: {str(e)}")
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=2 ** self.request.retries * 60)
            else:
                raise
    return wrapper

# Tarea básica para pruebas
@shared_task
def add(x, y):
    """
    Simple tarea de suma para probar que Celery funciona correctamente.
    
    Args:
        x: Primer número
        y: Segundo número
        
    Returns:
        int: La suma de x + y
    """
    return x + y
