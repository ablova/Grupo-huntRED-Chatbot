from django.contrib import admin
from app.models import Pago, Empleador, Worker, Oportunidad

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'monto', 'metodo', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'metodo')
    search_fields = ('empleado__email', 'empleado__nombre')

@admin.register(Empleador)
class EmpleadorAdmin(admin.ModelAdmin):
    list_display = ('persona', 'rfc', 'direccion_fiscal')
    search_fields = ('persona__email', 'persona__nombre', 'rfc')

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('persona', 'especialidad', 'experiencia')
    search_fields = ('persona__email', 'persona__nombre', 'especialidad')

@admin.register(Oportunidad)
class OportunidadAdmin(admin.ModelAdmin):
    list_display = ('empleador', 'titulo', 'ubicacion', 'fecha_publicacion')
    list_filter = ('ubicacion', 'tipo_contrato')
    search_fields = ('empleador__persona__nombre', 'titulo', 'descripcion')
