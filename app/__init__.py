from .lazy_imports import lazy_imports, register_module

# Establecer el paquete raíz
register_module('app', '.', package='app')

# Registrar módulos principales para lazy loading
register_module('models', '.models', package='app')
register_module('views', '.views', package='app')
register_module('forms', '.forms', package='app')
register_module('tasks', '.tasks', package='app')
register_module('signals', '.signals', package='app')
register_module('admin', '.admin', package='app')
register_module('utilidades', '.utilidades', package='app')
register_module('chatbot', '.chatbot', package='app')
register_module('ml', '.ml', package='app')
register_module('publish', '.publish', package='app')
register_module('sexsi', '.sexsi', package='app')
register_module('pagos', '.pagos', package='app')
register_module('milkyleak', '.milkyleak', package='app')
register_module('config', '.config', package='app')
register_module('analysis', '.analysis', package='app')
register_module('dashboard', '.dashboard', package='app')
register_module('integrations', '.integrations', package='app')
register_module('templates', '.templates', package='app')
register_module('templatetags', '.templatetags', package='app')
register_module('tests', '.tests', package='app')
register_module('urls', '.urls', package='app')
register_module('Event', '.Event', package='app')
register_module('decorators', '.decorators', package='app')
register_module('singleton', '.singleton', package='app')

default_app_config = 'app.apps.AppConfig'