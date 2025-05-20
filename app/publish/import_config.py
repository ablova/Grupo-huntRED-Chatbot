# /home/pablo/app/publish/import_config.py
#
# NOTA: Este archivo está obsoleto y se mantiene temporalmente para compatibilidad.
# El registro de módulos ahora es gestionado automáticamente por ModuleRegistry en app/module_registry.py
#
# Siguiendo las reglas globales de Grupo huntRED®:
# - No Redundancies: Verificar antes de añadir funciones que no existan en el código
# - Modularity: Escribir código modular, reutilizable; evitar duplicar funcionalidad
# - Code Consistency: Seguir estándares de Django

# Los módulos de Publish deben ser importados directamente:
# from app.publish.integrations.telegram import TelegramPublisher
# from app.publish.integrations.whatsapp import WhatsAppPublisher
# from app.publish.publisher_manager import PublisherManager
# etc.


def get_telegram_publisher():
    """Get TelegramPublisher instance."""
    from app.publish.integrations.telegram import TelegramPublisher
    return TelegramPublisher

def get_slack_publisher():
    """Get SlackPublisher instance."""
    from app.publish.integrations.slack import SlackPublisher
    return SlackPublisher

def get_instagram_publisher():
    """Get InstagramPublisher instance."""
    from app.publish.integrations.instagram import InstagramPublisher
    return InstagramPublisher

def get_whatsapp_publisher():
    """Get WhatsAppPublisher instance."""
    from app.publish.integrations.whatsapp import WhatsAppPublisher
    return WhatsAppPublisher

def get_email_publisher():
    """Get EmailPublisher instance."""
    from app.publish.integrations.email import EmailPublisher
    return EmailPublisher

def get_publisher_manager():
    """Get PublisherManager instance."""
    from app.publish.publisher_manager import PublisherManager
    return PublisherManager

def get_publish_scheduler():
    """Get PublishScheduler instance."""
    from app.publish.publish_scheduler import PublishScheduler
    return PublishScheduler

def get_content_formatter():
    """Get ContentFormatter instance."""
    from app.publish.content_formatter import ContentFormatter
    return ContentFormatter
