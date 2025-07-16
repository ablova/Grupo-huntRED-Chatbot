from django.contrib import admin
from app.payroll.models import PermisoEspecial

@admin.register(PermisoEspecial)
class PermisoEspecialAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo', 'estado', 'fecha_inicio', 'fecha_fin', 'fecha_solicitud', 'supervisor', 'rh')
    list_filter = ('tipo', 'estado', 'fecha_inicio', 'fecha_fin', 'fecha_solicitud')
    search_fields = ('empleado__user__username', 'motivo', 'reconocimiento')
    readonly_fields = ('fecha_solicitud', 'fecha_respuesta')
    actions = ['aprobar_permiso', 'rechazar_permiso', 'finalizar_permiso', 'reconocer_empleado']

    def aprobar_permiso(self, request, queryset):
        for permiso in queryset:
            permiso.estado = 'aprobado'
            permiso.save()
    aprobar_permiso.short_description = "Aprobar permisos seleccionados"

    def rechazar_permiso(self, request, queryset):
        for permiso in queryset:
            permiso.estado = 'rechazado'
            permiso.save()
    rechazar_permiso.short_description = "Rechazar permisos seleccionados"

    def finalizar_permiso(self, request, queryset):
        for permiso in queryset:
            permiso.estado = 'finalizado'
            permiso.save()
    finalizar_permiso.short_description = "Finalizar permisos seleccionados"

    def reconocer_empleado(self, request, queryset):
        for permiso in queryset:
            permiso.reconocimiento = '¡Felicidades por tu logro!'
            permiso.save()
    reconocer_empleado.short_description = "Reconocer empleado" 