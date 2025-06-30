"""
Configuración de programación para tareas de notificaciones estratégicas.
"""
from celery.schedules import crontab
from django.conf import settings

# Configuración de tareas periódicas para notificaciones estratégicas
STRATEGIC_NOTIFICATION_BEAT_SCHEDULE = {
    # Monitoreo general cada hora
    'monitor-strategic-notifications-hourly': {
        'task': 'monitor_strategic_notifications',
        'schedule': crontab(minute=0, hour='*'),  # Cada hora
        'args': (None,),  # Todas las business units
    },
    
    # Monitoreo de campañas cada 30 minutos
    'monitor-campaign-notifications': {
        'task': 'monitor_campaign_notifications',
        'schedule': crontab(minute='*/30'),  # Cada 30 minutos
        'args': (None,),
    },
    
    # Monitoreo de insights cada 2 horas
    'monitor-insights-notifications': {
        'task': 'monitor_insights_notifications',
        'schedule': crontab(minute=0, hour='*/2'),  # Cada 2 horas
        'args': (None,),
    },
    
    # Monitoreo de métricas críticas cada 15 minutos
    'monitor-critical-metrics-notifications': {
        'task': 'monitor_critical_metrics_notifications',
        'schedule': crontab(minute='*/15'),  # Cada 15 minutos
        'args': (None,),
    },
    
    # Monitoreo de factores del entorno cada 6 horas
    'monitor-environmental-factors-notifications': {
        'task': 'monitor_environmental_factors_notifications',
        'schedule': crontab(minute=0, hour='*/6'),  # Cada 6 horas
        'args': (None,),
    },
    
    # Limpieza de notificaciones antiguas diaria
    'cleanup-old-notifications': {
        'task': 'cleanup_old_notifications',
        'schedule': crontab(minute=0, hour=2),  # 2:00 AM diario
        'args': (30,),  # 30 días
    },
    
    # Reporte de notificaciones semanal
    'generate-notification-report': {
        'task': 'generate_notification_report',
        'schedule': crontab(minute=0, hour=9, day_of_week=1),  # Lunes 9:00 AM
        'args': (None, 7),  # Todas las business units, últimos 7 días
    },
}

# Configuración específica por business unit (si es necesario)
BUSINESS_UNIT_SPECIFIC_SCHEDULES = {
    'tech': {
        'monitor-strategic-notifications-tech': {
            'task': 'monitor_strategic_notifications',
            'schedule': crontab(minute=15, hour='*'),  # Cada hora a los 15 minutos
            'args': ('tech',),
        },
    },
    'finance': {
        'monitor-strategic-notifications-finance': {
            'task': 'monitor_strategic_notifications',
            'schedule': crontab(minute=30, hour='*'),  # Cada hora a los 30 minutos
            'args': ('finance',),
        },
    },
    'healthcare': {
        'monitor-strategic-notifications-healthcare': {
            'task': 'monitor_strategic_notifications',
            'schedule': crontab(minute=45, hour='*'),  # Cada hora a los 45 minutos
            'args': ('healthcare',),
        },
    },
}

# Función para obtener la configuración completa
def get_strategic_notification_schedule():
    """
    Obtiene la configuración completa de programación de notificaciones estratégicas.
    """
    schedule = STRATEGIC_NOTIFICATION_BEAT_SCHEDULE.copy()
    
    # Añadir configuraciones específicas por business unit
    for business_unit, unit_schedules in BUSINESS_UNIT_SPECIFIC_SCHEDULES.items():
        schedule.update(unit_schedules)
    
    return schedule

# Configuración de retry para tareas fallidas
STRATEGIC_NOTIFICATION_RETRY_CONFIG = {
    'max_retries': 3,
    'default_retry_delay': 300,  # 5 minutos
    'retry_backoff': True,
    'retry_jitter': True,
}

# Configuración de timeouts
STRATEGIC_NOTIFICATION_TIMEOUTS = {
    'monitor_strategic_notifications': 300,  # 5 minutos
    'monitor_campaign_notifications': 120,   # 2 minutos
    'monitor_insights_notifications': 180,   # 3 minutos
    'monitor_critical_metrics_notifications': 60,  # 1 minuto
    'monitor_environmental_factors_notifications': 240,  # 4 minutos
    'send_manual_strategic_notification': 60,  # 1 minuto
    'cleanup_old_notifications': 30,  # 30 segundos
    'generate_notification_report': 120,  # 2 minutos
}

# Configuración de prioridades
STRATEGIC_NOTIFICATION_PRIORITIES = {
    'monitor_strategic_notifications': 5,  # Baja prioridad
    'monitor_campaign_notifications': 3,   # Prioridad media
    'monitor_insights_notifications': 4,   # Prioridad media-baja
    'monitor_critical_metrics_notifications': 1,  # Alta prioridad
    'monitor_environmental_factors_notifications': 6,  # Muy baja prioridad
    'send_manual_strategic_notification': 1,  # Alta prioridad
    'cleanup_old_notifications': 9,  # Muy baja prioridad
    'generate_notification_report': 7,  # Baja prioridad
}

# Configuración de rate limiting
STRATEGIC_NOTIFICATION_RATE_LIMITS = {
    'monitor_strategic_notifications': '10/m',  # 10 por minuto
    'monitor_campaign_notifications': '30/m',   # 30 por minuto
    'monitor_insights_notifications': '5/m',    # 5 por minuto
    'monitor_critical_metrics_notifications': '60/m',  # 60 por minuto
    'monitor_environmental_factors_notifications': '2/m',  # 2 por minuto
    'send_manual_strategic_notification': '100/m',  # 100 por minuto
    'cleanup_old_notifications': '1/h',  # 1 por hora
    'generate_notification_report': '1/h',  # 1 por hora
}

# Configuración de notificaciones por tipo
NOTIFICATION_TYPE_CONFIG = {
    'campaign_created': {
        'enabled': True,
        'priority': 'medium',
        'recipients': ['consultants', 'super_admins'],
        'channels': ['email', 'telegram'],
        'cooldown_hours': 1,
    },
    'campaign_launched': {
        'enabled': True,
        'priority': 'high',
        'recipients': ['consultants', 'super_admins'],
        'channels': ['email', 'telegram', 'whatsapp'],
        'cooldown_hours': 1,
    },
    'campaign_performance': {
        'enabled': True,
        'priority': 'high',
        'recipients': ['consultants', 'super_admins'],
        'channels': ['email', 'telegram'],
        'cooldown_hours': 24,
    },
    'sector_opportunity': {
        'enabled': True,
        'priority': 'high',
        'recipients': ['consultants', 'super_admins'],
        'channels': ['email', 'telegram'],
        'cooldown_hours': 12,
    },
    'process_optimization': {
        'enabled': True,
        'priority': 'medium',
        'recipients': ['super_admins'],
        'channels': ['email'],
        'cooldown_hours': 12,
    },
    'strategic_insight': {
        'enabled': True,
        'priority': 'medium',
        'recipients': ['consultants', 'super_admins'],
        'channels': ['email'],
        'cooldown_hours': 24,
    },
    'error_alert': {
        'enabled': True,
        'priority': 'urgent',
        'recipients': ['super_admins'],
        'channels': ['telegram', 'email'],
        'cooldown_hours': 1,
    },
}

# Configuración de thresholds para alertas
NOTIFICATION_THRESHOLDS = {
    'low_success_rate': 0.8,  # 80%
    'low_conversion_rate': 0.2,  # 20%
    'high_growth_threshold': 0.8,  # 80%
    'high_engagement_rate': 0.15,  # 15%
    'low_efficiency_score': 0.7,  # 70%
    'high_automation_impact': 0.5,  # 50%
}

# Configuración de business units específicas
BUSINESS_UNIT_CONFIG = {
    'tech': {
        'enabled': True,
        'notification_frequency': 'high',
        'critical_metrics': ['engagement_rate', 'conversion_rate'],
        'sector_focus': ['technology', 'software', 'ai'],
    },
    'finance': {
        'enabled': True,
        'notification_frequency': 'medium',
        'critical_metrics': ['success_rate', 'roi'],
        'sector_focus': ['finance', 'banking', 'insurance'],
    },
    'healthcare': {
        'enabled': True,
        'notification_frequency': 'medium',
        'critical_metrics': ['compliance_rate', 'success_rate'],
        'sector_focus': ['healthcare', 'pharmaceuticals', 'medical'],
    },
    'retail': {
        'enabled': True,
        'notification_frequency': 'low',
        'critical_metrics': ['conversion_rate', 'engagement_rate'],
        'sector_focus': ['retail', 'ecommerce', 'consumer_goods'],
    },
}

# Función para validar configuración
def validate_notification_config():
    """
    Valida la configuración de notificaciones estratégicas.
    """
    errors = []
    
    # Validar thresholds
    for threshold_name, threshold_value in NOTIFICATION_THRESHOLDS.items():
        if not isinstance(threshold_value, (int, float)) or threshold_value < 0 or threshold_value > 1:
            errors.append(f"Threshold inválido para {threshold_name}: {threshold_value}")
    
    # Validar business units
    for business_unit, config in BUSINESS_UNIT_CONFIG.items():
        if not isinstance(config.get('enabled'), bool):
            errors.append(f"Configuración inválida para business unit {business_unit}")
    
    # Validar tipos de notificación
    for notification_type, config in NOTIFICATION_TYPE_CONFIG.items():
        if not isinstance(config.get('enabled'), bool):
            errors.append(f"Configuración inválida para tipo de notificación {notification_type}")
    
    if errors:
        raise ValueError(f"Errores en configuración de notificaciones: {errors}")
    
    return True

# Función para obtener configuración por business unit
def get_business_unit_notification_config(business_unit: str):
    """
    Obtiene la configuración de notificaciones para una business unit específica.
    """
    return BUSINESS_UNIT_CONFIG.get(business_unit, {
        'enabled': True,
        'notification_frequency': 'medium',
        'critical_metrics': ['success_rate', 'conversion_rate'],
        'sector_focus': [],
    })

# Función para obtener configuración por tipo de notificación
def get_notification_type_config(notification_type: str):
    """
    Obtiene la configuración para un tipo de notificación específico.
    """
    return NOTIFICATION_TYPE_CONFIG.get(notification_type, {
        'enabled': True,
        'priority': 'medium',
        'recipients': ['super_admins'],
        'channels': ['email'],
        'cooldown_hours': 24,
    }) 