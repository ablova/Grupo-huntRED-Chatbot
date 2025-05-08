from ..lazy_imports import lazy_imports, register_module

# Register ml modules for lazy loading
lazy_imports.register('check_dependencies', '.check_dependencies')
lazy_imports.register('core', '.core')
lazy_imports.register('data', '.data')
lazy_imports.register('integrations', '.integrations')
lazy_imports.register('ml_config', '.ml_config')
lazy_imports.register('ml_core', '.ml_core')
lazy_imports.register('ml_optimizer', '.ml_optimizer')
lazy_imports.register('ml_scrape', '.ml_scrape')
lazy_imports.register('ml_utils', '.ml_utils')
lazy_imports.register('monitoring', '.monitoring')
lazy_imports.register('tests', '.tests')
lazy_imports.register('utils', '.utils')