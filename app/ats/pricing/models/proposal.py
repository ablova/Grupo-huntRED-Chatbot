from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

class Proposal(models.Model):
    """
    Modelo para propuestas.
    """
    ESTADOS = [
        ('BORRADOR', 'Borrador'),
        ('ENVIADA', 'Enviada'),
        ('EN_REVISION', 'En revisión'),
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
        verbose_name = "Propuesta"
        verbose_name_plural = "Propuestas"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"{self.titulo} - {self.estado}"

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
        Proposal,
        on_delete=models.CASCADE,
        related_name='secciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    orden = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    class Meta:
        verbose_name = "Sección de Propuesta"
        verbose_name_plural = "Secciones de Propuesta"
        ordering = ['orden']
        
    def __str__(self):
        return f"{self.propuesta} - {self.titulo}"

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