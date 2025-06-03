# /home/pablo/app/pagos/import_config.py
#
# NOTA: Este archivo está obsoleto y se mantiene temporalmente para compatibilidad.
# El registro de módulos ahora es gestionado automáticamente por ModuleRegistry en app/module_registry.py
#
# De acuerdo con las reglas globales de Grupo huntRED®:
# - No Redundancies: Se evitan duplicaciones en el código
# - Code Consistency: Se siguen estándares de Django
# - Modularity: Se usa código modular y reusable

# Manteniendo estas funciones temporalmente para compatibilidad

def get_payment_processor():
    """Get PaymentProcessor instance."""
{{ ... }}

def get_payment_validator():
    """Get PaymentValidator instance."""
    from app.ats.pagos.payment_validator import PaymentValidator
    return PaymentValidator

def get_subscription_manager():
    """Get SubscriptionManager instance."""
    from app.ats.pagos.subscription_manager import SubscriptionManager
    return SubscriptionManager
{{ ... }}
def get_discount_calculator():
    """Get DiscountCalculator instance."""
    from app.ats.pagos.discount_calculator import DiscountCalculator
    return DiscountCalculator

def get_payment_history():
    """Get PaymentHistory instance."""
    from app.ats.pagos.payment_history import PaymentHistory
    return PaymentHistory

def get_webhook_handler():
    """Get WebhookHandler instance."""
    from app.ats.pagos.webhook_handler import WebhookHandler
    return WebhookHandler

def get_refund_processor():
    """Get RefundProcessor instance."""
    from app.ats.pagos.refund_processor import RefundProcessor
    return RefundProcessor
