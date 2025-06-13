from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count

from app.ats.pagos.models import (
    Pago,
    Empleador,
    Worker,
    Oportunidad,
    SincronizacionLog,
    SincronizacionError,
    EstadoSincronizacion,
    ConfiguracionSincronizacion,
    HistorialSincronizacion,
    EstadoSincronizacionGlobal
)

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """Administración de Pagos"""
    
    list_display = (
        'id',
        'empleador',
        'vacante',
        'monto',
        'moneda',
        'metodo',
        'estado',
        'fecha_creacion',
        'fecha_actualizacion'
    )
    
    list_filter = (
        'estado',
        'metodo',
        'moneda',
        'fecha_creacion'
    )
    
    search_fields = (
        'empleador__email',
        'empleador__nombre',
        'vacante__titulo',
        'id_transaccion'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion',
        'webhook_payload'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'empleador',
                'vacante',
                'monto',
                'moneda',
                'metodo',
                'estado'
            )
        }),
        ('Detalles de la Transacción', {
            'fields': (
                'id_transaccion',
                'url_webhook',
                'webhook_payload'
            )
        }),
        ('Información de la Oportunidad', {
            'fields': (
                'oportunidad_id',
                'oportunidad_descripcion',
                'numero_plazas',
                'plazas_contratadas'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion'
            )
        })
    )

@admin.register(Empleador)
class EmpleadorAdmin(admin.ModelAdmin):
    """Administración de Empleadores"""
    
    list_display = (
        'persona',
        'rfc',
        'direccion_fiscal',
        'total_pagos',
        'monto_total'
    )
    
    search_fields = (
        'persona__email',
        'persona__nombre',
        'rfc'
    )
    
    def total_pagos(self, obj):
        """Muestra el total de pagos realizados"""
        count = Pago.objects.filter(empleador=obj).count()
        return format_html(
            '<a href="{}?empleador__id__exact={}">{}</a>',
            reverse('admin:pagos_pago_changelist'),
            obj.id,
            count
        )
    
    def monto_total(self, obj):
        """Calcula el monto total de pagos"""
        total = Pago.objects.filter(
            empleador=obj,
            estado='completado'
        ).aggregate(
            total=Sum('monto')
        )['total'] or 0
        return f"${total:,.2f}"

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    """Administración de Trabajadores"""
    
    list_display = (
        'persona',
        'especialidad',
        'experiencia',
        'total_contratos'
    )
    
    list_filter = (
        'especialidad',
        'experiencia'
    )
    
    search_fields = (
        'persona__email',
        'persona__nombre',
        'especialidad'
    )
    
    def total_contratos(self, obj):
        """Muestra el total de contratos"""
        count = Oportunidad.objects.filter(
            trabajador=obj,
            estado='completado'
        ).count()
        return format_html(
            '<a href="{}?trabajador__id__exact={}">{}</a>',
            reverse('admin:pagos_oportunidad_changelist'),
            obj.id,
            count
        )

@admin.register(Oportunidad)
class OportunidadAdmin(admin.ModelAdmin):
    """Administración de Oportunidades"""
    
    list_display = (
        'id',
        'empleador',
        'titulo',
        'ubicacion',
        'tipo_contrato',
        'estado',
        'fecha_publicacion',
        'total_pagos'
    )
    
    list_filter = (
        'ubicacion',
        'tipo_contrato',
        'estado',
        'fecha_publicacion'
    )
    
    search_fields = (
        'empleador__persona__nombre',
        'titulo',
        'descripcion'
    )
    
    def total_pagos(self, obj):
        """Muestra el total de pagos asociados"""
        count = Pago.objects.filter(vacante=obj).count()
        return format_html(
            '<a href="{}?vacante__id__exact={}">{}</a>',
            reverse('admin:pagos_pago_changelist'),
            obj.id,
            count
        )

@admin.register(SincronizacionLog)
class SincronizacionLogAdmin(admin.ModelAdmin):
    """Administración de Logs de Sincronización"""
    
    list_display = (
        'oportunidad',
        'estado',
        'fecha_creacion',
        'fecha_actualizacion'
    )
    
    list_filter = (
        'estado',
        'fecha_creacion'
    )
    
    search_fields = (
        'oportunidad__titulo',
        'detalle'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion'
    )

@admin.register(SincronizacionError)
class SincronizacionErrorAdmin(admin.ModelAdmin):
    """Administración de Errores de Sincronización"""
    
    list_display = (
        'oportunidad',
        'mensaje',
        'intento',
        'resuelto',
        'fecha_creacion',
        'fecha_resolucion'
    )
    
    list_filter = (
        'resuelto',
        'fecha_creacion'
    )
    
    search_fields = (
        'oportunidad__titulo',
        'mensaje'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_resolucion'
    )

@admin.register(EstadoSincronizacion)
class EstadoSincronizacionAdmin(admin.ModelAdmin):
    """Administración de Estados de Sincronización"""
    
    list_display = (
        'nombre',
        'estado',
        'ultima_actualizacion'
    )
    
    list_filter = (
        'estado',
        'ultima_actualizacion'
    )
    
    search_fields = (
        'nombre',
        'detalles'
    )
    
    readonly_fields = (
        'ultima_actualizacion'
    )

@admin.register(ConfiguracionSincronizacion)
class ConfiguracionSincronizacionAdmin(admin.ModelAdmin):
    """Administración de Configuraciones de Sincronización"""
    
    list_display = (
        'nombre',
        'activo',
        'intervalo_minutos',
        'max_reintentos',
        'tiempo_entre_reintentos',
        'fecha_ultimo_exitoso'
    )
    
    list_filter = (
        'activo',
        'fecha_ultimo_exitoso'
    )
    
    search_fields = (
        'nombre'
    )
    
    readonly_fields = (
        'fecha_ultimo_exitoso'
    )

@admin.register(HistorialSincronizacion)
class HistorialSincronizacionAdmin(admin.ModelAdmin):
    """Administración de Historial de Sincronización"""
    
    list_display = (
        'configuracion',
        'fecha',
        'exitos',
        'errores'
    )
    
    list_filter = (
        'fecha',
        'configuracion'
    )
    
    search_fields = (
        'configuracion__nombre',
        'detalles'
    )
    
    readonly_fields = (
        'fecha'
    )

@admin.register(EstadoSincronizacionGlobal)
class EstadoSincronizacionGlobalAdmin(admin.ModelAdmin):
    """Administración del Estado Global de Sincronización"""
    
    list_display = (
        'estado',
        'ultima_actualizacion'
    )
    
    list_filter = (
        'estado',
        'ultima_actualizacion'
    )
    
    search_fields = (
        'detalles'
    )
    
    readonly_fields = (
        'ultima_actualizacion'
    ) 