"""
Admin para huntRED® Solucions (Consultora).
"""

from django.contrib import admin
from app.models import *

@admin.register(ConsultingProject)
class ConsultingProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'start_date']
    search_fields = ['name', 'client']
