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
    from . import whatsapp, telegram
    
    # Registrar integraciones
    register_integration('whatsapp', whatsapp.WhatsAppIntegration())
    register_integration('telegram', telegram.TelegramIntegration())

def initialize_integrations():
    """
    Inicializa todas las integraciones
    """
    for integration in _integrations.values():
        integration.initialize()
