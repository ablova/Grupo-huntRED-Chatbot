"""
Admin para huntRED® Solucions (Consultora).
"""

from django.contrib import admin
from app.models import Vacante, Company

@admin.register(Vacante)
class SolucionsVacanteAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'empresa', 'activa', 'fecha_publicacion']
    list_filter = ['activa', 'fecha_publicacion', 'modalidad']
    search_fields = ['titulo', 'empresa__nombre']
    readonly_fields = ['fecha_scraping']
