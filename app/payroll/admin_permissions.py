from django.contrib import admin
from app.payroll.models import PermisoEspecial

@admin.register(PermisoEspecial)
class PermisoEspecialAdmin(admin.ModelAdmin):
    list_display = ('employee', 'permiso_type', 'status', 'start_date', 'end_date', 'created_at', 'approved_by_supervisor', 'approved_by_hr')
    list_filter = ('permiso_type', 'status', 'start_date', 'end_date', 'created_at')
    search_fields = ('employee__first_name', 'employee__last_name', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['aprobar_permiso', 'rechazar_permiso', 'finalizar_permiso']

    def aprobar_permiso(self, request, queryset):
        for permiso in queryset:
            permiso.status = 'approved'
            permiso.save()
    aprobar_permiso.short_description = "Aprobar permisos seleccionados"

    def rechazar_permiso(self, request, queryset):
        for permiso in queryset:
            permiso.status = 'rejected'
            permiso.save()
    rechazar_permiso.short_description = "Rechazar permisos seleccionados"

    def finalizar_permiso(self, request, queryset):
        for permiso in queryset:
            permiso.status = 'completed'
            permiso.save()
    finalizar_permiso.short_description = "Finalizar permisos seleccionados" 