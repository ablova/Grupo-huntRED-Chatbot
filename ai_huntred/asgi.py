# /home/pablo/ai_huntred/asgi.py
"""
Configuración ASGI para el proyecto AI HuntRED.

Este archivo configura el servidor ASGI para el proyecto, incluyendo middlewares
de seguridad y optimizaciones para entornos de producción.
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
from django.core.asgi import get_asgi_application
from ai_huntred.settings.production import LOGGING, SECURITY_CONFIG

# Configurar logging
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('asgi')

# Verificar configuración de seguridad
if not SECURITY_CONFIG['SECURE_SSL_REDIRECT']:
    logger.warning("SSL redirection is disabled")

# Middleware de seguridad
class SecureHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                message['headers'].extend([
                    (b'x-frame-options', b'DENY'),
                    (b'x-content-type-options', b'nosniff'),
                    (b'referrer-policy', b'strict-origin-when-cross-origin'),
                    (b'strict-transport-security', b'max-age=31536000; includeSubDomains; preload'),
                    (b'content-security-policy', b"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"),
                ])
            await send(message)

        await self.app(scope, receive, send_wrapper)

# Obtener la aplicación ASGI
application = get_asgi_application()

# Aplicar middleware de seguridad
application = SecureHeadersMiddleware(application)
