from ..lazy_imports import lazy_imports, register_module

# Register sexsi modules for lazy loading
lazy_imports.register('admin', '.admin')
lazy_imports.register('forms', '.forms')
lazy_imports.register('models', '.models')
lazy_imports.register('signals', '.signals')
lazy_imports.register('tasks', '.tasks')
lazy_imports.register('templates', '.templates')
lazy_imports.register('tests', '.tests')
lazy_imports.register('views', '.views')