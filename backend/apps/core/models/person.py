"""
Person Model - Sistema Completo huntRED® v2
Modelo central para candidatos con todas las funcionalidades del sistema original optimizado.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Dict, Any, List, Optional
import uuid
import json

from ..validators import validate_phone, validate_linkedin_url


class Person(models.Model):
    """
    Modelo principal para candidatos/personas en el sistema huntRED®.
    Incluye todas las funcionalidades del sistema original optimizadas.
    """
    
    # === IDENTIFICACIÓN BÁSICA ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number_interaction = models.IntegerField(default=0, help_text="Número de interacciones")
    ref_num = models.CharField(max_length=50, blank=True, null=True, 
                              help_text="Número de referencia para identificar origen del registro")
    
    # Información Personal
    nombre = models.CharField(max_length=100, db_index=True)
    apellido_paterno = models.CharField(max_length=200, blank=True, null=True)
    apellido_materno = models.CharField(max_length=200, blank=True, null=True)
    nacionalidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True, db_index=True)
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('N', 'Prefiero no decir')
    ]
    sexo = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    
    # === CONTACTO ===
    email = models.EmailField(unique=True, db_index=True)
    company_email = models.EmailField(blank=True, null=True, 
                                    help_text="Correo empresarial del contacto")
    phone = models.CharField(max_length=40, blank=True, null=True, 
                           validators=[validate_phone])
    linkedin_url = models.URLField(max_length=200, blank=True, null=True,
                                 validators=[validate_linkedin_url],
                                 help_text="URL del perfil de LinkedIn")
    
    # === CONFIGURACIÓN ===
    preferred_language = models.CharField(max_length=5, default='es_MX',
                                        help_text="Ej: es_MX, en_US")
    tos_accepted = models.BooleanField(default=False, db_index=True)
    
    # === BÚSQUEDA DE EMPLEO ===
    JOB_SEARCH_STATUS_CHOICES = [
        ('activa', 'Búsqueda Activa'),
        ('pasiva', 'Búsqueda Pasiva'),
        ('local', 'Solo Local'),
        ('remota', 'Solo Remoto'),
        ('no_busca', 'No en búsqueda'),
        ('hired', 'Contratado'),
        ('on_hold', 'En pausa')
    ]
    job_search_status = models.CharField(
        max_length=20, 
        choices=JOB_SEARCH_STATUS_CHOICES,
        blank=True, null=True,
        db_index=True,
        help_text="Estado actual de la búsqueda de empleo"
    )
    
    # === EXPERIENCIA Y HABILIDADES ===
    skills = models.TextField(blank=True, null=True, 
                            help_text="Listado libre de skills del candidato")
    experience_years = models.IntegerField(blank=True, null=True,
                                         validators=[MinValueValidator(0), MaxValueValidator(60)],
                                         help_text="Años totales de experiencia")
    desired_job_types = models.CharField(max_length=100, blank=True, null=True,
                                       help_text="Tipos de trabajo deseados")
    
    # === CV Y ANÁLISIS ===
    cv_file = models.FileField(upload_to='person_files/', blank=True, null=True,
                              help_text="CV u otro documento del candidato")
    cv_parsed = models.BooleanField(default=False, db_index=True,
                                  help_text="Indica si el CV ha sido analizado")
    cv_analysis = models.JSONField(blank=True, null=True,
                                 help_text="Datos analizados del CV")
    
    # === DATOS ESTRUCTURADOS ===
    salary_data = models.JSONField(default=dict, blank=True,
                                 help_text="Información salarial, beneficios y expectativas")
    personality_data = models.JSONField(default=dict, blank=True,
                                      help_text="Perfil de personalidad")
    experience_data = models.JSONField(default=dict, blank=True,
                                     help_text="Experiencia profesional detallada")
    metadata = models.JSONField(default=dict, blank=True,
                              help_text="Información adicional del candidato")
    
    # === CONTRATACIÓN ===
    hire_date = models.DateField(null=True, blank=True, db_index=True)
    
    # === GAMIFICACIÓN ===
    points = models.IntegerField(default=0, db_index=True)
    badges = models.ManyToManyField('Badge', blank=True, related_name='persons')
    
    # === WORKFLOW ===
    current_stage = models.ForeignKey('WorkflowStage', on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='candidatos', db_index=True)
    
    # === PERSONALIDAD (Big Five) ===
    openness = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    conscientiousness = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    extraversion = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    agreeableness = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    neuroticism = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # === ACTIVACIÓN WHATSAPP ===
    whatsapp_enabled = models.BooleanField(default=False, db_index=True,
                                         help_text="¿WhatsApp está activado para este usuario?")
    whatsapp_activation_token = models.CharField(max_length=36, blank=True, null=True,
                                               help_text="Token de activación para WhatsApp")
    whatsapp_activation_expires = models.DateTimeField(blank=True, null=True,
                                                      help_text="Fecha de expiración del token")
    
    # === TRABAJO EN GRUPO (Amigro) ===
    group_work_history = models.JSONField(default=list,
                                        help_text="Historial de trabajo en grupo")
    group_success_rate = models.FloatField(default=0.0,
                                         validators=[MinValueValidator(0), MaxValueValidator(1)],
                                         help_text="Tasa de éxito en trabajos grupales")
    group_stability = models.FloatField(default=0.0,
                                      validators=[MinValueValidator(0), MaxValueValidator(1)],
                                      help_text="Estabilidad en grupos de trabajo")
    community_integration = models.FloatField(default=0.0,
                                            validators=[MinValueValidator(0), MaxValueValidator(1)],
                                            help_text="Nivel de integración en la comunidad")
    
    # === ANÁLISIS GENERACIONAL ===
    generational_insights = models.JSONField(null=True, blank=True,
                                           help_text="Insights generacionales basados en edad y respuestas")
    motivational_insights = models.JSONField(null=True, blank=True,
                                           help_text="Perfil motivacional del candidato")
    work_style_preferences = models.JSONField(null=True, blank=True,
                                            help_text="Preferencias de estilo de trabajo")
    
    # === EVALUACIONES COMPLETADAS ===
    completed_evaluations = models.JSONField(default=list,
                                           help_text="Lista de evaluaciones completadas")
    
    # === RELACIONES ===
    social_connections = models.ManyToManyField('self', through='SocialConnection',
                                              symmetrical=False, related_name='connected_to')
    family_members = models.ManyToManyField('self', through='FamilyRelationship',
                                          symmetrical=False, related_name='related_family_members',
                                          blank=True)
    
    # === TIMESTAMPS ===
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['email', 'job_search_status']),
            models.Index(fields=['nombre', 'apellido_paterno']),
            models.Index(fields=['fecha_nacimiento', 'nacionalidad']),
            models.Index(fields=['experience_years', 'job_search_status']),
            models.Index(fields=['points', 'current_stage']),
            models.Index(fields=['whatsapp_enabled', 'tos_accepted']),
        ]
    
    def __str__(self):
        nombre_completo = f"{self.nombre} {self.apellido_paterno or ''} {self.apellido_materno or ''}".strip()
        return nombre_completo
    
    @property
    def full_name(self):
        """Retorna el nombre completo."""
        return str(self)
    
    @property
    def age(self):
        """Calcula la edad basada en fecha de nacimiento."""
        if not self.fecha_nacimiento:
            return None
        today = timezone.now().date()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    def is_profile_complete(self):
        """Verifica si el perfil está completo."""
        required_fields = ['nombre', 'apellido_paterno', 'email', 'phone', 'skills']
        missing_fields = [field for field in required_fields if not getattr(self, field, None)]
        return not missing_fields
    
    def get_generational_profile(self):
        """Obtiene el perfil generacional basado en la edad."""
        if not self.fecha_nacimiento:
            return None
            
        birth_year = self.fecha_nacimiento.year
        if 1946 <= birth_year <= 1964:
            return 'BB'  # Baby Boomers
        elif 1965 <= birth_year <= 1980:
            return 'X'   # Generación X
        elif 1981 <= birth_year <= 1996:
            return 'Y'   # Millennials
        elif 1997 <= birth_year <= 2012:
            return 'Z'   # Generación Z
        return None
    
    def get_motivational_profile(self):
        """Analiza las respuestas para determinar el perfil motivacional."""
        if not self.motivational_insights:
            return None
            
        profile = {
            'intrinsic': {
                'autonomy': self.motivational_insights.get('autonomy', 0),
                'mastery': self.motivational_insights.get('mastery', 0),
                'purpose': self.motivational_insights.get('purpose', 0)
            },
            'extrinsic': {
                'recognition': self.motivational_insights.get('recognition', 0),
                'compensation': self.motivational_insights.get('compensation', 0),
                'status': self.motivational_insights.get('status', 0)
            }
        }
        return profile
    
    def get_references_given(self):
        """Obtiene todas las referencias que ha dado esta persona."""
        return self.references_given.all()
    
    def get_references_received(self):
        """Obtiene todas las referencias que ha recibido esta persona."""
        return self.references_received.all()
    
    def get_pending_reference_requests(self):
        """Obtiene las solicitudes de referencia pendientes de esta persona."""
        return self.references_given.filter(status='pending')
    
    def can_give_reference(self, candidate):
        """Verifica si esta persona puede dar una referencia al candidato."""
        # Verificar si ya ha dado una referencia
        existing_reference = self.references_given.filter(candidate=candidate).exists()
        if existing_reference:
            return False
        return True
    
    def award_points(self, points: int, reason: str = None):
        """Otorga puntos al candidato."""
        self.points += points
        self.save(update_fields=['points'])
        
        # Log the activity
        if hasattr(self, 'enhancednetworkgamificationprofile'):
            self.enhancednetworkgamificationprofile.award_points(points, reason)
    
    def generate_generational_insights(self):
        """Genera insights generacionales basados en la evaluación."""
        generational_profile = self.get_generational_profile()
        if not generational_profile:
            return None
            
        insights = {
            'generation': generational_profile,
            'characteristics': self._get_generational_characteristics(generational_profile),
            'work_preferences': self._get_generational_work_preferences(generational_profile),
            'communication_style': self._get_generational_communication_style(generational_profile),
            'technology_comfort': self._get_generational_tech_comfort(generational_profile),
            'career_values': self._get_generational_career_values(generational_profile)
        }
        
        self.generational_insights = insights
        self.save(update_fields=['generational_insights'])
        return insights
    
    def _get_generational_characteristics(self, generation):
        """Retorna características típicas de la generación."""
        characteristics = {
            'BB': ['experienced', 'loyal', 'disciplined', 'hierarchical'],
            'X': ['independent', 'skeptical', 'adaptable', 'work_life_balance'],
            'Y': ['tech_savvy', 'collaborative', 'achievement_oriented', 'feedback_seeking'],
            'Z': ['digital_native', 'entrepreneurial', 'diverse', 'pragmatic']
        }
        return characteristics.get(generation, [])
    
    def _get_generational_work_preferences(self, generation):
        """Retorna preferencias laborales de la generación."""
        preferences = {
            'BB': {'structure': 'high', 'autonomy': 'medium', 'feedback': 'formal'},
            'X': {'structure': 'medium', 'autonomy': 'high', 'feedback': 'periodic'},
            'Y': {'structure': 'medium', 'autonomy': 'high', 'feedback': 'frequent'},
            'Z': {'structure': 'low', 'autonomy': 'very_high', 'feedback': 'immediate'}
        }
        return preferences.get(generation, {})
    
    def _get_generational_communication_style(self, generation):
        """Retorna estilo de comunicación preferido."""
        styles = {
            'BB': 'phone_email',
            'X': 'email_meeting',
            'Y': 'email_chat_video',
            'Z': 'chat_social_mobile'
        }
        return styles.get(generation, 'email')
    
    def _get_generational_tech_comfort(self, generation):
        """Retorna nivel de comodidad con tecnología."""
        comfort_levels = {
            'BB': 2,  # Basic
            'X': 3,   # Intermediate
            'Y': 4,   # Advanced
            'Z': 5    # Expert
        }
        return comfort_levels.get(generation, 3)
    
    def _get_generational_career_values(self, generation):
        """Retorna valores profesionales de la generación."""
        values = {
            'BB': ['stability', 'loyalty', 'hierarchy', 'respect'],
            'X': ['independence', 'efficiency', 'results', 'balance'],
            'Y': ['growth', 'meaning', 'collaboration', 'recognition'],
            'Z': ['impact', 'flexibility', 'diversity', 'innovation']
        }
        return values.get(generation, [])