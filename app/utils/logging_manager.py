"""
Sistema de registro centralizado para Grupo huntRED®.
Este módulo implementa configuraciones y herramientas para registro uniforme
en todos los componentes, siguiendo las reglas globales del sistema.
"""

import logging
import json
import functools
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from asgiref.sync import sync_to_async

# Configuración de formatters avanzados
class BusinessUnitContextFilter(logging.Filter):
    """Filtro para añadir contexto de BU a los logs."""
    
    def filter(self, record):
        """Añade contexto de BU al registro."""
        # Si ya existe un BusinessUnit, no modificar
        if hasattr(record, 'bu_name'):
            return True
            
        # Contexto predeterminado
        record.bu_name = 'global'
        record.bu_id = None
        
        # Obtener contexto de datos adicionales
        if hasattr(record, 'extras') and isinstance(record.extras, dict):
            record.bu_name = record.extras.get('bu_name', 'global')
            record.bu_id = record.extras.get('bu_id')
            
        return True


class ModuleContextFilter(logging.Filter):
    """Filtro para añadir contexto de módulo a los logs."""
    
    def filter(self, record):
        """Añade información de módulo al registro."""
        module_path = record.pathname
        
        # Extraer nombre de módulo
        module_name = 'unknown'
        
        try:
            # Obtener primer directorio después de app/
            if 'app/' in module_path:
                path_parts = module_path.split('app/')[1].split('/')
                if len(path_parts) > 0:
                    module_name = path_parts[0]
        except Exception:
            pass
            
        record.module_name = module_name
        return True


# Clase principal para gestión de logs
class LoggingManager:
    """
    Clase centralizada para gestión de logs en todo el sistema.
    Proporciona métodos para registro uniforme con contexto relevante.
    """
    
    # Niveles de log
    LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # Módulos principales para categorización
    MODULES = [
        'chatbot', 'ml', 'payments', 'publish', 'utils', 
        'views', 'tasks', 'signals', 'sexsi', 'utilidades'
    ]
    
    @classmethod
    def setup_logging(cls):
        """
        Configura el sistema de logging central.
        Se llama una vez durante la inicialización de la aplicación.
        """
        # Configurar filtros personalizados
        bu_filter = BusinessUnitContextFilter()
        module_filter = ModuleContextFilter()
        
        # Obtener loggers principales
        root_logger = logging.getLogger()
        app_logger = logging.getLogger('app')
        
        # Añadir filtros a los loggers principales
        root_logger.addFilter(bu_filter)
        root_logger.addFilter(module_filter)
        app_logger.addFilter(bu_filter)
        app_logger.addFilter(module_filter)
        
        # Configurar formato detallado para entornos de desarrollo
        if settings.DEBUG:
            # Formato detallado para desarrollo
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(module_name)s] [BU:%(bu_name)s] '
                '[%(pathname)s:%(lineno)d] - %(message)s'
            )
            
            # Asegurar handler de consola con el formatter
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            
            # Verificar si ya existe un handler similar
            replace_handler = True
            for handler in root_logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setFormatter(formatter)
                    replace_handler = False
                    
            if replace_handler:
                root_logger.addHandler(console_handler)
        
        # Configurar loggers específicos para los módulos principales
        for module in cls.MODULES:
            module_logger = logging.getLogger(f'app.{module}')
            module_logger.addFilter(bu_filter)
            module_logger.addFilter(module_filter)
            
        return True
    
    @classmethod
    def get_logger(cls, module_name):
        """
        Obtiene un logger para un módulo específico.
        
        Args:
            module_name: Nombre del módulo
            
        Returns:
            logging.Logger: Logger configurado
        """
        # Normalizar nombre del módulo
        if not module_name.startswith('app.'):
            module_name = f'app.{module_name}'
            
        return logging.getLogger(module_name)
    
    @classmethod
    def log(cls, level, message, module=None, extras=None, exc_info=None, bu_id=None, user=None):
        """
        Registra un mensaje con contexto enriquecido.
        
        Args:
            level: Nivel de log (debug, info, warning, error, critical)
            message: Mensaje a registrar
            module: Módulo específico (opcional)
            extras: Datos adicionales para el registro
            exc_info: Información de excepción
            bu_id: ID de Business Unit
            user: Usuario relacionado con la acción
            
        Returns:
            bool: True si se registró correctamente
        """
        # Normalizar nivel
        level = level.lower()
        if level not in cls.LEVELS:
            level = 'info'
            
        # Preparar contexto enriquecido
        extra_context = extras or {}
        
        # Añadir contexto de BU
        if bu_id:
            extra_context['bu_id'] = bu_id
            
            # Intentar obtener nombre de BU si está disponible
            try:
                from django.apps import apps
                BusinessUnit = apps.get_model('app', 'BusinessUnit')
                bu = BusinessUnit.objects.filter(id=bu_id).first()
                if bu:
                    extra_context['bu_name'] = bu.name
            except Exception:
                pass
        
        # Añadir contexto de usuario
        if user:
            if isinstance(user, User):
                extra_context['user_id'] = user.id
                extra_context['username'] = user.username
            elif isinstance(user, dict):
                extra_context['user_id'] = user.get('id')
                extra_context['username'] = user.get('username')
            elif isinstance(user, int):
                extra_context['user_id'] = user
        
        # Obtener logger apropiado
        logger = cls.get_logger(module or 'app')
        
        # Convertir extras a formato JSON si contiene objetos complejos
        if extras:
            for key, value in list(extra_context.items()):
                if isinstance(value, (models.Model, object)) and not isinstance(value, (str, int, float, bool, dict, list)):
                    try:
                        if hasattr(value, 'to_dict'):
                            extra_context[key] = value.to_dict()
                        elif hasattr(value, '__dict__'):
                            extra_context[key] = str(value)
                        else:
                            extra_context[key] = str(value)
                    except Exception:
                        extra_context[key] = str(value)
        
        # Registrar con nivel apropiado
        log_method = getattr(logger, level)
        
        # Añadir extra_context como 'extras' para filtros
        log_method(
            message,
            exc_info=exc_info,
            extra={'extras': extra_context}
        )
        
        # Persistir logs críticos en base de datos para auditoría
        if level in ['error', 'critical']:
            try:
                from app.models import SystemLog
                
                # Serializar extras
                json_extras = json.dumps(extra_context, default=str)
                
                # Crear registro asíncrono
                @sync_to_async
                def create_system_log():
                    SystemLog.objects.create(
                        level=level.upper(),
                        message=message,
                        module=module or 'app',
                        data=json_extras,
                        user_id=extra_context.get('user_id'),
                        bu_id=extra_context.get('bu_id')
                    )
                
                # Ejecutar creación asíncrona
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(create_system_log())
                    else:
                        asyncio.run(create_system_log())
                except RuntimeError:
                    # Fallback a síncrono si no hay event loop
                    SystemLog.objects.create(
                        level=level.upper(),
                        message=message,
                        module=module or 'app',
                        data=json_extras,
                        user_id=extra_context.get('user_id'),
                        bu_id=extra_context.get('bu_id')
                    )
            except Exception as e:
                # No debería fallar el flujo principal por problemas al persistir logs
                logger.warning(f"Error persisting log to database: {str(e)}")
        
        return True


# Decoradores para integración en todo el sistema

def log_function_call(module=None, level='info'):
    """
    Decorador para registrar llamadas a funciones con parámetros y resultado.
    
    Args:
        module: Módulo para categorización de logs
        level: Nivel de log para la entrada
        
    Returns:
        Decorador configurado
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Preparar información inicial
            func_module = module or func.__module__
            func_name = func.__name__
            
            # Extraer usuario y BU de argumentos cuando sea posible
            user = None
            bu_id = None
            
            # Buscar request en los argumentos
            request = None
            for arg in args:
                if hasattr(arg, 'user') and hasattr(arg, 'method'):
                    request = arg
                    break
            
            if request and hasattr(request, 'user'):
                user = request.user
                
            if request and hasattr(request, 'active_bu_id'):
                bu_id = request.active_bu_id
            
            # Registrar inicio de función
            LoggingManager.log(
                level=level,
                message=f"Function call: {func_name}",
                module=func_module,
                extras={
                    'function': func_name,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs),
                    'kwargs_keys': list(kwargs.keys())
                },
                user=user,
                bu_id=bu_id
            )
            
            try:
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Registrar finalización exitosa
                duration = time.time() - start_time
                
                LoggingManager.log(
                    level=level,
                    message=f"Function completed: {func_name} in {duration:.3f}s",
                    module=func_module,
                    extras={
                        'function': func_name,
                        'duration': duration,
                        'success': True
                    },
                    user=user,
                    bu_id=bu_id
                )
                
                return result
            except Exception as e:
                # Registrar error
                duration = time.time() - start_time
                
                LoggingManager.log(
                    level='error',
                    message=f"Function error: {func_name} - {str(e)}",
                    module=func_module,
                    extras={
                        'function': func_name,
                        'duration': duration,
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True,
                    user=user,
                    bu_id=bu_id
                )
                
                # Re-lanzar excepción
                raise
                
        return wrapper
        
    return decorator


def log_async_function_call(module=None, level='info'):
    """
    Decorador para registrar llamadas a funciones asíncronas.
    
    Args:
        module: Módulo para categorización de logs
        level: Nivel de log para la entrada
        
    Returns:
        Decorador configurado
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Preparar información inicial
            func_module = module or func.__module__
            func_name = func.__name__
            
            # Extraer usuario y BU de argumentos cuando sea posible
            user = None
            bu_id = None
            
            # Buscar request en los argumentos
            request = None
            for arg in args:
                if hasattr(arg, 'user') and hasattr(arg, 'method'):
                    request = arg
                    break
            
            if request and hasattr(request, 'user'):
                user = request.user
                
            if request and hasattr(request, 'active_bu_id'):
                bu_id = request.active_bu_id
            
            # Registrar inicio de función
            LoggingManager.log(
                level=level,
                message=f"Async function call: {func_name}",
                module=func_module,
                extras={
                    'function': func_name,
                    'async': True,
                    'args_count': len(args),
                    'kwargs_count': len(kwargs),
                    'kwargs_keys': list(kwargs.keys())
                },
                user=user,
                bu_id=bu_id
            )
            
            try:
                # Ejecutar función asíncrona
                result = await func(*args, **kwargs)
                
                # Registrar finalización exitosa
                duration = time.time() - start_time
                
                LoggingManager.log(
                    level=level,
                    message=f"Async function completed: {func_name} in {duration:.3f}s",
                    module=func_module,
                    extras={
                        'function': func_name,
                        'async': True,
                        'duration': duration,
                        'success': True
                    },
                    user=user,
                    bu_id=bu_id
                )
                
                return result
            except Exception as e:
                # Registrar error
                duration = time.time() - start_time
                
                LoggingManager.log(
                    level='error',
                    message=f"Async function error: {func_name} - {str(e)}",
                    module=func_module,
                    extras={
                        'function': func_name,
                        'async': True,
                        'duration': duration,
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True,
                    user=user,
                    bu_id=bu_id
                )
                
                # Re-lanzar excepción
                raise
                
        return wrapper
        
    return decorator


# Aplicar configuración al importar el módulo
# Esto asegura que al importar logging_manager, la configuración se aplica automáticamente
LoggingManager.setup_logging()
