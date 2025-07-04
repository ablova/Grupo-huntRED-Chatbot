"""
Advanced 360° Feedback System - huntRED® v2
Sistema completo de feedback 360° con evaluación multi-dimensional, análisis comparativo y generación de reportes.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class EvaluatorRole(Enum):
    """Roles de evaluadores en feedback 360°."""
    SELF = "self"
    MANAGER = "manager"
    PEER = "peer"
    SUBORDINATE = "subordinate"
    CLIENT = "client"
    CUSTOMER = "customer"
    EXTERNAL_STAKEHOLDER = "external_stakeholder"


class CompetencyType(Enum):
    """Tipos de competencias evaluables."""
    TECHNICAL = "technical"
    LEADERSHIP = "leadership"
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    TEAMWORK = "teamwork"
    INNOVATION = "innovation"
    ADAPTABILITY = "adaptability"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    STRATEGIC_THINKING = "strategic_thinking"
    CUSTOMER_FOCUS = "customer_focus"


class FeedbackStatus(Enum):
    """Estados del proceso de feedback."""
    DRAFT = "draft"
    LAUNCHED = "launched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    REPORTED = "reported"


@dataclass
class CompetencyDefinition:
    """Definición de una competencia evaluable."""
    id: str
    name: str
    description: str
    competency_type: CompetencyType
    behavioral_indicators: List[str]
    weight: float = 1.0
    is_required: bool = True
    level_descriptions: Dict[int, str] = field(default_factory=dict)


@dataclass
class EvaluationQuestion:
    """Pregunta de evaluación."""
    id: str
    competency_id: str
    question_text: str
    question_type: str  # rating, text, multiple_choice, ranking
    scale_min: int = 1
    scale_max: int = 5
    options: Optional[List[str]] = None
    is_required: bool = True
    weight: float = 1.0


@dataclass
class Evaluator:
    """Evaluador en proceso 360°."""
    id: str
    user_id: str
    name: str
    email: str
    role: EvaluatorRole
    relationship_context: str = ""
    years_working_together: Optional[int] = None
    anonymous: bool = False
    invited_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reminder_count: int = 0


@dataclass
class EvaluationResponse:
    """Respuesta a una pregunta de evaluación."""
    question_id: str
    evaluator_id: str
    value: Any  # Puede ser rating, texto, opción seleccionada
    confidence_level: Optional[int] = None  # 1-5 qué tan seguro está
    comments: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.now)


@dataclass
class Feedback360Process:
    """Proceso completo de feedback 360°."""
    id: str
    subject_id: str  # Usuario siendo evaluado
    subject_name: str
    title: str
    description: str
    competencies: List[CompetencyDefinition]
    questions: List[EvaluationQuestion]
    evaluators: List[Evaluator]
    responses: List[EvaluationResponse] = field(default_factory=list)
    
    # Configuración
    anonymous_feedback: bool = True
    allow_self_evaluation: bool = True
    minimum_evaluators_per_role: Dict[EvaluatorRole, int] = field(default_factory=dict)
    deadline: Optional[datetime] = None
    
    # Estado
    status: FeedbackStatus = FeedbackStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    launched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Análisis
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    report_generated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompetencyScore:
    """Puntuación de una competencia."""
    competency_id: str
    overall_score: float
    scores_by_role: Dict[EvaluatorRole, float]
    response_count: int
    confidence_average: float
    variance: float
    percentile_rank: Optional[float] = None


@dataclass
class Feedback360Report:
    """Reporte de resultados de feedback 360°."""
    process_id: str
    subject_name: str
    competency_scores: List[CompetencyScore]
    strengths: List[str]
    development_areas: List[str]
    key_insights: List[str]
    role_comparisons: Dict[str, Any]
    trend_analysis: Optional[Dict[str, Any]] = None
    action_recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


class Advanced360FeedbackSystem:
    """
    Sistema avanzado de feedback 360° con:
    - Evaluación multi-dimensional de competencias
    - Análisis estadístico avanzado
    - Comparación por roles de evaluadores
    - Detección de sesgos y outliers
    - Generación automática de insights
    - Reportes personalizables
    - Seguimiento longitudinal
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Procesos activos
        self.active_processes: Dict[str, Feedback360Process] = {}
        
        # Reportes generados
        self.reports: Dict[str, Feedback360Report] = {}
        
        # Configurar competencias predefinidas
        self._setup_default_competencies()
        
        # Configurar templates de preguntas
        self._setup_question_templates()
        
        # Métricas del sistema
        self.metrics = {
            'total_processes': 0,
            'completed_processes': 0,
            'average_participation_rate': 0.0,
            'average_completion_time': 0.0
        }
    
    def _setup_default_competencies(self):
        """Configura competencias predefinidas."""
        self.default_competencies = [
            CompetencyDefinition(
                id="leadership_vision",
                name="Liderazgo Visionario",
                description="Capacidad para establecer y comunicar una visión clara del futuro",
                competency_type=CompetencyType.LEADERSHIP,
                behavioral_indicators=[
                    "Comunica una visión clara y convincente",
                    "Inspira a otros a seguir la visión",
                    "Piensa estratégicamente a largo plazo",
                    "Toma decisiones basadas en la visión organizacional"
                ],
                weight=1.5,
                level_descriptions={
                    1: "Raramente muestra comportamientos de liderazgo visionario",
                    2: "Ocasionalmente demuestra liderazgo visionario",
                    3: "Consistentemente muestra liderazgo visionario",
                    4: "Frecuentemente exhibe liderazgo visionario excepcional",
                    5: "Constantemente ejemplifica liderazgo visionario sobresaliente"
                }
            ),
            CompetencyDefinition(
                id="communication_effectiveness",
                name="Comunicación Efectiva",
                description="Habilidad para comunicarse clara y persuasivamente",
                competency_type=CompetencyType.COMMUNICATION,
                behavioral_indicators=[
                    "Se expresa con claridad y concisión",
                    "Escucha activamente a otros",
                    "Adapta su comunicación a la audiencia",
                    "Facilita conversaciones difíciles"
                ],
                weight=1.3,
                level_descriptions={
                    1: "Comunicación poco clara o inefectiva",
                    2: "Comunicación básica pero mejorable",
                    3: "Comunicación clara y efectiva",
                    4: "Comunicación muy efectiva y persuasiva",
                    5: "Comunicación excepcional que inspira acción"
                }
            ),
            CompetencyDefinition(
                id="problem_solving_analytical",
                name="Resolución Analítica de Problemas",
                description="Capacidad para analizar problemas complejos y encontrar soluciones efectivas",
                competency_type=CompetencyType.PROBLEM_SOLVING,
                behavioral_indicators=[
                    "Identifica la causa raíz de los problemas",
                    "Considera múltiples soluciones alternativas",
                    "Usa datos para tomar decisiones",
                    "Implementa soluciones de manera efectiva"
                ],
                weight=1.4,
                level_descriptions={
                    1: "Dificultad para resolver problemas complejos",
                    2: "Resuelve problemas básicos con apoyo",
                    3: "Resuelve problemas de complejidad media independientemente",
                    4: "Resuelve problemas complejos creativamente",
                    5: "Resuelve problemas altamente complejos con soluciones innovadoras"
                }
            ),
            CompetencyDefinition(
                id="teamwork_collaboration",
                name="Trabajo en Equipo y Colaboración",
                description="Habilidad para trabajar efectivamente con otros hacia objetivos comunes",
                competency_type=CompetencyType.TEAMWORK,
                behavioral_indicators=[
                    "Contribuye activamente al éxito del equipo",
                    "Comparte conocimientos y recursos",
                    "Resuelve conflictos constructivamente",
                    "Apoya el desarrollo de otros miembros"
                ],
                weight=1.2
            ),
            CompetencyDefinition(
                id="adaptability_change",
                name="Adaptabilidad al Cambio",
                description="Capacidad para adaptarse y prosperar en entornos cambiantes",
                competency_type=CompetencyType.ADAPTABILITY,
                behavioral_indicators=[
                    "Se adapta rápidamente a nuevas situaciones",
                    "Mantiene una actitud positiva ante el cambio",
                    "Aprende continuamente nuevas habilidades",
                    "Ayuda a otros a adaptarse al cambio"
                ],
                weight=1.1
            ),
            CompetencyDefinition(
                id="emotional_intelligence",
                name="Inteligencia Emocional",
                description="Capacidad para entender y manejar emociones propias y ajenas",
                competency_type=CompetencyType.EMOTIONAL_INTELLIGENCE,
                behavioral_indicators=[
                    "Reconoce sus propias emociones y las de otros",
                    "Mantiene la compostura bajo presión",
                    "Muestra empatía hacia otros",
                    "Influye positivamente en el estado emocional del equipo"
                ],
                weight=1.3
            ),
            CompetencyDefinition(
                id="innovation_creativity",
                name="Innovación y Creatividad",
                description="Capacidad para generar ideas nuevas y implementar soluciones creativas",
                competency_type=CompetencyType.INNOVATION,
                behavioral_indicators=[
                    "Genera ideas originales y creativas",
                    "Experimenta con nuevos enfoques",
                    "Desafía el status quo constructivamente",
                    "Implementa mejoras innovadoras"
                ],
                weight=1.0
            ),
            CompetencyDefinition(
                id="customer_focus",
                name="Enfoque en el Cliente",
                description="Orientación hacia la satisfacción y éxito del cliente",
                competency_type=CompetencyType.CUSTOMER_FOCUS,
                behavioral_indicators=[
                    "Comprende profundamente las necesidades del cliente",
                    "Actúa como defensor del cliente internamente",
                    "Entrega valor consistente al cliente",
                    "Busca retroalimentación del cliente regularmente"
                ],
                weight=1.4
            )
        ]
    
    def _setup_question_templates(self):
        """Configura templates de preguntas por competencia."""
        self.question_templates = {
            "rating_overall": "¿Cómo evalúas a {subject_name} en {competency_name}?",
            "rating_frequency": "¿Con qué frecuencia observas que {subject_name} demuestra {competency_name}?",
            "rating_effectiveness": "¿Qué tan efectivo es {subject_name} en {competency_name}?",
            "text_strengths": "¿Cuáles son las principales fortalezas de {subject_name} en {competency_name}?",
            "text_development": "¿En qué aspectos de {competency_name} podría mejorar {subject_name}?",
            "text_examples": "Proporciona un ejemplo específico donde {subject_name} demostró {competency_name}",
            "text_impact": "¿Cuál ha sido el impacto de {subject_name} en {competency_name} en tu trabajo/equipo?"
        }
    
    def create_feedback_process(self, subject_id: str, subject_name: str, title: str,
                              competency_ids: List[str], evaluator_configs: List[Dict[str, Any]],
                              deadline_days: int = 14, anonymous: bool = True) -> str:
        """Crea un nuevo proceso de feedback 360°."""
        try:
            process_id = str(uuid.uuid4())
            
            # Seleccionar competencias
            selected_competencies = [
                comp for comp in self.default_competencies 
                if comp.id in competency_ids
            ]
            
            if not selected_competencies:
                raise ValueError("No valid competencies selected")
            
            # Crear preguntas para las competencias seleccionadas
            questions = self._generate_questions_for_competencies(selected_competencies)
            
            # Crear evaluadores
            evaluators = []
            for eval_config in evaluator_configs:
                evaluator = Evaluator(
                    id=str(uuid.uuid4()),
                    user_id=eval_config['user_id'],
                    name=eval_config['name'],
                    email=eval_config['email'],
                    role=EvaluatorRole(eval_config['role']),
                    relationship_context=eval_config.get('relationship_context', ''),
                    years_working_together=eval_config.get('years_working_together'),
                    anonymous=anonymous
                )
                evaluators.append(evaluator)
            
            # Crear proceso
            process = Feedback360Process(
                id=process_id,
                subject_id=subject_id,
                subject_name=subject_name,
                title=title,
                description=f"Evaluación 360° para {subject_name}",
                competencies=selected_competencies,
                questions=questions,
                evaluators=evaluators,
                anonymous_feedback=anonymous,
                deadline=datetime.now() + timedelta(days=deadline_days)
            )
            
            self.active_processes[process_id] = process
            self.metrics['total_processes'] += 1
            
            logger.info(f"Created 360° feedback process {process_id} for {subject_name}")
            return process_id
            
        except Exception as e:
            logger.error(f"Error creating feedback process: {str(e)}")
            raise
    
    def _generate_questions_for_competencies(self, competencies: List[CompetencyDefinition]) -> List[EvaluationQuestion]:
        """Genera preguntas para las competencias seleccionadas."""
        questions = []
        
        for competency in competencies:
            # Pregunta de rating general
            questions.append(EvaluationQuestion(
                id=f"{competency.id}_overall_rating",
                competency_id=competency.id,
                question_text=self.question_templates["rating_overall"].format(
                    subject_name="{subject_name}",
                    competency_name=competency.name
                ),
                question_type="rating",
                scale_min=1,
                scale_max=5,
                weight=competency.weight
            ))
            
            # Pregunta de frecuencia
            questions.append(EvaluationQuestion(
                id=f"{competency.id}_frequency",
                competency_id=competency.id,
                question_text=self.question_templates["rating_frequency"].format(
                    subject_name="{subject_name}",
                    competency_name=competency.name
                ),
                question_type="rating",
                scale_min=1,
                scale_max=5,
                weight=0.8
            ))
            
            # Pregunta de fortalezas (texto)
            questions.append(EvaluationQuestion(
                id=f"{competency.id}_strengths",
                competency_id=competency.id,
                question_text=self.question_templates["text_strengths"].format(
                    subject_name="{subject_name}",
                    competency_name=competency.name
                ),
                question_type="text",
                is_required=False,
                weight=0.5
            ))
            
            # Pregunta de desarrollo (texto)
            questions.append(EvaluationQuestion(
                id=f"{competency.id}_development",
                competency_id=competency.id,
                question_text=self.question_templates["text_development"].format(
                    subject_name="{subject_name}",
                    competency_name=competency.name
                ),
                question_type="text",
                is_required=False,
                weight=0.5
            ))
        
        return questions
    
    async def launch_feedback_process(self, process_id: str) -> bool:
        """Lanza un proceso de feedback (envía invitaciones)."""
        try:
            process = self.active_processes.get(process_id)
            if not process:
                raise ValueError("Process not found")
            
            if process.status != FeedbackStatus.DRAFT:
                raise ValueError(f"Process is in {process.status.value} state, cannot launch")
            
            # Enviar invitaciones a evaluadores
            for evaluator in process.evaluators:
                await self._send_evaluation_invitation(process, evaluator)
                evaluator.invited_at = datetime.now()
            
            # Actualizar estado
            process.status = FeedbackStatus.LAUNCHED
            process.launched_at = datetime.now()
            
            logger.info(f"Launched 360° feedback process {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error launching feedback process: {str(e)}")
            raise
    
    async def _send_evaluation_invitation(self, process: Feedback360Process, evaluator: Evaluator):
        """Envía invitación de evaluación a un evaluador."""
        try:
            # Crear URL de evaluación
            evaluation_url = f"{self.config.get('base_url')}/feedback360/{process.id}/evaluate/{evaluator.id}"
            
            # Aquí se integraría con el sistema de notificaciones
            logger.info(f"Sending evaluation invitation to {evaluator.email} for process {process.id}")
            
        except Exception as e:
            logger.error(f"Error sending evaluation invitation: {str(e)}")
    
    def submit_evaluation(self, process_id: str, evaluator_id: str, 
                         responses: List[Dict[str, Any]]) -> bool:
        """Procesa la sumisión de una evaluación."""
        try:
            process = self.active_processes.get(process_id)
            if not process:
                raise ValueError("Process not found")
            
            # Verificar evaluador
            evaluator = next((e for e in process.evaluators if e.id == evaluator_id), None)
            if not evaluator:
                raise ValueError("Evaluator not found")
            
            if evaluator.completed_at:
                raise ValueError("Evaluation already completed")
            
            # Verificar deadline
            if process.deadline and datetime.now() > process.deadline:
                raise ValueError("Evaluation deadline has passed")
            
            # Procesar respuestas
            evaluation_responses = []
            for response_data in responses:
                response = EvaluationResponse(
                    question_id=response_data['question_id'],
                    evaluator_id=evaluator_id,
                    value=response_data['value'],
                    confidence_level=response_data.get('confidence_level'),
                    comments=response_data.get('comments')
                )
                evaluation_responses.append(response)
            
            # Validar completitud
            required_questions = [q for q in process.questions if q.is_required]
            answered_required = set(r.question_id for r in evaluation_responses 
                                   if any(q.id == r.question_id for q in required_questions))
            
            if len(answered_required) < len(required_questions):
                raise ValueError("Not all required questions answered")
            
            # Agregar respuestas al proceso
            process.responses.extend(evaluation_responses)
            
            # Marcar evaluador como completado
            evaluator.completed_at = datetime.now()
            
            # Verificar si el proceso está completo
            self._check_process_completion(process)
            
            logger.info(f"Evaluation submitted by {evaluator_id} for process {process_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting evaluation: {str(e)}")
            raise
    
    def _check_process_completion(self, process: Feedback360Process):
        """Verifica si un proceso está completo y actualiza el estado."""
        completed_evaluators = [e for e in process.evaluators if e.completed_at]
        total_evaluators = len(process.evaluators)
        
        # Verificar mínimos por rol si están configurados
        if process.minimum_evaluators_per_role:
            for role, minimum in process.minimum_evaluators_per_role.items():
                completed_for_role = [e for e in completed_evaluators if e.role == role]
                if len(completed_for_role) < minimum:
                    return  # No está completo aún
        
        # Si todos han completado o se cumplieron los mínimos
        if len(completed_evaluators) == total_evaluators or (
            process.deadline and datetime.now() > process.deadline
        ):
            process.status = FeedbackStatus.COMPLETED
            process.completed_at = datetime.now()
            
            # Actualizar métricas
            self.metrics['completed_processes'] += 1
            participation_rate = len(completed_evaluators) / total_evaluators
            
            # Actualizar promedio de participación
            current_avg = self.metrics['average_participation_rate']
            completed_count = self.metrics['completed_processes']
            self.metrics['average_participation_rate'] = (
                (current_avg * (completed_count - 1) + participation_rate) / completed_count
            )
            
            logger.info(f"Process {process.id} completed with {len(completed_evaluators)}/{total_evaluators} participants")
    
    async def analyze_feedback_results(self, process_id: str) -> Dict[str, Any]:
        """Analiza los resultados de un proceso de feedback 360°."""
        try:
            process = self.active_processes.get(process_id)
            if not process:
                raise ValueError("Process not found")
            
            if process.status != FeedbackStatus.COMPLETED:
                raise ValueError(f"Process is in {process.status.value} state, cannot analyze")
            
            # Analizar competencias
            competency_scores = []
            for competency in process.competencies:
                score = self._analyze_competency_scores(process, competency)
                competency_scores.append(score)
            
            # Análisis comparativo por roles
            role_analysis = self._analyze_by_evaluator_roles(process)
            
            # Detectar outliers y sesgos
            outlier_analysis = self._detect_outliers_and_bias(process)
            
            # Generar insights automáticos
            insights = self._generate_insights(competency_scores, role_analysis)
            
            # Identificar fortalezas y áreas de desarrollo
            strengths, development_areas = self._identify_strengths_and_development(competency_scores)
            
            # Compilar resultados
            analysis_results = {
                'competency_scores': [
                    {
                        'competency_id': cs.competency_id,
                        'competency_name': next(c.name for c in process.competencies if c.id == cs.competency_id),
                        'overall_score': cs.overall_score,
                        'scores_by_role': {role.value: score for role, score in cs.scores_by_role.items()},
                        'response_count': cs.response_count,
                        'confidence_average': cs.confidence_average,
                        'variance': cs.variance
                    } for cs in competency_scores
                ],
                'role_analysis': role_analysis,
                'outlier_analysis': outlier_analysis,
                'insights': insights,
                'strengths': strengths,
                'development_areas': development_areas,
                'overall_summary': self._generate_overall_summary(competency_scores)
            }
            
            process.analysis_results = analysis_results
            process.status = FeedbackStatus.ANALYZED
            
            logger.info(f"Analysis completed for process {process_id}")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing feedback results: {str(e)}")
            raise
    
    def _analyze_competency_scores(self, process: Feedback360Process, 
                                  competency: CompetencyDefinition) -> CompetencyScore:
        """Analiza las puntuaciones de una competencia específica."""
        # Obtener todas las respuestas de rating para esta competencia
        rating_responses = [
            r for r in process.responses 
            if any(q.competency_id == competency.id and q.question_type == "rating" and q.id == r.question_id 
                  for q in process.questions)
        ]
        
        if not rating_responses:
            return CompetencyScore(
                competency_id=competency.id,
                overall_score=0.0,
                scores_by_role={},
                response_count=0,
                confidence_average=0.0,
                variance=0.0
            )
        
        # Calcular score general
        scores = [float(r.value) for r in rating_responses if isinstance(r.value, (int, float))]
        overall_score = statistics.mean(scores) if scores else 0.0
        variance = statistics.variance(scores) if len(scores) > 1 else 0.0
        
        # Calcular scores por rol
        scores_by_role = {}
        for role in EvaluatorRole:
            role_evaluators = [e.id for e in process.evaluators if e.role == role]
            role_responses = [r for r in rating_responses if r.evaluator_id in role_evaluators]
            role_scores = [float(r.value) for r in role_responses if isinstance(r.value, (int, float))]
            
            if role_scores:
                scores_by_role[role] = statistics.mean(role_scores)
        
        # Calcular promedio de confianza
        confidence_scores = [r.confidence_level for r in rating_responses if r.confidence_level]
        confidence_average = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        return CompetencyScore(
            competency_id=competency.id,
            overall_score=overall_score,
            scores_by_role=scores_by_role,
            response_count=len(rating_responses),
            confidence_average=confidence_average,
            variance=variance
        )
    
    def _analyze_by_evaluator_roles(self, process: Feedback360Process) -> Dict[str, Any]:
        """Analiza diferencias entre roles de evaluadores."""
        role_analysis = {}
        
        for role in EvaluatorRole:
            role_evaluators = [e for e in process.evaluators if e.role == role]
            if not role_evaluators:
                continue
            
            role_responses = [
                r for r in process.responses 
                if r.evaluator_id in [e.id for e in role_evaluators]
            ]
            
            # Calcular estadísticas por rol
            rating_responses = [r for r in role_responses if isinstance(r.value, (int, float))]
            
            if rating_responses:
                scores = [float(r.value) for r in rating_responses]
                role_analysis[role.value] = {
                    'evaluator_count': len(role_evaluators),
                    'response_count': len(rating_responses),
                    'average_score': statistics.mean(scores),
                    'score_variance': statistics.variance(scores) if len(scores) > 1 else 0.0,
                    'completion_rate': len([e for e in role_evaluators if e.completed_at]) / len(role_evaluators)
                }
        
        return role_analysis
    
    def _detect_outliers_and_bias(self, process: Feedback360Process) -> Dict[str, Any]:
        """Detecta outliers y posibles sesgos en las respuestas."""
        outlier_analysis = {
            'outlier_responses': [],
            'potential_bias_indicators': [],
            'response_patterns': {}
        }
        
        # Analizar outliers por evaluador
        for evaluator in process.evaluators:
            evaluator_responses = [r for r in process.responses if r.evaluator_id == evaluator.id]
            rating_responses = [r for r in evaluator_responses if isinstance(r.value, (int, float))]
            
            if len(rating_responses) >= 3:
                scores = [float(r.value) for r in rating_responses]
                mean_score = statistics.mean(scores)
                
                # Detectar si todas las respuestas son muy similares (posible sesgo)
                if statistics.variance(scores) < 0.1:
                    outlier_analysis['potential_bias_indicators'].append({
                        'evaluator_id': evaluator.id,
                        'type': 'low_variance',
                        'description': f'Evaluador {evaluator.role.value} dio puntuaciones muy similares'
                    })
                
                # Detectar puntuaciones extremas consistentes
                if all(score >= 4.5 for score in scores):
                    outlier_analysis['potential_bias_indicators'].append({
                        'evaluator_id': evaluator.id,
                        'type': 'positive_bias',
                        'description': f'Evaluador {evaluator.role.value} dio puntuaciones consistentemente altas'
                    })
                elif all(score <= 2.0 for score in scores):
                    outlier_analysis['potential_bias_indicators'].append({
                        'evaluator_id': evaluator.id,
                        'type': 'negative_bias',
                        'description': f'Evaluador {evaluator.role.value} dio puntuaciones consistentemente bajas'
                    })
        
        return outlier_analysis
    
    def _generate_insights(self, competency_scores: List[CompetencyScore], 
                          role_analysis: Dict[str, Any]) -> List[str]:
        """Genera insights automáticos basados en el análisis."""
        insights = []
        
        # Analizar diferencias entre roles
        if len(role_analysis) >= 2:
            role_averages = {role: data['average_score'] for role, data in role_analysis.items()}
            max_role = max(role_averages.keys(), key=lambda k: role_averages[k])
            min_role = min(role_averages.keys(), key=lambda k: role_averages[k])
            
            if role_averages[max_role] - role_averages[min_role] > 1.0:
                insights.append(
                    f"Existe una diferencia significativa entre las evaluaciones de {max_role} "
                    f"(promedio: {role_averages[max_role]:.1f}) y {min_role} "
                    f"(promedio: {role_averages[min_role]:.1f})"
                )
        
        # Analizar competencias con mayor varianza
        high_variance_competencies = [cs for cs in competency_scores if cs.variance > 1.0]
        if high_variance_competencies:
            comp_names = [cs.competency_id for cs in high_variance_competencies]
            insights.append(
                f"Las competencias {', '.join(comp_names)} muestran opiniones divididas entre evaluadores"
            )
        
        # Analizar competencias destacadas
        top_competencies = sorted(competency_scores, key=lambda x: x.overall_score, reverse=True)[:2]
        if top_competencies:
            insights.append(
                f"Las competencias mejor evaluadas son: {', '.join([cs.competency_id for cs in top_competencies])}"
            )
        
        return insights
    
    def _identify_strengths_and_development(self, competency_scores: List[CompetencyScore]) -> tuple:
        """Identifica fortalezas y áreas de desarrollo."""
        # Ordenar por score
        sorted_scores = sorted(competency_scores, key=lambda x: x.overall_score, reverse=True)
        
        # Top 30% como fortalezas
        top_count = max(1, len(sorted_scores) * 30 // 100)
        strengths = [cs.competency_id for cs in sorted_scores[:top_count] if cs.overall_score >= 3.5]
        
        # Bottom 30% como áreas de desarrollo
        bottom_count = max(1, len(sorted_scores) * 30 // 100)
        development_areas = [cs.competency_id for cs in sorted_scores[-bottom_count:] if cs.overall_score < 3.5]
        
        return strengths, development_areas
    
    def _generate_overall_summary(self, competency_scores: List[CompetencyScore]) -> Dict[str, Any]:
        """Genera resumen general de la evaluación."""
        if not competency_scores:
            return {}
        
        overall_scores = [cs.overall_score for cs in competency_scores]
        
        return {
            'overall_average': statistics.mean(overall_scores),
            'highest_score': max(overall_scores),
            'lowest_score': min(overall_scores),
            'score_range': max(overall_scores) - min(overall_scores),
            'total_responses': sum(cs.response_count for cs in competency_scores)
        }
    
    async def generate_report(self, process_id: str) -> str:
        """Genera un reporte detallado del proceso de feedback."""
        try:
            process = self.active_processes.get(process_id)
            if not process:
                raise ValueError("Process not found")
            
            if process.status != FeedbackStatus.ANALYZED:
                # Auto-analizar si no se ha hecho
                if process.status == FeedbackStatus.COMPLETED:
                    await self.analyze_feedback_results(process_id)
                else:
                    raise ValueError(f"Process is in {process.status.value} state, cannot generate report")
            
            # Extraer datos del análisis
            analysis = process.analysis_results
            
            # Crear competency scores
            competency_scores = []
            for comp_data in analysis['competency_scores']:
                scores_by_role = {
                    EvaluatorRole(role): score 
                    for role, score in comp_data['scores_by_role'].items()
                }
                
                competency_scores.append(CompetencyScore(
                    competency_id=comp_data['competency_id'],
                    overall_score=comp_data['overall_score'],
                    scores_by_role=scores_by_role,
                    response_count=comp_data['response_count'],
                    confidence_average=comp_data['confidence_average'],
                    variance=comp_data['variance']
                ))
            
            # Generar recomendaciones de acción
            action_recommendations = self._generate_action_recommendations(
                analysis['strengths'], 
                analysis['development_areas'],
                competency_scores
            )
            
            # Crear reporte
            report = Feedback360Report(
                process_id=process_id,
                subject_name=process.subject_name,
                competency_scores=competency_scores,
                strengths=analysis['strengths'],
                development_areas=analysis['development_areas'],
                key_insights=analysis['insights'],
                role_comparisons=analysis['role_analysis'],
                action_recommendations=action_recommendations
            )
            
            # Guardar reporte
            report_id = str(uuid.uuid4())
            self.reports[report_id] = report
            
            # Actualizar proceso
            process.status = FeedbackStatus.REPORTED
            process.report_generated = True
            
            logger.info(f"Report generated for process {process_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    def _generate_action_recommendations(self, strengths: List[str], 
                                       development_areas: List[str],
                                       competency_scores: List[CompetencyScore]) -> List[str]:
        """Genera recomendaciones de acción específicas."""
        recommendations = []
        
        # Recomendaciones basadas en fortalezas
        if strengths:
            recommendations.append(
                f"Continúa desarrollando y aprovechando tus fortalezas en: {', '.join(strengths)}"
            )
            recommendations.append(
                "Considera mentorear a otros en estas áreas donde destacas"
            )
        
        # Recomendaciones basadas en áreas de desarrollo
        if development_areas:
            recommendations.append(
                f"Enfócate en desarrollar: {', '.join(development_areas)}"
            )
            recommendations.append(
                "Busca oportunidades de capacitación o mentoring en estas áreas"
            )
        
        # Recomendaciones basadas en varianza
        high_variance_competencies = [cs for cs in competency_scores if cs.variance > 1.0]
        if high_variance_competencies:
            recommendations.append(
                "Busca clarificar expectativas en competencias donde hay opiniones divididas"
            )
        
        return recommendations
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """Obtiene el estado actual de un proceso."""
        process = self.active_processes.get(process_id)
        if not process:
            return {'error': 'Process not found'}
        
        completed_evaluators = [e for e in process.evaluators if e.completed_at]
        
        return {
            'process_id': process_id,
            'status': process.status.value,
            'subject_name': process.subject_name,
            'total_evaluators': len(process.evaluators),
            'completed_evaluators': len(completed_evaluators),
            'completion_rate': len(completed_evaluators) / len(process.evaluators),
            'deadline': process.deadline.isoformat() if process.deadline else None,
            'days_remaining': (process.deadline - datetime.now()).days if process.deadline else None,
            'competencies_count': len(process.competencies),
            'questions_count': len(process.questions),
            'launched_at': process.launched_at.isoformat() if process.launched_at else None,
            'completed_at': process.completed_at.isoformat() if process.completed_at else None
        }
    
    def get_evaluation_form(self, process_id: str, evaluator_id: str) -> Dict[str, Any]:
        """Obtiene el formulario de evaluación para un evaluador."""
        process = self.active_processes.get(process_id)
        if not process:
            return {'error': 'Process not found'}
        
        evaluator = next((e for e in process.evaluators if e.id == evaluator_id), None)
        if not evaluator:
            return {'error': 'Evaluator not found'}
        
        if evaluator.completed_at:
            return {'error': 'Evaluation already completed'}
        
        if process.deadline and datetime.now() > process.deadline:
            return {'error': 'Evaluation deadline has passed'}
        
        # Preparar formulario
        form_questions = []
        for question in process.questions:
            competency = next((c for c in process.competencies if c.id == question.competency_id), None)
            
            form_question = {
                'question_id': question.id,
                'competency_name': competency.name if competency else '',
                'competency_description': competency.description if competency else '',
                'question_text': question.question_text.format(subject_name=process.subject_name),
                'question_type': question.question_type,
                'is_required': question.is_required,
                'scale_min': question.scale_min,
                'scale_max': question.scale_max,
                'options': question.options
            }
            
            # Agregar descripciones de nivel si es rating
            if question.question_type == "rating" and competency and competency.level_descriptions:
                form_question['level_descriptions'] = competency.level_descriptions
            
            form_questions.append(form_question)
        
        return {
            'process_id': process_id,
            'evaluator_id': evaluator_id,
            'subject_name': process.subject_name,
            'evaluator_role': evaluator.role.value,
            'anonymous': process.anonymous_feedback,
            'deadline': process.deadline.isoformat() if process.deadline else None,
            'questions': form_questions,
            'progress': {
                'total_evaluators': len(process.evaluators),
                'completed_evaluators': len([e for e in process.evaluators if e.completed_at])
            }
        }
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un reporte generado."""
        report = self.reports.get(report_id)
        if not report:
            return None
        
        return {
            'report_id': report_id,
            'process_id': report.process_id,
            'subject_name': report.subject_name,
            'generated_at': report.generated_at.isoformat(),
            'competency_scores': [
                {
                    'competency_id': cs.competency_id,
                    'overall_score': cs.overall_score,
                    'scores_by_role': {role.value: score for role, score in cs.scores_by_role.items()},
                    'response_count': cs.response_count,
                    'confidence_average': cs.confidence_average,
                    'variance': cs.variance
                } for cs in report.competency_scores
            ],
            'strengths': report.strengths,
            'development_areas': report.development_areas,
            'key_insights': report.key_insights,
            'role_comparisons': report.role_comparisons,
            'action_recommendations': report.action_recommendations
        }
    
    async def send_reminders(self, process_id: str):
        """Envía recordatorios a evaluadores que no han completado."""
        try:
            process = self.active_processes.get(process_id)
            if not process or process.status != FeedbackStatus.LAUNCHED:
                return
            
            now = datetime.now()
            pending_evaluators = [e for e in process.evaluators if not e.completed_at]
            
            for evaluator in pending_evaluators:
                # Enviar recordatorio si han pasado 3+ días sin completar
                if evaluator.invited_at and (now - evaluator.invited_at).days >= 3:
                    await self._send_evaluation_reminder(process, evaluator)
                    evaluator.reminder_count += 1
            
        except Exception as e:
            logger.error(f"Error sending reminders: {str(e)}")
    
    async def _send_evaluation_reminder(self, process: Feedback360Process, evaluator: Evaluator):
        """Envía recordatorio a un evaluador específico."""
        try:
            # Aquí se integraría con el sistema de notificaciones
            logger.info(f"Sending reminder to {evaluator.email} for process {process.id}")
            
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema de feedback 360°."""
        active_processes = len([p for p in self.active_processes.values() 
                              if p.status in [FeedbackStatus.LAUNCHED, FeedbackStatus.IN_PROGRESS]])
        
        return {
            **self.metrics,
            'active_processes': active_processes,
            'total_reports_generated': len(self.reports),
            'completion_rate': (self.metrics['completed_processes'] / self.metrics['total_processes']) * 100 
                              if self.metrics['total_processes'] > 0 else 0
        }