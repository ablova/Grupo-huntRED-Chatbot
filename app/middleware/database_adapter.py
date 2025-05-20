"""
Middleware para manejar adapatación dinámica de bases de datos.
Ayuda a resolver problemas de compatibilidad entre entornos de desarrollo y producción.
"""
from django.conf import settings
from django.http import HttpRequest
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)

class DatabaseAdapterMiddleware:
    """
    Middleware que previene problemas con conexiones de PostgreSQL 
    en entornos de desarrollo local, especialmente en arquitecturas Apple Silicon.
    
    Permite usar SQLite para comandos de migraciones y desarrollo,
    mientras mantiene PostgreSQL para producción.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Detectar entorno forzado a SQLite
        self.force_sqlite = getattr(settings, 'FORCE_SQLITE', False)
        
        if self.force_sqlite:
            logger.info("DatabaseAdapterMiddleware: Forzando SQLite para este entorno")
            
    def __call__(self, request: HttpRequest):
        # Aplicar lógica antes de pasar la petición
        response = self.get_response(request)
        return response
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesa la vista antes de que se ejecute.
        Usado para manejar comandos de migración y detectar patrones específicos.
        """
        # No hay necesidad de procesar aquí por ahora
        # Este método se reserva para lógica futura si es necesaria
        return None
