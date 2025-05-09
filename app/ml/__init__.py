from ..lazy_imports import lazy_imports, register_module, get_module

# Establecer el paquete actual
register_module('ml', '.', package='app.ml')

# Registrar módulos de ml para lazy loading
register_module('check_dependencies', '.check_dependencies', package='app.ml')
register_module('core', '.core', package='app.ml')
register_module('data', '.data', package='app.ml')
register_module('integrations', '.integrations', package='app.ml')
register_module('ml_config', '.ml_config', package='app.ml')
# Los módulos ml_core y ml_optimizer han sido reemplazados por los servicios en core
register_module('scrape', '.utils.scrape', package='app.ml')
register_module('utils', '.utils.utils', package='app.ml')
register_module('monitoring', '.monitoring', package='app.ml')
register_module('tests', '.tests', package='app.ml')
register_module('utils', '.utils', package='app.ml')