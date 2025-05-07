# /home/pablo/ai_huntred/wsgi.py
"""
WSGI config for ai_huntred project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""
import os
import logging
from django.core.wsgi import get_wsgi_application
from ai_huntred.settings import LOGGING, SECURITY_CONFIG

# Configurar logging
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('gunicorn')

# Verificar configuración de seguridad
if not SECURITY_CONFIG['SECURE_SSL_REDIRECT']:
    logger.warning("SSL redirection is disabled")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings')

application = get_wsgi_application()

# Middleware de seguridad
def secure_headers(get_response):
    def middleware(request):
        response = get_response(request)
        
        # Configurar headers de seguridad
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    return middleware

application = secure_headers(application)