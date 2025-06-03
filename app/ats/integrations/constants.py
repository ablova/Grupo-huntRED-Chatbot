# Tipos de integración
INTEGRATION_TYPES = {
    'WHATSAPP': 'whatsapp',
    'TELEGRAM': 'telegram',
    'MESSENGER': 'messenger',
    'INSTAGRAM': 'instagram',
    'SLACK': 'slack',
    'EMAIL': 'email',
}

# Tipos de eventos
EVENT_TYPES = {
    'MESSAGE_SENT': 'message_sent',
    'MESSAGE_RECEIVED': 'message_received',
    'ERROR': 'error',
    'WEBHOOK': 'webhook',
    'OTHER': 'other',
}

# Estados de la integración
INTEGRATION_STATUS = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'ERROR': 'error',
}

# Configuraciones por defecto
DEFAULT_CONFIGS = {
    'WHATSAPP': {
        'api_key': '',
        'api_secret': '',
        'phone_number': '',
    },
    'TELEGRAM': {
        'bot_token': '',
        'chat_id': '',
    },
    'MESSENGER': {
        'page_token': '',
        'app_secret': '',
    },
    'INSTAGRAM': {
        'access_token': '',
        'app_id': '',
    },
    'SLACK': {
        'bot_token': '',
        'app_token': '',
    },
    'EMAIL': {
        'smtp_host': '',
        'smtp_port': '',
        'username': '',
        'password': '',
    },
} 