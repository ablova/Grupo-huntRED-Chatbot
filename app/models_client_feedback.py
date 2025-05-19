"""
Modelos para la gestión de feedback y satisfacción de clientes.

Este módulo contiene los modelos necesarios para el seguimiento y análisis
de la satisfacción de los clientes con los servicios prestados por Grupo huntRED®.
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

# Períodos recomendados para enviar encuestas a clientes
CLIENT_FEEDBACK_PERIODS = [30, 90, 180, 365]  # Días

CLIENT_FEEDBACK_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('SENT', 'Enviada'),
    ('COMPLETED', 'Completada')
]

class ClientFeedback(models.Model):
    """
    Modelo para gestionar el feedback de los clientes sobre los servicios
    prestados por Grupo huntRED®.
    """
    
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text="Empresa cliente que proporciona el feedback"
    )
    
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='client_feedback',
        help_text="Business Unit asociada a este feedback"
    )
    
    respondent = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_feedback_given',
        help_text="Persona que respondió la encuesta"
    )
    
    consultant = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_feedback_received',
        help_text="Consultor evaluado o responsable de la cuenta"
    )
    
    period_days = models.IntegerField(
        help_text="Período en días después del inicio de la relación comercial",
        default=90
    )
    
    status = models.CharField(
        max_length=20,
        choices=CLIENT_FEEDBACK_STATUS_CHOICES,
        default='PENDING',
        help_text="Estado del feedback"
    )
    
    responses = models.JSONField(
        default=dict,
        blank=True,
        help_text="Respuestas a la encuesta en formato JSON"
    )
    
    satisfaction_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Puntuación general de satisfacción (0-10)"
    )
    
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se envió la encuesta"
    )
    
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se completó la encuesta"
    )
    
    token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Token único para acceder a la encuesta"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales sobre el feedback"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Feedback de Cliente"
        verbose_name_plural = "Feedback de Clientes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['empresa']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['status']),
            models.Index(fields=['period_days']),
        ]
    
    def __str__(self):
        return f"Feedback de {self.empresa.name} - {self.period_days} días"
    
    def record_responses(self, response_data):
        """
        Registra las respuestas recibidas y calcula el puntaje de satisfacción.
        
        Args:
            response_data (dict): Datos de respuesta de la encuesta
            
        Returns:
            bool: True si se grabó correctamente
        """
        self.responses = response_data
        self.status = 'COMPLETED'
        self.completed_date = timezone.now()
        
        # Calcular puntaje general de satisfacción
        if 'general_satisfaction' in response_data:
            try:
                self.satisfaction_score = float(response_data['general_satisfaction'])
            except (ValueError, TypeError):
                pass
        
        self.save(update_fields=['responses', 'status', 'completed_date', 'satisfaction_score'])
        return True
    
    def is_low_satisfaction(self):
        """
        Verifica si la satisfacción es baja y requiere atención.
        
        Returns:
            bool: True si la satisfacción es < 6
        """
        return self.satisfaction_score is not None and self.satisfaction_score < 6.0
    
    def get_improvement_areas(self):
        """
        Identifica áreas de mejora según las respuestas.
        
        Returns:
            list: Lista de áreas que necesitan mejora
        """
        improvement_areas = []
        
        if not self.responses:
            return improvement_areas
            
        # Verificar puntuaciones bajas
        if self.responses.get('candidate_quality') and float(self.responses.get('candidate_quality')) < 7:
            improvement_areas.append('calidad_candidatos')
            
        if self.responses.get('recruitment_speed') and float(self.responses.get('recruitment_speed')) < 7:
            improvement_areas.append('velocidad_reclutamiento')
            
        if self.responses.get('clear_communication') == 'no':
            improvement_areas.append('comunicacion')
            
        if self.responses.get('candidate_adaptation') == 'no':
            improvement_areas.append('adaptacion_candidatos')
            
        if self.responses.get('would_recommend') == 'no':
            improvement_areas.append('reputacion_general')
            
        return improvement_areas


class ClientFeedbackSchedule(models.Model):
    """
    Modelo para gestionar la programación de encuestas de satisfacción a clientes.
    """
    
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.CASCADE,
        related_name='feedback_schedules',
        help_text="Empresa cliente a la que se enviará la encuesta"
    )
    
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.CASCADE,
        related_name='client_feedback_schedules',
        help_text="Business Unit asociada"
    )
    
    start_date = models.DateTimeField(
        help_text="Fecha de inicio de la relación comercial"
    )
    
    next_feedback_date = models.DateTimeField(
        help_text="Fecha para la próxima encuesta"
    )
    
    period_days = models.IntegerField(
        help_text="Período en días para la próxima encuesta",
        choices=[(p, f"{p} días") for p in CLIENT_FEEDBACK_PERIODS],
        default=90
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si la programación está activa"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Programación de Feedback"
        verbose_name_plural = "Programaciones de Feedback"
        ordering = ['next_feedback_date']
    
    def __str__(self):
        return f"Programación para {self.empresa.name} - {self.period_days} días"
    
    def update_next_feedback_date(self):
        """
        Actualiza la fecha de la próxima encuesta al siguiente período.
        
        Returns:
            datetime: Nueva fecha programada
        """
        # Si es la primera encuesta, mantener el period_days actual
        # Si ya se han enviado encuestas, pasar al siguiente período
        next_index = CLIENT_FEEDBACK_PERIODS.index(self.period_days) + 1
        
        if next_index < len(CLIENT_FEEDBACK_PERIODS):
            self.period_days = CLIENT_FEEDBACK_PERIODS[next_index]
            
        self.next_feedback_date = timezone.now() + timezone.timedelta(days=self.period_days)
        self.save(update_fields=['period_days', 'next_feedback_date'])
        
        return self.next_feedback_date
