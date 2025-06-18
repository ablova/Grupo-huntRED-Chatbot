# app/ats/integrations/notifications/channels/__init__.py
"""Notification channels package.

Provides utility to retrieve channel classes by name. Channels should implement
`send_notification` and inherit from `BaseNotificationChannel`.
"""
from importlib import import_module
from functools import lru_cache
from typing import Type, Optional

from app.ats.integrations.notifications.core.base import BaseNotificationChannel

_CHANNEL_PATHS = {
    'telegram': 'app.ats.integrations.notifications.channels.telegram.TelegramNotificationChannel',
    'whatsapp': 'app.ats.integrations.notifications.channels.whatsapp.WhatsAppNotificationChannel',
    'slack': 'app.ats.integrations.notifications.channels.slack.SlackNotificationChannel',
    'messenger': 'app.ats.integrations.notifications.channels.messenger.MessengerNotificationChannel',
    'instagram': 'app.ats.integrations.notifications.channels.instagram.InstagramNotificationChannel',
    'x': 'app.ats.integrations.notifications.channels.x.XNotificationChannel',
    'linkedin': 'app.ats.integrations.notifications.channels.linkedin.LinkedInNotificationChannel',
    'sms': 'app.ats.integrations.notifications.channels.sms.SMSNotificationChannel',
}

@lru_cache(maxsize=None)
def _import_class(path: str) -> Type[BaseNotificationChannel]:
    """Dynamically import a class given its full dotted path."""
    module_path, class_name = path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, class_name)

def get_channel_class(channel_name: str):
    """Return the channel class for the given name, or None if not found."""
    path = _CHANNEL_PATHS.get(channel_name.lower())
    if not path:
        return None
    try:
        return _import_class(path)
    except Exception:
        # Import failed – swallow but return None to avoid propagating.
        return None

# ---------------------------------------------------------------------------
# Backward-compatibility: legacy code may still import `get_channel` expecting
# the previous behaviour of returning the class. Keep an alias so that old
# imports do not break while migrations complete.
# ---------------------------------------------------------------------------
get_channel = get_channel_class

