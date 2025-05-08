from ..lazy_imports import lazy_imports, register_module

# Establecer el paquete actual
register_module('sexsi', '.', package='app.sexsi')

# Registrar módulos de sexsi para lazy loading
register_module('admin', '.admin', package='app.sexsi')
register_module('forms', '.forms', package='app.sexsi')
register_module('models', '.models', package='app.sexsi')
register_module('signals', '.signals', package='app.sexsi')
register_module('tasks', '.tasks', package='app.sexsi')
register_module('templates', '.templates', package='app.sexsi')
register_module('tests', '.tests', package='app.sexsi')
register_module('views', '.views', package='app.sexsi')