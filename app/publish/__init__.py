"""
Módulo de publicación y campañas digitales
"""

__version__ = "1.0.0"

from ..lazy_imports import lazy_imports, register_module

# Register publish modules for lazy loading
lazy_imports.register('admin', '.admin')
lazy_imports.register('apps', '.apps')
lazy_imports.register('models', '.models')
lazy_imports.register('processors', '.processors')
lazy_imports.register('serializers', '.serializers')
lazy_imports.register('signals', '.signals')
lazy_imports.register('tasks', '.tasks')
lazy_imports.register('urls', '.urls')
lazy_imports.register('views', '.views')
lazy_imports.register('integrations', '.integrations')
lazy_imports.register('utils', '.utils')

# Registrar procesadores e integraciones usando lazy imports
def _register_processors():
    processors = lazy_imports.get('processors')
    processors.register_processors()

_register_processors()

def _register_integrations():
    integrations = lazy_imports.get('integrations')
    integrations.register_integrations()

_register_integrations()
