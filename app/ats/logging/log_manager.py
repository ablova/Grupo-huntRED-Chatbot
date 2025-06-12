import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json
from django.conf import settings

class LogManager:
    """Gestor centralizado de logs para el ATS"""
    
    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Configura el sistema de logging"""
        # Directorio de logs
        log_dir = os.path.join(settings.BASE_DIR, 'app/ats/logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configuración base
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Configurar handlers para diferentes módulos
        self._setup_module_logger('notifications', log_dir)
        self._setup_module_logger('chatbot', log_dir)
        self._setup_module_logger('market', log_dir)
        self._setup_module_logger('learning', log_dir)
        self._setup_module_logger('pricing', log_dir)
        self._setup_module_logger('analytics', log_dir)
    
    def _setup_module_logger(self, module_name: str, log_dir: str):
        """Configura un logger específico para un módulo"""
        logger = logging.getLogger(f'ats.{module_name}')
        
        # Handler para archivo
        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, f'{module_name}.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        
        # Handler para errores
        error_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, f'{module_name}_error.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s\n'
            'Exception: %(exc_info)s\n'
            'Stack Trace: %(stack_info)s'
        ))
        
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        self.loggers[module_name] = logger
    
    def get_logger(self, module_name: str) -> logging.Logger:
        """Obtiene un logger para un módulo específico"""
        return self.loggers.get(module_name, logging.getLogger(f'ats.{module_name}'))
    
    def log_event(
        self,
        module_name: str,
        event_type: str,
        message: str,
        level: str = 'INFO',
        extra: Optional[Dict[str, Any]] = None
    ):
        """Registra un evento con información adicional"""
        logger = self.get_logger(module_name)
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'message': message,
            'extra': extra or {}
        }
        
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(json.dumps(log_data))
    
    def log_error(
        self,
        module_name: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """Registra un error con contexto"""
        logger = self.get_logger(module_name)
        logger.error(
            f"Error en {module_name}: {str(error)}",
            exc_info=True,
            extra={'context': context or {}}
        )

# Instancia global del gestor de logs
log_manager = LogManager() 