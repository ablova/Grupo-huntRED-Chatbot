"""
Advanced Workflows - huntRED® v2
Sistema avanzado de workflows con máquinas de estado, automatización y reglas de negocio complejas.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import asyncio
import uuid
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Estados posibles de un workflow."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Estados posibles de un paso."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"


class TriggerType(Enum):
    """Tipos de triggers para workflows."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    API_WEBHOOK = "api_webhook"


@dataclass
class WorkflowStep:
    """Definición de un paso en el workflow."""
    id: str
    name: str
    type: str  # action, condition, wait, approval, notification
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    conditions: List[Dict] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None


@dataclass
class WorkflowExecution:
    """Instancia de ejecución de un workflow."""
    id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime]
    current_step: Optional[str]
    context: Dict[str, Any]
    steps_status: Dict[str, StepStatus] = field(default_factory=dict)
    execution_log: List[Dict] = field(default_factory=list)
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class WorkflowDefinition:
    """Definición completa de un workflow."""
    id: str
    name: str
    description: str
    version: str
    trigger: TriggerType
    steps: List[WorkflowStep]
    variables: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


class AdvancedWorkflowEngine:
    """
    Motor avanzado de workflows con soporte para:
    - Máquinas de estado complejas
    - Ejecución paralela y secuencial
    - Condiciones y validaciones
    - Timeouts y reintentos
    - Notificaciones y escalaciones
    - Integración con sistemas externos
    """
    
    def __init__(self, config: Dict[str, Any], db_session: Session):
        self.config = config
        self.db = db_session
        
        # Registro de workflows
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        
        # Configurar tipos de pasos
        self._setup_step_handlers()
        
        # Configurar workflows predefinidos
        self._setup_predefined_workflows()
        
        # Estados de ejecución
        self.running = False
        self.execution_tasks: Dict[str, asyncio.Task] = {}
    
    def _setup_step_handlers(self):
        """Configura los manejadores para diferentes tipos de pasos."""
        self.step_handlers = {
            'action': self._handle_action_step,
            'condition': self._handle_condition_step,
            'wait': self._handle_wait_step,
            'approval': self._handle_approval_step,
            'notification': self._handle_notification_step,
            'api_call': self._handle_api_call_step,
            'email': self._handle_email_step,
            'data_transformation': self._handle_data_transformation_step,
            'database_operation': self._handle_database_operation_step,
            'ml_prediction': self._handle_ml_prediction_step,
            'file_processing': self._handle_file_processing_step,
            'integration': self._handle_integration_step
        }
    
    def _setup_predefined_workflows(self):
        """Configura workflows predefinidos del sistema."""
        # Workflow de Aplicación a Trabajo
        job_application_workflow = WorkflowDefinition(
            id="job_application_process",
            name="Proceso de Aplicación a Trabajo",
            description="Workflow completo para procesar aplicaciones de candidatos",
            version="2.0.0",
            trigger=TriggerType.EVENT_DRIVEN,
            steps=[
                WorkflowStep(
                    id="receive_application",
                    name="Recibir Aplicación",
                    type="action",
                    config={
                        "action": "log_application_received",
                        "auto_acknowledge": True
                    }
                ),
                WorkflowStep(
                    id="parse_cv",
                    name="Analizar CV",
                    type="ml_prediction",
                    config={
                        "model": "cv_parser",
                        "extract_skills": True,
                        "calculate_match_score": True
                    },
                    dependencies=["receive_application"]
                ),
                WorkflowStep(
                    id="check_requirements",
                    name="Verificar Requisitos",
                    type="condition",
                    config={
                        "conditions": [
                            {"field": "experience_years", "operator": ">=", "value": 2},
                            {"field": "skills_match_score", "operator": ">=", "value": 0.7}
                        ]
                    },
                    dependencies=["parse_cv"],
                    on_success="schedule_screening",
                    on_failure="send_rejection"
                ),
                WorkflowStep(
                    id="schedule_screening",
                    name="Programar Screening",
                    type="action",
                    config={
                        "action": "schedule_interview",
                        "interview_type": "screening",
                        "duration_minutes": 30
                    }
                ),
                WorkflowStep(
                    id="send_rejection",
                    name="Enviar Rechazo",
                    type="notification",
                    config={
                        "template": "application_rejection",
                        "channels": ["email"],
                        "personalize": True
                    }
                ),
                WorkflowStep(
                    id="conduct_screening",
                    name="Realizar Screening",
                    type="approval",
                    config={
                        "assignee_role": "recruiter",
                        "form_fields": [
                            {"name": "communication_score", "type": "number", "required": True},
                            {"name": "technical_assessment", "type": "text", "required": True},
                            {"name": "proceed_to_interview", "type": "boolean", "required": True}
                        ]
                    },
                    dependencies=["schedule_screening"],
                    timeout_seconds=86400,  # 24 horas
                    on_success="evaluate_screening",
                    on_failure="close_application"
                ),
                WorkflowStep(
                    id="evaluate_screening",
                    name="Evaluar Screening",
                    type="condition",
                    config={
                        "conditions": [
                            {"field": "proceed_to_interview", "operator": "==", "value": True}
                        ]
                    },
                    dependencies=["conduct_screening"],
                    on_success="schedule_technical_interview",
                    on_failure="send_screening_rejection"
                )
            ],
            variables={
                "job_position": "",
                "candidate_id": "",
                "application_id": "",
                "minimum_experience": 2,
                "minimum_skills_match": 0.7
            }
        )
        
        # Workflow de Onboarding
        onboarding_workflow = WorkflowDefinition(
            id="candidate_onboarding",
            name="Onboarding de Candidatos",
            description="Proceso completo de onboarding para nuevos empleados",
            version="2.0.0",
            trigger=TriggerType.MANUAL,
            steps=[
                WorkflowStep(
                    id="welcome_email",
                    name="Email de Bienvenida",
                    type="email",
                    config={
                        "template": "welcome_onboarding",
                        "include_attachments": ["employee_handbook.pdf", "benefits_guide.pdf"]
                    }
                ),
                WorkflowStep(
                    id="setup_accounts",
                    name="Configurar Cuentas",
                    type="integration",
                    config={
                        "integrations": [
                            {"system": "active_directory", "action": "create_user"},
                            {"system": "slack", "action": "add_to_workspace"},
                            {"system": "email", "action": "create_mailbox"}
                        ]
                    },
                    dependencies=["welcome_email"]
                ),
                WorkflowStep(
                    id="assign_buddy",
                    name="Asignar Compañero",
                    type="action",
                    config={
                        "action": "assign_buddy",
                        "criteria": ["same_department", "experience_level"]
                    },
                    dependencies=["setup_accounts"]
                ),
                WorkflowStep(
                    id="schedule_orientation",
                    name="Programar Orientación",
                    type="action",
                    config={
                        "action": "schedule_meeting",
                        "meeting_type": "orientation",
                        "duration_hours": 4,
                        "attendees": ["new_hire", "hr_representative", "direct_manager"]
                    },
                    dependencies=["assign_buddy"]
                ),
                WorkflowStep(
                    id="first_week_checkin",
                    name="Check-in Primera Semana",
                    type="wait",
                    config={
                        "wait_type": "duration",
                        "duration_days": 7
                    },
                    dependencies=["schedule_orientation"],
                    on_success="send_feedback_form"
                ),
                WorkflowStep(
                    id="send_feedback_form",
                    name="Enviar Formulario de Feedback",
                    type="notification",
                    config={
                        "template": "onboarding_feedback",
                        "form_url": "/forms/onboarding-feedback",
                        "reminder_after_days": 2
                    }
                )
            ]
        )
        
        # Registrar workflows
        self.register_workflow(job_application_workflow)
        self.register_workflow(onboarding_workflow)
    
    def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Registra un nuevo workflow en el sistema."""
        try:
            # Validar workflow
            validation_result = self._validate_workflow(workflow)
            if not validation_result['valid']:
                logger.error(f"Invalid workflow: {validation_result['errors']}")
                return False
            
            # Registrar
            self.workflows[workflow.id] = workflow
            logger.info(f"Workflow '{workflow.name}' registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error registering workflow: {str(e)}")
            return False
    
    def _validate_workflow(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """Valida la definición de un workflow."""
        errors = []
        
        try:
            # Validar que tenga al menos un paso
            if not workflow.steps:
                errors.append("Workflow must have at least one step")
            
            # Validar IDs únicos de pasos
            step_ids = [step.id for step in workflow.steps]
            if len(step_ids) != len(set(step_ids)):
                errors.append("Step IDs must be unique")
            
            # Validar dependencias
            for step in workflow.steps:
                for dep in step.dependencies:
                    if dep not in step_ids:
                        errors.append(f"Step '{step.id}' has invalid dependency '{dep}'")
            
            # Validar tipos de pasos
            for step in workflow.steps:
                if step.type not in self.step_handlers:
                    errors.append(f"Unknown step type: {step.type}")
            
            # Validar que no haya ciclos
            if self._has_cycles(workflow.steps):
                errors.append("Workflow contains circular dependencies")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"]
            }
    
    def _has_cycles(self, steps: List[WorkflowStep]) -> bool:
        """Detecta ciclos en las dependencias de los pasos."""
        # Implementación simplificada de detección de ciclos
        visited = set()
        rec_stack = set()
        
        def has_cycle_util(step_id: str, step_map: Dict[str, WorkflowStep]) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            if step_id in step_map:
                for dep in step_map[step_id].dependencies:
                    if dep not in visited:
                        if has_cycle_util(dep, step_map):
                            return True
                    elif dep in rec_stack:
                        return True
            
            rec_stack.remove(step_id)
            return False
        
        step_map = {step.id: step for step in steps}
        
        for step in steps:
            if step.id not in visited:
                if has_cycle_util(step.id, step_map):
                    return True
        
        return False
    
    async def start_workflow(self, workflow_id: str, 
                           context: Dict[str, Any] = None,
                           triggered_by: str = "system") -> Optional[str]:
        """Inicia la ejecución de un workflow."""
        try:
            if workflow_id not in self.workflows:
                logger.error(f"Workflow '{workflow_id}' not found")
                return None
            
            workflow = self.workflows[workflow_id]
            
            # Crear nueva ejecución
            execution_id = str(uuid.uuid4())
            execution = WorkflowExecution(
                id=execution_id,
                workflow_id=workflow_id,
                status=WorkflowStatus.ACTIVE,
                started_at=datetime.now(),
                completed_at=None,
                current_step=None,
                context=context or {},
                steps_status={step.id: StepStatus.PENDING for step in workflow.steps}
            )
            
            # Registrar ejecución
            self.executions[execution_id] = execution
            
            # Log de inicio
            self._log_execution_event(execution, "workflow_started", {
                "triggered_by": triggered_by,
                "workflow_name": workflow.name
            })
            
            # Iniciar tarea de ejecución
            task = asyncio.create_task(self._execute_workflow(execution_id))
            self.execution_tasks[execution_id] = task
            
            logger.info(f"Workflow '{workflow.name}' started with execution ID: {execution_id}")
            return execution_id
            
        except Exception as e:
            logger.error(f"Error starting workflow: {str(e)}")
            return None
    
    async def _execute_workflow(self, execution_id: str):
        """Ejecuta un workflow completo."""
        try:
            execution = self.executions[execution_id]
            workflow = self.workflows[execution.workflow_id]
            
            # Obtener pasos iniciales (sin dependencias)
            ready_steps = self._get_ready_steps(workflow, execution)
            
            while ready_steps and execution.status == WorkflowStatus.ACTIVE:
                # Ejecutar pasos en paralelo cuando sea posible
                tasks = []
                for step_id in ready_steps:
                    task = asyncio.create_task(
                        self._execute_step(execution_id, step_id)
                    )
                    tasks.append(task)
                
                # Esperar a que todos los pasos actuales terminen
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Actualizar pasos listos para la siguiente iteración
                ready_steps = self._get_ready_steps(workflow, execution)
                
                # Verificar si el workflow está completo
                if self._is_workflow_complete(workflow, execution):
                    execution.status = WorkflowStatus.COMPLETED
                    execution.completed_at = datetime.now()
                    self._log_execution_event(execution, "workflow_completed", {})
                    break
                
                # Verificar si hay errores fatales
                if self._has_fatal_errors(workflow, execution):
                    execution.status = WorkflowStatus.FAILED
                    execution.completed_at = datetime.now()
                    self._log_execution_event(execution, "workflow_failed", {
                        "reason": "fatal_errors_detected"
                    })
                    break
                
                # Pequeña pausa para evitar busy waiting
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error executing workflow {execution_id}: {str(e)}")
            execution = self.executions.get(execution_id)
            if execution:
                execution.status = WorkflowStatus.FAILED
                execution.error_message = str(e)
                execution.completed_at = datetime.now()
        finally:
            # Limpiar tarea de ejecución
            if execution_id in self.execution_tasks:
                del self.execution_tasks[execution_id]
    
    def _get_ready_steps(self, workflow: WorkflowDefinition, 
                        execution: WorkflowExecution) -> List[str]:
        """Obtiene los pasos que están listos para ejecutar."""
        ready_steps = []
        
        for step in workflow.steps:
            # Saltar si ya está completado, fallido o en progreso
            step_status = execution.steps_status.get(step.id, StepStatus.PENDING)
            if step_status in [StepStatus.COMPLETED, StepStatus.FAILED, 
                             StepStatus.IN_PROGRESS, StepStatus.SKIPPED]:
                continue
            
            # Verificar que todas las dependencias estén completadas
            dependencies_met = True
            for dep_id in step.dependencies:
                dep_status = execution.steps_status.get(dep_id, StepStatus.PENDING)
                if dep_status != StepStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                ready_steps.append(step.id)
        
        return ready_steps
    
    async def _execute_step(self, execution_id: str, step_id: str):
        """Ejecuta un paso individual del workflow."""
        try:
            execution = self.executions[execution_id]
            workflow = self.workflows[execution.workflow_id]
            
            # Encontrar el paso
            step = next((s for s in workflow.steps if s.id == step_id), None)
            if not step:
                logger.error(f"Step '{step_id}' not found in workflow")
                return
            
            # Marcar como en progreso
            execution.steps_status[step_id] = StepStatus.IN_PROGRESS
            execution.current_step = step_id
            
            self._log_execution_event(execution, "step_started", {
                "step_id": step_id,
                "step_name": step.name,
                "step_type": step.type
            })
            
            # Verificar condiciones del paso
            if step.conditions and not self._evaluate_conditions(step.conditions, execution.context):
                execution.steps_status[step_id] = StepStatus.SKIPPED
                self._log_execution_event(execution, "step_skipped", {
                    "step_id": step_id,
                    "reason": "conditions_not_met"
                })
                return
            
            # Ejecutar el paso con timeout
            step_success = False
            error_message = None
            
            try:
                if step.timeout_seconds:
                    step_success = await asyncio.wait_for(
                        self._run_step_handler(step, execution),
                        timeout=step.timeout_seconds
                    )
                else:
                    step_success = await self._run_step_handler(step, execution)
                    
            except asyncio.TimeoutError:
                error_message = f"Step timed out after {step.timeout_seconds} seconds"
                step_success = False
            except Exception as e:
                error_message = str(e)
                step_success = False
            
            # Manejar resultado
            if step_success:
                execution.steps_status[step_id] = StepStatus.COMPLETED
                self._log_execution_event(execution, "step_completed", {
                    "step_id": step_id
                })
                
                # Ejecutar siguiente paso basado en on_success
                if step.on_success:
                    execution.context['next_step'] = step.on_success
                    
            else:
                # Manejar fallo del paso
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    execution.steps_status[step_id] = StepStatus.PENDING
                    self._log_execution_event(execution, "step_retry", {
                        "step_id": step_id,
                        "retry_count": step.retry_count,
                        "error": error_message
                    })
                    
                    # Esperar antes del retry
                    await asyncio.sleep(2 ** step.retry_count)  # Exponential backoff
                else:
                    execution.steps_status[step_id] = StepStatus.FAILED
                    execution.error_message = error_message
                    self._log_execution_event(execution, "step_failed", {
                        "step_id": step_id,
                        "error": error_message
                    })
                    
                    # Ejecutar siguiente paso basado en on_failure
                    if step.on_failure:
                        execution.context['next_step'] = step.on_failure
            
        except Exception as e:
            logger.error(f"Error executing step {step_id}: {str(e)}")
            execution.steps_status[step_id] = StepStatus.FAILED
            execution.error_message = str(e)
    
    async def _run_step_handler(self, step: WorkflowStep, 
                              execution: WorkflowExecution) -> bool:
        """Ejecuta el manejador específico para el tipo de paso."""
        handler = self.step_handlers.get(step.type)
        if not handler:
            raise ValueError(f"No handler found for step type: {step.type}")
        
        return await handler(step, execution)
    
    # Manejadores de pasos específicos
    async def _handle_action_step(self, step: WorkflowStep, 
                                execution: WorkflowExecution) -> bool:
        """Maneja pasos de tipo acción."""
        try:
            action = step.config.get('action')
            logger.info(f"Executing action: {action}")
            
            # Aquí se implementarían las acciones específicas
            action_handlers = {
                'log_application_received': self._log_application_received,
                'schedule_interview': self._schedule_interview,
                'assign_buddy': self._assign_buddy,
                'schedule_meeting': self._schedule_meeting
            }
            
            if action in action_handlers:
                return await action_handlers[action](step, execution)
            
            # Acción genérica
            execution.context[f"{step.id}_result"] = {
                'action': action,
                'executed_at': datetime.now().isoformat(),
                'success': True
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error in action step: {str(e)}")
            return False
    
    async def _handle_condition_step(self, step: WorkflowStep, 
                                   execution: WorkflowExecution) -> bool:
        """Maneja pasos de tipo condición."""
        try:
            conditions = step.config.get('conditions', [])
            return self._evaluate_conditions(conditions, execution.context)
            
        except Exception as e:
            logger.error(f"Error in condition step: {str(e)}")
            return False
    
    async def _handle_wait_step(self, step: WorkflowStep, 
                              execution: WorkflowExecution) -> bool:
        """Maneja pasos de tipo espera."""
        try:
            wait_type = step.config.get('wait_type')
            
            if wait_type == 'duration':
                duration_days = step.config.get('duration_days', 0)
                duration_hours = step.config.get('duration_hours', 0)
                duration_minutes = step.config.get('duration_minutes', 0)
                
                total_seconds = (duration_days * 24 * 3600 + 
                               duration_hours * 3600 + 
                               duration_minutes * 60)
                
                await asyncio.sleep(total_seconds)
                
            elif wait_type == 'until_date':
                target_date = step.config.get('target_date')
                # Implementar espera hasta fecha específica
                pass
                
            elif wait_type == 'external_event':
                # Implementar espera por evento externo
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error in wait step: {str(e)}")
            return False
    
    async def _handle_approval_step(self, step: WorkflowStep, 
                                  execution: WorkflowExecution) -> bool:
        """Maneja pasos de tipo aprobación."""
        try:
            # Crear solicitud de aprobación
            approval_data = {
                'execution_id': execution.id,
                'step_id': step.id,
                'assignee': step.assignee,
                'form_fields': step.config.get('form_fields', []),
                'due_date': step.due_date,
                'created_at': datetime.now()
            }
            
            # Aquí se integraría con el sistema de aprobaciones
            execution.context[f"{step.id}_approval"] = approval_data
            
            # Marcar como esperando aprobación
            execution.steps_status[step.id] = StepStatus.WAITING
            
            # Simular aprobación automática para testing
            # En producción, esto se manejaría por la UI de aprobaciones
            await asyncio.sleep(1)  # Simular tiempo de procesamiento
            
            return True
            
        except Exception as e:
            logger.error(f"Error in approval step: {str(e)}")
            return False
    
    async def _handle_notification_step(self, step: WorkflowStep, 
                                      execution: WorkflowExecution) -> bool:
        """Maneja pasos de tipo notificación."""
        try:
            template = step.config.get('template')
            channels = step.config.get('channels', [])
            
            notification_data = {
                'template': template,
                'channels': channels,
                'execution_id': execution.id,
                'context': execution.context,
                'sent_at': datetime.now()
            }
            
            # Aquí se integraría con el sistema de notificaciones
            execution.context[f"{step.id}_notification"] = notification_data
            
            logger.info(f"Notification sent: {template} via {channels}")
            return True
            
        except Exception as e:
            logger.error(f"Error in notification step: {str(e)}")
            return False
    
    # Manejadores adicionales (implementación simplificada)
    async def _handle_api_call_step(self, step: WorkflowStep, 
                                  execution: WorkflowExecution) -> bool:
        """Maneja llamadas a APIs externas."""
        return True
    
    async def _handle_email_step(self, step: WorkflowStep, 
                               execution: WorkflowExecution) -> bool:
        """Maneja envío de emails."""
        return True
    
    async def _handle_data_transformation_step(self, step: WorkflowStep, 
                                             execution: WorkflowExecution) -> bool:
        """Maneja transformación de datos."""
        return True
    
    async def _handle_database_operation_step(self, step: WorkflowStep, 
                                            execution: WorkflowExecution) -> bool:
        """Maneja operaciones de base de datos."""
        return True
    
    async def _handle_ml_prediction_step(self, step: WorkflowStep, 
                                       execution: WorkflowExecution) -> bool:
        """Maneja predicciones de ML."""
        return True
    
    async def _handle_file_processing_step(self, step: WorkflowStep, 
                                         execution: WorkflowExecution) -> bool:
        """Maneja procesamiento de archivos."""
        return True
    
    async def _handle_integration_step(self, step: WorkflowStep, 
                                     execution: WorkflowExecution) -> bool:
        """Maneja integraciones con sistemas externos."""
        return True
    
    # Métodos auxiliares
    def _evaluate_conditions(self, conditions: List[Dict], 
                           context: Dict[str, Any]) -> bool:
        """Evalúa condiciones lógicas."""
        try:
            for condition in conditions:
                field = condition.get('field')
                operator = condition.get('operator')
                expected_value = condition.get('value')
                
                actual_value = context.get(field)
                
                if operator == '==':
                    if actual_value != expected_value:
                        return False
                elif operator == '!=':
                    if actual_value == expected_value:
                        return False
                elif operator == '>':
                    if not (actual_value > expected_value):
                        return False
                elif operator == '>=':
                    if not (actual_value >= expected_value):
                        return False
                elif operator == '<':
                    if not (actual_value < expected_value):
                        return False
                elif operator == '<=':
                    if not (actual_value <= expected_value):
                        return False
                elif operator == 'in':
                    if actual_value not in expected_value:
                        return False
                elif operator == 'contains':
                    if expected_value not in str(actual_value):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions: {str(e)}")
            return False
    
    def _is_workflow_complete(self, workflow: WorkflowDefinition, 
                            execution: WorkflowExecution) -> bool:
        """Verifica si el workflow está completo."""
        for step in workflow.steps:
            status = execution.steps_status.get(step.id, StepStatus.PENDING)
            if status not in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
                return False
        return True
    
    def _has_fatal_errors(self, workflow: WorkflowDefinition, 
                        execution: WorkflowExecution) -> bool:
        """Verifica si hay errores fatales que impidan continuar."""
        critical_steps = [step for step in workflow.steps 
                         if step.config.get('critical', False)]
        
        for step in critical_steps:
            status = execution.steps_status.get(step.id, StepStatus.PENDING)
            if status == StepStatus.FAILED:
                return True
        
        return False
    
    def _log_execution_event(self, execution: WorkflowExecution, 
                           event_type: str, data: Dict[str, Any]):
        """Registra eventos de ejecución."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }
        execution.execution_log.append(event)
        logger.info(f"Workflow {execution.id}: {event_type}")
    
    # Acciones específicas del dominio
    async def _log_application_received(self, step: WorkflowStep, 
                                      execution: WorkflowExecution) -> bool:
        """Registra recepción de aplicación."""
        execution.context['application_logged'] = True
        execution.context['logged_at'] = datetime.now().isoformat()
        return True
    
    async def _schedule_interview(self, step: WorkflowStep, 
                                execution: WorkflowExecution) -> bool:
        """Programa una entrevista."""
        interview_type = step.config.get('interview_type', 'general')
        duration = step.config.get('duration_minutes', 60)
        
        execution.context['interview_scheduled'] = {
            'type': interview_type,
            'duration_minutes': duration,
            'scheduled_at': datetime.now().isoformat()
        }
        return True
    
    async def _assign_buddy(self, step: WorkflowStep, 
                          execution: WorkflowExecution) -> bool:
        """Asigna un compañero buddy."""
        criteria = step.config.get('criteria', [])
        execution.context['buddy_assigned'] = {
            'criteria': criteria,
            'assigned_at': datetime.now().isoformat()
        }
        return True
    
    async def _schedule_meeting(self, step: WorkflowStep, 
                              execution: WorkflowExecution) -> bool:
        """Programa una reunión."""
        meeting_type = step.config.get('meeting_type', 'general')
        duration = step.config.get('duration_hours', 1)
        attendees = step.config.get('attendees', [])
        
        execution.context['meeting_scheduled'] = {
            'type': meeting_type,
            'duration_hours': duration,
            'attendees': attendees,
            'scheduled_at': datetime.now().isoformat()
        }
        return True
    
    # Métodos de gestión
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado actual de una ejecución."""
        execution = self.executions.get(execution_id)
        if not execution:
            return None
        
        return {
            'execution_id': execution_id,
            'workflow_id': execution.workflow_id,
            'status': execution.status.value,
            'current_step': execution.current_step,
            'steps_status': {k: v.value for k, v in execution.steps_status.items()},
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'context': execution.context,
            'execution_log': execution.execution_log[-10:]  # Últimos 10 eventos
        }
    
    async def pause_workflow(self, execution_id: str) -> bool:
        """Pausa la ejecución de un workflow."""
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        execution.status = WorkflowStatus.PAUSED
        self._log_execution_event(execution, "workflow_paused", {})
        return True
    
    async def resume_workflow(self, execution_id: str) -> bool:
        """Reanuda la ejecución de un workflow."""
        execution = self.executions.get(execution_id)
        if not execution or execution.status != WorkflowStatus.PAUSED:
            return False
        
        execution.status = WorkflowStatus.ACTIVE
        self._log_execution_event(execution, "workflow_resumed", {})
        
        # Reiniciar tarea de ejecución
        task = asyncio.create_task(self._execute_workflow(execution_id))
        self.execution_tasks[execution_id] = task
        
        return True
    
    async def cancel_workflow(self, execution_id: str) -> bool:
        """Cancela la ejecución de un workflow."""
        execution = self.executions.get(execution_id)
        if not execution:
            return False
        
        execution.status = WorkflowStatus.CANCELLED
        execution.completed_at = datetime.now()
        self._log_execution_event(execution, "workflow_cancelled", {})
        
        # Cancelar tarea de ejecución
        if execution_id in self.execution_tasks:
            self.execution_tasks[execution_id].cancel()
            del self.execution_tasks[execution_id]
        
        return True
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """Lista todos los workflows registrados."""
        return [
            {
                'id': workflow.id,
                'name': workflow.name,
                'description': workflow.description,
                'version': workflow.version,
                'trigger': workflow.trigger.value,
                'is_active': workflow.is_active,
                'steps_count': len(workflow.steps)
            }
            for workflow in self.workflows.values()
        ]
    
    def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista las ejecuciones de workflows."""
        executions = self.executions.values()
        
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        return [
            {
                'execution_id': execution.id,
                'workflow_id': execution.workflow_id,
                'status': execution.status.value,
                'started_at': execution.started_at.isoformat(),
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
                'current_step': execution.current_step,
                'progress': self._calculate_progress(execution)
            }
            for execution in executions
        ]
    
    def _calculate_progress(self, execution: WorkflowExecution) -> float:
        """Calcula el progreso de una ejecución."""
        if not execution.steps_status:
            return 0.0
        
        completed = sum(1 for status in execution.steps_status.values() 
                       if status in [StepStatus.COMPLETED, StepStatus.SKIPPED])
        total = len(execution.steps_status)
        
        return completed / total if total > 0 else 0.0