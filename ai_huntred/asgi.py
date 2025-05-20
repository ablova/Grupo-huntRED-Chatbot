# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/ai_huntred/asgi.py
#
# Configuración ASGI para el proyecto AI HuntRED.
# Configura el middleware de seguridad y la aplicación ASGI principal.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import os
import logging
from django.core.asgi import get_asgi_application
from ai_huntred.settings import LOGGING, SECURITY_CONFIG

# Configurar logging
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('asgi')

# Verificar configuración de seguridad
if not SECURITY_CONFIG['SECURE_SSL_REDIRECT']:
    logger.warning("SSL redirection is disabled")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.production')

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
