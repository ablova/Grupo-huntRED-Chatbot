"""
Admin para huntRED® Executive.
"""

from django.contrib import admin
from app.models import *

@admin.register(ExecutiveProfile)
class ExecutiveProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'company', 'experience_years']
    list_filter = ['experience_years', 'created_at']
    search_fields = ['name', 'position', 'company']
