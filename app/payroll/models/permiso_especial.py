from django.db import models
from django.conf import settings
from app.payroll.models import PayrollEmployee

class PermisoEspecial(models.Model):
    TIPO_PERMISO = [
        ('maternidad', 'Maternidad'),
        ('paternidad', 'Paternidad'),
        ('enfermedad', 'Enfermedad Prolongada'),
        ('home_office', 'Home Office'),
        ('licencia', 'Licencia Especial'),
        ('ascenso', 'Ascenso'),
        ('reconocimiento', 'Reconocimiento'),
        ('otro', 'Otro'),
    ]
    ESTADO = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('finalizado', 'Finalizado'),
    ]
    empleado = models.ForeignKey(PayrollEmployee, on_delete=models.CASCADE, related_name='permisos_especiales')
    tipo = models.CharField(max_length=20, choices=TIPO_PERMISO)
    motivo = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO, default='pendiente')
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='permisos_supervisados')
    rh = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='permisos_rh')
    respuesta_supervisor = models.TextField(blank=True)
    respuesta_rh = models.TextField(blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    reconocimiento = models.TextField(blank=True)
    notificado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Permiso Especial'
        verbose_name_plural = 'Permisos Especiales'
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.empleado} ({self.estado})" 