from ..lazy_imports import lazy_imports, register_module, get_module

# Establecer el paquete actual
register_module('config', '.', package='app.config')

# Registrar módulos de config para lazy loading
register_module('admin_config', '.admin_config', package='app.config')
register_module('chatbot_utils', '.chatbot_utils', package='app.config')
register_module('dashboard_config', '.dashboard_config', package='app.config')
register_module('dashboard_constants', '.dashboard_constants', package='app.config')
register_module('dashboard_utils', '.dashboard_utils', package='app.config')
register_module('system_utils', '.system_utils', package='app.config')
