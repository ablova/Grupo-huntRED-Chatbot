from django.contrib import admin
from django.apps import apps

# Importar todos los módulos de administración
from .notifications import *
from .chatbot import *
from .market import *
from .pricing import *
from .learning import *
from .analytics import *
from .core import *

# Registrar modelos automáticamente si no están registrados manualmente
def auto_register_models():
    """Registra automáticamente los modelos que no tienen un admin personalizado"""
    for model in apps.get_models():
        if not model._meta.abstract and not model._meta.proxy:
            try:
                admin.site.register(model)
            except admin.sites.AlreadyRegistered:
                pass

# Ejecutar el registro automático
auto_register_models() 