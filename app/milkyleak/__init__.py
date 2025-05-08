from ..lazy_imports import lazy_imports, register_module

# Establecer el paquete actual
register_module('milkyleak', '.', package='app.milkyleak')

# Registrar módulos de milkyleak para lazy loading
register_module('milkyleak', '.milkyleak', package='app.milkyleak')
register_module('templates', '.templates', package='app.milkyleak')
