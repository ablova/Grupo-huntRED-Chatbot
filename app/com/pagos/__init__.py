from ..lazy_imports import lazy_imports, register_module, get_module

# Establecer el paquete actual
register_module('pagos', '.', package='app.pagos')

# Registrar módulos de pagos para lazy loading
register_module('pagos', '.', package='app.pagos')

# Registrar módulos de pagos para lazy loading
register_module('admin', '.admin', package='app.pagos')
register_module('apps', '.apps', package='app.pagos')
register_module('gateways', '.gateways', package='app.pagos')
register_module('models', '.models', package='app.pagos')
register_module('services', '.services', package='app.pagos')
register_module('sync', '.sync', package='app.pagos')
register_module('urls', '.urls', package='app.pagos')
register_module('views', '.views', package='app.pagos')

from .models import Pago, EstadoPago, TipoPago, MetodoPago
from .services import PagoService

__all__ = ['Pago', 'EstadoPago', 'TipoPago', 'MetodoPago', 'PagoService']

register_module('admin', '.admin', package='app.pagos')
register_module('apps', '.apps', package='app.pagos')
register_module('gateways', '.gateways', package='app.pagos')
register_module('models', '.models', package='app.pagos')
register_module('sync', '.sync', package='app.pagos')
register_module('urls', '.urls', package='app.pagos')
register_module('views', '.views', package='app.pagos')
