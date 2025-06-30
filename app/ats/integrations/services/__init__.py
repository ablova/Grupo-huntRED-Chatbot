# app/ats/integrations/services/__init__.py
from app.ats.integrations.services.base import (
    UserDataFetcher,
    WhatsAppUserDataFetcher,
    TelegramUserDataFetcher,
    MessengerUserDataFetcher,
    InstagramUserDataFetcher,
    SlackUserDataFetcher,
    Button,
    apply_rate_limit,
    get_business_unit,
    run_async,
    reset_chat_state
)

from app.ats.integrations.services.message import (
    MessageService,
    WhatsAppMessageService,
    TelegramMessageService,
    MessengerMessageService,
    InstagramMessageService,
    SlackMessageService
)

from app.ats.integrations.services.menu import (
    MenuSystem,
    MenuItem,
    get_menus,
    get_available_assessments as get_menu_options,
    get_available_assessments,
    get_assessment_handler,
    menu_system as MENUS
)

from app.ats.integrations.services.assessment import (
    Assessment,
    AssessmentService,
    assessment_service
)

from app.ats.integrations.services.gamification import (
    Badge,
    GamificationService,
    gamification_service
)
from app.ats.integrations.services.gamification.achievement import Achievement

from app.ats.integrations.services.email import (
    EmailService,
    email_service
)

__all__ = [
    # Base
    'UserDataFetcher',
    'WhatsAppUserDataFetcher',
    'TelegramUserDataFetcher',
    'MessengerUserDataFetcher',
    'InstagramUserDataFetcher',
    'SlackUserDataFetcher',
    'Button',
    'apply_rate_limit',
    'get_business_unit',
    'run_async',
    'reset_chat_state',

    # Message
    'MessageService',
    'WhatsAppMessageService',
    'TelegramMessageService',
    'MessengerMessageService',
    'InstagramMessageService',
    'SlackMessageService',

    # Menu
    'MenuOption',
    'DynamicMenu',
    'get_menu',
    'get_menu_options',
    'MENUS',

    # Assessment
    'Assessment',
    'AssessmentService',
    'assessment_service',

    # Gamification
    'Achievement',
    'Badge',
    'GamificationService',
    'gamification_service',

    # Email
    'EmailService',
    'email_service'
] 