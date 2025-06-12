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
            'AUTH_HEADER_TYPES': ('Bearer',),
            'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
            'USER_ID_FIELD': 'id',
            'USER_ID_CLAIM': 'user_id',
            'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
            'TOKEN_TYPE_CLAIM': 'token_type',
            'JTI_CLAIM': 'jti',
            'TOKEN_USER_CLASS': 'django.contrib.auth.models.User',
        }

        # API Security Configuration
        api_security = {
            'whatsapp': {
                'TOKEN_VALIDATION': True,
                'RATE_LIMIT': '1000/hour',
                'IP_WHITELIST': env.list('WHATSAPP_IP_WHITELIST', default=[]),
                'WEBHOOK_SECRET': env('WHATSAPP_WEBHOOK_SECRET', default=None),
                'VERIFY_TOKEN': env('WHATSAPP_VERIFY_TOKEN', default=None),
            },
            'telegram': {
                'TOKEN_VALIDATION': True,
                'RATE_LIMIT': '1000/hour',
                'IP_WHITELIST': env.list('TELEGRAM_IP_WHITELIST', default=[]),
                'WEBHOOK_SECRET': env('TELEGRAM_WEBHOOK_SECRET', default=None),
                'BOT_TOKEN': env('TELEGRAM_BOT_TOKEN', default=None),
            },
            'messenger': {
                'TOKEN_VALIDATION': True,
                'RATE_LIMIT': '1000/hour',
                'IP_WHITELIST': env.list('MESSENGER_IP_WHITELIST', default=[]),
                'APP_SECRET': env('MESSENGER_APP_SECRET', default=None),
                'VERIFY_TOKEN': env('MESSENGER_VERIFY_TOKEN', default=None),
            },
            'instagram': {
                'TOKEN_VALIDATION': True,
                'RATE_LIMIT': '1000/hour',
                'IP_WHITELIST': env.list('INSTAGRAM_IP_WHITELIST', default=[]),
                'APP_SECRET': env('INSTAGRAM_APP_SECRET', default=None),
                'ACCESS_TOKEN': env('INSTAGRAM_ACCESS_TOKEN', default=None),
            }
        }

        # Rate Limiting
        rate_limiting = {
            'DEFAULT_RATE': '1000/hour',
            'LOGIN_RATE': '100/hour',
            'API_RATE': '500/hour',
            'MESSAGE_RATE': '1000/hour',
            'MEDIA_RATE': '100/hour',
            'ANALYSIS_RATE': '50/hour',
        }

        # Environment validation con valores por defecto para entornos de desarrollo
        # En producción estas variables deberían estar configuradas
        if not settings.DEBUG:  # Solo validamos estrictamente en entornos de producción
            required_env_vars = [
                'JWT_SECRET_KEY', 
                'DATABASE_URL', 
                'REDIS_URL',
                'WHATSAPP_WEBHOOK_SECRET',
                'TELEGRAM_BOT_TOKEN',
                'MESSENGER_APP_SECRET',
                'INSTAGRAM_APP_SECRET'
            ]
            for var in required_env_vars:
                if not env(var, default=None):
                    raise ImproperlyConfigured(f"Environment variable {var} is required")

        return {
            'JWT_CONFIG': jwt_config,
            'API_SECURITY': api_security,
            'RATE_LIMITING': rate_limiting,
            'SECURE_SSL_REDIRECT': env.bool('SECURE_SSL_REDIRECT', default=True),
            'SESSION_COOKIE_SECURE': env.bool('SESSION_COOKIE_SECURE', default=True),
            'CSRF_COOKIE_SECURE': env.bool('CSRF_COOKIE_SECURE', default=True),
            'SECURE_HSTS_SECONDS': 31536000,  # 1 year
            'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
            'SECURE_HSTS_PRELOAD': True,
            'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
            'SECURE_REFERRER_POLICY': 'same-origin',
            'SECURE_CONTENT_TYPE_NOSNIFF': True,
            'SECURE_BROWSER_XSS_FILTER': True,
            'X_FRAME_OPTIONS': 'DENY',
        }
