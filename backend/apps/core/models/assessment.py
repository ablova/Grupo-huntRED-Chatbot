"""
Assessment Models - Sistema huntRED® v2
Sistema completo de evaluaciones, assessments y pruebas de candidatos.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from typing import Dict, List, Any, Optional
import uuid
import json


class AssessmentCategory(models.Model):
    """
    Categoría de assessment para organizar diferentes tipos de evaluaciones.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, db_index=True,
                          help_text="Nombre de la categoría")
    description = models.TextField(blank=True,
                                 help_text="Descripción de la categoría")
    
    # === CONFIGURACIÓN ===
    CATEGORY_TYPE_CHOICES = [
        ('technical', 'Técnica'),
        ('cognitive', 'Cognitiva'),
        ('behavioral', 'Comportamental'),
        ('personality', 'Personalidad'),
        ('skills', 'Habilidades'),
        ('knowledge', 'Conocimiento'),
        ('psychometric', 'Psicométrica'),
        ('cultural_fit', 'Ajuste Cultural'),
        ('leadership', 'Liderazgo'),
        ('communication', 'Comunicación'),
        ('problem_solving', 'Resolución de Problemas'),
        ('creativity', 'Creatividad'),
        ('custom', 'Personalizada')
    ]
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES,
                                   db_index=True, help_text="Tipo de categoría")
    
    # === CONFIGURACIÓN AVANZADA ===
    config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración de la categoría:
    {
        'default_duration_minutes': 60,
        'scoring_method': 'weighted_average',
        'pass_threshold': 70,
        'auto_scoring': true,
        'requires_supervision': false,
        'can_retake': true,
        'max_retakes': 3,
        'cooling_period_hours': 24,
        'question_randomization': true,
        'time_tracking': true,
        'proctoring_required': false
    }
    """)
    
    # === ESTADO ===
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveIntegerField(default=0,
                                              help_text="Orden de visualización")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='created_assessment_categories')
    
    class Meta:
        verbose_name = "Categoría de Assessment"
        verbose_name_plural = "Categorías de Assessment"
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['category_type', 'is_active']),
            models.Index(fields=['display_order', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class AssessmentTemplate(models.Model):
    """
    Template base para crear assessments específicos.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True,
                          help_text="Nombre del template")
    description = models.TextField(blank=True,
                                 help_text="Descripción del assessment")
    version = models.CharField(max_length=20, default="1.0",
                             help_text="Versión del template")
    
    # === CATEGORÍA ===
    category = models.ForeignKey(AssessmentCategory, on_delete=models.CASCADE,
                               related_name='templates',
                               help_text="Categoría del assessment")
    
    # === BUSINESS UNIT ===
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE,
                                    related_name='assessment_templates',
                                    help_text="Business Unit propietaria")
    
    # === CONFIGURACIÓN DEL ASSESSMENT ===
    DIFFICULTY_CHOICES = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
        ('expert', 'Experto')
    ]
    difficulty_level = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES,
                                      default='intermediate', db_index=True)
    
    # === TIMING ===
    estimated_duration_minutes = models.PositiveIntegerField(
        default=60, help_text="Duración estimada en minutos")
    max_duration_minutes = models.PositiveIntegerField(
        null=True, blank=True, help_text="Duración máxima permitida")
    
    # === PUNTUACIÓN ===
    total_points = models.PositiveIntegerField(default=100,
                                             help_text="Puntuación total posible")
    pass_threshold = models.FloatField(default=70.0,
                                     validators=[MinValueValidator(0), MaxValueValidator(100)],
                                     help_text="Umbral de aprobación")
    
    # === CONFIGURACIÓN AVANZADA ===
    config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración del assessment:
    {
        'question_randomization': true,
        'option_randomization': false,
        'show_results_immediately': false,
        'allow_review': true,
        'allow_skip_questions': false,
        'require_all_questions': true,
        'auto_submit_on_timeout': true,
        'show_progress': true,
        'show_timer': true,
        'lockdown_browser': false,
        'webcam_required': false,
        'screen_recording': false,
        'plagiarism_detection': false,
        'ip_restriction': false,
        'allowed_ips': [],
        'password_protected': false,
        'access_password': '',
        'instructions': '',
        'scoring_rules': {
            'correct_answer': 1,
            'incorrect_answer': 0,
            'partial_credit': false,
            'negative_marking': false,
            'unanswered': 0
        }
    }
    """)
    
    # === INSTRUCCIONES ===
    instructions = models.TextField(blank=True,
                                  help_text="Instrucciones para el candidato")
    pre_assessment_message = models.TextField(blank=True,
                                            help_text="Mensaje antes del assessment")
    post_assessment_message = models.TextField(blank=True,
                                             help_text="Mensaje después del assessment")
    
    # === REQUISITOS ===
    prerequisites = models.JSONField(default=list, blank=True, help_text="""
    Prerrequisitos para tomar el assessment:
    [
        {
            'type': 'skill',
            'value': 'programming',
            'minimum_level': 'intermediate'
        },
        {
            'type': 'experience',
            'value': 'python',
            'minimum_years': 2
        }
    ]
    """)
    
    # === ESTADO ===
    is_active = models.BooleanField(default=True, db_index=True)
    is_published = models.BooleanField(default=False, db_index=True,
                                     help_text="¿Está publicado y disponible?")
    is_template = models.BooleanField(default=True,
                                    help_text="¿Es un template reutilizable?")
    
    # === MÉTRICAS ===
    usage_count = models.PositiveIntegerField(default=0,
                                            help_text="Número de veces utilizado")
    avg_score = models.FloatField(default=0.0,
                                validators=[MinValueValidator(0), MaxValueValidator(100)],
                                help_text="Puntuación promedio")
    avg_completion_time = models.DurationField(null=True, blank=True,
                                             help_text="Tiempo promedio de completado")
    completion_rate = models.FloatField(default=0.0,
                                      validators=[MinValueValidator(0), MaxValueValidator(1)],
                                      help_text="Tasa de completado")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='created_assessment_templates')
    
    class Meta:
        verbose_name = "Template de Assessment"
        verbose_name_plural = "Templates de Assessment"
        ordering = ['-created_at']
        unique_together = ['business_unit', 'name', 'version']
        indexes = [
            models.Index(fields=['category', 'difficulty_level', 'is_active']),
            models.Index(fields=['business_unit', 'is_published']),
            models.Index(fields=['usage_count', 'avg_score']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version} - {self.category.name}"
    
    def duplicate(self, new_name: str, new_version: str = None):
        """Duplica el template con un nuevo nombre."""
        if not new_version:
            new_version = f"{self.version}.copy"
        
        new_template = AssessmentTemplate.objects.create(
            name=new_name,
            description=f"Copia de {self.description}",
            version=new_version,
            category=self.category,
            business_unit=self.business_unit,
            difficulty_level=self.difficulty_level,
            estimated_duration_minutes=self.estimated_duration_minutes,
            max_duration_minutes=self.max_duration_minutes,
            total_points=self.total_points,
            pass_threshold=self.pass_threshold,
            config=self.config.copy(),
            instructions=self.instructions,
            pre_assessment_message=self.pre_assessment_message,
            post_assessment_message=self.post_assessment_message,
            prerequisites=self.prerequisites.copy(),
            created_by=None
        )
        
        # Duplicar preguntas
        for question in self.questions.all():
            question.duplicate(new_template)
        
        return new_template
    
    def calculate_metrics(self):
        """Calcula métricas del template."""
        assessments = self.assessment_instances.all()
        if not assessments.exists():
            return
        
        # Calcular tasa de completado
        total = assessments.count()
        completed = assessments.filter(status='completed').count()
        self.completion_rate = completed / total if total > 0 else 0
        
        # Calcular puntuación promedio
        completed_assessments = assessments.filter(status='completed')
        if completed_assessments.exists():
            self.avg_score = completed_assessments.aggregate(
                models.Avg('final_score'))['final_score__avg'] or 0.0
            
            # Calcular tiempo promedio
            total_time = sum([
                (a.completed_at - a.started_at).total_seconds()
                for a in completed_assessments
                if a.completed_at and a.started_at
            ])
            if total_time > 0:
                avg_seconds = total_time / completed_assessments.count()
                self.avg_completion_time = timezone.timedelta(seconds=avg_seconds)
        
        self.save(update_fields=['completion_rate', 'avg_score', 'avg_completion_time'])
    
    def get_question_count(self):
        """Obtiene el número total de preguntas."""
        return self.questions.filter(is_active=True).count()
    
    def can_user_take(self, person) -> tuple[bool, str]:
        """Verifica si una persona puede tomar el assessment."""
        if not self.is_active or not self.is_published:
            return False, "Assessment no disponible"
        
        # Verificar prerrequisitos
        for prereq in self.prerequisites:
            prereq_type = prereq.get('type')
            if prereq_type == 'skill':
                # Verificar habilidad
                pass
            elif prereq_type == 'experience':
                # Verificar experiencia
                pass
        
        return True, "OK"


class AssessmentQuestion(models.Model):
    """
    Pregunta individual dentro de un assessment.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE,
                               related_name='questions',
                               help_text="Template al que pertenece")
    
    # === CONTENIDO ===
    question_text = models.TextField(help_text="Texto de la pregunta")
    explanation = models.TextField(blank=True,
                                 help_text="Explicación de la respuesta correcta")
    
    # === TIPO DE PREGUNTA ===
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'Opción Múltiple'),
        ('true_false', 'Verdadero/Falso'),
        ('short_answer', 'Respuesta Corta'),
        ('long_answer', 'Respuesta Larga'),
        ('essay', 'Ensayo'),
        ('code', 'Código'),
        ('file_upload', 'Subir Archivo'),
        ('matching', 'Emparejar'),
        ('ordering', 'Ordenar'),
        ('fill_blanks', 'Llenar Espacios'),
        ('numeric', 'Numérica'),
        ('scale', 'Escala'),
        ('custom', 'Personalizada')
    ]
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES,
                                   db_index=True, help_text="Tipo de pregunta")
    
    # === ORDEN Y CONFIGURACIÓN ===
    order = models.PositiveIntegerField(default=0,
                                      help_text="Orden de la pregunta")
    points = models.FloatField(default=1.0,
                             validators=[MinValueValidator(0)],
                             help_text="Puntos asignados a esta pregunta")
    
    # === DIFICULTAD ===
    difficulty = models.CharField(max_length=15,
                                choices=AssessmentTemplate.DIFFICULTY_CHOICES,
                                default='intermediate')
    
    # === CONFIGURACIÓN ESPECÍFICA ===
    config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración específica de la pregunta:
    {
        'time_limit_seconds': 300,
        'allow_partial_credit': false,
        'case_sensitive': false,
        'require_explanation': false,
        'randomize_options': true,
        'show_explanation': true,
        'code_language': 'python',
        'code_template': '',
        'test_cases': [],
        'auto_grade': true,
        'manual_review_required': false
    }
    """)
    
    # === CONTENIDO MULTIMEDIA ===
    image = models.ImageField(upload_to='assessments/questions/', blank=True,
                            help_text="Imagen asociada a la pregunta")
    video_url = models.URLField(blank=True,
                              help_text="URL de video explicativo")
    audio_file = models.FileField(upload_to='assessments/audio/', blank=True,
                                help_text="Archivo de audio")
    
    # === TAGS Y CATEGORIZACIÓN ===
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list, blank=True,
        help_text="Tags para categorizar la pregunta"
    )
    
    skill_areas = models.ManyToManyField('Skill', blank=True,
                                       related_name='assessment_questions',
                                       help_text="Áreas de habilidad que evalúa")
    
    # === ESTADO ===
    is_active = models.BooleanField(default=True, db_index=True)
    is_required = models.BooleanField(default=True,
                                    help_text="¿Es obligatoria responder?")
    
    # === MÉTRICAS ===
    times_used = models.PositiveIntegerField(default=0,
                                           help_text="Veces que se ha usado")
    avg_score = models.FloatField(default=0.0,
                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    difficulty_rating = models.FloatField(default=0.0,
                                        validators=[MinValueValidator(0), MaxValueValidator(5)],
                                        help_text="Dificultad percibida por usuarios")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='created_assessment_questions')
    
    class Meta:
        verbose_name = "Pregunta de Assessment"
        verbose_name_plural = "Preguntas de Assessment"
        ordering = ['template', 'order']
        indexes = [
            models.Index(fields=['template', 'order', 'is_active']),
            models.Index(fields=['question_type', 'difficulty']),
            models.Index(fields=['avg_score', 'difficulty_rating']),
        ]
    
    def __str__(self):
        return f"{self.template.name} - Q{self.order}: {self.question_text[:50]}..."
    
    def duplicate(self, new_template):
        """Duplica la pregunta para un nuevo template."""
        new_question = AssessmentQuestion.objects.create(
            template=new_template,
            question_text=self.question_text,
            explanation=self.explanation,
            question_type=self.question_type,
            order=self.order,
            points=self.points,
            difficulty=self.difficulty,
            config=self.config.copy(),
            video_url=self.video_url,
            tags=self.tags.copy(),
            is_required=self.is_required
        )
        
        # Duplicar opciones
        for option in self.options.all():
            option.duplicate(new_question)
        
        return new_question
    
    def get_correct_options(self):
        """Obtiene las opciones correctas."""
        return self.options.filter(is_correct=True)
    
    def calculate_score(self, selected_options: List[str]) -> float:
        """Calcula la puntuación para las opciones seleccionadas."""
        if self.question_type == 'multiple_choice':
            correct_options = list(self.get_correct_options().values_list('id', flat=True))
            selected_ids = [uuid.UUID(opt_id) for opt_id in selected_options]
            
            if set(correct_options) == set(selected_ids):
                return self.points
            elif self.config.get('allow_partial_credit', False):
                # Implementar puntuación parcial
                correct_selected = len(set(correct_options) & set(selected_ids))
                total_correct = len(correct_options)
                if total_correct > 0:
                    return (correct_selected / total_correct) * self.points
        
        return 0.0


class AssessmentQuestionOption(models.Model):
    """
    Opción de respuesta para preguntas de opción múltiple.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE,
                               related_name='options')
    
    option_text = models.TextField(help_text="Texto de la opción")
    is_correct = models.BooleanField(default=False,
                                   help_text="¿Es la respuesta correcta?")
    order = models.PositiveIntegerField(default=0,
                                      help_text="Orden de la opción")
    
    # === CONTENIDO MULTIMEDIA ===
    image = models.ImageField(upload_to='assessments/options/', blank=True)
    
    # === CONFIGURACIÓN ===
    explanation = models.TextField(blank=True,
                                 help_text="Explicación de por qué es/no es correcta")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Opción de Pregunta"
        verbose_name_plural = "Opciones de Pregunta"
        ordering = ['question', 'order']
        indexes = [
            models.Index(fields=['question', 'order']),
            models.Index(fields=['question', 'is_correct']),
        ]
    
    def __str__(self):
        return f"{self.question.template.name} Q{self.question.order} - {self.option_text[:30]}..."
    
    def duplicate(self, new_question):
        """Duplica la opción para una nueva pregunta."""
        return AssessmentQuestionOption.objects.create(
            question=new_question,
            option_text=self.option_text,
            is_correct=self.is_correct,
            order=self.order,
            explanation=self.explanation
        )


class AssessmentInstance(models.Model):
    """
    Instancia específica de un assessment tomado por un candidato.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE,
                               related_name='assessment_instances')
    person = models.ForeignKey('Person', on_delete=models.CASCADE,
                             related_name='assessment_instances')
    
    # === ESTADO ===
    STATUS_CHOICES = [
        ('scheduled', 'Programado'),
        ('started', 'Iniciado'),
        ('in_progress', 'En Progreso'),
        ('paused', 'Pausado'),
        ('completed', 'Completado'),
        ('submitted', 'Enviado'),
        ('graded', 'Calificado'),
        ('expired', 'Expirado'),
        ('cancelled', 'Cancelado')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                            default='scheduled', db_index=True)
    
    # === PUNTUACIÓN ===
    final_score = models.FloatField(null=True, blank=True,
                                  validators=[MinValueValidator(0), MaxValueValidator(100)],
                                  help_text="Puntuación final")
    raw_score = models.FloatField(default=0.0,
                                validators=[MinValueValidator(0)],
                                help_text="Puntuación sin procesar")
    percentage_score = models.FloatField(null=True, blank=True,
                                       validators=[MinValueValidator(0), MaxValueValidator(100)])
    passed = models.BooleanField(null=True, blank=True,
                               help_text="¿Aprobó el assessment?")
    
    # === TIMING ===
    scheduled_start = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    duration_seconds = models.PositiveIntegerField(null=True, blank=True,
                                                 help_text="Duración real en segundos")
    
    # === CONFIGURACIÓN ===
    attempt_number = models.PositiveSmallIntegerField(default=1,
                                                    help_text="Número de intento")
    max_attempts = models.PositiveSmallIntegerField(default=1,
                                                  help_text="Máximo intentos permitidos")
    
    # === DATOS DEL ASSESSMENT ===
    responses = models.JSONField(default=dict, blank=True, help_text="""
    Respuestas del candidato:
    {
        'question_id': {
            'answer': 'selected_option_id',
            'time_spent_seconds': 45,
            'attempts': 1,
            'confidence_level': 'high'
        }
    }
    """)
    
    metadata = models.JSONField(default=dict, blank=True, help_text="""
    Metadata del assessment:
    {
        'browser': 'Chrome 91.0',
        'ip_address': '192.168.1.1',
        'screen_resolution': '1920x1080',
        'proctoring_data': {},
        'suspicious_activities': [],
        'question_order': [],
        'time_per_question': {}
    }
    """)
    
    # === PROCTORING Y SEGURIDAD ===
    proctoring_enabled = models.BooleanField(default=False)
    proctoring_data = models.JSONField(default=dict, blank=True)
    suspicious_activity_count = models.PositiveIntegerField(default=0)
    integrity_score = models.FloatField(default=100.0,
                                      validators=[MinValueValidator(0), MaxValueValidator(100)],
                                      help_text="Puntuación de integridad")
    
    # === FEEDBACK ===
    feedback = models.TextField(blank=True,
                              help_text="Feedback del evaluador")
    auto_feedback = models.TextField(blank=True,
                                   help_text="Feedback automático generado")
    
    # === RELACIONES ===
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='graded_assessments')
    workflow_instance = models.ForeignKey('WorkflowInstance', on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='assessments')
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Instancia de Assessment"
        verbose_name_plural = "Instancias de Assessment"
        ordering = ['-created_at']
        unique_together = ['template', 'person', 'attempt_number']
        indexes = [
            models.Index(fields=['person', 'status']),
            models.Index(fields=['template', 'final_score']),
            models.Index(fields=['status', 'scheduled_start']),
            models.Index(fields=['passed', 'completed_at']),
        ]
    
    def __str__(self):
        return f"{self.person} - {self.template.name} (Intento #{self.attempt_number})"
    
    def start_assessment(self):
        """Inicia el assessment."""
        if self.status != 'scheduled':
            raise ValueError("Assessment can only be started from scheduled status")
        
        self.status = 'started'
        self.started_at = timezone.now()
        self.save()
        
        # Generar orden de preguntas si está configurada la aleatorización
        if self.template.config.get('question_randomization', False):
            questions = list(self.template.questions.filter(is_active=True).values_list('id', flat=True))
            import random
            random.shuffle(questions)
            self.metadata['question_order'] = [str(q) for q in questions]
            self.save(update_fields=['metadata'])
    
    def submit_response(self, question_id: str, answer_data: dict):
        """Envía una respuesta a una pregunta."""
        if self.status not in ['started', 'in_progress']:
            raise ValueError("Cannot submit response in current status")
        
        self.responses[question_id] = answer_data
        self.status = 'in_progress'
        self.save(update_fields=['responses', 'status'])
    
    def complete_assessment(self):
        """Completa el assessment y calcula la puntuación."""
        if self.status not in ['started', 'in_progress']:
            raise ValueError("Cannot complete assessment in current status")
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        
        # Calcular duración
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        # Calcular puntuación
        self._calculate_score()
        
        self.save()
        
        # Actualizar métricas del template
        self.template.usage_count += 1
        self.template.save(update_fields=['usage_count'])
    
    def _calculate_score(self):
        """Calcula la puntuación del assessment."""
        total_points = 0
        earned_points = 0
        
        for question in self.template.questions.filter(is_active=True):
            total_points += question.points
            
            question_id = str(question.id)
            if question_id in self.responses:
                response_data = self.responses[question_id]
                answer = response_data.get('answer')
                
                if answer:
                    if question.question_type == 'multiple_choice':
                        selected_options = answer if isinstance(answer, list) else [answer]
                        earned_points += question.calculate_score(selected_options)
                    else:
                        # Implementar scoring para otros tipos de pregunta
                        pass
        
        self.raw_score = earned_points
        if total_points > 0:
            self.percentage_score = (earned_points / total_points) * 100
            self.final_score = self.percentage_score
            self.passed = self.final_score >= self.template.pass_threshold
        else:
            self.percentage_score = 0
            self.final_score = 0
            self.passed = False
    
    def can_retake(self) -> tuple[bool, str]:
        """Verifica si se puede volver a tomar el assessment."""
        if self.attempt_number >= self.max_attempts:
            return False, "Maximum attempts reached"
        
        if not self.template.config.get('can_retake', True):
            return False, "Retakes not allowed"
        
        # Verificar período de espera
        cooling_period = self.template.config.get('cooling_period_hours', 0)
        if cooling_period > 0 and self.completed_at:
            next_attempt_time = self.completed_at + timezone.timedelta(hours=cooling_period)
            if timezone.now() < next_attempt_time:
                return False, f"Must wait until {next_attempt_time}"
        
        return True, "OK"
    
    def create_retake(self):
        """Crea una nueva instancia para reintento."""
        can_retake, reason = self.can_retake()
        if not can_retake:
            raise ValueError(reason)
        
        return AssessmentInstance.objects.create(
            template=self.template,
            person=self.person,
            attempt_number=self.attempt_number + 1,
            max_attempts=self.max_attempts,
            proctoring_enabled=self.proctoring_enabled
        )
    
    def get_question_analytics(self):
        """Obtiene analytics por pregunta."""
        analytics = {}
        
        for question in self.template.questions.filter(is_active=True):
            question_id = str(question.id)
            response_data = self.responses.get(question_id, {})
            
            analytics[question_id] = {
                'question_text': question.question_text[:100],
                'points_possible': question.points,
                'points_earned': 0,  # Calcular según respuesta
                'time_spent': response_data.get('time_spent_seconds', 0),
                'attempts': response_data.get('attempts', 0),
                'confidence': response_data.get('confidence_level', 'unknown')
            }
        
        return analytics
    
    def generate_report(self) -> dict:
        """Genera un reporte completo del assessment."""
        return {
            'assessment': {
                'name': self.template.name,
                'category': self.template.category.name,
                'difficulty': self.template.get_difficulty_level_display(),
                'total_questions': self.template.get_question_count(),
            },
            'candidate': {
                'name': f"{self.person.first_name} {self.person.last_name}",
                'email': self.person.email,
            },
            'results': {
                'status': self.get_status_display(),
                'final_score': self.final_score,
                'percentage': self.percentage_score,
                'passed': self.passed,
                'attempt_number': self.attempt_number,
            },
            'timing': {
                'started_at': self.started_at,
                'completed_at': self.completed_at,
                'duration_minutes': self.duration_seconds // 60 if self.duration_seconds else 0,
                'estimated_duration': self.template.estimated_duration_minutes,
            },
            'integrity': {
                'score': self.integrity_score,
                'suspicious_activities': self.suspicious_activity_count,
                'proctoring_enabled': self.proctoring_enabled,
            },
            'question_analytics': self.get_question_analytics(),
        }