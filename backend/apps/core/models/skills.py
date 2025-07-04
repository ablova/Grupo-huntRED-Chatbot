"""
Skills Models - Sistema huntRED® v2
Modelos para habilidades, competencias y evaluaciones avanzadas.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from typing import Dict, Any, List
import uuid


class Skill(models.Model):
    """
    Modelo para habilidades y competencias con categorización avanzada.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True,
                          help_text="Nombre de la habilidad")
    slug = models.SlugField(max_length=120, unique=True, blank=True,
                          help_text="Slug para URLs")
    aliases = ArrayField(models.CharField(max_length=100), default=list, blank=True,
                        help_text="Nombres alternativos para la habilidad")
    
    # === CATEGORIZACIÓN ===
    CATEGORY_CHOICES = [
        ('technical', 'Técnica'),
        ('soft', 'Soft Skills'),
        ('language', 'Idioma'),
        ('certification', 'Certificación'),
        ('domain', 'Dominio específico'),
        ('leadership', 'Liderazgo'),
        ('communication', 'Comunicación'),
        ('analytical', 'Analítica'),
        ('creative', 'Creativa'),
        ('digital', 'Digital'),
        ('other', 'Otro')
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES,
                              db_index=True, help_text="Categoría de la habilidad")
    
    subcategory = models.CharField(max_length=100, blank=True, null=True,
                                 help_text="Subcategoría específica")
    
    # === COMPLEJIDAD Y NIVEL ===
    COMPLEXITY_CHOICES = [
        ('basic', 'Básica'),
        ('intermediate', 'Intermedia'),
        ('advanced', 'Avanzada'),
        ('expert', 'Experta'),
        ('master', 'Maestría')
    ]
    complexity_level = models.CharField(max_length=20, choices=COMPLEXITY_CHOICES,
                                      default='intermediate',
                                      help_text="Nivel de complejidad de la habilidad")
    
    learning_curve = models.PositiveSmallIntegerField(
        default=6,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Tiempo estimado de aprendizaje en meses"
    )
    
    # === DESCRIPCIÓN ===
    description = models.TextField(blank=True, help_text="Descripción detallada de la habilidad")
    keywords = ArrayField(models.CharField(max_length=50), default=list, blank=True,
                         help_text="Palabras clave relacionadas")
    
    # === INFORMACIÓN DEL MERCADO ===
    demand_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Puntuación de demanda en el mercado (0-1)"
    )
    growth_potential = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Potencial de crecimiento (0-1)"
    )
    market_salary_impact = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(3.0)],
        help_text="Impacto en salario (multiplicador)"
    )
    
    # === RELACIONES ===
    related_skills = models.ManyToManyField('self', blank=True, symmetrical=False,
                                          related_name='related_to',
                                          help_text="Habilidades relacionadas")
    prerequisite_skills = models.ManyToManyField('self', blank=True, symmetrical=False,
                                               related_name='enables_skills',
                                               help_text="Habilidades prerequisito")
    
    # === CERTIFICACIÓN ===
    certification_required = models.BooleanField(default=False,
                                                help_text="¿Requiere certificación?")
    certification_providers = models.JSONField(default=list, blank=True,
                                             help_text="Proveedores de certificación")
    certification_validity_months = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Meses de validez de la certificación"
    )
    
    # === RECURSOS DE APRENDIZAJE ===
    learning_resources = models.JSONField(default=dict, blank=True, help_text="""
    Recursos de aprendizaje asociados:
    {
        'courses': [
            {
                'title': 'Curso de Python',
                'provider': 'Coursera',
                'url': 'https://coursera.org/python',
                'duration_hours': 40,
                'level': 'beginner'
            }
        ],
        'books': [
            {
                'title': 'Python Crash Course',
                'author': 'Eric Matthes',
                'isbn': '978-1593279288'
            }
        ],
        'videos': [],
        'practice_platforms': []
    }
    """)
    
    # === INDUSTRIAS ===
    relevant_industries = ArrayField(
        models.CharField(max_length=100),
        default=list, blank=True,
        help_text="Industrias donde es relevante esta habilidad"
    )
    
    # === MÉTRICAS ===
    usage_count = models.PositiveIntegerField(default=0,
                                            help_text="Número de veces que se ha utilizado")
    assessment_count = models.PositiveIntegerField(default=0,
                                                 help_text="Número de evaluaciones realizadas")
    average_proficiency = models.FloatField(default=0.0,
                                          validators=[MinValueValidator(0), MaxValueValidator(100)],
                                          help_text="Nivel promedio de competencia")
    
    # === CONFIGURACIÓN ===
    is_active = models.BooleanField(default=True, db_index=True,
                                  help_text="¿La habilidad está activa?")
    is_trending = models.BooleanField(default=False, db_index=True,
                                    help_text="¿Es una habilidad en tendencia?")
    is_critical = models.BooleanField(default=False,
                                    help_text="¿Es una habilidad crítica?")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    last_used = models.DateTimeField(null=True, blank=True,
                                   help_text="Última vez que se utilizó")
    
    class Meta:
        verbose_name = "Habilidad"
        verbose_name_plural = "Habilidades"
        ordering = ['name']
        indexes = [
            models.Index(fields=['category', 'complexity_level']),
            models.Index(fields=['demand_score', 'growth_potential']),
            models.Index(fields=['is_active', 'is_trending']),
            models.Index(fields=['usage_count', 'average_proficiency']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    def increment_usage(self):
        """Incrementa el contador de uso."""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    def get_related_skills(self):
        """Obtiene habilidades relacionadas."""
        return self.related_skills.filter(is_active=True)
    
    def get_prerequisite_skills(self):
        """Obtiene habilidades prerequisito."""
        return self.prerequisite_skills.filter(is_active=True)
    
    def get_learning_resources(self):
        """Obtiene recursos de aprendizaje estructurados."""
        return self.learning_resources
    
    def get_certification_providers(self):
        """Obtiene proveedores de certificación."""
        return self.certification_providers
    
    def calculate_demand_score(self):
        """Calcula la puntuación de demanda basada en uso y mercado."""
        # Implementar lógica basada en datos de mercado y uso
        base_score = min(self.usage_count / 1000, 1.0)  # Normalizar uso
        market_factor = 1.0  # Factor de mercado (implementar con datos externos)
        self.demand_score = min(base_score * market_factor, 1.0)
        return self.demand_score
    
    def calculate_growth_potential(self):
        """Calcula el potencial de crecimiento."""
        # Implementar lógica basada en tendencias del mercado
        if self.is_trending:
            self.growth_potential = min(self.growth_potential + 0.1, 1.0)
        return self.growth_potential
    
    def update_average_proficiency(self):
        """Actualiza el promedio de competencia basado en evaluaciones."""
        assessments = self.skillassessment_set.all()
        if assessments.exists():
            total_score = sum(assessment.proficiency_score for assessment in assessments)
            self.average_proficiency = total_score / assessments.count()
            self.save(update_fields=['average_proficiency'])


class SkillAssessment(models.Model):
    """
    Modelo para evaluaciones de habilidades de candidatos.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # === RELACIONES ===
    person = models.ForeignKey('Person', on_delete=models.CASCADE,
                             related_name='skill_assessments',
                             help_text="Persona evaluada")
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE,
                            related_name='assessments',
                            help_text="Habilidad evaluada")
    evaluator = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                null=True, blank=True,
                                help_text="Persona que realizó la evaluación")
    
    # === EVALUACIÓN ===
    PROFICIENCY_CHOICES = [
        (1, 'Principiante'),
        (2, 'Básico'),
        (3, 'Intermedio'),
        (4, 'Avanzado'),
        (5, 'Experto')
    ]
    proficiency_level = models.PositiveSmallIntegerField(
        choices=PROFICIENCY_CHOICES,
        help_text="Nivel de competencia (1-5)"
    )
    proficiency_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Puntuación de competencia (0-100)"
    )
    
    # === MÉTODO DE EVALUACIÓN ===
    ASSESSMENT_TYPE_CHOICES = [
        ('self_assessment', 'Autoevaluación'),
        ('peer_review', 'Evaluación por pares'),
        ('manager_review', 'Evaluación gerencial'),
        ('technical_test', 'Prueba técnica'),
        ('project_based', 'Basada en proyecto'),
        ('certification', 'Certificación'),
        ('interview', 'Entrevista'),
        ('portfolio', 'Portafolio')
    ]
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES,
                                     help_text="Tipo de evaluación")
    
    # === DETALLES ===
    evidence = models.JSONField(default=dict, blank=True, help_text="""
    Evidencia de la competencia:
    {
        'projects': ['Proyecto Python', 'API REST'],
        'certifications': ['AWS Certified'],
        'experience_years': 3,
        'companies': ['TechCorp', 'StartupXYZ'],
        'achievements': ['Implementó microservicios']
    }
    """)
    
    notes = models.TextField(blank=True, help_text="Notas adicionales de la evaluación")
    strengths = ArrayField(models.CharField(max_length=200), default=list, blank=True,
                         help_text="Fortalezas identificadas")
    areas_for_improvement = ArrayField(models.CharField(max_length=200), default=list, blank=True,
                                     help_text="Áreas de mejora")
    
    # === RECOMENDACIONES ===
    learning_recommendations = models.JSONField(default=list, blank=True,
                                              help_text="Recomendaciones de aprendizaje")
    next_assessment_date = models.DateField(null=True, blank=True,
                                          help_text="Fecha recomendada para próxima evaluación")
    
    # === VALIDEZ ===
    is_valid = models.BooleanField(default=True, db_index=True,
                                 help_text="¿La evaluación es válida?")
    expires_at = models.DateField(null=True, blank=True,
                                help_text="Fecha de expiración de la evaluación")
    
    # === TIMESTAMPS ===
    assessed_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Evaluación de Habilidad"
        verbose_name_plural = "Evaluaciones de Habilidades"
        ordering = ['-assessed_at']
        unique_together = ['person', 'skill', 'assessed_at']
        indexes = [
            models.Index(fields=['person', 'skill']),
            models.Index(fields=['proficiency_score', 'assessment_type']),
            models.Index(fields=['is_valid', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.person} - {self.skill} ({self.proficiency_score}%)"
    
    @property
    def is_expired(self):
        """Verifica si la evaluación ha expirado."""
        if self.expires_at:
            return timezone.now().date() > self.expires_at
        return False
    
    def calculate_proficiency_score(self):
        """Calcula la puntuación de competencia basada en evidencia."""
        base_score = self.proficiency_level * 20  # Convierte 1-5 a 20-100
        
        # Ajustar basado en evidencia
        evidence_bonus = 0
        if self.evidence.get('certifications'):
            evidence_bonus += 10
        if self.evidence.get('experience_years', 0) > 2:
            evidence_bonus += 5
        if self.evidence.get('projects'):
            evidence_bonus += len(self.evidence['projects']) * 2
        
        self.proficiency_score = min(base_score + evidence_bonus, 100)
        return self.proficiency_score
    
    def generate_learning_recommendations(self):
        """Genera recomendaciones de aprendizaje."""
        recommendations = []
        
        if self.proficiency_score < 60:
            # Principiante - recomendar cursos básicos
            skill_resources = self.skill.learning_resources.get('courses', [])
            beginner_courses = [course for course in skill_resources if course.get('level') == 'beginner']
            recommendations.extend(beginner_courses)
        
        elif self.proficiency_score < 80:
            # Intermedio - recomendar práctica y proyectos
            recommendations.append({
                'type': 'practice',
                'description': f'Realizar más proyectos prácticos en {self.skill.name}'
            })
        
        else:
            # Avanzado - recomendar certificaciones y especialización
            if self.skill.certification_required:
                recommendations.append({
                    'type': 'certification',
                    'description': f'Obtener certificación en {self.skill.name}',
                    'providers': self.skill.certification_providers
                })
        
        self.learning_recommendations = recommendations
        return recommendations
    
    def save(self, *args, **kwargs):
        """Override save para cálculos automáticos."""
        if not self.proficiency_score:
            self.calculate_proficiency_score()
        
        # Calcular fecha de expiración si no existe
        if not self.expires_at and self.skill.certification_validity_months:
            from dateutil.relativedelta import relativedelta
            self.expires_at = self.assessed_at.date() + relativedelta(months=self.skill.certification_validity_months)
        
        super().save(*args, **kwargs)
        
        # Actualizar métricas de la habilidad
        self.skill.assessment_count += 1
        self.skill.update_average_proficiency()


class SkillCategory(models.Model):
    """
    Modelo para categorías personalizadas de habilidades.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE,
                                      null=True, blank=True,
                                      related_name='subcategories')
    color = models.CharField(max_length=7, default='#007bff',
                           help_text="Color hexadecimal para UI")
    icon = models.CharField(max_length=50, blank=True,
                          help_text="Icono de FontAwesome")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Categoría de Habilidad"
        verbose_name_plural = "Categorías de Habilidades"
        ordering = ['name']
    
    def __str__(self):
        return self.name