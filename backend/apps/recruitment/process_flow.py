"""
Sistema de Flujo de Proceso de Reclutamiento huntRED® v2
=====================================================

Funcionalidades:
- Visualización gráfica del proceso de reclutamiento
- Puntos de interacción dinámicos
- Estados y transiciones automatizadas
- Métricas y analíticas en tiempo real
- Configuración personalizable por cliente
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class ProcessStage(Enum):
    """Etapas del proceso de reclutamiento."""
    SOURCING = "sourcing"
    INITIAL_SCREENING = "initial_screening"
    APPLICATION_REVIEW = "application_review"
    PHONE_SCREENING = "phone_screening"
    ASSESSMENT = "assessment"
    FIRST_INTERVIEW = "first_interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    BEHAVIORAL_INTERVIEW = "behavioral_interview"
    PANEL_INTERVIEW = "panel_interview"
    FINAL_INTERVIEW = "final_interview"
    BACKGROUND_CHECK = "background_check"
    REFERENCE_CHECK = "reference_check"
    OFFER_NEGOTIATION = "offer_negotiation"
    CONTRACT_SIGNING = "contract_signing"
    ONBOARDING = "onboarding"
    FOLLOW_UP = "follow_up"

class StageStatus(Enum):
    """Estados de las etapas."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    FAILED = "failed"
    APPROVED = "approved"
    REJECTED = "rejected"

class InteractionType(Enum):
    """Tipos de interacción en el proceso."""
    AUTOMATED = "automated"
    MANUAL_REVIEW = "manual_review"
    SCHEDULED_CALL = "scheduled_call"
    EMAIL_EXCHANGE = "email_exchange"
    DOCUMENT_UPLOAD = "document_upload"
    ASSESSMENT_COMPLETION = "assessment_completion"
    INTERVIEW_CONDUCTED = "interview_conducted"
    DECISION_POINT = "decision_point"
    NOTIFICATION_SENT = "notification_sent"
    APPROVAL_REQUIRED = "approval_required"

@dataclass
class InteractionPoint:
    """Punto de interacción en el proceso."""
    id: str
    stage: ProcessStage
    interaction_type: InteractionType
    name: str
    description: str
    
    # Actores involucrados
    primary_actor: str  # candidate, recruiter, hiring_manager, client
    secondary_actors: List[str] = field(default_factory=list)
    
    # Configuración
    required: bool = True
    automated: bool = False
    estimated_duration: int = 0  # minutos
    deadline_hours: Optional[int] = None
    
    # Condiciones
    prerequisites: List[str] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    failure_criteria: Dict[str, Any] = field(default_factory=dict)
    
    # Metadatos
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    notification_templates: List[str] = field(default_factory=list)

@dataclass
class StageTransition:
    """Transición entre etapas."""
    from_stage: ProcessStage
    to_stage: ProcessStage
    condition_type: str  # automatic, approval_required, manual
    conditions: Dict[str, Any] = field(default_factory=dict)
    probability: float = 1.0  # Probabilidad de transición exitosa

@dataclass
class ProcessInstance:
    """Instancia específica del proceso para un candidato."""
    id: str
    job_id: str
    candidate_id: str
    client_id: str
    
    # Estado actual
    current_stage: ProcessStage
    current_status: StageStatus
    started_at: datetime
    expected_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    
    # Historial de etapas
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    interaction_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Métricas
    total_duration: Optional[timedelta] = None
    stages_completed: int = 0
    success_rate: float = 0.0
    
    # Configuración personalizada
    custom_flow: Optional[List[ProcessStage]] = None
    skip_stages: List[ProcessStage] = field(default_factory=list)
    priority_level: str = "normal"  # low, normal, high, urgent
    
    # Metadatos
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    assigned_recruiter: Optional[str] = None

class RecruitmentFlowEngine:
    """Motor principal del flujo de reclutamiento."""
    
    def __init__(self):
        self.active_processes: Dict[str, ProcessInstance] = {}
        self.flow_configurations: Dict[str, Dict] = {}
        self.interaction_points: Dict[ProcessStage, List[InteractionPoint]] = {}
        self.stage_transitions: List[StageTransition] = []
        
        # Configuración por defecto
        self._setup_default_flow()
        self._setup_default_interactions()
        self._setup_default_transitions()
    
    def _setup_default_flow(self):
        """Configura flujos por defecto según tipo de posición."""
        
        self.flow_configurations = {
            'standard': {
                'name': 'Proceso Estándar',
                'stages': [
                    ProcessStage.SOURCING,
                    ProcessStage.APPLICATION_REVIEW,
                    ProcessStage.PHONE_SCREENING,
                    ProcessStage.FIRST_INTERVIEW,
                    ProcessStage.BACKGROUND_CHECK,
                    ProcessStage.REFERENCE_CHECK,
                    ProcessStage.OFFER_NEGOTIATION,
                    ProcessStage.CONTRACT_SIGNING,
                    ProcessStage.ONBOARDING
                ],
                'estimated_duration_days': 21,
                'success_rate': 0.65
            },
            'technical': {
                'name': 'Proceso Técnico',
                'stages': [
                    ProcessStage.SOURCING,
                    ProcessStage.APPLICATION_REVIEW,
                    ProcessStage.PHONE_SCREENING,
                    ProcessStage.ASSESSMENT,
                    ProcessStage.TECHNICAL_INTERVIEW,
                    ProcessStage.BEHAVIORAL_INTERVIEW,
                    ProcessStage.BACKGROUND_CHECK,
                    ProcessStage.REFERENCE_CHECK,
                    ProcessStage.OFFER_NEGOTIATION,
                    ProcessStage.CONTRACT_SIGNING,
                    ProcessStage.ONBOARDING
                ],
                'estimated_duration_days': 28,
                'success_rate': 0.45
            },
            'executive': {
                'name': 'Proceso Ejecutivo',
                'stages': [
                    ProcessStage.SOURCING,
                    ProcessStage.INITIAL_SCREENING,
                    ProcessStage.FIRST_INTERVIEW,
                    ProcessStage.BEHAVIORAL_INTERVIEW,
                    ProcessStage.PANEL_INTERVIEW,
                    ProcessStage.FINAL_INTERVIEW,
                    ProcessStage.BACKGROUND_CHECK,
                    ProcessStage.REFERENCE_CHECK,
                    ProcessStage.OFFER_NEGOTIATION,
                    ProcessStage.CONTRACT_SIGNING,
                    ProcessStage.ONBOARDING,
                    ProcessStage.FOLLOW_UP
                ],
                'estimated_duration_days': 45,
                'success_rate': 0.35
            },
            'fast_track': {
                'name': 'Proceso Acelerado',
                'stages': [
                    ProcessStage.APPLICATION_REVIEW,
                    ProcessStage.FIRST_INTERVIEW,
                    ProcessStage.REFERENCE_CHECK,
                    ProcessStage.OFFER_NEGOTIATION,
                    ProcessStage.CONTRACT_SIGNING,
                    ProcessStage.ONBOARDING
                ],
                'estimated_duration_days': 7,
                'success_rate': 0.80
            }
        }
    
    def _setup_default_interactions(self):
        """Configura puntos de interacción por defecto."""
        
        interactions = [
            # SOURCING
            InteractionPoint(
                id="sourcing_search",
                stage=ProcessStage.SOURCING,
                interaction_type=InteractionType.AUTOMATED,
                name="Búsqueda de Candidatos",
                description="Búsqueda automática en bases de datos y LinkedIn",
                primary_actor="recruiter",
                automated=True,
                estimated_duration=30
            ),
            InteractionPoint(
                id="sourcing_contact",
                stage=ProcessStage.SOURCING,
                interaction_type=InteractionType.EMAIL_EXCHANGE,
                name="Contacto Inicial",
                description="Primer contacto con candidatos potenciales",
                primary_actor="recruiter",
                estimated_duration=15,
                notification_templates=["initial_contact"]
            ),
            
            # APPLICATION REVIEW
            InteractionPoint(
                id="cv_screening",
                stage=ProcessStage.APPLICATION_REVIEW,
                interaction_type=InteractionType.AUTOMATED,
                name="Análisis de CV",
                description="Análisis automático de CV con IA",
                primary_actor="recruiter",
                automated=True,
                estimated_duration=5,
                success_criteria={"min_score": 0.7}
            ),
            InteractionPoint(
                id="manual_review",
                stage=ProcessStage.APPLICATION_REVIEW,
                interaction_type=InteractionType.MANUAL_REVIEW,
                name="Revisión Manual",
                description="Revisión manual por parte del recruiter",
                primary_actor="recruiter",
                estimated_duration=20,
                deadline_hours=24
            ),
            
            # PHONE SCREENING
            InteractionPoint(
                id="phone_schedule",
                stage=ProcessStage.PHONE_SCREENING,
                interaction_type=InteractionType.SCHEDULED_CALL,
                name="Programar Llamada",
                description="Programación de llamada de screening",
                primary_actor="recruiter",
                secondary_actors=["candidate"],
                estimated_duration=10
            ),
            InteractionPoint(
                id="phone_conduct",
                stage=ProcessStage.PHONE_SCREENING,
                interaction_type=InteractionType.SCHEDULED_CALL,
                name="Realizar Llamada",
                description="Llamada de screening telefónico",
                primary_actor="recruiter",
                secondary_actors=["candidate"],
                estimated_duration=30,
                success_criteria={"min_score": 3.0, "max_score": 5.0}
            ),
            
            # INTERVIEWS
            InteractionPoint(
                id="interview_schedule",
                stage=ProcessStage.FIRST_INTERVIEW,
                interaction_type=InteractionType.SCHEDULED_CALL,
                name="Programar Entrevista",
                description="Programación de primera entrevista",
                primary_actor="recruiter",
                secondary_actors=["candidate", "hiring_manager"],
                estimated_duration=15
            ),
            InteractionPoint(
                id="interview_conduct",
                stage=ProcessStage.FIRST_INTERVIEW,
                interaction_type=InteractionType.INTERVIEW_CONDUCTED,
                name="Realizar Entrevista",
                description="Primera entrevista con el candidato",
                primary_actor="hiring_manager",
                secondary_actors=["candidate", "recruiter"],
                estimated_duration=60,
                success_criteria={"min_score": 3.5}
            ),
            
            # BACKGROUND CHECK
            InteractionPoint(
                id="background_initiate",
                stage=ProcessStage.BACKGROUND_CHECK,
                interaction_type=InteractionType.AUTOMATED,
                name="Iniciar Background Check",
                description="Iniciar verificación de antecedentes",
                primary_actor="recruiter",
                automated=True,
                estimated_duration=5
            ),
            InteractionPoint(
                id="background_review",
                stage=ProcessStage.BACKGROUND_CHECK,
                interaction_type=InteractionType.MANUAL_REVIEW,
                name="Revisar Resultados",
                description="Revisión de resultados de background check",
                primary_actor="recruiter",
                estimated_duration=30,
                deadline_hours=72
            ),
            
            # OFFER
            InteractionPoint(
                id="offer_preparation",
                stage=ProcessStage.OFFER_NEGOTIATION,
                interaction_type=InteractionType.MANUAL_REVIEW,
                name="Preparar Oferta",
                description="Preparación de oferta laboral",
                primary_actor="recruiter",
                secondary_actors=["hiring_manager", "client"],
                estimated_duration=45
            ),
            InteractionPoint(
                id="offer_presentation",
                stage=ProcessStage.OFFER_NEGOTIATION,
                interaction_type=InteractionType.SCHEDULED_CALL,
                name="Presentar Oferta",
                description="Presentación de oferta al candidato",
                primary_actor="recruiter",
                secondary_actors=["candidate"],
                estimated_duration=30
            ),
            InteractionPoint(
                id="offer_negotiation",
                stage=ProcessStage.OFFER_NEGOTIATION,
                interaction_type=InteractionType.EMAIL_EXCHANGE,
                name="Negociar Términos",
                description="Negociación de términos de la oferta",
                primary_actor="recruiter",
                secondary_actors=["candidate", "client"],
                estimated_duration=120
            )
        ]
        
        # Organizar por etapa
        for interaction in interactions:
            if interaction.stage not in self.interaction_points:
                self.interaction_points[interaction.stage] = []
            self.interaction_points[interaction.stage].append(interaction)
    
    def _setup_default_transitions(self):
        """Configura transiciones entre etapas."""
        
        self.stage_transitions = [
            # Flujo principal
            StageTransition(
                ProcessStage.SOURCING, 
                ProcessStage.APPLICATION_REVIEW,
                "automatic",
                {"min_candidates": 1},
                0.95
            ),
            StageTransition(
                ProcessStage.APPLICATION_REVIEW, 
                ProcessStage.PHONE_SCREENING,
                "approval_required",
                {"min_cv_score": 0.7},
                0.75
            ),
            StageTransition(
                ProcessStage.PHONE_SCREENING, 
                ProcessStage.FIRST_INTERVIEW,
                "approval_required",
                {"min_phone_score": 3.0},
                0.60
            ),
            StageTransition(
                ProcessStage.FIRST_INTERVIEW, 
                ProcessStage.BACKGROUND_CHECK,
                "approval_required",
                {"min_interview_score": 3.5},
                0.70
            ),
            StageTransition(
                ProcessStage.BACKGROUND_CHECK, 
                ProcessStage.REFERENCE_CHECK,
                "automatic",
                {"background_status": "passed"},
                0.85
            ),
            StageTransition(
                ProcessStage.REFERENCE_CHECK, 
                ProcessStage.OFFER_NEGOTIATION,
                "approval_required",
                {"min_references": 2, "reference_quality": "good"},
                0.80
            ),
            StageTransition(
                ProcessStage.OFFER_NEGOTIATION, 
                ProcessStage.CONTRACT_SIGNING,
                "manual",
                {"offer_accepted": True},
                0.75
            ),
            StageTransition(
                ProcessStage.CONTRACT_SIGNING, 
                ProcessStage.ONBOARDING,
                "automatic",
                {"contract_signed": True},
                0.95
            )
        ]
    
    async def start_process(self, job_id: str, candidate_id: str, 
                          client_id: str, flow_type: str = "standard",
                          custom_stages: Optional[List[ProcessStage]] = None) -> ProcessInstance:
        """Inicia un nuevo proceso de reclutamiento."""
        
        process_id = str(uuid.uuid4())
        
        # Determinar flujo
        if custom_stages:
            stages = custom_stages
            flow_config = {"stages": stages, "estimated_duration_days": 30}
        else:
            flow_config = self.flow_configurations.get(flow_type, self.flow_configurations["standard"])
            stages = flow_config["stages"]
        
        # Crear instancia del proceso
        process = ProcessInstance(
            id=process_id,
            job_id=job_id,
            candidate_id=candidate_id,
            client_id=client_id,
            current_stage=stages[0],
            current_status=StageStatus.PENDING,
            started_at=datetime.now(),
            expected_completion=datetime.now() + timedelta(days=flow_config.get("estimated_duration_days", 21)),
            custom_flow=stages if custom_stages else None
        )
        
        # Registrar inicio
        await self._log_stage_change(process, None, stages[0], "Process started")
        
        self.active_processes[process_id] = process
        
        # Iniciar primera etapa automáticamente
        await self._trigger_stage_interactions(process)
        
        logger.info(f"Started recruitment process {process_id} for candidate {candidate_id}")
        return process
    
    async def advance_stage(self, process_id: str, 
                          interaction_results: Dict[str, Any]) -> bool:
        """Avanza el proceso a la siguiente etapa."""
        
        if process_id not in self.active_processes:
            logger.error(f"Process {process_id} not found")
            return False
        
        process = self.active_processes[process_id]
        current_stage = process.current_stage
        
        # Validar que se pueden completar las interacciones de la etapa actual
        if not await self._validate_stage_completion(process, interaction_results):
            return False
        
        # Encontrar próxima etapa
        next_stage = await self._determine_next_stage(process, interaction_results)
        if not next_stage:
            logger.warning(f"No next stage determined for process {process_id}")
            return False
        
        # Ejecutar transición
        old_stage = process.current_stage
        process.current_stage = next_stage
        process.current_status = StageStatus.PENDING
        process.stages_completed += 1
        
        # Actualizar historial
        await self._log_stage_change(process, old_stage, next_stage, 
                                    f"Advanced from {old_stage.value}", interaction_results)
        
        # Trigger interacciones de nueva etapa
        await self._trigger_stage_interactions(process)
        
        logger.info(f"Advanced process {process_id} from {old_stage.value} to {next_stage.value}")
        return True
    
    async def _validate_stage_completion(self, process: ProcessInstance, 
                                       results: Dict[str, Any]) -> bool:
        """Valida si una etapa puede completarse."""
        
        stage_interactions = self.interaction_points.get(process.current_stage, [])
        
        for interaction in stage_interactions:
            if not interaction.required:
                continue
            
            # Verificar criterios de éxito
            if interaction.success_criteria:
                for criterion, expected_value in interaction.success_criteria.items():
                    actual_value = results.get(criterion)
                    
                    if actual_value is None:
                        logger.warning(f"Missing criterion {criterion} for interaction {interaction.id}")
                        return False
                    
                    # Validaciones específicas por tipo
                    if isinstance(expected_value, (int, float)):
                        if actual_value < expected_value:
                            logger.warning(f"Criterion {criterion} not met: {actual_value} < {expected_value}")
                            return False
        
        return True
    
    async def _determine_next_stage(self, process: ProcessInstance, 
                                  results: Dict[str, Any]) -> Optional[ProcessStage]:
        """Determina la próxima etapa basada en transiciones."""
        
        current_stage = process.current_stage
        flow_stages = process.custom_flow or self.flow_configurations["standard"]["stages"]
        
        # Buscar próxima etapa en el flujo
        try:
            current_index = flow_stages.index(current_stage)
            if current_index < len(flow_stages) - 1:
                return flow_stages[current_index + 1]
        except ValueError:
            logger.error(f"Current stage {current_stage} not found in flow")
        
        return None
    
    async def _trigger_stage_interactions(self, process: ProcessInstance):
        """Dispara las interacciones automáticas de una etapa."""
        
        stage_interactions = self.interaction_points.get(process.current_stage, [])
        
        for interaction in stage_interactions:
            if interaction.automated:
                await self._execute_automated_interaction(process, interaction)
            else:
                await self._schedule_manual_interaction(process, interaction)
    
    async def _execute_automated_interaction(self, process: ProcessInstance, 
                                           interaction: InteractionPoint):
        """Ejecuta una interacción automatizada."""
        
        logger.info(f"Executing automated interaction {interaction.id} for process {process.id}")
        
        # Simular ejecución
        result = {
            "interaction_id": interaction.id,
            "status": "completed",
            "duration": interaction.estimated_duration,
            "timestamp": datetime.now().isoformat(),
            "automated": True
        }
        
        # Log de la interacción
        process.interaction_history.append(result)
        
        # Enviar notificaciones si es necesario
        for template in interaction.notification_templates:
            await self._send_interaction_notification(process, interaction, template)
    
    async def _schedule_manual_interaction(self, process: ProcessInstance,
                                         interaction: InteractionPoint):
        """Programa una interacción manual."""
        
        logger.info(f"Scheduling manual interaction {interaction.id} for process {process.id}")
        
        # Calcular deadline
        deadline = None
        if interaction.deadline_hours:
            deadline = datetime.now() + timedelta(hours=interaction.deadline_hours)
        
        # Crear tarea pendiente
        task = {
            "interaction_id": interaction.id,
            "process_id": process.id,
            "status": "pending",
            "assigned_to": interaction.primary_actor,
            "deadline": deadline.isoformat() if deadline else None,
            "created_at": datetime.now().isoformat()
        }
        
        # En un sistema real, esto se almacenaría en la base de datos
        logger.info(f"Created task for {interaction.primary_actor}: {interaction.name}")
        
        # Enviar notificación de tarea asignada
        await self._send_task_notification(process, interaction, task)
    
    async def _log_stage_change(self, process: ProcessInstance, 
                              old_stage: Optional[ProcessStage],
                              new_stage: ProcessStage, 
                              reason: str,
                              additional_data: Optional[Dict] = None):
        """Registra cambio de etapa en el historial."""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "from_stage": old_stage.value if old_stage else None,
            "to_stage": new_stage.value,
            "reason": reason,
            "duration_minutes": None,
            "additional_data": additional_data or {}
        }
        
        # Calcular duración si hay etapa anterior
        if process.stage_history:
            last_entry = process.stage_history[-1]
            last_time = datetime.fromisoformat(last_entry["timestamp"])
            duration = datetime.now() - last_time
            log_entry["duration_minutes"] = duration.total_seconds() / 60
        
        process.stage_history.append(log_entry)
    
    async def _send_interaction_notification(self, process: ProcessInstance,
                                           interaction: InteractionPoint,
                                           template: str):
        """Envía notificación de interacción."""
        
        # En un sistema real, esto integraría con el sistema de notificaciones
        logger.info(f"Sending notification {template} for interaction {interaction.id}")
    
    async def _send_task_notification(self, process: ProcessInstance,
                                    interaction: InteractionPoint,
                                    task: Dict[str, Any]):
        """Envía notificación de tarea asignada."""
        
        logger.info(f"Sending task notification to {interaction.primary_actor} for {interaction.name}")
    
    def get_process_visualization(self, process_id: str) -> Dict[str, Any]:
        """Genera datos para visualización del proceso."""
        
        if process_id not in self.active_processes:
            return {}
        
        process = self.active_processes[process_id]
        flow_stages = process.custom_flow or self.flow_configurations["standard"]["stages"]
        
        # Construir nodos del grafico
        nodes = []
        edges = []
        
        for i, stage in enumerate(flow_stages):
            # Determinar estado del nodo
            if stage == process.current_stage:
                status = "current"
            elif i < flow_stages.index(process.current_stage):
                status = "completed"
            else:
                status = "pending"
            
            # Obtener métricas de la etapa
            stage_metrics = self._get_stage_metrics(process, stage)
            
            node = {
                "id": stage.value,
                "label": stage.value.replace("_", " ").title(),
                "status": status,
                "position": {"x": i * 200, "y": 100},
                "metrics": stage_metrics,
                "interactions": [
                    {
                        "id": interaction.id,
                        "name": interaction.name,
                        "type": interaction.interaction_type.value,
                        "automated": interaction.automated,
                        "required": interaction.required
                    }
                    for interaction in self.interaction_points.get(stage, [])
                ]
            }
            nodes.append(node)
            
            # Crear edge al siguiente nodo
            if i < len(flow_stages) - 1:
                edges.append({
                    "from": stage.value,
                    "to": flow_stages[i + 1].value,
                    "status": "completed" if status == "completed" else "pending"
                })
        
        return {
            "process_id": process_id,
            "nodes": nodes,
            "edges": edges,
            "current_stage": process.current_stage.value,
            "progress_percentage": (process.stages_completed / len(flow_stages)) * 100,
            "estimated_completion": process.expected_completion.isoformat() if process.expected_completion else None,
            "total_duration_days": (datetime.now() - process.started_at).days,
            "stage_history": process.stage_history[-10:],  # Últimas 10 entradas
            "interaction_history": process.interaction_history[-20:]  # Últimas 20 interacciones
        }
    
    def _get_stage_metrics(self, process: ProcessInstance, stage: ProcessStage) -> Dict[str, Any]:
        """Obtiene métricas específicas de una etapa."""
        
        # Buscar entradas de historial para esta etapa
        stage_entries = [
            entry for entry in process.stage_history 
            if entry.get("to_stage") == stage.value
        ]
        
        if not stage_entries:
            return {}
        
        entry = stage_entries[0]
        
        return {
            "start_time": entry.get("timestamp"),
            "duration_minutes": entry.get("duration_minutes"),
            "status": "completed" if entry.get("duration_minutes") else "in_progress"
        }
    
    def get_flow_analytics(self, client_id: Optional[str] = None,
                          date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Obtiene analíticas del flujo de reclutamiento."""
        
        # Filtrar procesos
        processes = list(self.active_processes.values())
        
        if client_id:
            processes = [p for p in processes if p.client_id == client_id]
        
        if date_range:
            start_date, end_date = date_range
            processes = [
                p for p in processes 
                if start_date <= p.started_at <= end_date
            ]
        
        if not processes:
            return {"message": "No processes found for the given criteria"}
        
        # Calcular métricas
        total_processes = len(processes)
        completed_processes = len([p for p in processes if p.actual_completion])
        avg_duration = sum(
            (p.actual_completion - p.started_at).days 
            for p in processes if p.actual_completion
        ) / completed_processes if completed_processes > 0 else 0
        
        # Métricas por etapa
        stage_metrics = {}
        for stage in ProcessStage:
            stage_processes = [
                p for p in processes 
                if any(entry.get("to_stage") == stage.value for entry in p.stage_history)
            ]
            
            if stage_processes:
                durations = [
                    entry.get("duration_minutes", 0)
                    for p in stage_processes
                    for entry in p.stage_history
                    if entry.get("to_stage") == stage.value and entry.get("duration_minutes")
                ]
                
                stage_metrics[stage.value] = {
                    "total_processes": len(stage_processes),
                    "avg_duration_minutes": sum(durations) / len(durations) if durations else 0,
                    "completion_rate": len(durations) / len(stage_processes) if stage_processes else 0
                }
        
        # Bottlenecks (etapas con mayor duración promedio)
        bottlenecks = sorted(
            stage_metrics.items(),
            key=lambda x: x[1]["avg_duration_minutes"],
            reverse=True
        )[:5]
        
        return {
            "summary": {
                "total_processes": total_processes,
                "completed_processes": completed_processes,
                "completion_rate": completed_processes / total_processes if total_processes > 0 else 0,
                "avg_duration_days": avg_duration
            },
            "stage_metrics": stage_metrics,
            "bottlenecks": [
                {
                    "stage": stage,
                    "avg_duration_minutes": metrics["avg_duration_minutes"],
                    "total_processes": metrics["total_processes"]
                }
                for stage, metrics in bottlenecks
            ],
            "recommendations": self._generate_flow_recommendations(stage_metrics, bottlenecks)
        }
    
    def _generate_flow_recommendations(self, stage_metrics: Dict, 
                                     bottlenecks: List) -> List[str]:
        """Genera recomendaciones para optimizar el flujo."""
        
        recommendations = []
        
        # Analizar bottlenecks
        if bottlenecks:
            top_bottleneck = bottlenecks[0]
            if top_bottleneck[1] > 1440:  # Más de 24 horas
                recommendations.append(
                    f"Considerar automatizar o streamlinear la etapa '{top_bottleneck[0]}' "
                    f"que toma en promedio {top_bottleneck[1]/60:.1f} horas"
                )
        
        # Analizar tasas de completion
        low_completion_stages = [
            stage for stage, metrics in stage_metrics.items()
            if metrics["completion_rate"] < 0.8
        ]
        
        if low_completion_stages:
            recommendations.append(
                f"Revisar las etapas {', '.join(low_completion_stages)} "
                "que tienen bajas tasas de completion"
            )
        
        # Sugerencias generales
        recommendations.extend([
            "Implementar más puntos de automatización para reducir tiempo manual",
            "Establecer SLAs claros para cada etapa del proceso",
            "Considerar procesos paralelos para etapas independientes"
        ])
        
        return recommendations[:5]  # Top 5 recomendaciones
    
    def create_custom_flow(self, name: str, stages: List[ProcessStage],
                         estimated_duration_days: int) -> str:
        """Crea un flujo personalizado."""
        
        flow_id = f"custom_{uuid.uuid4().hex[:8]}"
        
        self.flow_configurations[flow_id] = {
            "name": name,
            "stages": stages,
            "estimated_duration_days": estimated_duration_days,
            "success_rate": 0.5,  # Se actualizará con datos reales
            "custom": True
        }
        
        logger.info(f"Created custom flow {flow_id}: {name}")
        return flow_id

# Funciones de utilidad para generar visualizaciones
def generate_mermaid_diagram(process_id: str, flow_engine: RecruitmentFlowEngine) -> str:
    """Genera diagrama Mermaid del proceso."""
    
    viz_data = flow_engine.get_process_visualization(process_id)
    if not viz_data:
        return ""
    
    lines = ["graph TD"]
    
    # Agregar nodos
    for node in viz_data["nodes"]:
        status_class = f"class_{node['status']}"
        lines.append(f"    {node['id']}[{node['label']}]:::{status_class}")
    
    # Agregar edges
    for edge in viz_data["edges"]:
        lines.append(f"    {edge['from']} --> {edge['to']}")
    
    # Agregar estilos
    lines.extend([
        "",
        "    classDef class_completed fill:#d4edda,stroke:#28a745",
        "    classDef class_current fill:#fff3cd,stroke:#ffc107",
        "    classDef class_pending fill:#f8f9fa,stroke:#6c757d"
    ])
    
    return "\n".join(lines)

# Exportaciones
__all__ = [
    'ProcessStage', 'StageStatus', 'InteractionType', 'InteractionPoint',
    'StageTransition', 'ProcessInstance', 'RecruitmentFlowEngine',
    'generate_mermaid_diagram'
]