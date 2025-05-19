# /home/pablo/app/com/feedback/feedback_models.py
"""
Modelos para el sistema integrado de retroalimentación de Grupo huntRED®.

Este módulo contiene los modelos para almacenar y gestionar la retroalimentación
en todas las etapas del ciclo de vida del servicio: propuestas, durante la
prestación del servicio, y evaluación final.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ServiceFeedback(models.Model):
    """Modelo base para todas las retroalimentaciones de servicios."""
    
    # Etapas del servicio
    STAGE_CHOICES = [
        ('proposal', 'Propuesta'),
        ('ongoing', 'Servicio en Curso'),
        ('completed', 'Servicio Concluido'),
    ]
    
    # Tipos de servicio
    SERVICE_TYPE_CHOICES = [
        ('talent_analysis', 'Análisis de Talento 360°'),
        ('recruitment', 'Reclutamiento Especializado'),
        ('executive_search', 'Búsqueda de Ejecutivos'),
        ('consulting', 'Consultoría de HR'),
        ('outplacement', 'Outplacement'),
        ('training', 'Capacitación'),
        ('other', 'Otro Servicio'),
    ]
    
    # Relaciones
    company = models.ForeignKey(
        'Company', 
        on_delete=models.CASCADE, 
        related_name='feedback',
        null=True, blank=True
    )
    opportunity = models.ForeignKey(
        'Opportunity', 
        on_delete=models.CASCADE, 
        related_name='all_feedback',
        null=True, blank=True
    )
    proposal = models.ForeignKey(
        'Proposal', 
        on_delete=models.CASCADE, 
        related_name='all_feedback',
        null=True, blank=True
    )
    
    # Datos de identificación
    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        verbose_name="Etapa del servicio"
    )
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        verbose_name="Tipo de servicio"
    )
    token = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Token de identificación"
    )
    
    # Datos de contacto
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    company_name = models.CharField(max_length=100)
    
    # Datos generales de retroalimentación
    rating = models.IntegerField(
        null=True, blank=True,
        verbose_name="Calificación general (1-5)"
    )
    comments = models.TextField(
        null=True, blank=True,
        verbose_name="Comentarios generales"
    )
    
    # Sugerencias para nuevos servicios
    suggested_services = models.TextField(
        null=True, blank=True,
        verbose_name="Servicios sugeridos"
    )
    
    # Reunión con Managing Director
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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Retroalimentación de Servicio"
        verbose_name_plural = "Retroalimentaciones de Servicios"
        indexes = [
            models.Index(fields=['stage', 'service_type']),
            models.Index(fields=['company']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        stage_display = dict(self.STAGE_CHOICES).get(self.stage, self.stage)
        service_display = dict(self.SERVICE_TYPE_CHOICES).get(self.service_type, self.service_type)
        return f"{self.company_name} - {service_display} ({stage_display})"


class OngoingServiceFeedback(models.Model):
    """
    Retroalimentación específica durante la prestación del servicio.
    
    Captura información sobre la experiencia del cliente mientras el servicio
    está en curso, permitiendo realizar ajustes en tiempo real.
    """
    
    # Relaciones
    base_feedback = models.OneToOneField(
        ServiceFeedback,
        on_delete=models.CASCADE,
        related_name='ongoing_feedback',
        primary_key=True
    )
    
    # Evaluación específica del servicio en curso
    progress_satisfaction = models.IntegerField(
        null=True, blank=True,
        verbose_name="Satisfacción con el progreso (1-5)"
    )
    communication_rating = models.IntegerField(
        null=True, blank=True,
        verbose_name="Calificación de la comunicación (1-5)"
    )
    consultant_rating = models.IntegerField(
        null=True, blank=True,
        verbose_name="Calificación del consultor (1-5)"
    )
    platform_usability = models.IntegerField(
        null=True, blank=True,
        verbose_name="Usabilidad de la plataforma (1-5)"
    )
    
    # Áreas específicas de mejora
    needs_attention_areas = models.TextField(
        null=True, blank=True,
        verbose_name="Áreas que necesitan atención"
    )
    urgent_issues = models.TextField(
        null=True, blank=True,
        verbose_name="Problemas urgentes a resolver"
    )
    improvement_suggestions = models.TextField(
        null=True, blank=True,
        verbose_name="Sugerencias de mejora"
    )
    
    # Expectativas
    next_milestone_expectations = models.TextField(
        null=True, blank=True,
        verbose_name="Expectativas para el próximo hito"
    )
    
    # Metadatos para tracking
    service_progress = models.IntegerField(
        default=0,
        verbose_name="Progreso del servicio (%)"
    )
    milestone_number = models.IntegerField(
        default=1,
        verbose_name="Número de hito/etapa"
    )
    
    class Meta:
        verbose_name = "Feedback de Servicio en Curso"
        verbose_name_plural = "Feedback de Servicios en Curso"
    
    def __str__(self):
        return f"Feedback en curso: {self.base_feedback}"


class CompletedServiceFeedback(models.Model):
    """
    Retroalimentación al concluir un servicio.
    
    Captura la evaluación final del cliente después de completarse el servicio,
    permitiendo medir el éxito general y la satisfacción.
    """
    
    # Valoración del servicio
    VALUE_PERCEPTION_CHOICES = [
        ('excellent', 'Excelente relación calidad-precio'),
        ('good', 'Buena relación calidad-precio'),
        ('fair', 'Relación calidad-precio aceptable'),
        ('poor', 'Relación calidad-precio deficiente'),
        ('overpriced', 'Precio excesivo para el valor recibido'),
    ]
    
    # Probabilidad de recomendación (NPS)
    NPS_CHOICES = [
        (0, '0 - Nada probable'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (10, '10 - Extremadamente probable'),
    ]
    
    # Relaciones
    base_feedback = models.OneToOneField(
        ServiceFeedback,
        on_delete=models.CASCADE,
        related_name='completed_feedback',
        primary_key=True
    )
    
    # Evaluación general
    objectives_met = models.IntegerField(
        null=True, blank=True,
        verbose_name="Objetivos cumplidos (1-5)"
    )
    value_perception = models.CharField(
        max_length=20,
        choices=VALUE_PERCEPTION_CHOICES,
        null=True, blank=True,
        verbose_name="Percepción de valor"
    )
    recommendation_likelihood = models.IntegerField(
        choices=NPS_CHOICES,
        null=True, blank=True,
        verbose_name="Probabilidad de recomendarnos (0-10)"
    )
    
    # Áreas específicas de evaluación
    best_aspects = models.TextField(
        null=True, blank=True,
        verbose_name="Aspectos más destacados del servicio"
    )
    areas_for_improvement = models.TextField(
        null=True, blank=True,
        verbose_name="Áreas para mejorar"
    )
    consultant_evaluation = models.IntegerField(
        null=True, blank=True,
        verbose_name="Evaluación del consultor (1-5)"
    )
    process_evaluation = models.IntegerField(
        null=True, blank=True,
        verbose_name="Evaluación del proceso (1-5)"
    )
    
    # Posibilidad de nuevos negocios
    interested_in_other_services = models.BooleanField(
        default=False,
        verbose_name="Interesado en otros servicios"
    )
    services_of_interest = models.TextField(
        null=True, blank=True,
        verbose_name="Servicios de interés"
    )
    
    # Testimonial
    testimonial_provided = models.BooleanField(
        default=False,
        verbose_name="Proporcionó testimonial"
    )
    testimonial_text = models.TextField(
        null=True, blank=True,
        verbose_name="Texto del testimonial"
    )
    allow_public_testimonial = models.BooleanField(
        default=False,
        verbose_name="Permite uso público del testimonial"
    )
    
    class Meta:
        verbose_name = "Feedback de Servicio Concluido"
        verbose_name_plural = "Feedback de Servicios Concluidos"
    
    def __str__(self):
        return f"Evaluación final: {self.base_feedback}"
    
    @property
    def nps_category(self):
        """Categoriza el NPS como Promotor, Pasivo o Detractor."""
        if self.recommendation_likelihood is None:
            return None
        elif self.recommendation_likelihood >= 9:
            return "Promotor"
        elif self.recommendation_likelihood >= 7:
            return "Pasivo"
        else:
            return "Detractor"


class ServiceImprovementSuggestion(models.Model):
    """
    Sugerencias para nuevos servicios o mejoras.
    
    Este modelo permite capturar específicamente ideas para nuevos servicios
    o mejoras que los clientes sugieran durante cualquier etapa del feedback.
    """
    
    # Relaciones
    feedback = models.ForeignKey(
        ServiceFeedback,
        on_delete=models.CASCADE,
        related_name='improvement_suggestions'
    )
    
    # Detalles de la sugerencia
    suggestion_type = models.CharField(
        max_length=50,
        choices=[
            ('new_service', 'Nuevo Servicio'),
            ('enhancement', 'Mejora de Servicio Existente'),
            ('partnership', 'Oportunidad de Alianza'),
            ('other', 'Otra Sugerencia'),
        ],
        verbose_name="Tipo de sugerencia"
    )
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    potential_value = models.CharField(
        max_length=20,
        choices=[
            ('high', 'Alto potencial'),
            ('medium', 'Potencial medio'),
            ('low', 'Bajo potencial'),
            ('unknown', 'Potencial desconocido'),
        ],
        default='unknown'
    )
    
    # Seguimiento interno
    status = models.CharField(
        max_length=20,
        choices=[
            ('new', 'Nueva'),
            ('under_review', 'En revisión'),
            ('planned', 'Planificada'),
            ('implemented', 'Implementada'),
            ('declined', 'Descartada'),
        ],
        default='new'
    )
    
    internal_notes = models.TextField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_suggestions'
    )
    
    # Metadatos
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sugerencia de Mejora"
        verbose_name_plural = "Sugerencias de Mejora"
    
    def __str__(self):
        return f"{self.title} ({self.get_suggestion_type_display()})"
