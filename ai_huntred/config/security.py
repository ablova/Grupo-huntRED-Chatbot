# /home/pablo/ai_huntred/config/security.py
#
# Configuración de seguridad para AI HuntRED.
# Configura la seguridad de la aplicación, incluyendo JWT y limitación de tasas.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

from datetime import timedelta
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import environ

env = environ.Env()

class SecurityConfig:
    @staticmethod
    def get_config():
        # JWT Configuration
        jwt_config = {
            'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
            'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
            'ROTATE_REFRESH_TOKENS': True,
            'BLACKLIST_AFTER_ROTATION': True,
            'ALGORITHM': 'HS256',
            'SIGNING_KEY': env('JWT_SECRET_KEY', default=settings.SECRET_KEY),
        }

        # Rate Limiting
        rate_limiting = {
            'DEFAULT_RATE': '1000/hour',
            'LOGIN_RATE': '100/hour',
            'API_RATE': '500/hour',
        }

        # Environment validation con valores por defecto para entornos de desarrollo
        # En producción estas variables deberían estar configuradas
        if not settings.DEBUG:  # Solo validamos estrictamente en entornos de producción
            required_env_vars = ['JWT_SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
            for var in required_env_vars:
                if not env(var, default=None):
                    raise ImproperlyConfigured(f"Environment variable {var} is required")
        # En desarrollo usamos valores por defecto

        return {
            'JWT_CONFIG': jwt_config,
            'RATE_LIMITING': rate_limiting,
            'SECURE_SSL_REDIRECT': env.bool('SECURE_SSL_REDIRECT', default=True),
            'SESSION_COOKIE_SECURE': env.bool('SESSION_COOKIE_SECURE', default=True),
            'CSRF_COOKIE_SECURE': env.bool('CSRF_COOKIE_SECURE', default=True),
        }
