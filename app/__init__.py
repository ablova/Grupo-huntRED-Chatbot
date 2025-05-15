# app/__init__.py

# Exports for app module
default_app_config = 'app.apps.AppConfig'
__all__ = ['models', 'views', 'admin', 'forms', 'api', 'tasks', 'signals']

# Inicializar el registro de módulos
# La inicialización del registro de módulos se realizará en apps.py
# después de que se complete la migración inicial