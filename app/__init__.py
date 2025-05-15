# app/__init__.py

# Exports for app module
default_app_config = 'app.apps.AppConfig'
__all__ = ['models', 'views', 'admin', 'forms', 'api', 'tasks', 'signals']

# Inicializar el registro de módulos
from app.module_registry import auto_register
auto_register()