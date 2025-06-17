"""
Manejador de notificaciones para Telegram.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.conf import settings
from telegram import Bot, ParseMode
from telegram.error import TelegramError

from app.models import BusinessUnit, TelegramAPI
from app.ats.integrations.notifications.core.base import BaseNotificationChannel

logger = logging.getLogger('chatbot')

class TelegramNotificationChannel(BaseNotificationChannel):
    """Canal de notificaciones para Telegram."""
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        self.telegram_api = TelegramAPI.objects.filter(business_unit=business_unit, is_active=True).first()
        if not self.telegram_api:
            raise ValueError(f"No hay configuración activa de Telegram para la unidad de negocio {business_unit.name}")
        self.bot = Bot(token=self.telegram_api.bot_token)
        self.channel_id = self.telegram_api.chat_id
    
    async def send_notification(
        self,
        message: str,
        options: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> Dict[str, Any]:
        """
        Envía una notificación a través de Telegram.
        
        Args:
            message: Mensaje a enviar
            options: Opciones adicionales (botones, etc.)
            priority: Prioridad de la notificación
        
        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Formatear el mensaje según la prioridad
            formatted_message = self._format_message(message, priority)
            
            # Enviar el mensaje
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=formatted_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            
            return {
                'success': True,
                'channel': 'telegram',
                'timestamp': datetime.now().isoformat()
            }
            
        except TelegramError as e:
            logger.error(f"Error enviando notificación a Telegram: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'channel': 'telegram'
            }
    
    def _format_message(self, message: str, priority: int) -> str:
        """
        Formatea el mensaje según la prioridad.
        
        Args:
            message: Mensaje original
            priority: Nivel de prioridad (0-5)
        
        Returns:
            Mensaje formateado
        """
        if priority >= 4:
            return f"🚨 <b>URGENTE</b>\n\n{message}"
        elif priority >= 2:
            return f"⚠️ <b>Importante</b>\n\n{message}"
        else:
            return message 