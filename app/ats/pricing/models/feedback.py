# app/ats/pricing/models/feedback.py
"""
Re-exportación de modelos de feedback desde app.models.
Este archivo existe para mantener la compatibilidad con el código existente.
"""

from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

class ProposalFeedback(models.Model):
    """
    Modelo para feedback de propuestas.
    """
    # Choices para el tipo de respuesta (nuevos campos para formularios web)
    RESPONSE_CHOICES = [
        ('interested', 'Estoy interesado en contratar el servicio'),
        ('maybe_later', 'Me interesa pero no ahora'),
        ('not_interested', 'No estoy interesado'),
        ('need_more_info', 'Necesito más información'),
    ]
    
    # Razones de rechazo
    REJECTION_REASONS = [
        ('price', 'El precio es muy alto'),
        ('timing', 'No es el momento adecuado'),
        ('budget', 'No hay presupuesto disponible'),
        ('competitor', 'Contratamos a un competidor'),
        ('internal', 'Lo haremos internamente'),
        ('other', 'Otra razón'),
    ]
    
    # Fuentes de conocimiento
    SOURCE_CHOICES = [
        ('linkedin', 'LinkedIn'),
        ('website', 'Sitio web'),
        ('referral', 'Referencia de cliente'),
        ('social_media', 'Redes sociales'),
        ('email', 'Email marketing'),
        ('other', 'Otro'),
    ]
    
    # Campos existentes (mantener compatibilidad)
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En revisión'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado')
    ]
    
    propuesta = models.ForeignKey(
        'pricing.PricingProposal',
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    comentarios = models.TextField()
    calificacion = models.PositiveSmallIntegerField(null=True, blank=True)
    metadata = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    
    # Nuevos campos para formularios web
    token = models.CharField(max_length=100, unique=True, null=True, blank=True, help_text="Token único para identificar la propuesta")
    response_type = models.CharField(max_length=20, choices=RESPONSE_CHOICES, null=True, blank=True, verbose_name="Tipo de respuesta")
    rejection_reason = models.CharField(max_length=20, choices=REJECTION_REASONS, null=True, blank=True, verbose_name="Razón de rechazo")
    how_found_us = models.CharField(max_length=20, choices=SOURCE_CHOICES, null=True, blank=True, verbose_name="Cómo nos conoció")
    price_perception = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Percepción de precio (1-5)")
    missing_info = models.TextField(null=True, blank=True, verbose_name="Información faltante")
    improvement_suggestions = models.TextField(null=True, blank=True, verbose_name="Sugerencias de mejora")
    meeting_requested = models.BooleanField(default=False, verbose_name="Solicita reunión")
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feedback de Propuesta"
        verbose_name_plural = "Feedback de Propuestas"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        if self.response_type:
            return f"Feedback - {self.response_type} - {self.fecha_creacion.strftime('%Y-%m-%d')}"
        else:
            return f"{self.propuesta} - {self.estado}"

class MeetingRequest(models.Model):
    """
    Modelo para solicitudes de reunión.
    """
    # Tipos de reunión (nuevos campos para formularios web)
    MEETING_TYPES = [
        ('consultation', 'Consulta inicial'),
        ('proposal_review', 'Revisión de propuesta'),
        ('negotiation', 'Negociación'),
        ('implementation', 'Plan de implementación'),
        ('follow_up', 'Seguimiento'),
        ('other', 'Otro'),
    ]
    
    # Campos existentes (mantener compatibilidad)
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('COMPLETADA', 'Completada')
    ]
    
    propuesta = models.ForeignKey(
        'pricing.PricingProposal',
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
    
    # Nuevos campos para formularios web
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, null=True, blank=True, verbose_name="Tipo de reunión")
    preferred_date = models.DateField(null=True, blank=True, verbose_name="Fecha preferida")
    preferred_time_range = models.CharField(max_length=20, choices=[
        ('morning', 'Mañana (9:00 - 12:00)'),
        ('afternoon', 'Tarde (12:00 - 17:00)'),
        ('evening', 'Tarde-Noche (17:00 - 20:00)'),
    ], null=True, blank=True, verbose_name="Horario preferido")
    contact_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="Teléfono de contacto")
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solicitud de Reunión"
        verbose_name_plural = "Solicitudes de Reunión"
        ordering = ['-fecha_creacion']
        
    def __str__(self):
        if self.meeting_type and self.preferred_date:
            return f"Reunión - {self.meeting_type} - {self.preferred_date}"
        else:
            return f"{self.propuesta} - {self.fecha_reunion or self.fecha_solicitud}" 