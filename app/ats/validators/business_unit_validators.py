from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import json
import re

class BusinessUnitValidator:
    """Validador para las configuraciones de BusinessUnit."""
    
    @staticmethod
    def validate_settings(settings):
        """Valida la configuración general."""
        required_sections = ['general', 'notifications', 'security', 'branding']
        
        # Verificar secciones requeridas
        for section in required_sections:
            if section not in settings:
                raise ValidationError(_(f'Sección {section} es requerida en settings'))
        
        # Validar configuración general
        general = settings['general']
        if not isinstance(general.get('timezone'), str):
            raise ValidationError(_('Timezone debe ser una cadena de texto'))
        if not isinstance(general.get('language'), str):
            raise ValidationError(_('Language debe ser una cadena de texto'))
        if not isinstance(general.get('currency'), str):
            raise ValidationError(_('Currency debe ser una cadena de texto'))
        
        # Validar notificaciones
        notifications = settings['notifications']
        if not isinstance(notifications.get('email_enabled'), bool):
            raise ValidationError(_('email_enabled debe ser booleano'))
        if not isinstance(notifications.get('sms_enabled'), bool):
            raise ValidationError(_('sms_enabled debe ser booleano'))
        
        # Validar seguridad
        security = settings['security']
        password_policy = security.get('password_policy', {})
        if not isinstance(password_policy.get('min_length'), int):
            raise ValidationError(_('min_length debe ser un número entero'))
        
        return True
    
    @staticmethod
    def validate_integrations(integrations):
        """Valida las configuraciones de integración."""
        valid_platforms = ['whatsapp', 'telegram', 'messenger', 'instagram', 
                         'wordpress', 'linkedin', 'indeed', 'glassdoor']
        
        for platform, config in integrations.items():
            if platform not in valid_platforms:
                raise ValidationError(_(f'Plataforma {platform} no válida'))
            
            if not isinstance(config.get('enabled'), bool):
                raise ValidationError(_(f'enabled debe ser booleano para {platform}'))
            
            # Validaciones específicas por plataforma
            if platform == 'whatsapp':
                if config.get('enabled') and not config.get('api_key'):
                    raise ValidationError(_('WhatsApp requiere api_key cuando está habilitado'))
            
            elif platform == 'wordpress':
                if config.get('enabled'):
                    if not config.get('base_url'):
                        raise ValidationError(_('WordPress requiere base_url cuando está habilitado'))
                    if not config.get('auth_token'):
                        raise ValidationError(_('WordPress requiere auth_token cuando está habilitado'))
        
        return True
    
    @staticmethod
    def validate_pricing_config(pricing_config):
        """Valida la configuración de precios."""
        if 'services' not in pricing_config:
            raise ValidationError(_('Sección services es requerida en pricing_config'))
        
        services = pricing_config['services']
        for service_name, service_config in services.items():
            if not isinstance(service_config.get('base_price'), (int, float)):
                raise ValidationError(_(f'base_price debe ser numérico para {service_name}'))
            
            if 'tiers' in service_config:
                for tier_name, tier_config in service_config['tiers'].items():
                    if not isinstance(tier_config.get('price'), (int, float)):
                        raise ValidationError(_(f'price debe ser numérico para tier {tier_name}'))
        
        return True
    
    @staticmethod
    def validate_ats_config(ats_config):
        """Valida la configuración del ATS."""
        required_sections = ['workflow', 'scoring', 'automation', 'templates']
        
        for section in required_sections:
            if section not in ats_config:
                raise ValidationError(_(f'Sección {section} es requerida en ats_config'))
        
        # Validar workflow
        workflow = ats_config['workflow']
        if not isinstance(workflow.get('stages'), list):
            raise ValidationError(_('stages debe ser una lista'))
        if not workflow.get('stages'):
            raise ValidationError(_('stages no puede estar vacío'))
        
        # Validar scoring
        scoring = ats_config['scoring']
        if not isinstance(scoring.get('weights'), dict):
            raise ValidationError(_('weights debe ser un diccionario'))
        
        weights_sum = sum(scoring['weights'].values())
        if not 0.99 <= weights_sum <= 1.01:  # Permitir pequeñas diferencias por redondeo
            raise ValidationError(_('La suma de weights debe ser 1'))
        
        return True
    
    @staticmethod
    def validate_analytics_config(analytics_config):
        """Valida la configuración de analytics."""
        if 'metrics' not in analytics_config:
            raise ValidationError(_('Sección metrics es requerida en analytics_config'))
        
        metrics = analytics_config['metrics']
        for category, category_metrics in metrics.items():
            if not isinstance(category_metrics, dict):
                raise ValidationError(_(f'Métricas de {category} deben ser un diccionario'))
            
            for metric, enabled in category_metrics.items():
                if not isinstance(enabled, bool):
                    raise ValidationError(_(f'Estado de métrica {metric} debe ser booleano'))
        
        return True
    
    @staticmethod
    def validate_learning_config(learning_config):
        """Valida la configuración de learning."""
        if 'courses' not in learning_config:
            raise ValidationError(_('Sección courses es requerida en learning_config'))
        
        courses = learning_config['courses']
        if not isinstance(courses.get('enabled'), bool):
            raise ValidationError(_('courses.enabled debe ser booleano'))
        
        if courses.get('enabled'):
            if not isinstance(courses.get('categories'), list):
                raise ValidationError(_('courses.categories debe ser una lista'))
            
            completion_criteria = courses.get('completion_criteria', {})
            if not isinstance(completion_criteria.get('min_score'), (int, float)):
                raise ValidationError(_('completion_criteria.min_score debe ser numérico'))
        
        return True

def validate_business_unit_config(business_unit):
    """Valida todas las configuraciones de una BusinessUnit."""
    validator = BusinessUnitValidator()
    
    # Validar settings
    validator.validate_settings(business_unit.settings)
    
    # Validar integraciones
    validator.validate_integrations(business_unit.integrations)
    
    # Validar pricing
    validator.validate_pricing_config(business_unit.pricing_config)
    
    # Validar ATS
    validator.validate_ats_config(business_unit.ats_config)
    
    # Validar analytics
    validator.validate_analytics_config(business_unit.analytics_config)
    
    # Validar learning
    validator.validate_learning_config(business_unit.learning_config)
    
    return True 