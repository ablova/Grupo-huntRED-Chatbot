"""
Integraciones para publicación y campañas digitales
"""

_integrations = {}

def register_integration(name: str, integration):
    """
    Registra una nueva integración
    """
    _integrations[name] = integration
    
    # Registrar señales y webhook
    integration.register_signals()
    integration.register_webhook()
    
    # Inicializar configuración
    integration.initialize()

def get_integration(name: str):
    """
    Obtiene una integración registrada
    """
    return _integrations.get(name)

def register_integrations():
    """
    Registra todas las integraciones disponibles
    """
    # Evitar importaciones circulares y problemas de carga de apps
    from django.apps import apps
    if not apps.ready:
        return
        
    from app.publish.integrations import whatsapp, telegram
    from app.publish.integrations.linkedin import LinkedInIntegration
    
    # Registrar integraciones
    register_integration('whatsapp', whatsapp.WhatsAppIntegration())
    register_integration('telegram', telegram.TelegramIntegration())
    register_integration('linkedin', LinkedInIntegration())

def initialize_integrations():
    """
    Inicializa todas las integraciones
    """
    for integration in _integrations.values():
        integration.initialize()
