from django.conf import settings
from django.db import models
from app.ats.publish.integrations.base_integration import BaseIntegration
from app.models import TelegramAPI


class TelegramIntegration(BaseIntegration):
    """
    Integración con Telegram
    """
    def __init__(self):
        super().__init__()
        self.telegram_api = TelegramAPI.objects.filter(is_active=True).first()
        if not self.telegram_api:
            raise ValueError("No hay configuración activa de Telegram")
        self.bot_token = self.telegram_api.bot_token
        
    def register_channel(self, channel_type: str, identifier: str, name: str) -> models.Model:
        """
        Registra un canal de Telegram
        """
        from app.ats.publish.models import Channel, ChannelCredential
        
        channel = Channel.objects.create(
            type=channel_type,
            identifier=identifier,
            name=name,
            active=True
        )
        
        ChannelCredential.objects.create(
            channel=channel,
            api_key=self.bot_token,
            webhook_url=f"{settings.SITE_URL}/api/telegram/webhook/"
        )
        
        return channel
        
    def validate_channel(self, channel: models.Model) -> bool:
        """
        Valida las credenciales de un canal de Telegram
        """
        try:
            # Implementar validación específica para Telegram
            return True
        except Exception:
            return False
            
    def get_channel_status(self, channel: models.Model) -> dict:
        """
        Obtiene el estado de un canal de Telegram
        """
        try:
            # Implementar obtención de estado específico para Telegram
            return {
                'status': 'active',
                'subscriber_count': 1000,
                'last_post_date': '2025-05-07'
            }
        except Exception:
            return {'status': 'inactive'}
            
    def register():
        """
        Registra la integración de Telegram
        """
        from app.ats.publish.integrations import register_integration
        register_integration('telegram', TelegramIntegration())
