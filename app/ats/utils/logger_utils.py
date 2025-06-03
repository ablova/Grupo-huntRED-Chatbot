import logging
import json
import traceback
import sys
import os
from datetime import datetime
from functools import wraps

import os
from pathlib import Path

# Configuración de la ruta de logs
try:
    # En producción, usar /home/pablo/logs
    if os.path.exists('/home/pablo'):
        LOG_DIR = '/home/pablo/logs'
    else:
        # En desarrollo, usar un directorio dentro del proyecto
        PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
        LOG_DIR = PROJECT_ROOT / 'logs'
    
    # Asegurarse de que el directorio existe
    os.makedirs(LOG_DIR, exist_ok=True)
    LOG_DIR = str(LOG_DIR)
except Exception as e:
    # Si hay algún error, usar un directorio temporal
    import tempfile
    LOG_DIR = tempfile.mkdtemp(prefix='huntred_logs_')

# Formato personalizado para logs
class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage()
        }
        
        # Añadir información de excepción si está disponible
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        # Añadir cualquier información extra proporcionada
        if hasattr(record, 'data') and record.data:
            log_record["data"] = record.data
            
        return json.dumps(log_record)

# Configuración de loggers por módulo
def get_module_logger(module_name, log_level=logging.INFO):
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)
    
    # Evitar duplicación de handlers
    if not logger.handlers:
        # Handler para archivo (uno por módulo)
        file_handler = logging.FileHandler(f"{LOG_DIR}/{module_name}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler.setFormatter(CustomFormatter())
        
        # Handler para consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Decorador para registrar entrada/salida de funciones
def log_function_call(logger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Llamada a {func.__name__} con args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Salida de {func.__name__}: éxito")
                return result
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {str(e)}", exc_info=True,
                            extra={"data": {"args": str(args), "kwargs": str(kwargs)}})
                raise
        return wrapper
    return decorator

# Decorador para funciones asíncronas
def log_async_function_call(logger):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.debug(f"Llamada asíncrona a {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Salida de {func.__name__}: éxito")
                return result
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {str(e)}", exc_info=True,
                            extra={"data": {"args": str(args), "kwargs": str(kwargs)}})
                raise
        return wrapper
    return decorator

# Monitoreo de recursos
class ResourceMonitor:
    @staticmethod
    def log_memory_usage(logger, label=""):
        """Registra el uso de memoria actual"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        logger.info(f"Uso de memoria {label}: {mem_info.rss / (1024 * 1024):.2f} MB", 
                   extra={"data": {"memory_rss_mb": mem_info.rss / (1024 * 1024)}})
    
    @staticmethod
    def log_cpu_usage(logger, label=""):
        """Registra el uso de CPU actual"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        cpu_percent = process.cpu_percent(interval=0.1)
        
        logger.info(f"Uso de CPU {label}: {cpu_percent:.2f}%", 
                   extra={"data": {"cpu_percent": cpu_percent}})
