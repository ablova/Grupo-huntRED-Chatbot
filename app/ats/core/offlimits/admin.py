from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from app.ats.core.offlimits.models import OffLimitsRestriction, CandidateInitiatedContact, OffLimitsAudit


@admin.register(OffLimitsRestriction)
class OffLimitsRestrictionAdmin(admin.ModelAdmin):
    list_display = ('client', 'business_unit', 'service_type', 'start_date', 'end_date', 
                   'is_active', 'days_remaining', 'created_by')
    list_filter = ('business_unit', 'service_type', 'is_active')
    search_fields = ('client__name', 'client__company__name')
    date_hierarchy = 'start_date'
    readonly_fields = ('start_date', 'created_at', 'updated_at', 'created_by')
    actions = ['deactivate_restrictions', 'activate_restrictions']
    
    def days_remaining(self, obj):
        """Muestra los días restantes para que expire la restricción"""
        from django.utils import timezone
        import datetime
        
        if not obj.is_active:
            return "Inactivo"
            
        if obj.end_date < timezone.now().date():
            return "Expirado"
            
        days = (obj.end_date - timezone.now().date()).days
        if days <= 7:
            return format_html('<span style="color: red; font-weight: bold;">{} días</span>', days)
        elif days <= 30:
            return format_html('<span style="color: orange;">{} días</span>', days)
        return f"{days} días"
    days_remaining.short_description = "Días Restantes"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Solo en creación
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def deactivate_restrictions(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} restricciones desactivadas.")
    deactivate_restrictions.short_description = "Desactivar restricciones seleccionadas"
    
    def activate_restrictions(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} restricciones activadas.")
    activate_restrictions.short_description = "Activar restricciones seleccionadas"


@admin.register(CandidateInitiatedContact)
class CandidateInitiatedContactAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'client', 'evidence_type', 'timestamp', 'is_verified', 'verified_by')
    list_filter = ('evidence_type', 'verification_date__isnull')
    search_fields = ('candidate__name', 'client__name', 'notes')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
    
    def is_verified(self, obj):
        return obj.verification_date is not None
    is_verified.boolean = True
    is_verified.short_description = "Verificado"


@admin.register(OffLimitsAudit)
class OffLimitsAuditAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'candidate', 'client', 'business_unit', 'user', 'timestamp')
    list_filter = ('action_type', 'timestamp', 'business_unit')
    search_fields = ('candidate__name', 'client__name', 'details')
    date_hierarchy = 'timestamp'
    readonly_fields = ('action_type', 'candidate', 'client', 'business_unit', 
                      'user', 'timestamp', 'restriction', 'details')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
