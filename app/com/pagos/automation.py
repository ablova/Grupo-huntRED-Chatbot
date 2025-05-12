import stripe
from django.conf import settings
from app.models import Payment

class PaymentAutomation:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
    def create_payment_intent(self, amount, currency):
        """
        Crea un intento de pago.
        
        Args:
            amount: Monto en centavos
            currency: Código de moneda
            
        Returns:
            Dict con detalles del intento
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                automatic_payment_methods={'enabled': True}
            )
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'id': intent.id
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    def process_payment(self, payment_id, amount):
        """
        Procesa un pago y actualiza el estado.
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.status = 'processed'
            payment.amount = amount
            payment.processed_at = timezone.now()
            payment.save()
            return True
        except Payment.DoesNotExist:
            return False
