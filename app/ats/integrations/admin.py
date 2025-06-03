from django.contrib import admin
from .models import Integration, IntegrationConfig, IntegrationLog

@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('type', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(IntegrationConfig)
class IntegrationConfigAdmin(admin.ModelAdmin):
    list_display = ('integration', 'key', 'is_secret', 'created_at', 'updated_at')
    list_filter = ('is_secret', 'integration')
    search_fields = ('key', 'value')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = ('integration', 'event_type', 'created_at')
    list_filter = ('event_type', 'integration')
    search_fields = ('payload', 'error')
    readonly_fields = ('created_at',) 