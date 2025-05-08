from django.db import models
from django.conf import settings
from .base_integration import BaseIntegration
from app.models import WhatsAppAPI
from app.chatbot.integrations.whatsapp import fetch_whatsapp_user_data


class WhatsAppIntegration(BaseIntegration):
    """
    Integración con WhatsApp
    """
    def __init__(self):
        super().__init__()
        self.whatsapp_api = self._get_whatsapp_api()
        
    def _get_whatsapp_api(self) -> WhatsAppAPI:
        """
        Obtiene la configuración de WhatsApp para la unidad de negocio
        """
        from app.models import BusinessUnit
        business_unit = BusinessUnit.objects.first()  # TODO: Obtener el business unit correcto
        if not business_unit:
            raise ValueError("No se encontró ninguna unidad de negocio")
            
        whatsapp_api = WhatsAppAPI.objects.filter(
            business_unit=business_unit,
            is_active=True
        ).first()
        
        if not whatsapp_api:
            raise ValueError(f"No se encontró configuración de WhatsApp para la unidad de negocio {business_unit.name}")
            
        return whatsapp_api
        
    def register_channel(self, channel_type: str, identifier: str, name: str) -> models.Model:
        """
        Registra un canal de WhatsApp
        """
        from ..models import Channel, ChannelCredential
        
        channel = Channel.objects.create(
            type=channel_type,
            identifier=identifier,
            name=name,
            active=True
        )
        
        ChannelCredential.objects.create(
            channel=channel,
            api_key=self.whatsapp_api.api_token,
            webhook_url=f"{settings.SITE_URL}/api/whatsapp/webhook/"
        )
        
        return channel
        
    def validate_channel(self, channel: models.Model) -> bool:
        """
        Valida las credenciales de un canal de WhatsApp
        """
        try:
            # Implementar validación específica para WhatsApp
            return True
        except Exception:
            return False
            
    def get_channel_status(self, channel: models.Model) -> dict:
        """
        Obtiene el estado de un canal de WhatsApp
        """
        try:
            # Implementar obtención de estado específico para WhatsApp
            return {
                'status': 'active',
                'member_count': 500,
                'last_message_date': '2025-05-07'
            }
        except Exception:
            return {'status': 'inactive'}
            
    def register():
        """
        Registra la integración de WhatsApp
        """
        from ..integrations import register_integration
        register_integration('whatsapp', WhatsAppIntegration())
