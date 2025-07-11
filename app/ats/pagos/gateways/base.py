# app/ats/pagos/gateways/base.py
"""
Módulo puente para mantener compatibilidad con código legacy.
Este módulo implementa clases puente para mantener compatibilidad
con código que aún importa desde app.ats.pagos.gateways.base.
"""

# En lugar de importar directamente, implementamos una clase básica
# que sirve como puente para evitar importaciones circulares
class PaymentGateway:
    """Clase puente para PaymentGateway. Usar app.ats.pricing.gateways.PaymentGateway en su lugar."""
    
    def __init__(self, *args, **kwargs):
        """Constructor básico para compatibilidad."""
        pass
    
    def process_payment(self, *args, **kwargs):
        """Método básico para compatibilidad."""
        raise NotImplementedError("Esta es una clase puente. Usar app.ats.pricing.gateways.PaymentGateway en su lugar.")
    
    def get_payment_status(self, *args, **kwargs):
        """Método básico para compatibilidad."""
        raise NotImplementedError("Esta es una clase puente. Usar app.ats.pricing.gateways.PaymentGateway en su lugar.")

