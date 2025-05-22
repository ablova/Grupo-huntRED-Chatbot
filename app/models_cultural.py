# app/models_cultural.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class PersonCulturalProfile(models.Model):
    """Modelo para almacenar el perfil cultural de una persona."""
    
    person = models.OneToOneField(
        'Person',
        on_delete=models.CASCADE,
        related_name='cultural_profile',
        help_text="Persona asociada a este perfil cultural"
    )
    
    # Dimensiones culturales
    individualism_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación en individualismo vs colectivismo"
    )
    hierarchy_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación en jerarquía vs igualdad"
    )
    stability_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación en estabilidad vs cambio"
    )
    task_orientation_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación en orientación a tareas vs personas"
    )
    formality_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación en formalidad vs informalidad"
    )
    innovation_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación en innovación vs tradición"
    )
    
    # Valores core
    values_alignment = models.JSONField(
        default=dict,
        help_text="Alineación con valores core de la organización"
    )
    
    # Preferencias de trabajo
    work_preferences = models.JSONField(
        default=dict,
        help_text="Preferencias de trabajo y ambiente laboral"
    )
    
    # Metadatos
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Perfil Cultural"
        verbose_name_plural = "Perfiles Culturales"
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['last_updated'])
        ]
    
    def __str__(self):
        return f"Perfil Cultural de {self.person}"
    
    def get_cultural_dimensions(self):
        """Obtiene todas las dimensiones culturales en un diccionario."""
        return {
            'individualism': self.individualism_score,
            'hierarchy': self.hierarchy_score,
            'stability': self.stability_score,
            'task_orientation': self.task_orientation_score,
            'formality': self.formality_score,
            'innovation': self.innovation_score
        }
    
    def calculate_overall_fit(self, company_profile):
        """Calcula el fit cultural general con un perfil de compañía."""
        # Implementar lógica de cálculo de fit
        pass

class CulturalFitReport(models.Model):
    """Modelo para almacenar reportes de fit cultural."""
    
    person = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='cultural_fit_reports',
        help_text="Persona evaluada"
    )
    
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='cultural_fit_reports',
        help_text="Compañía evaluada"
    )
    
    # Puntuaciones
    overall_fit_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación general de fit cultural"
    )
    
    dimension_scores = models.JSONField(
        default=dict,
        help_text="Puntuaciones por dimensión cultural"
    )
    
    values_alignment = models.JSONField(
        default=dict,
        help_text="Alineación con valores de la compañía"
    )
    
    # Análisis y recomendaciones
    strengths = models.JSONField(
        default=list,
        help_text="Fortalezas identificadas"
    )
    
    areas_for_improvement = models.JSONField(
        default=list,
        help_text="Áreas de mejora identificadas"
    )
    
    recommendations = models.JSONField(
        default=list,
        help_text="Recomendaciones para mejorar el fit"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reporte de Fit Cultural"
        verbose_name_plural = "Reportes de Fit Cultural"
        unique_together = ['person', 'company']
        indexes = [
            models.Index(fields=['person', 'company']),
            models.Index(fields=['overall_fit_score']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"Fit Cultural: {self.person} - {self.company}"
    
    def get_fit_level(self):
        """Obtiene el nivel de fit basado en la puntuación general."""
        if self.overall_fit_score >= 0.8:
            return "Excelente"
        elif self.overall_fit_score >= 0.6:
            return "Bueno"
        elif self.overall_fit_score >= 0.4:
            return "Moderado"
        else:
            return "Bajo" 