from ..lazy_imports import lazy_imports, register_module

# Register config modules for lazy loading
lazy_imports.register('admin_config', '.admin_config')
lazy_imports.register('chatbot_utils', '.chatbot_utils')
lazy_imports.register('dashboard_config', '.dashboard_config')
lazy_imports.register('dashboard_constants', '.dashboard_constants')
lazy_imports.register('dashboard_utils', '.dashboard_utils')
lazy_imports.register('system_utils', '.system_utils')
