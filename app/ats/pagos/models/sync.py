from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

class SincronizacionLog(models.Model):
    """
    Modelo para registrar logs de sincronización.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En proceso'),
        ('EXITO', 'Éxito'),
        ('ERROR', 'Error')
    ]
    
    oportunidad = models.ForeignKey(
        'pagos.Oportunidad',
        on_delete=models.CASCADE,
        related_name='sincronizaciones'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    detalle = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Log de Sincronización"
        verbose_name_plural = "Logs de Sincronización"
        
    def __str__(self):
        return f"{self.oportunidad} - {self.estado}"

class SincronizacionError(models.Model):
    """
    Modelo para registrar errores de sincronización.
    """
    oportunidad = models.ForeignKey(
        'pagos.Oportunidad',
        on_delete=models.CASCADE,
        related_name='errores_sincronizacion'
    )
    mensaje = models.TextField()
    intento = models.PositiveSmallIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    resuelto = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Error de Sincronización"
        verbose_name_plural = "Errores de Sincronización"
        
    def __str__(self):
        return f"{self.oportunidad} - {self.mensaje[:50]}..."

class EstadoSincronizacion(models.Model):
    """
    Modelo para el estado general de sincronización.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En proceso'),
        ('EXITO', 'Éxito'),
        ('ERROR', 'Error'),
        ('DETENIDO', 'Detenido')
    ]
    
    nombre = models.CharField(max_length=50, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    detalles = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    class Meta:
        verbose_name = "Estado de Sincronización"
        verbose_name_plural = "Estados de Sincronización"
        
    def __str__(self):
        return f"{self.nombre} - {self.estado}"

class ConfiguracionSincronizacion(models.Model):
    """
    Modelo para configurar la sincronización.
    """
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)
    intervalo_minutos = models.PositiveIntegerField(default=15)
    max_reintentos = models.PositiveIntegerField(default=3)
    tiempo_entre_reintentos = models.PositiveIntegerField(default=60)  # en segundos
    fecha_ultimo_exitoso = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Configuración de Sincronización"
        verbose_name_plural = "Configuraciones de Sincronización"
        
    def __str__(self):
        return f"{self.nombre} - {self.activo}"

class HistorialSincronizacion(models.Model):
    """
    Modelo para historial de sincronizaciones.
    """
    configuracion = models.ForeignKey(
        ConfiguracionSincronizacion,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    exitos = models.PositiveIntegerField(default=0)
    errores = models.PositiveIntegerField(default=0)
    detalles = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    class Meta:
        verbose_name = "Historial de Sincronización"
        verbose_name_plural = "Historial de Sincronización"
        ordering = ['-fecha']
        
    def __str__(self):
        return f"{self.configuracion} - {self.fecha}"

class EstadoSincronizacionGlobal(models.Model):
    """
    Modelo para el estado global de la sincronización.
    """
    ESTADOS = [
        ('NORMAL', 'Normal'),
        ('ALERTA', 'Alerta'),
        ('CRITICO', 'Crítico'),
        ('DETENIDO', 'Detenido')
    ]
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='NORMAL')
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    detalles = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    class Meta:
        verbose_name = "Estado Global de Sincronización"
        verbose_name_plural = "Estado Global de Sincronización"
        
    def __str__(self):
        return f"Estado Global - {self.estado}" 