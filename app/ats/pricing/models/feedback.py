from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

class ProposalFeedback(models.Model):
    """
    Modelo para feedback de propuestas.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En revisión'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado')
    ]
    
    propuesta = models.ForeignKey(
        'pricing.Proposal',
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    comentarios = models.TextField()
    calificacion = models.PositiveSmallIntegerField(null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feedback de Propuesta"
        verbose_name_plural = "Feedback de Propuestas"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"{self.propuesta} - {self.estado}"

class MeetingRequest(models.Model):
    """
    Modelo para solicitudes de reunión.
    """
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('COMPLETADA', 'Completada')
    ]
    
    propuesta = models.ForeignKey(
        'pricing.Proposal',
        on_delete=models.CASCADE,
        related_name='solicitudes_reunion'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField()
    fecha_reunion = models.DateTimeField(null=True, blank=True)
    duracion_minutos = models.PositiveIntegerField(default=30)
    tipo_reunion = models.CharField(max_length=50)
    participantes = models.JSONField(encoder=DjangoJSONEncoder)
    notas = models.TextField(null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solicitud de Reunión"
        verbose_name_plural = "Solicitudes de Reunión"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        return f"{self.propuesta} - {self.fecha_reunion or self.fecha_solicitud}" 