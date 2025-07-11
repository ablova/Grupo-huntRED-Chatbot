# app/ats/config/settings/chatbot.py
"""
Configuración del chatbot ATS.
"""

import os
from typing import Dict, Any

# Configuración del chatbot
CHATBOT_CONFIG = {
    "name": "AURA Chatbot",
    "version": "2.0.0",
    "language": "es",
    "timezone": "America/Mexico_City",
    
    # Configuración de respuestas
    "response": {
        "max_length": 500,
        "default_greeting": "¡Hola! Soy AURA, tu asistente virtual. ¿En qué puedo ayudarte?",
        "default_farewell": "¡Gracias por tu tiempo! Ha sido un placer ayudarte.",
        "thinking_message": "Estoy procesando tu solicitud...",
        "error_message": "Lo siento, tuve un problema procesando tu solicitud. ¿Podrías intentarlo de nuevo?",
    },
    
    # Configuración de personalidad
    "personality": {
        "tone": "professional_friendly",
        "formality_level": "semi_formal",
        "empathy_level": "high",
        "response_style": "conversational",
    },
    
    # Configuración de ML/AI
    "ai": {
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 150,
        "enable_context": True,
        "context_window": 10,
        "enable_memory": True,
        "memory_duration": 3600,  # 1 hora en segundos
    },
    
    # Configuración de workflows
    "workflows": {
        "enable_personality_assessment": True,
        "enable_cultural_fit": True,
        "enable_skill_analysis": True,
        "enable_compatibility_matching": True,
        "enable_succession_planning": True,
    },
    
    # Configuración de canales
    "channels": {
        "whatsapp": {
            "enabled": True,
            "webhook_url": os.getenv("WHATSAPP_WEBHOOK_URL", ""),
            "api_token": os.getenv("WHATSAPP_API_TOKEN", ""),
        },
        "telegram": {
            "enabled": True,
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "webhook_url": os.getenv("TELEGRAM_WEBHOOK_URL", ""),
        },
        "messenger": {
            "enabled": True,
            "page_token": os.getenv("MESSENGER_PAGE_TOKEN", ""),
            "verify_token": os.getenv("MESSENGER_VERIFY_TOKEN", ""),
        },
        "instagram": {
            "enabled": True,
            "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
            "webhook_url": os.getenv("INSTAGRAM_WEBHOOK_URL", ""),
        },
    },
    
    # Configuración de seguridad
    "security": {
        "enable_encryption": True,
        "enable_authentication": True,
        "session_timeout": 1800,  # 30 minutos
        "max_requests_per_minute": 60,
        "enable_rate_limiting": True,
    },
    
    # Configuración de logging
    "logging": {
        "level": "INFO",
        "enable_file_logging": True,
        "log_file": "chatbot.log",
        "enable_console_logging": True,
        "enable_error_tracking": True,
    },
    
    # Configuración de analytics
    "analytics": {
        "enable_tracking": True,
        "track_conversations": True,
        "track_user_behavior": True,
        "track_performance_metrics": True,
        "enable_sentiment_analysis": True,
    },
    
    # Configuración de notificaciones
    "notifications": {
        "enable_email_notifications": True,
        "enable_sms_notifications": False,
        "enable_push_notifications": True,
        "notification_recipients": [],
    },
    
    # Configuración de integración
    "integration": {
        "enable_crm_integration": True,
        "enable_ats_integration": True,
        "enable_calendar_integration": True,
        "enable_email_integration": True,
        "enable_document_integration": True,
    },
    
    # Configuración de personalización
    "customization": {
        "enable_branding": True,
        "company_name": "Grupo HuntRED",
        "company_logo": "",
        "primary_color": "#007bff",
        "secondary_color": "#6c757d",
        "enable_custom_responses": True,
    },
    
    # Configuración de mantenimiento
    "maintenance": {
        "enable_auto_updates": True,
        "backup_frequency": "daily",
        "enable_health_checks": True,
        "enable_performance_monitoring": True,
    },
}

# Configuraciones específicas por entorno
def get_chatbot_config(environment: str = "development") -> Dict[str, Any]:
    """
    Obtiene la configuración del chatbot según el entorno.
    """
    config = CHATBOT_CONFIG.copy()
    
    if environment == "production":
        config["ai"]["temperature"] = 0.5
        config["security"]["enable_encryption"] = True
        config["logging"]["level"] = "WARNING"
        config["analytics"]["enable_tracking"] = True
        
    elif environment == "testing":
        config["ai"]["temperature"] = 0.1
        config["security"]["enable_encryption"] = False
        config["logging"]["level"] = "DEBUG"
        config["analytics"]["enable_tracking"] = False
        
    return config 