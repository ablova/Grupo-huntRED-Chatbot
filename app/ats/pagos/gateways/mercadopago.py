import mercadopago
from django.conf import settings
from app.models import ApiConfig
from app.ats.pagos.gateways.base import PaymentGateway
from typing import Dict, Any

class MercadoPagoGateway(PaymentGateway):
    def __init__(self, business_unit=None):
        """
        Inicializa el gateway de MercadoPago.
        
        Args:
            business_unit: Unidad de negocio asociada (opcional)
        """
        super().__init__(business_unit)
        self.api = self._get_api_config()
    
    def _get_api_config(self):
        """Obtiene la configuración de API de MercadoPago"""
        config = ApiConfig.get_config('mercado_pago', self.business_unit)
        if config:
            mp = mercadopago.SDK(config.api_key)
            mp.configure(
                access_token=config.api_key,
                public_key=config.additional_settings.get('public_key')
            )
        else:
            mp = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            mp.configure(
                access_token=settings.MERCADOPAGO_ACCESS_TOKEN,
                public_key=settings.MERCADOPAGO_PUBLIC_KEY
            )
        return mp
    
    def create_payment(self, amount: float, currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """
        Crea un nuevo pago en MercadoPago.
        
        Args:
            amount: Monto del pago
            currency: Código de moneda
            description: Descripción del pago
            **kwargs: Parámetros adicionales
                - email: Email del comprador
                - external_reference: Referencia externa (opcional)
                - metadata: Metadatos adicionales (opcional)
        """
        try:
            payment_data = {
                "transaction_amount": float(amount),
                "currency_id": currency,
                "description": description,
                "payment_method_id": "credit_card",
                "payer": {
                    "email": kwargs.get('email'),
                    "first_name": kwargs.get('first_name', ''),
                    "last_name": kwargs.get('last_name', ''),
                    "identification": {
                        "type": kwargs.get('identification_type', ''),
                        "number": kwargs.get('identification_number', '')
                    }
                },
                "notification_url": settings.MERCADOPAGO_WEBHOOK_URL
            }
            
            if kwargs.get('external_reference'):
                payment_data['external_reference'] = kwargs['external_reference']
            
            if kwargs.get('metadata'):
                payment_data['metadata'] = kwargs['metadata']
            
            payment = self.api.payment.create(payment_data)
            return {
                'success': True,
                'id': payment['response']['id'],
                'status': payment['response']['status'],
                'payment_url': payment['response']['payment_url']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment(self, payment_id: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta un pago existente en MercadoPago.
        
        Args:
            payment_id: ID del pago
            **kwargs: Parámetros adicionales
        """
        try:
            payment = self.api.payment.get(payment_id)
            return {
                'success': True,
                'status': payment['response']['status']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payout(self, payments: list, **kwargs) -> Dict[str, Any]:
        """
        Crea un payout para múltiples pagos en MercadoPago.
        
        Args:
            payments: Lista de pagos a incluir
            **kwargs: Parámetros adicionales
        """
        try:
            payout_data = {
                "amount": sum(p['amount'] for p in payments),
                "currency_id": payments[0]['currency'],
                "description": kwargs.get('description', 'Payout from huntRED'),
                "external_reference": kwargs.get('external_reference', ''),
                "metadata": kwargs.get('metadata', {})
            }
            
            payout = self.api.payout.create(payout_data)
            return {
                'success': True,
                'id': payout['response']['id'],
                'status': payout['response']['status']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook(self, request_body: Dict[str, Any]) -> bool:
        """
        Verifica la validez de un webhook de MercadoPago.
        
        Args:
            request_body: Cuerpo de la solicitud webhook
        """
        try:
            payment = self.api.payment.get(request_body['data']['id'])
            return True
        except Exception:
            return False
