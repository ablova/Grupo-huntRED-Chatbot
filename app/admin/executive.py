"""
Admin para huntRED® Executive.
"""

from django.contrib import admin
from app.models import BusinessUnit, Vacante

@admin.register(BusinessUnit)
class ExecutiveBusinessUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
