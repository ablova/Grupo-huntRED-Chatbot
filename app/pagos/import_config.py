from typing import Any, Callable
from app.import_config import register_module

# Register Pagos modules at startup
register_module('payment_processor', 'app.pagos.payment_processor.PaymentProcessor')
register_module('stripe_gateway', 'app.pagos.gateways.stripe_gateway.StripeGateway')
register_module('payment_validator', 'app.pagos.payment_validator.PaymentValidator')
register_module('subscription_manager', 'app.pagos.subscription_manager.SubscriptionManager')
register_module('discount_calculator', 'app.pagos.discount_calculator.DiscountCalculator')
register_module('payment_history', 'app.pagos.payment_history.PaymentHistory')
register_module('webhook_handler', 'app.pagos.webhook_handler.WebhookHandler')
register_module('refund_processor', 'app.pagos.refund_processor.RefundProcessor')

def get_payment_processor():
    """Get PaymentProcessor instance."""
    from app.pagos.payment_processor import PaymentProcessor
    return PaymentProcessor

def get_stripe_gateway():
    """Get StripeGateway instance."""
    from app.pagos.gateways.stripe_gateway import StripeGateway
    return StripeGateway

def get_payment_validator():
    """Get PaymentValidator instance."""
    from app.pagos.payment_validator import PaymentValidator
    return PaymentValidator

def get_subscription_manager():
    """Get SubscriptionManager instance."""
    from app.pagos.subscription_manager import SubscriptionManager
    return SubscriptionManager

def get_discount_calculator():
    """Get DiscountCalculator instance."""
    from app.pagos.discount_calculator import DiscountCalculator
    return DiscountCalculator

def get_payment_history():
    """Get PaymentHistory instance."""
    from app.pagos.payment_history import PaymentHistory
    return PaymentHistory

def get_webhook_handler():
    """Get WebhookHandler instance."""
    from app.pagos.webhook_handler import WebhookHandler
    return WebhookHandler

def get_refund_processor():
    """Get RefundProcessor instance."""
    from app.pagos.refund_processor import RefundProcessor
    return RefundProcessor
