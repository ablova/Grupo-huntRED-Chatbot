from .lazy_imports import lazy_imports, register_module

# Register main modules for lazy loading
lazy_imports.register('models', '.models')
lazy_imports.register('views', '.views')
lazy_imports.register('forms', '.forms')
lazy_imports.register('tasks', '.tasks')
lazy_imports.register('signals', '.signals')
lazy_imports.register('admin', '.admin')
lazy_imports.register('utilidades', '.utilidades')
lazy_imports.register('chatbot', '.chatbot')
lazy_imports.register('ml', '.ml')
lazy_imports.register('publish', '.publish')
lazy_imports.register('sexsi', '.sexsi')
lazy_imports.register('pagos', '.pagos')
lazy_imports.register('milkyleak', '.milkyleak')
lazy_imports.register('config', '.config')
lazy_imports.register('analysis', '.analysis')
lazy_imports.register('dashboard', '.dashboard')
lazy_imports.register('integrations', '.integrations')
lazy_imports.register('templates', '.templates')
lazy_imports.register('templatetags', '.templatetags')
lazy_imports.register('tests', '.tests')
lazy_imports.register('urls', '.urls')
lazy_imports.register('Event', '.Event')
lazy_imports.register('decorators', '.decorators')
lazy_imports.register('singleton', '.singleton')

default_app_config = 'app.apps.AppConfig'