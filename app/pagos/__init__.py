# app/pagos/__init__.py
# Removed manual lazy_imports registration as ModuleRegistry handles this automatically

# Establecer el paquete actual
# Registrar módulos de pagos para lazy loading
# ... (previous manual registrations removed)

# Exports for pagos module
from app.models import Pago, EstadoPago, TipoPago, MetodoPago
from .services import PagoService

__all__ = ['Pago', 'EstadoPago', 'TipoPago', 'MetodoPago', 'PagoService']
