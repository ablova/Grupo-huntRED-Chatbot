# app/models_cultural.py
# Modelos relacionados con el análisis cultural
# Este archivo debe ser importado desde models.py

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class PersonCulturalProfile(models.Model):
    """
    Modelo para almacenar el perfil cultural de una persona.
    Almacena los resultados del test cultural y las preferencias del candidato.
    """
    person = models.OneToOneField(
        'Person',
        on_delete=models.CASCADE,
        related_name='cultural_profile',
        help_text="Persona a la que pertenece este perfil cultural"
    )
    
    # Puntajes por dimensión cultural (escala 1-5)
    values_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de valores (1-5)"
    )
    
    motivators_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de motivadores (1-5)"
    )
    
    interests_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de intereses (1-5)"
    )
    
    work_style_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de estilo de trabajo (1-5)"
    )
    
    social_impact_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de impacto social (1-5)"
    )
    
    generational_values_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Puntaje en la dimensión de valores generacionales (1-5)"
    )
    
    # Datos estructurados del perfil
    compatibility_data = models.JSONField(
        default=dict,
        help_text="Datos de compatibilidad con diferentes unidades de negocio"
    )
    
    strengths = models.JSONField(
        default=list,
        help_text="Lista de fortalezas culturales identificadas"
    )
    
    areas_for_improvement = models.JSONField(
        default=list,
        help_text="Lista de áreas de mejora cultural identificadas"
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
