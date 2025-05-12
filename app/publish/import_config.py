from typing import Any, Callable
from app.import_config import register_module

# Register Publish modules at startup
register_module('telegram_publisher', 'app.publish.integrations.telegram.TelegramPublisher')
register_module('slack_publisher', 'app.publish.integrations.slack.SlackPublisher')
register_module('instagram_publisher', 'app.publish.integrations.instagram.InstagramPublisher')
register_module('whatsapp_publisher', 'app.publish.integrations.whatsapp.WhatsAppPublisher')
register_module('email_publisher', 'app.publish.integrations.email.EmailPublisher')
register_module('publisher_manager', 'app.publish.publisher_manager.PublisherManager')
register_module('publish_scheduler', 'app.publish.publish_scheduler.PublishScheduler')
register_module('content_formatter', 'app.publish.content_formatter.ContentFormatter')

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
