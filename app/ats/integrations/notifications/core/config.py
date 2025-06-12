"""
Configuración central del sistema de notificaciones de Grupo huntRED®.
"""
from typing import Dict, Any, List
from enum import Enum

class NotificationSeverity(Enum):
    """Niveles de severidad para notificaciones."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class NotificationType(Enum):
    """Tipos de notificaciones disponibles."""
    # Sistema
    SYSTEM_ALERT = "system_alert"
    SYSTEM_ERROR = "system_error"
    SYSTEM_EVENT = "system_event"
    
    # Negocio
    BUSINESS_ALERT = "business_alert"
    BUSINESS_EVENT = "business_event"
    PAYMENT = "payment"
    PLACEMENT = "placement"
    
    # Usuario
    USER_EVENT = "user_event"
    USER_ALERT = "user_alert"
    
    # Seguridad
    SECURITY_ALERT = "security_alert"
    SECURITY_EVENT = "security_event"
    
    # Rendimiento
    PERFORMANCE_ALERT = "performance_alert"
    METRICS = "metrics"
    
    # Procesos
    PROCESS_EVENT = "process_event"
    PROCESS_ALERT = "process_alert"
    
    # Chatbot
    CHATBOT_EVENT = "chatbot_event"
    CHATBOT_ALERT = "chatbot_alert"
    CHATBOT_ERROR = "chatbot_error"

# Configuración de canales por tipo de notificación
NOTIFICATION_CHANNELS: Dict[str, List[str]] = {
    NotificationType.SYSTEM_ALERT.value: ["telegram", "email"],
    NotificationType.SYSTEM_ERROR.value: ["telegram", "email"],
    NotificationType.SYSTEM_EVENT.value: ["telegram"],
    
    NotificationType.BUSINESS_ALERT.value: ["telegram", "whatsapp", "email"],
    NotificationType.BUSINESS_EVENT.value: ["telegram", "email"],
    NotificationType.PAYMENT.value: ["telegram", "whatsapp", "email"],
    NotificationType.PLACEMENT.value: ["telegram", "whatsapp", "email"],
    
    NotificationType.USER_EVENT.value: ["telegram", "email"],
    NotificationType.USER_ALERT.value: ["telegram", "whatsapp"],
    
    NotificationType.SECURITY_ALERT.value: ["telegram", "email"],
    NotificationType.SECURITY_EVENT.value: ["telegram"],
    
    NotificationType.PERFORMANCE_ALERT.value: ["telegram"],
    NotificationType.METRICS.value: ["telegram"],
    
    NotificationType.PROCESS_EVENT.value: ["telegram"],
    NotificationType.PROCESS_ALERT.value: ["telegram", "email"],
    
    NotificationType.CHATBOT_EVENT.value: ["telegram"],
    NotificationType.CHATBOT_ALERT.value: ["telegram", "email"],
    NotificationType.CHATBOT_ERROR.value: ["telegram", "email"]
}

# Emojis por tipo de notificación
NOTIFICATION_EMOJIS: Dict[str, str] = {
    NotificationType.SYSTEM_ALERT.value: "🔴",
    NotificationType.SYSTEM_ERROR.value: "❌",
    NotificationType.SYSTEM_EVENT.value: "🔔",
    
    NotificationType.BUSINESS_ALERT.value: "🏢",
    NotificationType.BUSINESS_EVENT.value: "📊",
    NotificationType.PAYMENT.value: "💰",
    NotificationType.PLACEMENT.value: "🎯",
    
    NotificationType.USER_EVENT.value: "👤",
    NotificationType.USER_ALERT.value: "⚠️",
    
    NotificationType.SECURITY_ALERT.value: "🔒",
    NotificationType.SECURITY_EVENT.value: "🛡️",
    
    NotificationType.PERFORMANCE_ALERT.value: "⚡",
    NotificationType.METRICS.value: "📈",
    
    NotificationType.PROCESS_EVENT.value: "⚙️",
    NotificationType.PROCESS_ALERT.value: "🚨",
    
    NotificationType.CHATBOT_EVENT.value: "🤖",
    NotificationType.CHATBOT_ALERT.value: "🤖⚠️",
    NotificationType.CHATBOT_ERROR.value: "🤖❌"
}

# Severidad por tipo de notificación
NOTIFICATION_SEVERITY: Dict[str, str] = {
    NotificationType.SYSTEM_ALERT.value: NotificationSeverity.HIGH.value,
    NotificationType.SYSTEM_ERROR.value: NotificationSeverity.CRITICAL.value,
    NotificationType.SYSTEM_EVENT.value: NotificationSeverity.INFO.value,
    
    NotificationType.BUSINESS_ALERT.value: NotificationSeverity.HIGH.value,
    NotificationType.BUSINESS_EVENT.value: NotificationSeverity.INFO.value,
    NotificationType.PAYMENT.value: NotificationSeverity.HIGH.value,
    NotificationType.PLACEMENT.value: NotificationSeverity.HIGH.value,
    
    NotificationType.USER_EVENT.value: NotificationSeverity.INFO.value,
    NotificationType.USER_ALERT.value: NotificationSeverity.MEDIUM.value,
    
    NotificationType.SECURITY_ALERT.value: NotificationSeverity.CRITICAL.value,
    NotificationType.SECURITY_EVENT.value: NotificationSeverity.HIGH.value,
    
    NotificationType.PERFORMANCE_ALERT.value: NotificationSeverity.HIGH.value,
    NotificationType.METRICS.value: NotificationSeverity.INFO.value,
    
    NotificationType.PROCESS_EVENT.value: NotificationSeverity.INFO.value,
    NotificationType.PROCESS_ALERT.value: NotificationSeverity.MEDIUM.value,
    
    NotificationType.CHATBOT_EVENT.value: NotificationSeverity.INFO.value,
    NotificationType.CHATBOT_ALERT.value: NotificationSeverity.MEDIUM.value,
    NotificationType.CHATBOT_ERROR.value: NotificationSeverity.HIGH.value
}

# Plantillas base por tipo de notificación
NOTIFICATION_TEMPLATES: Dict[str, str] = {
    NotificationType.SYSTEM_ALERT.value: "{emoji} *Alerta del Sistema*\n\n📝 *Alerta:* {alert_name}\n📋 *Tipo:* {alert_type}\n⚠️ *Severidad:* {severity}",
    NotificationType.SYSTEM_ERROR.value: "{emoji} *Error del Sistema*\n\n📝 *Tipo de Error:* {error_type}\n💬 *Mensaje:* {error_message}",
    NotificationType.SYSTEM_EVENT.value: "{emoji} *Evento del Sistema*\n\n📝 *Evento:* {event_name}\n📋 *Tipo:* {event_type}",
    
    NotificationType.BUSINESS_ALERT.value: "{emoji} *Alerta de Negocio*\n\n📝 *Alerta:* {alert_name}\n📋 *Tipo:* {alert_type}\n🏢 *Empresa:* {company_name}",
    NotificationType.BUSINESS_EVENT.value: "{emoji} *Evento de Negocio*\n\n📝 *Evento:* {event_name}\n📋 *Tipo:* {event_type}\n🏢 *Empresa:* {company_name}",
    NotificationType.PAYMENT.value: "{emoji} *Notificación de Pago*\n\n💰 *Monto:* {amount}\n👤 *Candidato:* {candidate_name}\n💼 *Posición:* {position}",
    NotificationType.PLACEMENT.value: "{emoji} *Notificación de Colocación*\n\n👤 *Candidato:* {candidate_name}\n💼 *Posición:* {position}\n🏢 *Empresa:* {company_name}",
    
    NotificationType.USER_EVENT.value: "{emoji} *Evento de Usuario*\n\n📝 *Evento:* {event_name}\n👤 *Usuario:* {user_name}",
    NotificationType.USER_ALERT.value: "{emoji} *Alerta de Usuario*\n\n📝 *Alerta:* {alert_name}\n👤 *Usuario:* {user_name}",
    
    NotificationType.SECURITY_ALERT.value: "{emoji} *Alerta de Seguridad*\n\n📝 *Alerta:* {alert_name}\n📋 *Tipo:* {alert_type}\n⚠️ *Severidad:* {severity}",
    NotificationType.SECURITY_EVENT.value: "{emoji} *Evento de Seguridad*\n\n📝 *Evento:* {event_name}\n📋 *Tipo:* {event_type}\n⚠️ *Severidad:* {severity}",
    
    NotificationType.PERFORMANCE_ALERT.value: "{emoji} *Alerta de Rendimiento*\n\n📝 *Alerta:* {alert_name}\n📊 *Métrica:* {metric_name}\n📈 *Valor Actual:* {current_value}",
    NotificationType.METRICS.value: "{emoji} *Métricas*\n\n📊 *Métrica:* {metric_name}\n📈 *Valor:* {value}\n📅 *Período:* {period}",
    
    NotificationType.PROCESS_EVENT.value: "{emoji} *Evento de Proceso*\n\n📝 *Evento:* {event_name}\n📋 *Tipo:* {event_type}\n⚙️ *Estado:* {status}",
    NotificationType.PROCESS_ALERT.value: "{emoji} *Alerta de Proceso*\n\n📝 *Alerta:* {alert_name}\n📋 *Tipo:* {alert_type}\n⚙️ *Estado:* {status}",
    
    NotificationType.CHATBOT_EVENT.value: "{emoji} *Evento del Chatbot*\n\n📝 *Evento:* {event_name}\n📋 *Tipo:* {event_type}\n🤖 *Estado:* {status}",
    NotificationType.CHATBOT_ALERT.value: "{emoji} *Alerta del Chatbot*\n\n📝 *Alerta:* {alert_name}\n📋 *Tipo:* {alert_type}\n🤖 *Estado:* {status}",
    NotificationType.CHATBOT_ERROR.value: "{emoji} *Error del Chatbot*\n\n📝 *Tipo de Error:* {error_type}\n💬 *Mensaje:* {error_message}"
}

# Configuración de reintentos por tipo de notificación
NOTIFICATION_RETRIES: Dict[str, int] = {
    NotificationType.SYSTEM_ALERT.value: 3,
    NotificationType.SYSTEM_ERROR.value: 3,
    NotificationType.SYSTEM_EVENT.value: 1,
    
    NotificationType.BUSINESS_ALERT.value: 3,
    NotificationType.BUSINESS_EVENT.value: 1,
    NotificationType.PAYMENT.value: 3,
    NotificationType.PLACEMENT.value: 3,
    
    NotificationType.USER_EVENT.value: 1,
    NotificationType.USER_ALERT.value: 2,
    
    NotificationType.SECURITY_ALERT.value: 3,
    NotificationType.SECURITY_EVENT.value: 2,
    
    NotificationType.PERFORMANCE_ALERT.value: 2,
    NotificationType.METRICS.value: 1,
    
    NotificationType.PROCESS_EVENT.value: 1,
    NotificationType.PROCESS_ALERT.value: 2,
    
    NotificationType.CHATBOT_EVENT.value: 1,
    NotificationType.CHATBOT_ALERT.value: 2,
    NotificationType.CHATBOT_ERROR.value: 3
}

# Configuración de timeouts por tipo de notificación (en segundos)
NOTIFICATION_TIMEOUTS: Dict[str, int] = {
    NotificationType.SYSTEM_ALERT.value: 30,
    NotificationType.SYSTEM_ERROR.value: 30,
    NotificationType.SYSTEM_EVENT.value: 10,
    
    NotificationType.BUSINESS_ALERT.value: 30,
    NotificationType.BUSINESS_EVENT.value: 10,
    NotificationType.PAYMENT.value: 30,
    NotificationType.PLACEMENT.value: 30,
    
    NotificationType.USER_EVENT.value: 10,
    NotificationType.USER_ALERT.value: 20,
    
    NotificationType.SECURITY_ALERT.value: 30,
    NotificationType.SECURITY_EVENT.value: 20,
    
    NotificationType.PERFORMANCE_ALERT.value: 20,
    NotificationType.METRICS.value: 10,
    
    NotificationType.PROCESS_EVENT.value: 10,
    NotificationType.PROCESS_ALERT.value: 20,
    
    NotificationType.CHATBOT_EVENT.value: 10,
    NotificationType.CHATBOT_ALERT.value: 20,
    NotificationType.CHATBOT_ERROR.value: 30
} 