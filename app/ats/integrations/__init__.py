# app/ats/integrations/__init__.py
"""Módulo de integraciones."""

from .models import Integration, IntegrationConfig, IntegrationLog
from .serializers import (
    IntegrationSerializer,
    IntegrationConfigSerializer,
    IntegrationLogSerializer
)
from .views import (
    IntegrationViewSet,
    IntegrationConfigViewSet,
    IntegrationLogViewSet
)
from .permissions import (
    IsIntegrationOwner,
    IsIntegrationConfigOwner,
    IsIntegrationLogOwner
)
from .exceptions import (
    IntegrationError,
    IntegrationNotFound,
    IntegrationConfigError,
    WebhookError
)
from .constants import (
    INTEGRATION_TYPES,
    EVENT_TYPES,
    INTEGRATION_STATUS,
    DEFAULT_CONFIGS
)
from .utils import (
    log_integration_event,
    format_webhook_payload,
    parse_webhook_payload,
    get_integration_config,
    set_integration_config
)
from .channels.linkedin.channel import LinkedInChannel
from .services import (
    EmailService,
    SMSService,
    WhatsAppService,
    TelegramMessageService,
    MessengerMessageService,
    InstagramMessageService,
    SlackMessageService
)
from app.ats.integrations.matchmaking.service import EnhancedMatchmakingService as MatchmakingService
from app.ats.chatbot.core.chatbot import ChatBotHandler as ChatbotService

__all__ = [
    'Integration',
    'IntegrationConfig',
    'IntegrationLog',
    'IntegrationSerializer',
    'IntegrationConfigSerializer',
    'IntegrationLogSerializer',
    'IntegrationViewSet',
    'IntegrationConfigViewSet',
    'IntegrationLogViewSet',
    'IsIntegrationOwner',
    'IsIntegrationConfigOwner',
    'IsIntegrationLogOwner',
    'IntegrationError',
    'IntegrationNotFound',
    'IntegrationConfigError',
    'WebhookError',
    'INTEGRATION_TYPES',
    'EVENT_TYPES',
    'INTEGRATION_STATUS',
    'DEFAULT_CONFIGS',
    'log_integration_event',
    'format_webhook_payload',
    'parse_webhook_payload',
    'get_integration_config',
    'set_integration_config',
    'LinkedInChannel',
    'EmailService',
    'SMSService',
    'WhatsAppService',
    'TelegramMessageService',
    'MessengerMessageService',
    'InstagramMessageService',
    'SlackMessageService',
    'MatchmakingService',
    'ChatbotService'
] 