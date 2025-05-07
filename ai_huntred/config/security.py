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

        # Environment validation
        required_env_vars = ['JWT_SECRET_KEY', 'DATABASE_URL', 'REDIS_URL']
        for var in required_env_vars:
            if not env(var, default=None):
                raise ImproperlyConfigured(f"Environment variable {var} is required")

        return {
            'JWT_CONFIG': jwt_config,
            'RATE_LIMITING': rate_limiting,
            'SECURE_SSL_REDIRECT': env.bool('SECURE_SSL_REDIRECT', default=True),
            'SESSION_COOKIE_SECURE': env.bool('SESSION_COOKIE_SECURE', default=True),
            'CSRF_COOKIE_SECURE': env.bool('CSRF_COOKIE_SECURE', default=True),
        }
