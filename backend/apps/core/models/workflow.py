"""
Workflow Models - Sistema huntRED® v2
Sistema completo de workflows personalizables con stages dinámicos.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
from typing import Dict, List, Any, Optional
import uuid
import json


class WorkflowTemplate(models.Model):
    """
    Template base para workflows reutilizables.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, db_index=True,
                          help_text="Nombre del template de workflow")
    description = models.TextField(blank=True,
                                 help_text="Descripción del workflow")
    
    # === CONFIGURACIÓN ===
    WORKFLOW_TYPE_CHOICES = [
        ('recruitment', 'Proceso de Reclutamiento'),
        ('onboarding', 'Proceso de Onboarding'),
        ('performance', 'Evaluación de Desempeño'),
        ('development', 'Desarrollo Profesional'),
        ('offboarding', 'Proceso de Salida'),
        ('custom', 'Personalizado')
    ]
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPE_CHOICES,
                                   db_index=True, help_text="Tipo de workflow")
    
    # === CONFIGURACIÓN AVANZADA ===
    config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración del workflow:
    {
        'auto_advance': true,
        'parallel_processing': false,
        'time_limits': {
            'stage_timeout_hours': 48,
            'workflow_timeout_days': 30
        },
        'notifications': {
            'stage_change': true,
            'timeout_warnings': true,
            'completion': true
        },
        'approval_required': false,
        'scoring_enabled': true,
        'document_required': false,
        'interview_scheduling': true
    }
    """)
    
    # === BUSINESS UNIT ===
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE,
                                    related_name='workflow_templates',
                                    help_text="Unidad de negocio propietaria")
    
    # === ESTADO ===
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False,
                                   help_text="¿Es el workflow por defecto para este tipo?")
    
    # === MÉTRICAS ===
    usage_count = models.PositiveIntegerField(default=0,
                                            help_text="Número de veces utilizado")
    success_rate = models.FloatField(default=0.0,
                                   validators=[MinValueValidator(0), MaxValueValidator(1)],
                                   help_text="Tasa de éxito del workflow")
    avg_completion_time = models.DurationField(null=True, blank=True,
                                             help_text="Tiempo promedio de completado")
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='created_workflow_templates')
    
    class Meta:
        verbose_name = "Template de Workflow"
        verbose_name_plural = "Templates de Workflow"
        ordering = ['name']
        unique_together = ['name', 'business_unit']
        indexes = [
            models.Index(fields=['workflow_type', 'is_active']),
            models.Index(fields=['business_unit', 'is_default']),
            models.Index(fields=['usage_count', 'success_rate']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_workflow_type_display()})"
    
    def get_stages(self):
        """Obtiene todas las etapas del workflow ordenadas."""
        return self.stages.filter(is_active=True).order_by('order')
    
    def duplicate(self, new_name: str, business_unit=None):
        """Duplica el template con un nuevo nombre."""
        new_template = WorkflowTemplate.objects.create(
            name=new_name,
            description=f"Copia de {self.description}",
            workflow_type=self.workflow_type,
            config=self.config.copy(),
            business_unit=business_unit or self.business_unit,
            created_by=None
        )
        
        # Duplicar stages
        for stage in self.get_stages():
            stage.duplicate(new_template)
        
        return new_template
    
    def calculate_metrics(self):
        """Calcula métricas del workflow."""
        workflows = self.workflow_instances.all()
        if not workflows.exists():
            return
        
        total = workflows.count()
        completed = workflows.filter(status='completed').count()
        self.success_rate = completed / total if total > 0 else 0
        
        # Calcular tiempo promedio
        completed_workflows = workflows.filter(
            status='completed',
            completed_at__isnull=False
        )
        if completed_workflows.exists():
            total_time = sum([
                (w.completed_at - w.created_at).total_seconds()
                for w in completed_workflows
            ])
            avg_seconds = total_time / completed_workflows.count()
            self.avg_completion_time = timezone.timedelta(seconds=avg_seconds)
        
        self.save(update_fields=['success_rate', 'avg_completion_time'])


class WorkflowStage(models.Model):
    """
    Etapa individual dentro de un workflow.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True,
                          help_text="Nombre de la etapa")
    description = models.TextField(blank=True,
                                 help_text="Descripción de la etapa")
    
    # === RELACIÓN CON TEMPLATE ===
    workflow_template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE,
                                        related_name='stages',
                                        help_text="Template al que pertenece")
    
    # === ORDEN Y TIPO ===
    order = models.PositiveIntegerField(db_index=True,
                                      help_text="Orden de la etapa en el workflow")
    
    STAGE_TYPE_CHOICES = [
        ('screening', 'Screening Inicial'),
        ('application_review', 'Revisión de Aplicación'),
        ('phone_interview', 'Entrevista Telefónica'),
        ('technical_test', 'Prueba Técnica'),
        ('video_interview', 'Entrevista por Video'),
        ('onsite_interview', 'Entrevista Presencial'),
        ('reference_check', 'Verificación de Referencias'),
        ('background_check', 'Verificación de Antecedentes'),
        ('final_interview', 'Entrevista Final'),
        ('offer_preparation', 'Preparación de Oferta'),
        ('offer_negotiation', 'Negociación de Oferta'),
        ('contract_signing', 'Firma de Contrato'),
        ('onboarding', 'Onboarding'),
        ('probation', 'Período de Prueba'),
        ('evaluation', 'Evaluación'),
        ('decision', 'Decisión'),
        ('custom', 'Personalizada')
    ]
    stage_type = models.CharField(max_length=30, choices=STAGE_TYPE_CHOICES,
                                db_index=True, help_text="Tipo de etapa")
    
    # === CONFIGURACIÓN DE ETAPA ===
    config = models.JSONField(default=dict, blank=True, help_text="""
    Configuración específica de la etapa:
    {
        'auto_advance': false,
        'requires_approval': true,
        'approval_roles': ['hr_manager', 'hiring_manager'],
        'time_limit_hours': 48,
        'scoring_enabled': true,
        'scoring_criteria': ['technical', 'cultural_fit', 'experience'],
        'documents_required': ['cv', 'portfolio'],
        'interview_duration_minutes': 60,
        'interviewers_required': 2,
        'assessment_types': ['technical', 'behavioral'],
        'notifications': {
            'on_entry': true,
            'before_timeout': 24,
            'on_completion': true
        }
    }
    """)
    
    # === CONDICIONES DE TRANSICIÓN ===
    entry_conditions = models.JSONField(default=dict, blank=True, help_text="""
    Condiciones para entrar a esta etapa:
    {
        'previous_stage_status': 'passed',
        'minimum_score': 70,
        'required_documents': ['cv'],
        'custom_conditions': []
    }
    """)
    
    exit_conditions = models.JSONField(default=dict, blank=True, help_text="""
    Condiciones para salir de esta etapa:
    {
        'approval_required': true,
        'minimum_score': 80,
        'all_tasks_completed': true,
        'documents_uploaded': true,
        'custom_conditions': []
    }
    """)
    
    # === ACCIONES AUTOMÁTICAS ===
    entry_actions = models.JSONField(default=list, blank=True, help_text="""
    Acciones al entrar a la etapa:
    [
        {'type': 'send_notification', 'target': 'candidate'},
        {'type': 'schedule_interview', 'auto': true},
        {'type': 'assign_task', 'task_type': 'technical_test'},
        {'type': 'create_calendar_event'},
        {'type': 'send_email', 'template': 'stage_entry'}
    ]
    """)
    
    exit_actions = models.JSONField(default=list, blank=True, help_text="""
    Acciones al salir de la etapa:
    [
        {'type': 'send_notification', 'target': 'hiring_manager'},
        {'type': 'update_score', 'aggregate': true},
        {'type': 'generate_report'},
        {'type': 'archive_documents'}
    ]
    """)
    
    # === RESPONSABLES ===
    responsible_roles = ArrayField(
        models.CharField(max_length=50),
        default=list, blank=True,
        help_text="Roles responsables de esta etapa"
    )
    responsible_users = models.ManyToManyField(User, blank=True,
                                             related_name='responsible_workflow_stages',
                                             help_text="Usuarios específicos responsables")
    
    # === ESTADO ===
    is_active = models.BooleanField(default=True, db_index=True)
    is_optional = models.BooleanField(default=False,
                                    help_text="¿Es una etapa opcional?")
    can_skip = models.BooleanField(default=False,
                                 help_text="¿Se puede saltar esta etapa?")
    
    # === MÉTRICAS ===
    avg_completion_time = models.DurationField(null=True, blank=True)
    pass_rate = models.FloatField(default=0.0,
                                validators=[MinValueValidator(0), MaxValueValidator(1)])
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Etapa de Workflow"
        verbose_name_plural = "Etapas de Workflow"
        ordering = ['workflow_template', 'order']
        unique_together = ['workflow_template', 'order']
        indexes = [
            models.Index(fields=['workflow_template', 'order']),
            models.Index(fields=['stage_type', 'is_active']),
            models.Index(fields=['pass_rate', 'avg_completion_time']),
        ]
    
    def __str__(self):
        return f"{self.workflow_template.name} - {self.name} (#{self.order})"
    
    def get_next_stage(self):
        """Obtiene la siguiente etapa en el workflow."""
        return WorkflowStage.objects.filter(
            workflow_template=self.workflow_template,
            order__gt=self.order,
            is_active=True
        ).order_by('order').first()
    
    def get_previous_stage(self):
        """Obtiene la etapa anterior en el workflow."""
        return WorkflowStage.objects.filter(
            workflow_template=self.workflow_template,
            order__lt=self.order,
            is_active=True
        ).order_by('-order').first()
    
    def can_advance_to_next(self, workflow_instance):
        """Verifica si se puede avanzar a la siguiente etapa."""
        # Verificar condiciones de salida
        if not self._check_exit_conditions(workflow_instance):
            return False, "Exit conditions not met"
        
        next_stage = self.get_next_stage()
        if not next_stage:
            return True, "Workflow completed"
        
        # Verificar condiciones de entrada de la siguiente etapa
        if not next_stage._check_entry_conditions(workflow_instance):
            return False, "Next stage entry conditions not met"
        
        return True, "Can advance"
    
    def _check_entry_conditions(self, workflow_instance):
        """Verifica las condiciones de entrada."""
        conditions = self.entry_conditions
        
        # Verificar estado de etapa anterior
        if 'previous_stage_status' in conditions:
            required_status = conditions['previous_stage_status']
            previous_stage = self.get_previous_stage()
            if previous_stage:
                # Verificar en el historial del workflow instance
                pass
        
        # Verificar puntuación mínima
        if 'minimum_score' in conditions:
            min_score = conditions['minimum_score']
            if hasattr(workflow_instance, 'current_score'):
                if workflow_instance.current_score < min_score:
                    return False
        
        # Verificar documentos requeridos
        if 'required_documents' in conditions:
            required_docs = conditions['required_documents']
            # Implementar verificación de documentos
            pass
        
        return True
    
    def _check_exit_conditions(self, workflow_instance):
        """Verifica las condiciones de salida."""
        conditions = self.exit_conditions
        
        # Verificar aprobación requerida
        if conditions.get('approval_required', False):
            # Verificar si hay aprobación pendiente
            pass
        
        # Verificar puntuación mínima
        if 'minimum_score' in conditions:
            min_score = conditions['minimum_score']
            if hasattr(workflow_instance, 'current_score'):
                if workflow_instance.current_score < min_score:
                    return False
        
        # Verificar tareas completadas
        if conditions.get('all_tasks_completed', False):
            # Verificar tareas pendientes
            pass
        
        return True
    
    def execute_entry_actions(self, workflow_instance):
        """Ejecuta las acciones de entrada a la etapa."""
        for action in self.entry_actions:
            self._execute_action(action, workflow_instance, 'entry')
    
    def execute_exit_actions(self, workflow_instance):
        """Ejecuta las acciones de salida de la etapa."""
        for action in self.exit_actions:
            self._execute_action(action, workflow_instance, 'exit')
    
    def _execute_action(self, action, workflow_instance, phase):
        """Ejecuta una acción específica."""
        action_type = action.get('type')
        
        if action_type == 'send_notification':
            self._send_notification_action(action, workflow_instance)
        elif action_type == 'schedule_interview':
            self._schedule_interview_action(action, workflow_instance)
        elif action_type == 'assign_task':
            self._assign_task_action(action, workflow_instance)
        elif action_type == 'create_calendar_event':
            self._create_calendar_event_action(action, workflow_instance)
        elif action_type == 'send_email':
            self._send_email_action(action, workflow_instance)
        # Agregar más tipos de acción según necesidad
    
    def _send_notification_action(self, action, workflow_instance):
        """Envía una notificación."""
        # Implementar envío de notificación
        pass
    
    def _schedule_interview_action(self, action, workflow_instance):
        """Programa una entrevista."""
        # Implementar programación de entrevista
        pass
    
    def _assign_task_action(self, action, workflow_instance):
        """Asigna una tarea."""
        # Implementar asignación de tarea
        pass
    
    def _create_calendar_event_action(self, action, workflow_instance):
        """Crea un evento de calendario."""
        # Implementar creación de evento
        pass
    
    def _send_email_action(self, action, workflow_instance):
        """Envía un email."""
        # Implementar envío de email
        pass
    
    def duplicate(self, new_workflow_template):
        """Duplica la etapa para un nuevo template."""
        return WorkflowStage.objects.create(
            name=self.name,
            description=self.description,
            workflow_template=new_workflow_template,
            order=self.order,
            stage_type=self.stage_type,
            config=self.config.copy(),
            entry_conditions=self.entry_conditions.copy(),
            exit_conditions=self.exit_conditions.copy(),
            entry_actions=self.entry_actions.copy(),
            exit_actions=self.exit_actions.copy(),
            responsible_roles=self.responsible_roles.copy(),
            is_optional=self.is_optional,
            can_skip=self.can_skip
        )


class WorkflowInstance(models.Model):
    """
    Instancia específica de un workflow en ejecución.
    """
    
    # === IDENTIFICACIÓN ===
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True,
                          help_text="Nombre de la instancia")
    
    # === RELACIONES ===
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.PROTECT,
                               related_name='workflow_instances',
                               help_text="Template base utilizado")
    person = models.ForeignKey('Person', on_delete=models.CASCADE,
                             related_name='workflow_instances',
                             help_text="Persona asociada al workflow")
    current_stage = models.ForeignKey(WorkflowStage, on_delete=models.SET_NULL,
                                    null=True, blank=True,
                                    related_name='current_workflow_instances',
                                    help_text="Etapa actual")
    
    # === ESTADO ===
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('active', 'Activo'),
        ('paused', 'Pausado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('failed', 'Fallido')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                            default='pending', db_index=True)
    
    # === DATOS DEL WORKFLOW ===
    current_score = models.FloatField(default=0.0,
                                    validators=[MinValueValidator(0), MaxValueValidator(100)],
                                    help_text="Puntuación actual acumulada")
    data = models.JSONField(default=dict, blank=True,
                          help_text="Datos específicos del workflow")
    metadata = models.JSONField(default=dict, blank=True,
                              help_text="Metadata adicional")
    
    # === RESPONSABLES ===
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='assigned_workflow_instances',
                                  help_text="Usuario responsable actual")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                 null=True, related_name='created_workflow_instances')
    
    # === TIMING ===
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    resumed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Instancia de Workflow"
        verbose_name_plural = "Instancias de Workflow"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['person', 'status']),
            models.Index(fields=['template', 'current_stage']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.person} ({self.get_status_display()})"
    
    def start(self):
        """Inicia el workflow."""
        if self.status != 'pending':
            raise ValueError("Workflow can only be started from pending status")
        
        first_stage = self.template.get_stages().first()
        if not first_stage:
            raise ValueError("Workflow template has no stages")
        
        self.status = 'active'
        self.started_at = timezone.now()
        self.current_stage = first_stage
        self.save()
        
        # Ejecutar acciones de entrada de la primera etapa
        first_stage.execute_entry_actions(self)
        
        # Crear log de transición
        self.create_stage_log(first_stage, 'started')
    
    def advance_to_next_stage(self, user=None, notes=""):
        """Avanza a la siguiente etapa del workflow."""
        if not self.current_stage:
            raise ValueError("No current stage to advance from")
        
        can_advance, reason = self.current_stage.can_advance_to_next(self)
        if not can_advance:
            raise ValueError(f"Cannot advance: {reason}")
        
        # Ejecutar acciones de salida de la etapa actual
        self.current_stage.execute_exit_actions(self)
        
        # Crear log de salida
        self.create_stage_log(self.current_stage, 'exited', user, notes)
        
        # Avanzar a la siguiente etapa
        next_stage = self.current_stage.get_next_stage()
        
        if next_stage:
            self.current_stage = next_stage
            self.save()
            
            # Ejecutar acciones de entrada de la nueva etapa
            next_stage.execute_entry_actions(self)
            
            # Crear log de entrada
            self.create_stage_log(next_stage, 'entered', user)
        else:
            # Workflow completado
            self.complete()
    
    def complete(self, user=None):
        """Marca el workflow como completado."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Crear log de completado
        self.create_workflow_log('completed', user)
        
        # Actualizar métricas del template
        self.template.usage_count += 1
        self.template.save(update_fields=['usage_count'])
    
    def pause(self, user=None, reason=""):
        """Pausa el workflow."""
        if self.status != 'active':
            raise ValueError("Can only pause active workflows")
        
        self.status = 'paused'
        self.paused_at = timezone.now()
        self.save()
        
        self.create_workflow_log('paused', user, reason)
    
    def resume(self, user=None):
        """Reanuda el workflow."""
        if self.status != 'paused':
            raise ValueError("Can only resume paused workflows")
        
        self.status = 'active'
        self.resumed_at = timezone.now()
        self.save()
        
        self.create_workflow_log('resumed', user)
    
    def cancel(self, user=None, reason=""):
        """Cancela el workflow."""
        if self.status in ['completed', 'cancelled']:
            raise ValueError("Cannot cancel completed or already cancelled workflow")
        
        self.status = 'cancelled'
        self.save()
        
        self.create_workflow_log('cancelled', user, reason)
    
    def create_stage_log(self, stage, action, user=None, notes=""):
        """Crea un log de transición de etapa."""
        return WorkflowStageLog.objects.create(
            workflow_instance=self,
            stage=stage,
            action=action,
            user=user,
            notes=notes
        )
    
    def create_workflow_log(self, action, user=None, notes=""):
        """Crea un log de acción del workflow."""
        return WorkflowLog.objects.create(
            workflow_instance=self,
            action=action,
            user=user,
            notes=notes
        )
    
    def get_stage_history(self):
        """Obtiene el historial de etapas."""
        return self.stage_logs.all().order_by('created_at')
    
    def get_workflow_history(self):
        """Obtiene el historial completo del workflow."""
        return self.workflow_logs.all().order_by('created_at')
    
    def calculate_progress_percentage(self):
        """Calcula el porcentaje de progreso."""
        total_stages = self.template.get_stages().count()
        if total_stages == 0:
            return 0
        
        if not self.current_stage:
            return 0
        
        current_order = self.current_stage.order
        return (current_order / total_stages) * 100
    
    def is_overdue(self):
        """Verifica si el workflow está vencido."""
        if not self.due_date:
            return False
        return timezone.now() > self.due_date and self.status == 'active'


class WorkflowStageLog(models.Model):
    """
    Log de transiciones entre etapas.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE,
                                        related_name='stage_logs')
    stage = models.ForeignKey(WorkflowStage, on_delete=models.CASCADE,
                            related_name='stage_logs')
    
    ACTION_CHOICES = [
        ('entered', 'Ingresó a la etapa'),
        ('exited', 'Salió de la etapa'),
        ('started', 'Inició en esta etapa'),
        ('skipped', 'Saltó esta etapa'),
        ('failed', 'Falló en esta etapa')
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = "Log de Etapa"
        verbose_name_plural = "Logs de Etapas"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.workflow_instance.name} - {self.stage.name} ({self.action})"


class WorkflowLog(models.Model):
    """
    Log general de acciones del workflow.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE,
                                        related_name='workflow_logs')
    
    ACTION_CHOICES = [
        ('created', 'Creado'),
        ('started', 'Iniciado'),
        ('paused', 'Pausado'),
        ('resumed', 'Reanudado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('failed', 'Falló'),
        ('modified', 'Modificado')
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = "Log de Workflow"
        verbose_name_plural = "Logs de Workflow"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.workflow_instance.name} - {self.action}"