# /home/pablo/ai_huntred/wsgi.py
"""
WSGI config for ai_huntred project.
"""
import os
import logging
from django.core.wsgi import get_wsgi_application
from ai_huntred.settings.production import LOGGING, security_config as SECURITY_CONFIG

# Configurar logging
logging.config.dictConfig(LOGGING)
logger = logging.getLogger('gunicorn')

# Verificar configuración de seguridad
if not SECURITY_CONFIG['SECURE_SSL_REDIRECT']:
    logger.warning("SSL redirection is disabled")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_huntred.settings.production')

application = get_wsgi_application()

# Middleware de seguridad
def secure_headers(get_response):
    def middleware(request):
        response = get_response(request)
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        return response
    return middleware

application = secure_headers(application)