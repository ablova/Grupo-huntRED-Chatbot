import stripe
from django.conf import settings
from app.models import ApiConfig
from app.com.pagos.gateways.base import PaymentGateway

class StripeGateway(PaymentGateway):
    def __init__(self, business_unit=None):
        """
        Inicializa el gateway de Stripe.
        
        Args:
            business_unit: Unidad de negocio asociada (opcional)
        """
        super().__init__(business_unit)
        self.api = self._get_api_config()
    
    def _get_api_config(self):
        """Obtiene la configuración de API de Stripe"""
        config = ApiConfig.get_config('stripe', self.business_unit)
        if config:
            stripe.api_key = config.api_key
            stripe.api_version = config.additional_settings.get('version', '2023-10-16')
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe.api_version = '2023-10-16'
        return stripe
    
    def create_payment(self, amount: float, currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """
        Crea un nuevo pago en Stripe.
        
        Args:
            amount: Monto del pago
            currency: Código de moneda
            description: Descripción del pago
            **kwargs: Parámetros adicionales
                - customer: ID del cliente en Stripe (opcional)
                - metadata: Metadatos adicionales (opcional)
        """
        try:
            payment_intent = self.api.PaymentIntent.create(
                amount=int(amount * 100),  # Convertir a centavos
                currency=currency.lower(),
                description=description,
                customer=kwargs.get('customer'),
                metadata=kwargs.get('metadata', {})
            )
            return {
                'success': True,
                'id': payment_intent.id,
                'client_secret': payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment(self, payment_id: str, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta un pago existente en Stripe.
        
        Args:
            payment_id: ID del pago
            **kwargs: Parámetros adicionales
                - payment_method: Método de pago (opcional)
        """
        try:
            payment_intent = self.api.PaymentIntent.retrieve(payment_id)
            if kwargs.get('payment_method'):
                payment_intent = self.api.PaymentIntent.modify(
                    payment_id,
                    payment_method=kwargs['payment_method']
                )
            return {
                'success': True,
                'status': payment_intent.status
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payout(self, payments: list, **kwargs) -> Dict[str, Any]:
        """
        Crea un payout para múltiples pagos en Stripe.
        
        Args:
            payments: Lista de pagos a incluir
            **kwargs: Parámetros adicionales
        """
        try:
            payout = self.api.Payout.create(
                amount=int(sum(p['amount'] for p in payments) * 100),
                currency=payments[0]['currency'].lower(),
                description=kwargs.get('description', 'Payout from huntRED'),
                metadata=kwargs.get('metadata', {})
            )
            return {
                'success': True,
                'id': payout.id,
                'status': payout.status
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_webhook(self, request_body: Dict[str, Any]) -> bool:
        """
        Verifica la validez de un webhook de Stripe.
        
        Args:
            request_body: Cuerpo de la solicitud webhook
        """
        try:
            event = self.api.Webhook.construct_event(
                request_body['data'],
                request_body['signature'],
                settings.STRIPE_WEBHOOK_SECRET
            )
            return True
        except ValueError:
            return False
        except stripe.error.SignatureVerificationError:
            return False
