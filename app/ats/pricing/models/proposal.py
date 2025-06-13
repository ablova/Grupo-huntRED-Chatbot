# /home/pablo/app/ats/pricing/models/proposal.py
from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

class PricingProposal(models.Model):
    """
    Modelo para propuestas de servicio.
    """
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('ENVIADA', 'Enviada'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('CANCELADA', 'Cancelada')
    ]
    
    oportunidad = models.ForeignKey(
        'pricing.Oportunidad',
        on_delete=models.CASCADE,
        related_name='propuestas'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='MXN')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_rechazo = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    class Meta:
        verbose_name = "Propuesta de Servicio"
        verbose_name_plural = "Propuestas de Servicio"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"

class ProposalSection(models.Model):
    """
    Modelo para secciones de propuestas.
    """
    TIPOS = [
        ('INTRODUCCION', 'Introducción'),
        ('SERVICIOS', 'Servicios'),
        ('PRECIOS', 'Precios'),
        ('PLAZOS', 'Plazos'),
        ('TERMINOS', 'Términos y Condiciones'),
        ('CONTACTO', 'Información de Contacto')
    ]
    
    propuesta = models.ForeignKey(
        PricingProposal,
        on_delete=models.CASCADE,
        related_name='secciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    orden = models.IntegerField(default=0)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    class Meta:
        verbose_name = "Sección de Propuesta"
        verbose_name_plural = "Secciones de Propuesta"
        ordering = ['orden']
        
    def __str__(self):
        return f"{self.propuesta.titulo} - {self.get_tipo_display()}"

class ProposalTemplate(models.Model):
    """
    Modelo para plantillas de propuestas.
    """
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    activo = models.BooleanField(default=True)
    secciones = models.JSONField(encoder=DjangoJSONEncoder)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla de Propuesta"
        verbose_name_plural = "Plantillas de Propuesta"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return self.nombre 