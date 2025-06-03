from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.http import HttpResponse
from app.models import BusinessUnit

class BaseWebhook(ABC):
    """
    Clase base para todos los webhooks de integración
    """
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit

    @abstractmethod
    async def handle_webhook(self, request: Any) -> HttpResponse:
        """
        Maneja una solicitud de webhook
        """
        pass

    @abstractmethod
    async def verify_webhook(self, request: Any) -> bool:
        """
        Verifica la autenticidad del webhook
        """
        pass

    @abstractmethod
    async def process_webhook_data(self, data: Dict[str, Any]) -> bool:
        """
        Procesa los datos del webhook
        """
        pass

    async def log_webhook_event(self, event_type: str, payload: Dict[str, Any], error: Optional[str] = None) -> None:
        """
        Registra un evento de webhook
        """
        from app.ats.integrations.utils import log_integration_event
        await log_integration_event(
            integration=self.business_unit,
            event_type='WEBHOOK',
            payload={
                'type': event_type,
                'data': payload
            },
            error=error
        ) 