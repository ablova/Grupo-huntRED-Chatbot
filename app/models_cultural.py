# app/models_cultural.py
# Modelos relacionados con el análisis cultural
# Este archivo debe ser importado desde models.py

"""Modelos de datos para el Sistema de Análisis de Cultura Organizacional de Grupo huntRED

Este módulo define los modelos de datos necesarios para la evaluación, análisis y 
reporte de compatibilidad cultural entre personas y organizaciones.

Optimizado para bajo uso de CPU y alta escalabilidad, siguiendo reglas globales.
"""

from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.crypto import get_random_string
from app.models import Person, BusinessUnit, Organization, Application, Vacante, Team, Department, User
import uuid
import hashlib


class CulturalDimension(models.Model):
    """Define una dimensión cultural para evaluación y análisis"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=50, default='general')
    weight = models.FloatField(default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(10.0)])
    icon = models.CharField(max_length=50, help_text="Nombre del icono para UI", null=True, blank=True)
    active = models.BooleanField(default=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [models.Index(fields=['business_unit', 'active'])]
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class CulturalValue(models.Model):
    """Representa un valor cultural específico dentro de una dimensión"""
    dimension = models.ForeignKey(CulturalDimension, on_delete=models.CASCADE, related_name='values')
    name = models.CharField(max_length=100)
    description = models.TextField()
    positive_statement = models.TextField(help_text="Afirmación positiva para evaluación")
    negative_statement = models.TextField(help_text="Afirmación negativa para evaluación", null=True, blank=True)
    weight = models.FloatField(default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(5.0)])
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['dimension', 'name']
        indexes = [models.Index(fields=['dimension', 'active'])]
    
    def __str__(self):
        return f"{self.name} ({self.dimension.name})"


class OrganizationalCulture(models.Model):
    """Define el perfil cultural de una organización"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='cultural_profiles')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    is_current = models.BooleanField(default=True, help_text="Si es el perfil cultural actual")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    completion_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    confidence_score = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    status = models.CharField(max_length=50, default='in_progress', choices=[
        ('not_started', 'No iniciado'),
        ('in_progress', 'En progreso'),
        ('partial', 'Datos parciales (>80%)'),
        ('complete', 'Completo')
    ])
    cultural_insights = JSONField(default=dict, help_text="Insights culturales agregados")
    
    class Meta:
        ordering = ['-is_current', '-updated_at']
        indexes = [models.Index(fields=['organization', 'is_current'])]
    
    def __str__(self):
        return f"Perfil cultural: {self.organization.name} ({self.status})"

    def update_completion_status(self):
        """Actualiza el estado de compleción basado en el porcentaje"""
        if self.completion_percentage >= 100:
            self.status = 'complete'
        elif self.completion_percentage >= 80:
            self.status = 'partial'
        elif self.completion_percentage > 0:
            self.status = 'in_progress'
        else:
            self.status = 'not_started'
        self.save(update_fields=['status'])


class CulturalProfile(models.Model):
    """Representa un perfil cultural de una persona"""
    person = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='cultural_profile')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_assessment_date = models.DateTimeField(null=True, blank=True)
    
    # Puntajes por dimensión cultural (escala 0-5)
    values_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de valores (0-5)"
    )
    motivators_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de motivadores (0-5)"
    )
    interests_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de intereses (0-5)"
    )
    work_style_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de estilo de trabajo (0-5)"
    )
    social_impact_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de impacto social (0-5)"
    )
    generational_values_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de valores generacionales (0-5)"
    )
    
    # Datos de transformación y liderazgo
    leadership_potential = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Potencial de liderazgo (0-100)"
    )
    transformation_potential = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Potencial como agente de transformación (0-100)"
    )
    risk_factor = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Factor de riesgo cultural (0-100)"
    )
    
    # Datos estructurados del perfil
    compatibility_data = JSONField(
        default=dict,
        help_text="Datos de compatibilidad con diferentes culturas organizacionales"
    )
    
    strengths = models.JSONField(
        default=list,
        help_text="Fortalezas culturales identificadas"
    )
    
    areas_of_improvement = models.JSONField(
        default=list,
        help_text="Áreas de mejora cultural identificadas"
    )
    
    recommendations = models.JSONField(
        default=list,
        help_text="Lista de recomendaciones basadas en el perfil cultural"
    )
    
    # Todos los datos del perfil
    full_profile_data = models.JSONField(
        default=dict,
        help_text="Datos completos del perfil cultural"
    )
    
    # Metadatos
    last_test_date = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha de la última evaluación cultural"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil Cultural"
        verbose_name_plural = "Perfiles Culturales"
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['last_test_date']),
        ]
    
    def __str__(self):
        return f"Perfil Cultural de {self.person}"
    
    def get_cultural_match_percentage(self, business_unit=None):
        """
        Obtiene el porcentaje de compatibilidad cultural con una unidad de negocio específica
        o general si no se especifica.
        
        Args:
            business_unit (str, optional): Unidad de negocio. Defaults to None.
            
        Returns:
            float: Porcentaje de compatibilidad (0-100)
        """
        if not business_unit:
            business_unit = 'general'
        
        if not self.compatibility_data:
            return 0.0
        
        return self.compatibility_data.get(business_unit, 0.0)
    
    def get_cultural_fit_level(self, business_unit=None):
        """
        Obtiene el nivel de compatibilidad cultural en formato de texto.
        
        Args:
            business_unit (str, optional): Unidad de negocio. Defaults to None.
            
        Returns:
            str: Nivel de compatibilidad (Excelente, Muy bueno, Bueno, Regular, Bajo)
        """
        percentage = self.get_cultural_match_percentage(business_unit)
        
        if percentage >= 85:
            return "Excelente"
        elif percentage >= 70:
            return "Muy bueno"
        elif percentage >= 50:
            return "Bueno"
        elif percentage >= 30:
            return "Regular"
        else:
            return "Bajo"
    
    def update_from_test_results(self, test_results):
        """
        Actualiza el perfil cultural con los resultados de un nuevo test.
        
        Args:
            test_results (dict): Resultados del test cultural
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Extraer puntajes
            scores = test_results.get('scores', {})
            self.values_score = scores.get('values', self.values_score)
            self.motivators_score = scores.get('motivators', self.motivators_score)
            self.interests_score = scores.get('interests', self.interests_score)
            self.work_style_score = scores.get('work_style', self.work_style_score)
            self.social_impact_score = scores.get('social_impact', self.social_impact_score)
            self.generational_values_score = scores.get('generational_values', self.generational_values_score)
            
            # Actualizar datos estructurados
            self.compatibility_data = test_results.get('compatibility', self.compatibility_data)
            self.strengths = test_results.get('strengths', self.strengths)
            self.areas_for_improvement = test_results.get('areas_for_improvement', self.areas_for_improvement)
            self.recommendations = test_results.get('recommendations', self.recommendations)
            
            # Actualizar datos completos
            self.full_profile_data = test_results
            
            # Actualizar fecha de último test
            self.last_test_date = timezone.now()
            
            self.save()
            return True
        except Exception as e:
            # Loggear el error pero no propagarlo
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error actualizando perfil cultural: {e}", exc_info=True)
            return False

class CulturalFitReport(models.Model):
    """
    Modelo para almacenar reportes de compatibilidad cultural.
    Esto permite guardar análisis específicos de compatibilidad cultural
    entre una persona y una empresa u otra persona.
    """
    report_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador único del reporte de compatibilidad cultural"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Título del reporte de compatibilidad cultural"
    )
    
    person = models.ForeignKey(
        'Person',
        on_delete=models.CASCADE,
        related_name='cultural_fit_reports',
        help_text="Persona evaluada en este reporte"
    )
    
    target_entity_type = models.CharField(
        max_length=20,
        choices=[
            ('COMPANY', 'Empresa'),
            ('PERSON', 'Persona'),
            ('TEAM', 'Equipo'),
            ('BU', 'Unidad de Negocio')
        ],
        default='COMPANY',
        help_text="Tipo de entidad con la que se compara la compatibilidad"
    )
    
    target_entity_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID de la entidad objetivo (empresa, persona, equipo, etc.)"
    )
    
    business_unit = models.ForeignKey(
        'BusinessUnit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cultural_fit_reports',
        help_text="Unidad de negocio relacionada con este reporte"
    )
    
    compatibility_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Puntuación global de compatibilidad cultural (0-100)"
    )
    
    report_data = models.JSONField(
        default=dict,
        help_text="Datos completos del reporte de compatibilidad cultural"
    )
    
    created_by = models.ForeignKey(
        'Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cultural_fit_reports',
        help_text="Persona que generó este reporte"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reporte de Compatibilidad Cultural"
        verbose_name_plural = "Reportes de Compatibilidad Cultural"
        indexes = [
            models.Index(fields=['person']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['target_entity_type', 'target_entity_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Reporte Cultural: {self.title}"
    
    def get_compatibility_level(self):
        """
        Obtiene el nivel de compatibilidad cultural en formato de texto.
        
        Returns:
            str: Nivel de compatibilidad (Excelente, Muy bueno, Bueno, Regular, Bajo)
        """
        if self.compatibility_score >= 85:
            return "Excelente"
        elif self.compatibility_score >= 70:
            return "Muy bueno"
        elif self.compatibility_score >= 50:
            return "Bueno"
        elif self.compatibility_score >= 30:
            return "Regular"
        else:
            return "Bajo"
