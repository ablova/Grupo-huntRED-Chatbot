import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class StripeGateway:
    """
    Gateway for handling payments through Stripe.
    """
    def __init__(self):
        """
        Initialize Stripe API with secret key from settings.
        """
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.currency = settings.STRIPE_CURRENCY or 'usd'
        logger.info("StripeGateway initialized")

    def create_payment_intent(self, amount: float, description: str, metadata: dict = None) -> dict:
        """
        Create a payment intent for a given amount and description.

        Args:
            amount (float): The amount to charge.
            description (str): Description of the payment.
            metadata (dict, optional): Additional metadata for the payment intent.

        Returns:
            dict: Stripe Payment Intent object.
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=self.currency,
                description=description,
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            logger.info(f"Payment intent created: {intent.id}")
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            raise ValidationError(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {str(e)}")
            raise ValidationError(f"Error processing payment: {str(e)}")

    def confirm_payment_intent(self, payment_intent_id: str) -> dict:
        """
        Confirm a payment intent.

        Args:
            payment_intent_id (str): The ID of the payment intent to confirm.

        Returns:
            dict: Confirmed Stripe Payment Intent object.
        """
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
            logger.info(f"Payment intent confirmed: {intent.id}")
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment intent: {str(e)}")
            raise ValidationError(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error confirming payment intent: {str(e)}")
            raise ValidationError(f"Error confirming payment: {str(e)}")

    def refund_payment(self, charge_id: str, amount: float = None) -> dict:
        """
        Refund a payment.

        Args:
            charge_id (str): The ID of the charge to refund.
            amount (float, optional): The amount to refund. If None, full refund.

        Returns:
            dict: Stripe Refund object.
        """
        try:
            refund_data = {'charge': charge_id}
            if amount:
                refund_data['amount'] = int(amount * 100)  # Convert to cents
            refund = stripe.Refund.create(**refund_data)
            logger.info(f"Refund processed: {refund.id}")
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing refund: {str(e)}")
            raise ValidationError(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing refund: {str(e)}")
            raise ValidationError(f"Error processing refund: {str(e)}")

    def get_payment_status(self, payment_intent_id: str) -> str:
        """
        Get the status of a payment intent.

        Args:
            payment_intent_id (str): The ID of the payment intent.

        Returns:
            str: Status of the payment intent.
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            logger.info(f"Payment status retrieved for intent: {intent.id}")
            return intent.status
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment status: {str(e)}")
            raise ValidationError(f"Stripe error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving payment status: {str(e)}")
            raise ValidationError(f"Error retrieving payment status: {str(e)}")
