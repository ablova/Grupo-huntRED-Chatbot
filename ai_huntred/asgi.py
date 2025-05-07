# /home/pablo/ai_huntred/asgi.py
"""
ASGI config for ai_huntred project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

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

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

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
                ])
            await send(message)

        await self.app(scope, receive, send_wrapper)

application = get_asgi_application()
application = SecureHeadersMiddleware(application)
