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
from django.conf import settings

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
            models.Index(fields=['stage', 'service_type'], name='feedback_service_stage_type_idx'),
            models.Index(fields=['company'], name='feedback_service_company_idx'),
            models.Index(fields=['created_at'], name='feedback_service_created_at_idx'),
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
        settings.AUTH_USER_MODEL,
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


class SkillFeedback(models.Model):
    """
    Retroalimentación específica sobre la detección de skills.
    
    Captura la evaluación de la precisión del sistema de detección de skills
    y proporciona información para mejorar el modelo ML.
    """
    
    # Relaciones
    base_feedback = models.OneToOneField(
        ServiceFeedback,
        on_delete=models.CASCADE,
        related_name='skill_feedback',
        primary_key=True
    )
    
    # Validación de Skills
    skill_accuracy = models.CharField(
        max_length=20,
        choices=[
            ('CORRECT', 'Totalmente Correcto'),
            ('PARTIAL', 'Parcialmente Correcto'),
            ('INCORRECT', 'Incorrecto')
        ],
        verbose_name="Precisión de la detección"
    )
    missing_skills = models.JSONField(
        null=True, blank=True,
        verbose_name="Skills no detectados"
    )
    extra_skills = models.JSONField(
        null=True, blank=True,
        verbose_name="Skills detectados incorrectamente"
    )
    
    # Evaluación del Candidato
    was_hired = models.BooleanField(
        default=False,
        verbose_name="¿Fue contratado?"
    )
    technical_fit = models.IntegerField(
        null=True, blank=True,
        verbose_name="Ajuste Técnico (1-5)"
    )
    cultural_fit = models.IntegerField(
        null=True, blank=True,
        verbose_name="Ajuste Cultural (1-5)"
    )
    strengths = models.TextField(
        null=True, blank=True,
        verbose_name="Fortalezas"
    )
    areas_for_improvement = models.TextField(
        null=True, blank=True,
        verbose_name="Áreas de Mejora"
    )
    
    # Análisis de Potencial
    potential_roles = models.JSONField(
        null=True, blank=True,
        verbose_name="Roles Potenciales"
    )
    growth_potential = models.IntegerField(
        null=True, blank=True,
        verbose_name="Potencial de Crecimiento (1-5)"
    )
    development_path = models.TextField(
        null=True, blank=True,
        verbose_name="Ruta de Desarrollo"
    )
    
    # Nuevo: Análisis de Desarrollo Detallado
    development_time = models.CharField(
        max_length=20,
        choices=[
            ('1-3', '1-3 meses'),
            ('3-6', '3-6 meses'),
            ('6-12', '6-12 meses'),
            ('12+', 'Más de 12 meses')
        ],
        null=True, blank=True,
        verbose_name="Tiempo Estimado de Desarrollo"
    )
    critical_skills = models.JSONField(
        null=True, blank=True,
        verbose_name="Skills Críticos para Desarrollo"
    )
    training_recommendations = models.TextField(
        null=True, blank=True,
        verbose_name="Formación Recomendada"
    )
    practical_experience = models.TextField(
        null=True, blank=True,
        verbose_name="Experiencia Práctica Recomendada"
    )
    mentorship_needs = models.TextField(
        null=True, blank=True,
        verbose_name="Necesidades de Mentoría"
    )
    
    # Nuevo: Comparativa con Perfil Ideal
    main_gaps = models.TextField(
        null=True, blank=True,
        verbose_name="Gaps Principales"
    )
    comparative_advantages = models.TextField(
        null=True, blank=True,
        verbose_name="Ventajas Comparativas"
    )
    development_risks = models.TextField(
        null=True, blank=True,
        verbose_name="Riesgos de Desarrollo"
    )
    
    # Nuevo: Seguimiento y Alertas
    development_status = models.CharField(
        max_length=20,
        choices=[
            ('NOT_STARTED', 'No Iniciado'),
            ('IN_PROGRESS', 'En Progreso'),
            ('COMPLETED', 'Completado'),
            ('ON_HOLD', 'En Pausa')
        ],
        default='NOT_STARTED',
        verbose_name="Estado del Desarrollo"
    )
    last_review_date = models.DateField(
        null=True, blank=True,
        verbose_name="Última Revisión"
    )
    next_review_date = models.DateField(
        null=True, blank=True,
        verbose_name="Próxima Revisión"
    )
    critical_skills_alert = models.BooleanField(
        default=False,
        verbose_name="Alerta de Skills Críticos"
    )
    
    # Nuevo: Benchmarks y Métricas
    market_benchmark = models.JSONField(
        null=True, blank=True,
        verbose_name="Benchmarks del Mercado"
    )
    role_specific_metrics = models.JSONField(
        null=True, blank=True,
        verbose_name="Métricas Específicas del Rol"
    )
    performance_indicators = models.JSONField(
        null=True, blank=True,
        verbose_name="Indicadores de Rendimiento"
    )
    
    # Contexto de Mercado
    market_demand = models.IntegerField(
        null=True, blank=True,
        verbose_name="Demanda en el Mercado (1-5)"
    )
    salary_range = models.CharField(
        max_length=100,
        null=True, blank=True,
        verbose_name="Rango Salarial"
    )
    market_notes = models.TextField(
        null=True, blank=True,
        verbose_name="Notas de Mercado"
    )
    
    # Metadatos
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feedback de Skills"
        verbose_name_plural = "Feedback de Skills"
        indexes = [
            models.Index(fields=['development_status'], name='feedback_skill_development_status_idx'),
            models.Index(fields=['critical_skills_alert'], name='feedback_skill_critical_alert_idx'),
            models.Index(fields=['next_review_date'], name='feedback_skill_next_review_idx'),
        ]
    
    def __str__(self):
        return f"Feedback de Skills: {self.base_feedback}"
    
    def update_development_status(self):
        """Actualiza el estado del desarrollo basado en los skills críticos y el tiempo."""
        if not self.critical_skills:
            return
        
        # Lógica para actualizar el estado
        if self.development_status == 'NOT_STARTED':
            self.development_status = 'IN_PROGRESS'
        elif self.development_status == 'IN_PROGRESS':
            # Verificar si se han completado los skills críticos
            # Implementar lógica específica aquí
            pass
    
    def check_critical_skills_alert(self):
        """Verifica si hay skills críticos que requieren atención inmediata."""
        if not self.critical_skills:
            return False
        
        # Implementar lógica de alerta basada en:
        # - Tiempo desde la última revisión
        # - Progreso en skills críticos
        # - Cambios en el mercado
        return self.critical_skills_alert
    
    def get_market_benchmarks(self):
        """Obtiene benchmarks actualizados del mercado."""
        # Implementar lógica para obtener benchmarks
        # Podría incluir:
        # - Salarios promedio
        # - Demandas de skills
        # - Tendencias del mercado
        return self.market_benchmark
    
    def generate_development_report(self):
        """Genera un reporte detallado del desarrollo."""
        return {
            'status': self.development_status,
            'critical_skills': self.critical_skills,
            'progress': {
                'training': self.training_recommendations,
                'experience': self.practical_experience,
                'mentorship': self.mentorship_needs
            },
            'next_steps': self.development_path,
            'alerts': self.check_critical_skills_alert(),
            'market_context': {
                'demand': self.market_demand,
                'benchmarks': self.get_market_benchmarks()
            }
        }
