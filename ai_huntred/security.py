from datetime import timedelta
from django.conf import settings

# Configuración de JWT
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': timedelta(hours=1),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_ALLOW_REFRESH': True,
    'JWT_AUTH_COOKIE': 'jwt',
    'JWT_AUTH_COOKIE_SECURE': not settings.DEBUG,
    'JWT_AUTH_COOKIE_HTTPONLY': True,
    'JWT_AUTH_COOKIE_SAMESITE': 'Lax',
}

# Configuración de Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_KEY_PREFIX = 'ratelimit'

# Límites de rate por endpoint
RATELIMIT_VIEWS = {
    'api:login': '5/m',  # 5 intentos por minuto
    'api:register': '3/h',  # 3 registros por hora
    'api:password-reset': '3/h',  # 3 resets por hora
    'api:verify-email': '5/h',  # 5 verificaciones por hora
    'api:refresh-token': '10/m',  # 10 refrescos por minuto
    'api:chat': '60/m',  # 60 mensajes por minuto
    'api:feedback': '10/m',  # 10 feedbacks por minuto
}

# Configuración de seguridad adicional
SECURITY_CONFIG = {
    'PASSWORD_HASHERS': [
        'django.contrib.auth.hashers.Argon2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    ],
    'PASSWORD_MIN_LENGTH': 12,
    'PASSWORD_MAX_LENGTH': 128,
    'PASSWORD_VALIDATORS': [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 12,
            }
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ],
    'SESSION_COOKIE_AGE': 3600,  # 1 hora
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
    'CSRF_COOKIE_AGE': 3600,  # 1 hora
    'CSRF_COOKIE_SECURE': not settings.DEBUG,
    'CSRF_COOKIE_HTTPONLY': True,
    'CSRF_COOKIE_SAMESITE': 'Lax',
    'CSRF_TRUSTED_ORIGINS': settings.ALLOWED_HOSTS,
}

# Configuración de CORS
CORS_ALLOWED_ORIGINS = [
    'https://huntred.com',
    'https://www.huntred.com',
    'https://api.huntred.com',
]

CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
] 