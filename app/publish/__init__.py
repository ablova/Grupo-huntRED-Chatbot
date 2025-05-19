"""
Módulo de publicación y campañas digitales
"""

__version__ = "1.0.0"

from app.lazy_imports import LazyImporter, register_module, get_module

# Establecer el paquete actual
register_module('publish', '.', package='app.publish')

# Registrar módulos de publish para lazy loading
register_module('admin', '.admin', package='app.publish')
register_module('apps', '.apps', package='app.publish')
register_module('models', '.models', package='app.publish')
register_module('processors', '.processors', package='app.publish')
register_module('serializers', '.serializers', package='app.publish')
register_module('signals', '.signals', package='app.publish')
register_module('tasks', '.tasks', package='app.publish')
register_module('urls', '.urls', package='app.publish')
register_module('views', '.views', package='app.publish')
register_module('integrations', '.integrations', package='app.publish')
register_module('utils', '.utils', package='app.publish')

# Registrar procesadores e integraciones usando lazy imports
def _register_processors():
    processors = get_module('processors')
    # No necesitamos llamar a register_processors() ya que los procesadores se registran automáticamente
    # cuando se importan los módulos

_register_processors()

def _register_integrations():
    from django.apps import apps
    if not apps.ready:
        return
        
    integrations = get_module('integrations')
    integrations.register_integrations()

_register_integrations()
