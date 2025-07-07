"""
huntRED® Payroll System - Sistema de Administración de Nómina Inteligente
Módulo independiente para gestión de nómina con WhatsApp dedicado por cliente
"""

# ============================================================================
# VERSION Y METADATA
# ============================================================================
__version__ = '1.0.0'
__author__ = 'huntRED Team'
__description__ = 'Sistema de nómina conversacional con WhatsApp dedicado por cliente'

# ============================================================================
# CONFIGURACIÓN DEFAULT
# ============================================================================
default_app_config = 'app.payroll.apps.PayrollConfig'

# ============================================================================
# CONSTANTES CRÍTICAS
# ============================================================================

# Estados de nómina
PAYROLL_STATUSES = [
    ('draft', 'Borrador'),
    ('calculated', 'Calculada'),
    ('approved', 'Aprobada'),
    ('disbursed', 'Dispersada'),
    ('cancelled', 'Cancelada'),
]

# Tipos de empleado
EMPLOYEE_TYPES = [
    ('permanent', 'Permanente'),
    ('temporary', 'Temporal'),
    ('contractor', 'Contratista'),
    ('intern', 'Interno'),
]

# Frecuencias de pago
PAYROLL_FREQUENCIES = [
    ('weekly', 'Semanal'),
    ('biweekly', 'Quincenal'),
    ('monthly', 'Mensual'),
    ('bimonthly', 'Bimestral'),
]

# Estados de asistencia
ATTENDANCE_STATUSES = [
    ('present', 'Presente'),
    ('absent', 'Ausente'),
    ('late', 'Tardanza'),
    ('half_day', 'Medio día'),
    ('remote', 'Remoto'),
]

# Tipos de solicitud
REQUEST_TYPES = [
    ('vacation', 'Vacaciones'),
    ('sick_leave', 'Incapacidad'),
    ('personal_leave', 'Permiso personal'),
    ('overtime', 'Horas extra'),
    ('advance', 'Adelanto'),
]

# Estados de solicitud
REQUEST_STATUSES = [
    ('pending', 'Pendiente'),
    ('approved', 'Aprobada'),
    ('rejected', 'Rechazada'),
    ('cancelled', 'Cancelada'),
]

# Roles de usuario
PAYROLL_ROLES = [
    ('employee', 'Empleado'),
    ('supervisor', 'Supervisor'),
    ('hr_admin', 'Administrador RH'),
    ('payroll_admin', 'Administrador Nómina'),
    ('super_admin', 'Super Administrador'),
]

# ============================================================================
# CONFIGURACIÓN DE REVENUE STREAMS - PRICING ESTRATÉGICO 2024
# ============================================================================

# Precios base por empleado/mes - ESTRATEGIA SOSTENIBLE
PAYROLL_PRICING = {
    'starter': {
        'price_per_employee': 35.00,  # USD (equivalente a ~630 MXN)
        'setup_fee': 2000.00,  # USD - Setup básico
        'min_employees': 10,
        'max_employees': 50,
        'monthly_base_fee': 500.00,  # USD - Costo base mensual
        'features': [
            'basic_whatsapp', 
            'single_country', 
            'basic_reports',
            'attendance_tracking',
            'basic_payroll_calculation',
            'email_support'
        ],
        'target_market': 'Micro-PYMEs (10-50 empleados)',
        'competitive_advantage': 'WhatsApp integrado + IA básica',
        'profit_margin': 0.75,  # 75% margen
        'break_even_employees': 15  # Empleados para break even
    },
    'professional': {
        'price_per_employee': 28.00,  # USD (equivalente a ~504 MXN)
        'setup_fee': 5000.00,  # USD - Setup completo
        'min_employees': 51,
        'max_employees': 500,
        'monthly_base_fee': 800.00,  # USD - Costo base mensual
        'features': [
            'advanced_whatsapp', 
            'multi_country', 
            'api_access', 
            'overtime_management',
            'advanced_analytics',
            'chat_support',
            'predictive_analytics',
            'sentiment_analysis',
            'benefits_optimization',
            'compliance_automation',
            'workflow_automation'
        ],
        'target_market': 'PYMEs medianas (51-500 empleados)',
        'competitive_advantage': 'IA avanzada + multi-país + analytics + compliance auto',
        'profit_margin': 0.80,  # 80% margen
        'break_even_employees': 35  # Empleados para break even
    },
    'enterprise': {
        'price_per_employee': 22.00,  # USD (equivalente a ~396 MXN)
        'setup_fee': 15000.00,  # USD - Setup enterprise
        'min_employees': 501,
        'max_employees': None,
        'monthly_base_fee': 1500.00,  # USD - Costo base mensual
        'features': [
            'full_whatsapp', 
            'unlimited_countries', 
            'ai_analytics', 
            'custom_integrations',
            'dedicated_support',
            'compliance_automation',
            'workflow_automation',
            'advanced_dashboard',
            'white_label_options',
            'custom_development',
            'priority_support'
        ],
        'target_market': 'Grandes empresas (500+ empleados)',
        'competitive_advantage': 'Compliance automático + workflows + dashboard avanzado + soporte dedicado',
        'profit_margin': 0.85,  # 85% margen
        'break_even_employees': 80  # Empleados para break even
    }
}

# Servicios premium - STREAMS DE REVENUE ADICIONALES
PREMIUM_SERVICES = {
    'bank_disbursement': {
        'fee_percentage': 0.8,  # 0.8% del monto (más competitivo que 1.2%)
        'min_amount': 500000,  # MXN
        'sla_hours': 2,
        'target_market': 'Empresas con nómina >500K MXN',
        'profit_margin': 0.90  # 90% margen
    },
    'tax_stamping': {
        'fee_per_receipt': 10.00,  # MXN por recibo (más competitivo que 15 MXN)
        'volume_discount': True,
        'bulk_discounts': {
            '1000+': 0.15,  # 15% descuento
            '5000+': 0.25,  # 25% descuento
            '10000+': 0.35  # 35% descuento
        },
        'profit_margin': 0.85  # 85% margen
    },
    'salary_advance': {
        'fee_per_transaction': 30.00,  # MXN (más competitivo que 50 MXN)
        'monthly_fee': 85.00,  # MXN
        'max_percentage': 40,  # % del sueldo neto
        'target_market': 'Empleados con necesidades de liquidez',
        'profit_margin': 0.75  # 75% margen
    },
    'analytics_pro': {
        'price_per_employee': 8.00,  # USD/mes (más accesible)
        'features': [
            'predictive_analytics', 
            'benchmarking', 
            'custom_reports',
            'sentiment_analysis',
            'benefits_optimization',
            'turnover_prediction',
            'performance_analytics',
            'advanced_dashboards'
        ],
        'target_market': 'Empresas que buscan insights avanzados',
        'profit_margin': 0.88  # 88% margen
    },
    'outplacement': {
        'price_per_employee': 1800.00,  # USD (más competitivo)
        'integration_fee': 400.00,  # USD
        'features': [
            'career_coaching',
            'resume_optimization',
            'interview_preparation',
            'job_market_analysis',
            'networking_support'
        ],
        'profit_margin': 0.70  # 70% margen
    },
    'compliance_automation': {
        'price_per_employee': 12.00,  # USD/mes
        'features': [
            'automatic_tax_updates',
            'regulatory_alerts',
            'compliance_reports',
            'audit_trail',
            'legal_document_generation',
            'real_time_validation'
        ],
        'target_market': 'Empresas que requieren compliance automático',
        'profit_margin': 0.82  # 82% margen
    },
    'workflow_automation': {
        'price_per_employee': 10.00,  # USD/mes
        'features': [
            'automated_approvals',
            'smart_notifications',
            'process_optimization',
            'workflow_analytics',
            'custom_workflows',
            'ai_optimization'
        ],
        'target_market': 'Empresas que buscan automatización de procesos',
        'profit_margin': 0.85  # 85% margen
    }
}

# Nuevos servicios de IA y Analytics - ALTO MARGEN
AI_SERVICES = {
    'predictive_analytics': {
        'price_per_employee': 8.00,  # USD/mes
        'features': [
            'turnover_prediction',
            'performance_forecasting',
            'attendance_prediction',
            'anomaly_detection',
            'trend_analysis',
            'risk_assessment'
        ],
        'profit_margin': 0.90  # 90% margen
    },
    'sentiment_analysis': {
        'price_per_employee': 5.00,  # USD/mes
        'features': [
            'employee_satisfaction_monitoring',
            'feedback_analysis',
            'engagement_tracking',
            'mood_analysis',
            'proactive_intervention',
            'real_time_alerts'
        ],
        'profit_margin': 0.92  # 92% margen
    },
    'benefits_optimization': {
        'price_per_employee': 6.00,  # USD/mes
        'features': [
            'benefits_analysis',
            'cost_optimization',
            'employee_preferences',
            'market_comparison',
            'customization_recommendations',
            'savings_tracking'
        ],
        'profit_margin': 0.88  # 88% margen
    }
}

# Servicios de implementación - MARGEN MEDIO-ALTO
IMPLEMENTATION_SERVICES = {
    'basic_setup': {
        'price': 5000.00,  # USD
        'duration': '1-2 semanas',
        'includes': [
            'data_migration',
            'user_training',
            'basic_configuration',
            'go_live_support',
            'whatsapp_setup'
        ],
        'profit_margin': 0.65  # 65% margen
    },
    'standard_setup': {
        'price': 12000.00,  # USD
        'duration': '2-4 semanas',
        'includes': [
            'data_migration',
            'user_training',
            'advanced_configuration',
            'custom_integrations',
            'go_live_support',
            'post_go_live_support',
            'compliance_setup',
            'analytics_setup'
        ],
        'profit_margin': 0.70  # 70% margen
    },
    'enterprise_setup': {
        'price': 35000.00,  # USD
        'duration': '4-8 semanas',
        'includes': [
            'data_migration',
            'user_training',
            'advanced_configuration',
            'custom_integrations',
            'white_label_setup',
            'dedicated_project_manager',
            'go_live_support',
            'post_go_live_support',
            'ongoing_consulting',
            'custom_development',
            'compliance_audit'
        ],
        'profit_margin': 0.75  # 75% margen
    }
}

# Configuración de costos base por empresa
COST_BREAKDOWN = {
    'infrastructure_per_company': {
        'whatsapp_bot': 300.00,  # USD/mes
        'ai_servers': 400.00,    # USD/mes
        'compliance_automation': 200.00,  # USD/mes
        'support': 150.00,       # USD/mes
        'backup_storage': 100.00,  # USD/mes
        'total_monthly': 1150.00  # USD/mes
    },
    'setup_costs': {
        'basic': 1500.00,    # USD
        'standard': 3000.00, # USD
        'enterprise': 8000.00  # USD
    },
    'profit_margins': {
        'starter': 0.75,      # 75% margen
        'professional': 0.80, # 80% margen
        'enterprise': 0.85    # 85% margen
    }
}

# Configuración de descuentos por volumen
VOLUME_DISCOUNTS = {
    'employee_discounts': {
        '100+': 0.05,   # 5% descuento
        '250+': 0.10,   # 10% descuento
        '500+': 0.15,   # 15% descuento
        '1000+': 0.20   # 20% descuento
    },
    'annual_discounts': {
        'annual_payment': 0.10,  # 10% descuento por pago anual
        '2_year_commitment': 0.15,  # 15% descuento por 2 años
        '3_year_commitment': 0.20   # 20% descuento por 3 años
    },
    'addon_discounts': {
        '3_addons': 0.05,   # 5% descuento en add-ons
        '5_addons': 0.10,   # 10% descuento en add-ons
        'all_addons': 0.15  # 15% descuento en todos los add-ons
    }
}

# ============================================================================
# CONFIGURACIÓN DE COMPLIANCE
# ============================================================================

# Países soportados
SUPPORTED_COUNTRIES = {
    'MEX': {
        'name': 'México',
        'currency': 'MXN',
        'uma_daily': 108.57,
        'uma_monthly': 3257.10,
        'required_fields': ['rfc', 'curp', 'nss', 'clabe'],
        'payroll_frequencies': ['weekly', 'biweekly', 'monthly'],
        'overtime_rules': {
            'max_daily': 3,
            'max_weekly': 9,
            'double_time_hours': 9
        }
    }
}

# ============================================================================
# CONFIGURACIÓN DE MENSAJERÍA
# ============================================================================

# Canales soportados
MESSAGING_CHANNELS = [
    ('whatsapp', 'WhatsApp'),
    ('telegram', 'Telegram'),
    ('sms', 'SMS'),
    ('email', 'Email'),
    ('slack', 'Slack'),
    ('teams', 'Microsoft Teams'),
]

# Prioridades de mensaje
MESSAGE_PRIORITIES = [
    ('critical', 'Crítico'),
    ('high', 'Alto'),
    ('normal', 'Normal'),
    ('low', 'Bajo'),
]

# ============================================================================
# EXPORTS
# ============================================================================
__all__ = [
    'PAYROLL_STATUSES',
    'EMPLOYEE_TYPES', 
    'PAYROLL_FREQUENCIES',
    'ATTENDANCE_STATUSES',
    'REQUEST_TYPES',
    'REQUEST_STATUSES',
    'PAYROLL_ROLES',
    'PAYROLL_PRICING',
    'PREMIUM_SERVICES',
    'SUPPORTED_COUNTRIES',
    'MESSAGING_CHANNELS',
    'MESSAGE_PRIORITIES',
] 