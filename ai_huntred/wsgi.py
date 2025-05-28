# /home/pablo/ai_huntred/wsgi.py
"""
Configuración WSGI para el proyecto ai_huntred.

Este archivo actúa como punto de entrada para servidores web compatibles con WSGI
y define la configuración de la aplicación para entornos de producción.
"""

# Importaciones estándar
import os
import sys
import logging
from pathlib import Path

# Configuración de rutas
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.production')

# Importar después de configurar el entorno
from django.core.wsgi import get_wsgi_application

try:
    # Cargar la aplicación WSGI
    application = get_wsgi_application()
    logger.info("Aplicación WSGI cargada correctamente")
except Exception as e:
    logger.error(f"Error al cargar la aplicación WSGI: {str(e)}")
    raise

# Middleware de seguridad
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Configuración de cabeceras de seguridad
        security_headers = {
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self';",
            'Permissions-Policy': "camera=(), microphone=(), geolocation=()",
        }
        
        for header, value in security_headers.items():
            if header not in response:
                response[header] = value
                
        return response

# Aplicar el middleware de seguridad
application = SecurityHeadersMiddleware(application)