# Configuración para funcionalidades avanzadas

# Configuración de Stripe
STRIPE_CONFIG = {
    'api_key': 'your_stripe_api_key',
    'webhook_secret': 'your_webhook_secret',
    'currency': 'mxn',
    'success_url': '/payments/success/',
    'cancel_url': '/payments/cancel/'
}

# Configuración de X (Twitter)
X_CONFIG = {
    'api_key': 'your_x_api_key',
    'api_secret': 'your_x_api_secret',
    'access_token': 'your_x_access_token',
    'access_token_secret': 'your_x_access_token_secret'
}

# Configuración de Redis para caching
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'ttl': 3600  # Tiempo de vida en segundos
}

# Configuración de Celery
CELERY_CONFIG = {
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json'],
    'timezone': 'America/Mexico_City'
}

# Configuración de QR
QR_CONFIG = {
    'version': 1,
    'error_correction': 'L',
    'box_size': 10,
    'border': 4,
    'upload_path': 'proposals/qr/'
}

# Configuración de análisis
ANALYTICS_CONFIG = {
    'time_window': 30,  # Días para análisis
    'open_threshold': 0.7,
    'response_threshold': 24,  # Horas
    'max_discount': 0.10  # Máximo descuento
}
