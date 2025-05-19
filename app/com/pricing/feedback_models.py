# /home/pablo/app/com/pricing/feedback_models.py
"""
Modelos para el sistema de retroalimentación de propuestas en Grupo huntRED®.

Este módulo permite capturar información valiosa sobre las razones por las que
los clientes contratan o no los servicios, facilitando la mejora continua
del proceso de ventas y la personalización de propuestas futuras.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ProposalFeedback(models.Model):
    """Modelo para capturar retroalimentación sobre propuestas enviadas."""
    
    # Tipos de respuesta
    RESPONSE_CHOICES = [
        ('interested', 'Interesado - Solicitará el servicio'),
        ('considering', 'Considerando - Evaluando opciones'),
        ('not_now', 'No por ahora - Podría considerar en el futuro'),
        ('not_interested', 'No interesado - No es relevante actualmente'),
        ('went_competitor', 'Eligió competidor'),
    ]
    
    # Razones para no contratar
    REJECTION_REASONS = [
        ('price', 'Precio demasiado alto'),
        ('timing', 'No es el momento adecuado'),
        ('features', 'Faltan características/servicios clave'),
        ('needs', 'No se ajusta a nuestras necesidades'),
        ('budget', 'Sin presupuesto actualmente'),
        ('internal_process', 'Proceso interno de aprobación'),
        ('competitor', 'Eligió una solución de la competencia'),
        ('clarity', 'Falta de claridad en la propuesta'),
        ('other', 'Otra razón'),
    ]
    
    # Fuentes de información sobre huntRED
    SOURCE_CHOICES = [
        ('referral', 'Recomendación/Referencia'),
        ('linkedin', 'LinkedIn'),
        ('search', 'Búsqueda en internet'),
        ('event', 'Evento/Conferencia'),
        ('content', 'Contenido/Blog/Webinar'),
        ('cold_contact', 'Contacto directo de huntRED'),
        ('other', 'Otra fuente'),
    ]
    
    # Relaciones
    proposal = models.ForeignKey(
        'Proposal', 
        on_delete=models.CASCADE, 
        related_name='feedback',
        null=True, blank=True
    )
    opportunity = models.ForeignKey(
        'Opportunity', 
        on_delete=models.CASCADE, 
        related_name='feedback',
        null=True, blank=True
    )
    talent_analysis_request = models.ForeignKey(
        'TalentAnalysisRequest', 
        on_delete=models.CASCADE, 
        related_name='feedback',
        null=True, blank=True
    )
    
    # Datos básicos
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    company_name = models.CharField(max_length=100)
    
    # Retroalimentación
    response_type = models.CharField(
        max_length=20, 
        choices=RESPONSE_CHOICES,
        verbose_name="Tipo de respuesta"
    )
    rejection_reason = models.CharField(
        max_length=20, 
        choices=REJECTION_REASONS,
        null=True, blank=True,
        verbose_name="Razón para no contratar"
    )
    competitor_name = models.CharField(
        max_length=100, 
        null=True, blank=True,
        verbose_name="Nombre del competidor (si aplica)"
    )
    
    # Información adicional
    how_found_us = models.CharField(
        max_length=20, 
        choices=SOURCE_CHOICES,
        null=True, blank=True,
        verbose_name="¿Cómo nos encontró?"
    )
    price_perception = models.IntegerField(
        null=True, blank=True,
        verbose_name="Percepción de precio (1-5, donde 5 es muy caro)"
    )
    missing_info = models.TextField(
        null=True, blank=True,
        verbose_name="Información que faltó en la propuesta"
    )
    improvement_suggestions = models.TextField(
        null=True, blank=True,
        verbose_name="Sugerencias de mejora"
    )
    
    # Seguimiento
    meeting_requested = models.BooleanField(
        default=False,
        verbose_name="Solicitó reunión con Managing Director"
    )
    meeting_scheduled_for = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Reunión agendada para"
    )
    meeting_link = models.URLField(
        null=True, blank=True,
        verbose_name="Enlace a la reunión agendada"
    )
    
    # Metadatos
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Retroalimentación de Propuesta"
        verbose_name_plural = "Retroalimentación de Propuestas"
    
    def __str__(self):
        return f"Feedback: {self.company_name} - {self.get_response_type_display()}"


class MeetingRequest(models.Model):
    """Modelo para rastrear solicitudes de reunión con el Managing Director."""
    
    # Tipos de reunión
    MEETING_TYPES = [
        ('proposal_review', 'Revisión de Propuesta'),
        ('service_explanation', 'Explicación Detallada del Servicio'),
        ('pricing_discussion', 'Discusión de Precios/Términos'),
        ('custom_solution', 'Solución Personalizada'),
        ('general', 'Conversación General'),
    ]
    
    # Información de contacto
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    company_name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, null=True, blank=True)
    
    # Detalles de la reunión
    meeting_type = models.CharField(
        max_length=20, 
        choices=MEETING_TYPES,
        default='general',
        verbose_name="Tipo de reunión"
    )
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time_range = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # Relaciones
    proposal_feedback = models.OneToOneField(
        ProposalFeedback,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='meeting_request'
    )
    
    # Estado
    is_scheduled = models.BooleanField(default=False)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    meeting_link = models.URLField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    meeting_completed = models.BooleanField(default=False)
    
    # Metadatos
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solicitud de Reunión"
        verbose_name_plural = "Solicitudes de Reunión"
    
    def __str__(self):
        status = "Agendada" if self.is_scheduled else "Pendiente"
        return f"Reunión ({status}): {self.contact_name} - {self.company_name}"
