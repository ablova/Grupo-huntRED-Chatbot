"""
Sistema de Configuración Centralizado para Grupo huntRED®.
Este módulo implementa un gestor de configuración unificado para todo el sistema,
permitiendo control granular sobre todas las funcionalidades.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from asgiref.sync import sync_to_async

from app.utils.logging_manager import LoggingManager

logger = LoggingManager.get_logger('config')

class ConfigScope:
    """Alcances disponibles para la configuración."""
    GLOBAL = 'global'
    BUSINESS_UNIT = 'business_unit'
    USER = 'user'
    MODULE = 'module'
    ENVIRONMENT = 'environment'


class SystemConfig:
    """
    Gestor centralizado de configuración para todas las funcionalidades del sistema.
    Proporciona acceso unificado a parámetros de configuración con caché inteligente.
    """
    
    # Configuración predeterminada del sistema
    DEFAULT_CONFIG = {
        # Configuración general
        'app_name': 'Grupo huntRED® IA',
        'app_version': '1.0.0',
        'debug_mode': False,
        'maintenance_mode': False,
        
        # Configuración de servicios
        'services': {
            'chatbot': {
                'enabled': True,
                'model': 'gpt-4',
                'temperature': 0.7,
                'rate_limit': 100,  # Peticiones por hora
                'allowed_channels': ['whatsapp', 'telegram', 'web']
            },
            'ml': {
                'enabled': True,
                'embedding_model': 'text-embedding-3-large',
                'update_interval': 86400,  # Segundos (1 día)
                'similarity_threshold': 0.8
            },
            'payments': {
                'enabled': True,
                'default_provider': 'stripe',
                'auto_retry_failed': True,
                'notification_on_status_change': True
            },
            'publish': {
                'enabled': True,
                'default_platforms': ['web', 'linkedin'],
                'require_approval': True
            },
            'notify': {
                'enabled': True,
                'channels': ['email', 'sms', 'internal'],
                'batch_size': 50,
                'parallel_workers': 4
            }
        },
        
        # Configuración de integraciones externas
        'integrations': {
            'stripe': {
                'enabled': True,
                'api_version': '2022-11-15',
                'webhook_tolerance': 300  # Segundos
            },
            'gpt': {
                'enabled': True,
                'api_version': 'v1',
                'request_timeout': 30,  # Segundos
                'max_tokens': 2000
            },
            'blacktrust': {
                'enabled': True,
                'api_version': 'v2',
                'request_timeout': 60  # Segundos
            }
        },
        
        # Configuración de rendimiento
        'performance': {
            'cache_enabled': True,
            'default_cache_timeout': 300,  # Segundos
            'db_query_logging_threshold': 0.5,  # Segundos
            'request_logging_threshold': 1.0,  # Segundos
            'slow_task_threshold': 5.0  # Segundos
        },
        
        # Configuración de seguridad
        'security': {
            'jwt_expiry': 900,  # Segundos (15 minutos)
            'jwt_refresh_expiry': 604800,  # Segundos (7 días)
            'password_min_length': 10,
            'require_mfa_for_critical': True,
            'rate_limit_enabled': True,
            'login_rate_limit': 5,  # Intentos por minuto
            'api_rate_limit': 60  # Peticiones por minuto
        }
    }
    
    # Mapeo de variables de entorno a configuración
    ENV_MAPPING = {
        'DEBUG': ('debug_mode', bool),
        'MAINTENANCE_MODE': ('maintenance_mode', bool),
        'CHATBOT_ENABLED': ('services.chatbot.enabled', bool),
        'CHATBOT_MODEL': ('services.chatbot.model', str),
        'CHATBOT_TEMPERATURE': ('services.chatbot.temperature', float),
        'ML_ENABLED': ('services.ml.enabled', bool),
        'ML_EMBEDDING_MODEL': ('services.ml.embedding_model', str),
        'ML_UPDATE_INTERVAL': ('services.ml.update_interval', int),
        'PAYMENTS_ENABLED': ('services.payments.enabled', bool),
        'PAYMENTS_PROVIDER': ('services.payments.default_provider', str),
        'PUBLISH_ENABLED': ('services.publish.enabled', bool),
        'STRIPE_ENABLED': ('integrations.stripe.enabled', bool),
        'GPT_ENABLED': ('integrations.gpt.enabled', bool),
        'GPT_API_VERSION': ('integrations.gpt.api_version', str),
        'BLACKTRUST_ENABLED': ('integrations.blacktrust.enabled', bool),
        'CACHE_ENABLED': ('performance.cache_enabled', bool),
        'CACHE_TIMEOUT': ('performance.default_cache_timeout', int),
        'JWT_EXPIRY': ('security.jwt_expiry', int),
        'PASSWORD_MIN_LENGTH': ('security.password_min_length', int),
        'RATE_LIMIT_ENABLED': ('security.rate_limit_enabled', bool)
    }
    
    @classmethod
    def get_config(cls, key: str = None, scope: str = ConfigScope.GLOBAL,
                  scope_id: Union[int, str] = None, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración del sistema.
        
        Args:
            key: Clave de configuración (puede usar notación de puntos para anidados)
            scope: Alcance de la configuración (global, bu, user, etc.)
            scope_id: ID del alcance (ID de BU, ID de usuario, etc.)
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor de configuración
        """
        # Verificar caché
        cache_key = cls._build_cache_key(key, scope, scope_id)
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
        
        value = None
        # Intentar obtener de la base de datos
        try:
            from app.models import SystemConfiguration
            
            # Construir filtro según alcance
            filters = Q(key=key)
            
            if scope == ConfigScope.GLOBAL:
                filters &= Q(scope=scope, scope_id__isnull=True)
            else:
                filters &= Q(scope=scope, scope_id=scope_id)
                
            # Buscar configuración
            config = SystemConfiguration.objects.filter(filters).first()
            
            if config:
                try:
                    # Interpretar valor JSON
                    value = json.loads(config.value)
                except json.JSONDecodeError:
                    # Si no es JSON válido, usar como string
                    value = config.value
        except Exception as e:
            logger.error(f"Error fetching configuration from database: {str(e)}")
        
        # Si no se encontró en BD, buscar en los valores predeterminados
        if value is None and key:
            # Comprobar variables de entorno
            env_value = cls._get_from_env(key)
            if env_value is not None:
                value = env_value
            else:
                # Buscar en configuración predeterminada
                value = cls._get_from_default_config(key)
        
        # Si sigue sin encontrarse, usar el valor predeterminado
        if value is None:
            value = default
        
        # Guardar en caché
        if key:  # Solo cachear consultas específicas
            cache_timeout = cls.get_config('performance.default_cache_timeout', default=300)
            cache.set(cache_key, value, cache_timeout)
        
        return value
    
    @classmethod
    def set_config(cls, key: str, value: Any, scope: str = ConfigScope.GLOBAL,
                  scope_id: Union[int, str] = None) -> bool:
        """
        Establece un valor de configuración en el sistema.
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
            scope: Alcance de la configuración
            scope_id: ID del alcance
            
        Returns:
            bool: True si se estableció correctamente
        """
        if not key:
            return False
            
        try:
            from app.models import SystemConfiguration
            
            # Convertir valor a JSON para almacenamiento uniforme
            if not isinstance(value, str):
                json_value = json.dumps(value)
            else:
                # Intentar validar como JSON
                try:
                    json.loads(value)
                    json_value = value
                except json.JSONDecodeError:
                    # No es JSON, almacenar como string
                    json_value = json.dumps(value)
            
            # Buscar configuración existente
            filters = Q(key=key)
            
            if scope == ConfigScope.GLOBAL:
                filters &= Q(scope=scope, scope_id__isnull=True)
            else:
                filters &= Q(scope=scope, scope_id=scope_id)
                
            config, created = SystemConfiguration.objects.update_or_create(
                filters,
                defaults={
                    'key': key,
                    'value': json_value,
                    'scope': scope,
                    'scope_id': scope_id,
                    'updated_at': timezone.now()
                }
            )
            
            # Invalidar caché
            cache_key = cls._build_cache_key(key, scope, scope_id)
            cache.delete(cache_key)
            
            logger.info(f"Configuration updated: {key} ({scope})")
            
            return True
        except Exception as e:
            logger.error(f"Error setting configuration: {str(e)}")
            return False
    
    @classmethod
    def delete_config(cls, key: str, scope: str = ConfigScope.GLOBAL,
                     scope_id: Union[int, str] = None) -> bool:
        """
        Elimina una configuración del sistema.
        
        Args:
            key: Clave de configuración
            scope: Alcance de la configuración
            scope_id: ID del alcance
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            from app.models import SystemConfiguration
            
            # Construir filtro
            filters = Q(key=key)
            
            if scope == ConfigScope.GLOBAL:
                filters &= Q(scope=scope, scope_id__isnull=True)
            else:
                filters &= Q(scope=scope, scope_id=scope_id)
                
            # Eliminar configuración
            deleted, _ = SystemConfiguration.objects.filter(filters).delete()
            
            # Invalidar caché
            cache_key = cls._build_cache_key(key, scope, scope_id)
            cache.delete(cache_key)
            
            return deleted > 0
        except Exception as e:
            logger.error(f"Error deleting configuration: {str(e)}")
            return False
    
    @classmethod
    def get_all_configs(cls, scope: str = ConfigScope.GLOBAL,
                       scope_id: Union[int, str] = None) -> Dict:
        """
        Obtiene todas las configuraciones para un alcance específico.
        
        Args:
            scope: Alcance de la configuración
            scope_id: ID del alcance
            
        Returns:
            Dict con todas las configuraciones
        """
        # Verificar caché
        cache_key = cls._build_cache_key('all', scope, scope_id)
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
            
        result = {}
        
        # Obtener de base de datos
        try:
            from app.models import SystemConfiguration
            
            # Construir filtro
            if scope == ConfigScope.GLOBAL:
                configs = SystemConfiguration.objects.filter(scope=scope, scope_id__isnull=True)
            else:
                configs = SystemConfiguration.objects.filter(scope=scope, scope_id=scope_id)
                
            # Procesar resultados
            for config in configs:
                try:
                    # Interpretar valor JSON
                    result[config.key] = json.loads(config.value)
                except json.JSONDecodeError:
                    # Si no es JSON válido, usar como string
                    result[config.key] = config.value
                    
        except Exception as e:
            logger.error(f"Error fetching all configurations: {str(e)}")
        
        # Combinar con valores predeterminados para configuración global
        if scope == ConfigScope.GLOBAL:
            # Comenzar con valores predeterminados
            merged_config = cls._deep_copy(cls.DEFAULT_CONFIG)
            
            # Sobrescribir con valores de base de datos
            cls._deep_update(merged_config, result)
            
            # Sobrescribir con variables de entorno
            for env_key, (config_key, type_func) in cls.ENV_MAPPING.items():
                if env_key in os.environ:
                    try:
                        value = type_func(os.environ[env_key])
                        cls._set_nested_dict_value(merged_config, config_key, value)
                    except Exception as e:
                        logger.warning(f"Error parsing environment variable {env_key}: {str(e)}")
            
            result = merged_config
        
        # Guardar en caché
        cache_timeout = cls.get_config('performance.default_cache_timeout', default=300)
        cache.set(cache_key, result, cache_timeout)
        
        return result
    
    @classmethod
    async def get_config_async(cls, key: str = None, scope: str = ConfigScope.GLOBAL,
                             scope_id: Union[int, str] = None, default: Any = None) -> Any:
        """
        Versión asíncrona de get_config.
        Todos los parámetros son idénticos a get_config.
        """
        get_func = sync_to_async(cls.get_config)
        return await get_func(key, scope, scope_id, default)
    
    @classmethod
    async def set_config_async(cls, key: str, value: Any, scope: str = ConfigScope.GLOBAL,
                             scope_id: Union[int, str] = None) -> bool:
        """
        Versión asíncrona de set_config.
        Todos los parámetros son idénticos a set_config.
        """
        set_func = sync_to_async(cls.set_config)
        return await set_func(key, value, scope, scope_id)
    
    @classmethod
    def reload_config(cls):
        """
        Recarga toda la configuración, invalidando las cachés.
        Útil después de actualizaciones importantes.
        """
        # Invalidar cachés de configuración
        for key_pattern in ['config:*', 'config_all:*']:
            cache.delete_pattern(key_pattern)
            
        logger.info("System configuration reloaded")
        return True
    
    # Métodos auxiliares
    
    @classmethod
    def _build_cache_key(cls, key: str, scope: str, scope_id: Union[int, str]) -> str:
        """Construye una clave de caché uniforme."""
        if key == 'all':
            prefix = 'config_all'
        else:
            prefix = 'config'
            
        if scope == ConfigScope.GLOBAL:
            return f"{prefix}:{key or 'root'}"
        else:
            return f"{prefix}:{scope}:{scope_id}:{key or 'root'}"
    
    @classmethod
    def _get_from_default_config(cls, key: str) -> Any:
        """Obtiene un valor de la configuración predeterminada."""
        if not key:
            return cls.DEFAULT_CONFIG
            
        # Dividir la clave por puntos para navegación anidada
        parts = key.split('.')
        current = cls.DEFAULT_CONFIG
        
        try:
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current
        except Exception:
            return None
    
    @classmethod
    def _get_from_env(cls, key: str) -> Any:
        """Obtiene un valor de variables de entorno."""
        # Buscar en mapeo directo
        for env_key, (config_key, type_func) in cls.ENV_MAPPING.items():
            if config_key == key and env_key in os.environ:
                try:
                    return type_func(os.environ[env_key])
                except Exception:
                    return None
                
        return None
    
    @classmethod
    def _deep_copy(cls, obj: Any) -> Any:
        """Crea una copia profunda de un objeto."""
        if isinstance(obj, dict):
            return {k: cls._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls._deep_copy(v) for v in obj]
        else:
            return obj
            
    @classmethod
    def _deep_update(cls, target: Dict, source: Dict) -> Dict:
        """Actualiza un diccionario de forma recursiva."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                cls._deep_update(target[key], value)
            else:
                target[key] = value
        return target
    
    @classmethod
    def _set_nested_dict_value(cls, d: Dict, key_path: str, value: Any) -> None:
        """Establece un valor en un diccionario anidado usando una ruta de clave."""
        keys = key_path.split('.')
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value


# Función para inicializar configuración en arranque de aplicación
def initialize_system_config():
    """
    Inicializa la configuración del sistema.
    Esta función debe llamarse durante el arranque de la aplicación.
    """
    logger.info("Initializing system configuration")
    
    # Asegurar que existe la tabla de configuración
    try:
        from django.db import connection
        table_name = 'app_systemconfiguration'
        
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            
            if table_name not in tables:
                logger.warning(f"Table {table_name} does not exist, migrations may be pending")
                return
    except Exception as e:
        logger.error(f"Error checking configuration table: {str(e)}")
        return
    
    # Cargar configuraciones predeterminadas en BD si no existen
    try:
        from app.models import SystemConfiguration
        
        # Verificar si ya hay configuraciones
        if SystemConfiguration.objects.filter(scope=ConfigScope.GLOBAL).exists():
            logger.info("System configuration already initialized")
            return
            
        # Cargar configuraciones esenciales
        config_pairs = [
            ('app_name', 'Grupo huntRED®'),
            ('app_version', '1.0.0'),
            ('debug_mode', settings.DEBUG),
            ('maintenance_mode', False),
            ('services.chatbot.enabled', True),
            ('services.ml.enabled', True),
            ('services.payments.enabled', True),
            ('services.publish.enabled', True),
            ('integrations.stripe.enabled', True),
            ('integrations.gpt.enabled', True),
            ('performance.cache_enabled', True),
            ('security.rate_limit_enabled', True),
        ]
        
        # Crear configuraciones
        for key, value in config_pairs:
            SystemConfig.set_config(key, value)
            
        logger.info("Default system configuration initialized")
    except Exception as e:
        logger.error(f"Error initializing system configuration: {str(e)}")
