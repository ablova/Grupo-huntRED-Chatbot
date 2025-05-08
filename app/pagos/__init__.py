from ..lazy_imports import lazy_imports, register_module

# Establecer el paquete actual
register_module('pagos', '.', package='app.pagos')

# Registrar módulos de pagos para lazy loading
register_module('admin', '.admin', package='app.pagos')
register_module('apps', '.apps', package='app.pagos')
register_module('gateways', '.gateways', package='app.pagos')
register_module('models', '.models', package='app.pagos')
register_module('sync', '.sync', package='app.pagos')
register_module('urls', '.urls', package='app.pagos')
register_module('views', '.views', package='app.pagos')
