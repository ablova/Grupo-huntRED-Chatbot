"""
Módulo de menús para las integraciones
"""

from .base import BaseMenu
from .whatsapp import WhatsAppMenu
from .telegram import TelegramMenu
from .options import MENU_OPTIONS_BY_BU, EVALUATIONS_MENU

__all__ = [
    'BaseMenu',
    'WhatsAppMenu',
    'TelegramMenu',
    'MENU_OPTIONS_BY_BU',
    'EVALUATIONS_MENU'
] 