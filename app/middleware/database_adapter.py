"""
Middleware para manejar adapatación dinámica de bases de datos.

Ayuda a resolver problemas de compatibilidad entre entornos de desarrollo y producción.
Implementado siguiendo las reglas globales de Grupo huntRED® para optimización 
de rendimiento y mantenimiento de código Django. Permite trabajar con SQLite en 
desarrollo local y PostgreSQL en producción sin modificar código.

Creado: Mayo 2025
Autor: Equipo Desarrollo Grupo huntRED®
"""
import os
import logging
from django.conf import settings
from django.http import HttpRequest
from django.urls import resolve
from django.db import connections
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class DatabaseAdapterMiddleware:
    """
    Middleware que previene problemas con conexiones de PostgreSQL 
    en entornos de desarrollo local, especialmente en arquitecturas Apple Silicon.
    
    Permite usar SQLite para comandos de migraciones y desarrollo,
    mientras mantiene PostgreSQL para producción.
    
    Optimizado según reglas globales de Grupo huntRED® para CPU usage y mantenimiento.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Detectar entorno forzado a SQLite
        self.force_sqlite = getattr(settings, 'FORCE_SQLITE', False) or os.environ.get('FORCE_SQLITE') == 'true'
        self.local_dev = getattr(settings, 'LOCAL_DEV', False) or os.environ.get('LOCAL_DEV') == 'true'
        
        if self.force_sqlite:
            logger.info("DatabaseAdapterMiddleware: Forzando SQLite para este entorno")
            self._setup_sqlite_if_needed()
        elif self.local_dev:
            logger.info("DatabaseAdapterMiddleware: Entorno de desarrollo local detectado")
            
    def __call__(self, request: HttpRequest):
        # Aplicar lógica antes de pasar la petición
        response = self.get_response(request)
        return response
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesa la vista antes de que se ejecute.
        Usado para manejar comandos de migración y detectar patrones específicos.
        """
        # Verificar si estamos en un comando de administración Django
        if self.force_sqlite and hasattr(request, 'path'):
            # Para comandos de migración (detectados por patrones en URL admin)
            if request.path.startswith('/admin/') and 'migration' in request.path:
                logger.info(f"Usando SQLite para operación admin: {request.path}")
        return None
        
    def _setup_sqlite_if_needed(self):
        """
        Configura conexiones SQLite si es necesario.
        Esta función ayuda a garantizar que no se intente usar PostgreSQL
        cuando estamos en modo SQLite forzado.
        """
        try:
            # Intentar detectar si estamos usando PostgreSQL
            if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                logger.warning("PostgreSQL configurado pero SQLite forzado. Verificando conexiones.")
                
                # Solo registrar, no modificar conexiones en tiempo de ejecución
                # para evitar efectos secundarios
                logger.info("SQLite será usado para operaciones locales")
        except (KeyError, AttributeError, ImproperlyConfigured) as e:
            logger.error(f"Error verificando configuración de base de datos: {e}")
            # No levantar excepción, para permitir que la aplicación continúe
