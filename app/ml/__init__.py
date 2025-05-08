from ..lazy_imports import lazy_imports, register_module, get_module

# Establecer el paquete actual
register_module('ml', '.', package='app.ml')

# Registrar módulos de ml para lazy loading
register_module('check_dependencies', '.check_dependencies', package='app.ml')
register_module('core', '.core', package='app.ml')
register_module('data', '.data', package='app.ml')
register_module('integrations', '.integrations', package='app.ml')
register_module('ml_config', '.ml_config', package='app.ml')
register_module('ml_core', '.ml_core', package='app.ml')
register_module('ml_optimizer', '.ml_optimizer', package='app.ml')
register_module('ml_scrape', '.ml_scrape', package='app.ml')
register_module('ml_utils', '.ml_utils', package='app.ml')
register_module('monitoring', '.monitoring', package='app.ml')
register_module('tests', '.tests', package='app.ml')
register_module('utils', '.utils', package='app.ml')