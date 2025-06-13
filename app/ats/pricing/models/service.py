from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

class ServiceCalculation(models.Model):
    """
    Modelo para cálculos de servicios.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado')
    ]
    
    oportunidad = models.ForeignKey(
        'pricing.Oportunidad',
        on_delete=models.CASCADE,
        related_name='calculos_servicio'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    monto_base = models.DecimalField(max_digits=10, decimal_places=2)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='MXN')
    descuentos = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    addons = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cálculo de Servicio"
        verbose_name_plural = "Cálculos de Servicio"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"{self.oportunidad} - {self.monto_final} {self.moneda}"

class Payment(models.Model):
    """
    Modelo para pagos de servicios.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En proceso'),
        ('COMPLETADO', 'Completado'),
        ('FALLIDO', 'Fallido'),
        ('REEMBOLSADO', 'Reembolsado')
    ]
    
    calculo = models.ForeignKey(
        ServiceCalculation,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='MXN')
    metodo = models.CharField(max_length=50)
    id_transaccion = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"{self.calculo} - {self.monto} {self.moneda}" 