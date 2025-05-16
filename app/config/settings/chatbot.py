"""
Configuración del sistema de chatbot
Ubicación: /app/config/settings/chatbot.py
Responsabilidad: Configuración global del chatbot y sus componentes

Created: 2025-05-15
Updated: 2025-05-15
"""

CHATBOT_CONFIG = {
    'ENABLED': True,
    'CHANNELS': {
        'WHATSAPP': True,
        'TELEGRAM': True,
        'SLACK': True,
        'MESSENGER': True,
        'INSTAGRAM': True
    },
    'NETWORKS': {
        'LINKEDIN': True,
        'X': True
    },
    'NLP': {
        'MODEL': 'gpt-4',
        'MAX_TOKENS': 2000,
        'TEMPERATURE': 0.7
    },
    'RATE_LIMITING': {
        'WHATSAPP': 30,  # segundos
        'TELEGRAM': 15,
        'SLACK': 20
    }
}
