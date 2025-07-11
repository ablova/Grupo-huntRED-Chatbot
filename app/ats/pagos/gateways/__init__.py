# app/ats/pagos/gateways/__init__.py
"""
Paquete gateways (legacy).
Este paquete existe para mantener compatibilidad con código legacy
que importa desde app.ats.pagos.gateways.
"""

# Evitamos importaciones circulares no importando directamente desde app.ats.pricing.gateways
from .base import PaymentGateway

# Definimos clases de gateway que serán importadas por otros módulos
class StripeGateway:
    """Clase puente para StripeGateway. Usar app.ats.pricing.gateways.StripeGateway en su lugar."""
    pass

class PayPalGateway:
    """Clase puente para PayPalGateway. Usar app.ats.pricing.gateways.PayPalGateway en su lugar."""
    pass

class MercadoPagoGateway:
    """Clase puente para MercadoPagoGateway. Usar app.ats.pricing.gateways.MercadoPagoGateway en su lugar."""
    pass

class ConektaGateway:
    """Clase puente para ConektaGateway. Usar app.ats.pricing.gateways.ConektaGateway en su lugar."""
    pass
