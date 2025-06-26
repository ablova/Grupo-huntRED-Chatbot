"""
Integraciones de optimización para Grupo huntRED®.
Este módulo proporciona funciones para integrar las optimizaciones
del sistema en la configuración principal de Django.
"""

import os
import logging
from typing import Dict, List, Any
from django.conf import settings
from django.apps import apps
from django.core.cache import cache
from django.db import connection

# Importar el integrador que creamos
from app.ats.utils.system_integrator import SystemIntegrator

logger = logging.getLogger(__name__)

def initialize_optimizations():
    """
    Inicializa todas las optimizaciones del sistema.
    Esta función debe llamarse durante el arranque de la aplicación.
    """
    # Inicialización centralizada a través del integrador
    SystemIntegrator.initialize()
    logger.info("Grupo huntRED® optimizations initialized")
    return True

def get_middleware_classes() -> List[str]:
    """
    Obtiene las clases de middleware optimizadas.
    Para incluir en la configuración principal de Django.
    
    Returns:
        Lista de clases de middleware para MIDDLEWARE setting
    """
    # Middlewares base que deben ir al principio
    security_middlewares = [
        'app.utils.system_middleware.SecurityMiddleware',
    ]
    
    # Middlewares que deben ir al final
    performance_middlewares = [
        'app.utils.system_middleware.PerformanceMiddleware',
        'app.utils.system_middleware.LoggingMiddleware',
    ]
    
    # Middlewares específicos que deben ir después de los middlewares de Django
    business_middlewares = [
        'app.utils.system_middleware.RBACMiddleware',
        'app.utils.system_middleware.BusinessUnitMiddleware',
    ]
    
    # Obtener middlewares de Django predeterminados
    django_middlewares = getattr(settings, 'MIDDLEWARE', [])
    
    # Eliminar duplicados si ya están configurados
    django_middlewares = [m for m in django_middlewares 
                         if m not in security_middlewares and 
                            m not in performance_middlewares and
                            m not in business_middlewares]
    
    # Ordenar según prioridad
    return security_middlewares + django_middlewares + business_middlewares + performance_middlewares

def get_optimized_cache_config() -> Dict:
    """
    Obtiene una configuración de caché optimizada.
    Para incluir en la configuración principal de Django.
    
    Returns:
        Dict: Configuración de caché para CACHES setting
    """
    # Intentar detectar Redis
    has_redis = False
    try:
        import redis
        from redis.exceptions import ConnectionError
        
        # Verificar conexión a Redis
        client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=0,
            socket_timeout=1,
        )
        client.ping()
        has_redis = True
    except (ImportError, ConnectionError):
        has_redis = False
        
    # Configuración de caché optimizada según disponibilidad
    if has_redis:
        return {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"redis://{getattr(settings, 'REDIS_HOST', 'localhost')}:{getattr(settings, 'REDIS_PORT', 6379)}/1",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'PARSER_CLASS': 'redis.connection.HiredisParser',
                    'SOCKET_CONNECT_TIMEOUT': 5,
                    'SOCKET_TIMEOUT': 5,
                    'CONNECTION_POOL_KWARGS': {'max_connections': 100},
                }
            },
            'sessions': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': f"redis://{getattr(settings, 'REDIS_HOST', 'localhost')}:{getattr(settings, 'REDIS_PORT', 6379)}/2",
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'PARSER_CLASS': 'redis.connection.HiredisParser',
                }
            },
        }
    else:
        # Fallback a caché local
        return {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }

def get_logging_config() -> Dict:
    """
    Obtiene una configuración de logging optimizada.
    Para incluir en la configuración principal de Django.
    
    Returns:
        Dict: Configuración de logging para LOGGING setting
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[%(asctime)s] [%(levelname)s] [%(name)s] [%(pathname)s:%(lineno)d] - %(message)s'
            },
            'simple': {
                'format': '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s'
            },
        },
        'filters': {
            'business_unit_context': {
                '()': 'app.utils.logging_manager.BusinessUnitContextFilter',
            },
            'module_context': {
                '()': 'app.utils.logging_manager.ModuleContextFilter',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
                'filters': ['business_unit_context', 'module_context'],
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(settings.BASE_DIR, 'logs', 'grupo_huntred.log'),
                'maxBytes': 1024 * 1024 * 5,  # 5 MB
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['business_unit_context', 'module_context'],
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(settings.BASE_DIR, 'logs', 'error.log'),
                'maxBytes': 1024 * 1024 * 5,  # 5 MB
                'backupCount': 10,
                'formatter': 'verbose',
                'filters': ['business_unit_context', 'module_context'],
            }
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.server': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'app': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG',
                'propagate': False,
                'filters': ['business_unit_context', 'module_context'],
            },
        },
        'root': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'filters': ['business_unit_context', 'module_context'],
        }
    }

def apply_query_optimizations():
    """
    Aplica optimizaciones de consulta a los modelos principales.
    Esta función debe llamarse después de que se carguen todas las aplicaciones.
    """
    # Modelos con acceso frecuente que se beneficiarían de índices
    critical_models = [
        ('app', 'BusinessUnit'),
        ('app', 'Person'),
        ('app', 'Vacante'),
        ('app', 'Pago'),
        ('app', 'NotificationChannel'),
    ]
    
    # Aplicar análisis de rendimiento de consultas
    for app_label, model_name in critical_models:
        try:
            Model = apps.get_model(app_label, model_name)
            
            # Obtener sugerencias de índices
            from app.ats.utils.orm_optimizer import QueryPerformanceAnalyzer
            suggestions = QueryPerformanceAnalyzer.suggest_indexes(Model)
            
            # Registrar sugerencias
            if suggestions:
                logger.info(f"Index suggestions for {app_label}.{model_name}: {', '.join(suggestions)}")
                
        except Exception as e:
            logger.error(f"Error analyzing model {app_label}.{model_name}: {str(e)}")
    
    # Verificar índices en tablas principales
    with connection.cursor() as cursor:
        try:
            # Verificar índice en tabla de BusinessUnit
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND tbl_name='app_businessunit' AND name='idx_businessunit_name'
            """)
            if cursor.fetchone()[0] == 0:
                logger.warning("Missing index on BusinessUnit.name, consider adding for performance")
                
            # Verificar índice en tabla de Person
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND tbl_name='app_person' AND name='idx_person_email'
            """)
            if cursor.fetchone()[0] == 0:
                logger.warning("Missing index on Person.email, consider adding for performance")
                
        except Exception as e:
            logger.error(f"Error checking indexes: {str(e)}")
            
    return True

def get_optimized_templates_config() -> Dict:
    """
    Obtiene una configuración de templates optimizada.
    Para incluir en la configuración principal de Django.
    
    Returns:
        Dict: Configuración de templates para TEMPLATES setting
    """
    # Configuración base
    templates_config = {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(settings.BASE_DIR, 'app', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.business_units',
            ],
            'libraries': {
                'business_unit_tags': 'app.templatetags.business_unit_tags',
            },
        },
    }
    
    # En producción, añadir caché de templates
    if not getattr(settings, 'DEBUG', False):
        templates_config['OPTIONS']['loaders'] = [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ]
        
    return templates_config
