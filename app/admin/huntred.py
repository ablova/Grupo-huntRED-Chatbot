"""
Admin para huntRED® (Unidad de Negocio Principal).
"""

from django.contrib import admin
from app.ats.models import Person

definir_imports = False
try:
    from app.ats.models import Person
    definir_imports = True
except ImportError:
    from app.models import Person
    definir_imports = True

definir_admins = False
try:
    @admin.register(Person)
    class PersonAdmin(admin.ModelAdmin):
        pass
    definir_admins = True
except Exception:
    pass
