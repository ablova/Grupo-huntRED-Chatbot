"""
💬 ADVANCED FEEDBACK SERVICE - GHUNTRED V2
Sistema avanzado de feedback con dos vertientes específicas:
1. Feedback del cliente ante una entrevista
2. Feedback del candidato dentro del proceso
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Tipos de feedback"""
    CLIENT_INTERVIEW = "client_interview"        # Cliente sobre entrevista
    CANDIDATE_PROCESS = "candidate_process"      # Candidato sobre proceso
    CONSULTANT_PERFORMANCE = "consultant_performance"  # Consultor sobre performance
    SUPER_ADMIN_SYSTEM = "super_admin_system"    # Súper Admin sobre sistema
    RECRUITER_CLIENT = "recruiter_client"        # Recruiter sobre cliente
    RECRUITER_PERFORMANCE = "recruiter_performance"
    SYSTEM_IMPROVEMENT = "system_improvement"

class FeedbackStage(Enum):
    """Etapas del proceso donde se solicita feedback"""
    POST_INTERVIEW = "post_interview"
    POST_TECHNICAL = "post_technical"
    POST_REJECTION = "post_rejection"
    POST_OFFER = "post_offer"
    MID_PROCESS = "mid_process"
    FINAL_PROCESS = "final_process"

class FeedbackStatus(Enum):
    """Estados del feedback"""
    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    EXPIRED = "expired"
    DECLINED = "declined"

class FeedbackPriority(Enum):
    """Prioridades de feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class FeedbackQuestion:
    """Pregunta de feedback"""
    id: str
    question: str
    category: str
    type: str  # rating, text, multiple_choice, boolean, scale
    required: bool
    weight: float
    options: List[str] = field(default_factory=list)
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    placeholder: Optional[str] = None

@dataclass
class FeedbackResponse:
    """Respuesta de feedback"""
    question_id: str
    response: Any
    score: Optional[float] = None
    sentiment: Optional[str] = None
    keywords: List[str] = field(default_factory=list)

@dataclass
class FeedbackRequest:
    """Solicitud de feedback"""
    id: str
    feedback_type: FeedbackType
    stage: FeedbackStage
    requester_id: str
    respondent_id: str
    respondent_type: str  # client, candidate, recruiter
    context: Dict[str, Any]
    questions: List[FeedbackQuestion]
    status: FeedbackStatus
    priority: FeedbackPriority
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    responses: List[FeedbackResponse] = field(default_factory=list)
    overall_score: Optional[float] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    action_items: List[str] = field(default_factory=list)

class AdvancedFeedbackService:
    """
    Servicio avanzado de feedback con dos vertientes específicas
    """
    
    def __init__(self):
        self.feedback_requests = {}
        self.feedback_templates = {}
        self.analytics = {}
        self.sentiment_keywords = {}
        
        # Configuración por tipo de feedback
        self.feedback_config = {
            FeedbackType.CLIENT_INTERVIEW: {
                'expiry_hours': 48,
                'reminder_hours': [24, 6],
                'required_questions': 5,
                'categories': ['technical_fit', 'cultural_fit', 'communication', 'overall_impression', 'recommendation']
            },
            FeedbackType.CANDIDATE_PROCESS: {
                'expiry_hours': 72,
                'reminder_hours': [48, 12],
                'required_questions': 6,
                'categories': ['process_clarity', 'communication_quality', 'interview_experience', 'recruiter_performance', 'improvements', 'overall_satisfaction']
            },
            FeedbackType.CONSULTANT_PERFORMANCE: {
                'expiry_hours': 96,
                'reminder_hours': [72, 24],
                'required_questions': 8,
                'categories': ['recruiter_evaluation', 'process_optimization', 'client_satisfaction', 'efficiency_metrics', 'improvement_recommendations', 'strategic_insights', 'team_performance', 'overall_assessment']
            },
            FeedbackType.SUPER_ADMIN_SYSTEM: {
                'expiry_hours': 168,  # 1 semana
                'reminder_hours': [120, 48],
                'required_questions': 10,
                'categories': ['system_performance', 'technical_optimization', 'user_experience', 'scalability', 'security', 'feature_requests', 'bug_reports', 'integration_issues', 'performance_metrics', 'strategic_roadmap']
            },
            FeedbackType.RECRUITER_CLIENT: {
                'expiry_hours': 48,
                'reminder_hours': [24, 6],
                'required_questions': 6,
                'categories': ['requirement_clarity', 'communication_quality', 'collaboration', 'responsiveness', 'feedback_quality', 'relationship_improvement']
            }
        }
        
        self.initialized = False
    
    async def initialize_service(self):
        """Inicializa el servicio de feedback"""
        if self.initialized:
            return
            
        logger.info("💬 Inicializando Advanced Feedback Service...")
        
        # Cargar plantillas de feedback
        await self._load_feedback_templates()
        
        # Configurar análisis de sentimientos
        await self._setup_sentiment_analysis()
        
        # Inicializar analytics
        await self._initialize_analytics()
        
        self.initialized = True
        logger.info("✅ Advanced Feedback Service inicializado")
    
    async def _load_feedback_templates(self):
        """Carga plantillas de feedback"""
        logger.info("📋 Cargando plantillas de feedback...")
        
        # Plantilla para Feedback de Cliente sobre Entrevista
        client_interview_questions = [
            FeedbackQuestion(
                id="technical_fit",
                question="¿Cómo calificaría el fit técnico del candidato para esta posición?",
                category="technical_fit",
                type="scale",
                required=True,
                weight=0.25,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="cultural_fit",
                question="¿Qué tan bien se alinea el candidato con la cultura de su empresa?",
                category="cultural_fit",
                type="scale",
                required=True,
                weight=0.20,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="communication_skills",
                question="¿Cómo evalúa las habilidades de comunicación del candidato?",
                category="communication",
                type="multiple_choice",
                required=True,
                weight=0.15,
                options=["Excelente", "Muy buenas", "Buenas", "Regulares", "Deficientes"]
            ),
            FeedbackQuestion(
                id="strengths_observed",
                question="¿Cuáles fueron las principales fortalezas que observó en el candidato?",
                category="strengths",
                type="text",
                required=True,
                weight=0.15,
                placeholder="Describa las fortalezas más destacadas..."
            ),
            FeedbackQuestion(
                id="concerns_areas",
                question="¿Hay alguna área de preocupación o que requiera desarrollo?",
                category="concerns",
                type="text",
                required=False,
                weight=0.10,
                placeholder="Mencione cualquier preocupación o área de mejora..."
            ),
            FeedbackQuestion(
                id="next_steps",
                question="¿Cuál sería su recomendación para los próximos pasos?",
                category="recommendation",
                type="multiple_choice",
                required=True,
                weight=0.15,
                options=["Avanzar a siguiente etapa", "Segunda entrevista", "Solicitar más información", "No continuar", "Necesito discutir con el equipo"]
            )
        ]
        
        # Plantilla para Feedback de Candidato sobre Proceso
        candidate_process_questions = [
            FeedbackQuestion(
                id="process_clarity",
                question="¿Qué tan claro fue el proceso de selección desde el inicio?",
                category="process_clarity",
                type="scale",
                required=True,
                weight=0.18,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="communication_quality",
                question="¿Cómo calificaría la calidad de comunicación durante el proceso?",
                category="communication_quality",
                type="scale",
                required=True,
                weight=0.18,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="interview_experience",
                question="¿Cómo fue su experiencia en las entrevistas?",
                category="interview_experience",
                type="multiple_choice",
                required=True,
                weight=0.16,
                options=["Excelente", "Muy buena", "Buena", "Regular", "Mala"]
            ),
            FeedbackQuestion(
                id="recruiter_performance",
                question="¿Cómo evalúa el desempeño del recruiter asignado?",
                category="recruiter_performance",
                type="scale",
                required=True,
                weight=0.16,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="improvement_suggestions",
                question="¿Qué sugeriría para mejorar el proceso de selección?",
                category="improvements",
                type="text",
                required=False,
                weight=0.16,
                placeholder="Comparta sus sugerencias para mejorar la experiencia..."
            ),
            FeedbackQuestion(
                id="overall_satisfaction",
                question="En general, ¿qué tan satisfecho está con el proceso?",
                category="overall_satisfaction",
                type="scale",
                required=True,
                weight=0.16,
                min_value=1,
                max_value=10
            )
        ]
        
        # Plantilla para Feedback de Consultor sobre Performance
        consultant_performance_questions = [
            FeedbackQuestion(
                id="recruiter_evaluation",
                question="¿Cómo evalúa el desempeño general del recruiter en este proceso?",
                category="recruiter_evaluation",
                type="scale",
                required=True,
                weight=0.15,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="process_optimization",
                question="¿Qué tan eficiente fue el proceso de reclutamiento ejecutado?",
                category="process_optimization",
                type="scale",
                required=True,
                weight=0.15,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="client_satisfaction",
                question="¿Cómo califica la satisfacción del cliente con el servicio brindado?",
                category="client_satisfaction",
                type="multiple_choice",
                required=True,
                weight=0.15,
                options=["Muy satisfecho", "Satisfecho", "Neutral", "Insatisfecho", "Muy insatisfecho"]
            ),
            FeedbackQuestion(
                id="efficiency_metrics",
                question="¿Considera que se cumplieron los KPIs y métricas de eficiencia?",
                category="efficiency_metrics",
                type="multiple_choice",
                required=True,
                weight=0.12,
                options=["Superó expectativas", "Cumplió completamente", "Cumplió parcialmente", "No cumplió", "Muy por debajo"]
            ),
            FeedbackQuestion(
                id="improvement_recommendations",
                question="¿Qué recomendaciones específicas tiene para mejorar el performance?",
                category="improvement_recommendations",
                type="text",
                required=True,
                weight=0.13,
                placeholder="Proporcione recomendaciones específicas y accionables..."
            ),
            FeedbackQuestion(
                id="strategic_insights",
                question="¿Qué insights estratégicos puede compartir sobre el proceso?",
                category="strategic_insights",
                type="text",
                required=False,
                weight=0.10,
                placeholder="Comparta insights valiosos para futuras mejoras..."
            ),
            FeedbackQuestion(
                id="team_performance",
                question="¿Cómo evalúa el trabajo en equipo y colaboración?",
                category="team_performance",
                type="scale",
                required=True,
                weight=0.10,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="overall_assessment",
                question="Evaluación general del recruiter y recomendación futura",
                category="overall_assessment",
                type="multiple_choice",
                required=True,
                weight=0.10,
                options=["Altamente recomendado", "Recomendado", "Aceptable", "Necesita mejoras", "No recomendado"]
            )
        ]
        
        # Plantilla para Feedback de Súper Admin sobre Sistema
        super_admin_system_questions = [
            FeedbackQuestion(
                id="system_performance",
                question="¿Cómo evalúa el rendimiento general del sistema?",
                category="system_performance",
                type="scale",
                required=True,
                weight=0.12,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="technical_optimization",
                question="¿Qué optimizaciones técnicas considera prioritarias?",
                category="technical_optimization",
                type="text",
                required=True,
                weight=0.12,
                placeholder="Describa las optimizaciones técnicas más importantes..."
            ),
            FeedbackQuestion(
                id="user_experience",
                question="¿Cómo califica la experiencia de usuario actual?",
                category="user_experience",
                type="scale",
                required=True,
                weight=0.11,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="scalability",
                question="¿El sistema está preparado para el crecimiento esperado?",
                category="scalability",
                type="multiple_choice",
                required=True,
                weight=0.11,
                options=["Completamente preparado", "Mayormente preparado", "Parcialmente preparado", "Poco preparado", "No preparado"]
            ),
            FeedbackQuestion(
                id="security",
                question="¿Cómo evalúa los aspectos de seguridad del sistema?",
                category="security",
                type="scale",
                required=True,
                weight=0.11,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="feature_requests",
                question="¿Qué nuevas funcionalidades considera más importantes?",
                category="feature_requests",
                type="text",
                required=False,
                weight=0.10,
                placeholder="Liste las funcionalidades más importantes a desarrollar..."
            ),
            FeedbackQuestion(
                id="bug_reports",
                question="¿Hay bugs o problemas críticos que requieran atención inmediata?",
                category="bug_reports",
                type="text",
                required=False,
                weight=0.09,
                placeholder="Describa cualquier bug crítico encontrado..."
            ),
            FeedbackQuestion(
                id="integration_issues",
                question="¿Cómo funcionan las integraciones con sistemas externos?",
                category="integration_issues",
                type="multiple_choice",
                required=True,
                weight=0.08,
                options=["Funcionan perfectamente", "Funcionan bien", "Algunos problemas", "Problemas frecuentes", "Problemas críticos"]
            ),
            FeedbackQuestion(
                id="performance_metrics",
                question="¿Los KPIs y métricas del sistema son satisfactorios?",
                category="performance_metrics",
                type="scale",
                required=True,
                weight=0.08,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="strategic_roadmap",
                question="¿Qué dirección estratégica recomienda para el roadmap?",
                category="strategic_roadmap",
                type="text",
                required=True,
                weight=0.08,
                placeholder="Proporcione su visión estratégica para el desarrollo futuro..."
            )
        ]
        
        # Plantilla para Feedback de Recruiter sobre Cliente
        recruiter_client_questions = [
            FeedbackQuestion(
                id="requirement_clarity",
                question="¿Qué tan claros fueron los requisitos del cliente desde el inicio?",
                category="requirement_clarity",
                type="scale",
                required=True,
                weight=0.20,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="communication_quality",
                question="¿Cómo califica la calidad de comunicación con el cliente?",
                category="communication_quality",
                type="scale",
                required=True,
                weight=0.20,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="collaboration",
                question="¿Cómo fue la colaboración durante el proceso de selección?",
                category="collaboration",
                type="multiple_choice",
                required=True,
                weight=0.18,
                options=["Excelente", "Muy buena", "Buena", "Regular", "Mala"]
            ),
            FeedbackQuestion(
                id="responsiveness",
                question="¿Qué tan responsivo fue el cliente durante el proceso?",
                category="responsiveness",
                type="scale",
                required=True,
                weight=0.16,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="feedback_quality",
                question="¿La calidad del feedback del cliente fue constructiva?",
                category="feedback_quality",
                type="scale",
                required=True,
                weight=0.16,
                min_value=1,
                max_value=10
            ),
            FeedbackQuestion(
                id="relationship_improvement",
                question="¿Qué sugiere para mejorar la relación con este cliente?",
                category="relationship_improvement",
                type="text",
                required=False,
                weight=0.10,
                placeholder="Comparta sugerencias para optimizar la relación cliente-recruiter..."
            )
        ]
        
        # Registrar plantillas
        self.feedback_templates[FeedbackType.CLIENT_INTERVIEW] = client_interview_questions
        self.feedback_templates[FeedbackType.CANDIDATE_PROCESS] = candidate_process_questions
        self.feedback_templates[FeedbackType.CONSULTANT_PERFORMANCE] = consultant_performance_questions
        self.feedback_templates[FeedbackType.SUPER_ADMIN_SYSTEM] = super_admin_system_questions
        self.feedback_templates[FeedbackType.RECRUITER_CLIENT] = recruiter_client_questions
        
        logger.info(f"✅ {len(self.feedback_templates)} plantillas de feedback cargadas")
    
    async def _setup_sentiment_analysis(self):
        """Configura análisis de sentimientos"""
        logger.info("🎭 Configurando análisis de sentimientos...")
        
        self.sentiment_keywords = {
            'positive': [
                'excelente', 'excepcional', 'impresionante', 'sobresaliente', 'fantástico',
                'muy bueno', 'profesional', 'preparado', 'competente', 'talentoso',
                'recomiendo', 'satisfecho', 'positivo', 'eficiente', 'claro'
            ],
            'negative': [
                'deficiente', 'malo', 'preocupante', 'inadecuado', 'insatisfactorio',
                'confuso', 'desorganizado', 'poco profesional', 'no recomiendo',
                'negativo', 'frustrante', 'lento', 'poco claro', 'problemático'
            ],
            'neutral': [
                'promedio', 'regular', 'aceptable', 'estándar', 'normal',
                'adecuado', 'suficiente', 'típico', 'común', 'básico'
            ]
        }
        
        logger.info("✅ Análisis de sentimientos configurado")
    
    async def _initialize_analytics(self):
        """Inicializa sistema de analytics"""
        logger.info("📊 Inicializando analytics de feedback...")
        
        self.analytics = {
            'response_rates': {},
            'satisfaction_scores': {},
            'sentiment_trends': {},
            'improvement_areas': {},
            'recruiter_performance': {}
        }
        
        logger.info("✅ Analytics de feedback inicializado")
    
    async def request_client_interview_feedback(self,
                                              interview_id: str,
                                              client_id: str,
                                              candidate_id: str,
                                              job_id: str,
                                              interview_details: Dict[str, Any],
                                              priority: FeedbackPriority = FeedbackPriority.HIGH) -> str:
        """
        Solicita feedback del cliente sobre una entrevista
        """
        if not self.initialized:
            await self.initialize_service()
        
        try:
            logger.info(f"💬 Solicitando feedback de cliente para entrevista {interview_id}")
            
            # Crear contexto de la entrevista
            context = {
                'interview_id': interview_id,
                'candidate_id': candidate_id,
                'job_id': job_id,
                'interview_date': interview_details.get('date'),
                'interview_type': interview_details.get('type', 'presencial'),
                'duration': interview_details.get('duration'),
                'interviewers': interview_details.get('interviewers', []),
                'candidate_name': interview_details.get('candidate_name'),
                'job_title': interview_details.get('job_title')
            }
            
            # Obtener plantilla de preguntas
            questions = self.feedback_templates[FeedbackType.CLIENT_INTERVIEW].copy()
            
            # Personalizar preguntas con contexto
            for question in questions:
                question.question = self._personalize_question(question.question, context)
            
            # Crear solicitud de feedback
            feedback_request = FeedbackRequest(
                id=str(uuid.uuid4()),
                feedback_type=FeedbackType.CLIENT_INTERVIEW,
                stage=FeedbackStage.POST_INTERVIEW,
                requester_id=interview_details.get('recruiter_id', 'system'),
                respondent_id=client_id,
                respondent_type='client',
                context=context,
                questions=questions,
                status=FeedbackStatus.PENDING,
                priority=priority,
                expires_at=datetime.now() + timedelta(hours=self.feedback_config[FeedbackType.CLIENT_INTERVIEW]['expiry_hours'])
            )
            
            # Registrar solicitud
            self.feedback_requests[feedback_request.id] = feedback_request
            
            # Enviar solicitud
            await self._send_feedback_request(feedback_request)
            
            # Programar recordatorios
            await self._schedule_reminders(feedback_request)
            
            logger.info(f"✅ Feedback de cliente solicitado - ID: {feedback_request.id}")
            return feedback_request.id
            
        except Exception as e:
            logger.error(f"❌ Error solicitando feedback de cliente: {e}")
            raise
    
    async def request_candidate_process_feedback(self,
                                               process_id: str,
                                               candidate_id: str,
                                               job_id: str,
                                               stage: FeedbackStage,
                                               process_details: Dict[str, Any],
                                               priority: FeedbackPriority = FeedbackPriority.MEDIUM) -> str:
        """
        Solicita feedback del candidato sobre el proceso
        """
        try:
            logger.info(f"💬 Solicitando feedback de candidato para proceso {process_id}")
            
            # Crear contexto del proceso
            context = {
                'process_id': process_id,
                'candidate_id': candidate_id,
                'job_id': job_id,
                'stage': stage.value,
                'job_title': process_details.get('job_title'),
                'company_name': process_details.get('company_name'),
                'recruiter_name': process_details.get('recruiter_name'),
                'process_start_date': process_details.get('start_date'),
                'current_stage': process_details.get('current_stage'),
                'interviews_completed': process_details.get('interviews_completed', 0),
                'total_process_duration': process_details.get('duration_days')
            }
            
            # Obtener plantilla de preguntas
            questions = self.feedback_templates[FeedbackType.CANDIDATE_PROCESS].copy()
            
            # Personalizar preguntas con contexto
            for question in questions:
                question.question = self._personalize_question(question.question, context)
            
            # Crear solicitud de feedback
            feedback_request = FeedbackRequest(
                id=str(uuid.uuid4()),
                feedback_type=FeedbackType.CANDIDATE_PROCESS,
                stage=stage,
                requester_id=process_details.get('recruiter_id', 'system'),
                respondent_id=candidate_id,
                respondent_type='candidate',
                context=context,
                questions=questions,
                status=FeedbackStatus.PENDING,
                priority=priority,
                expires_at=datetime.now() + timedelta(hours=self.feedback_config[FeedbackType.CANDIDATE_PROCESS]['expiry_hours'])
            )
            
            # Registrar solicitud
            self.feedback_requests[feedback_request.id] = feedback_request
            
            # Enviar solicitud
            await self._send_feedback_request(feedback_request)
            
            # Programar recordatorios
            await self._schedule_reminders(feedback_request)
            
            logger.info(f"✅ Feedback de candidato solicitado - ID: {feedback_request.id}")
            return feedback_request.id
            
        except Exception as e:
            logger.error(f"❌ Error solicitando feedback de candidato: {e}")
            raise
    
    async def request_consultant_performance_feedback(self,
                                                    process_id: str,
                                                    consultant_id: str,
                                                    recruiter_id: str,
                                                    performance_period: Dict[str, Any],
                                                    priority: FeedbackPriority = FeedbackPriority.MEDIUM) -> str:
        """
        Solicita feedback del consultor sobre performance del recruiter
        """
        try:
            logger.info(f"💬 Solicitando feedback de consultor para proceso {process_id}")
            
            # Crear contexto del performance
            context = {
                'process_id': process_id,
                'consultant_id': consultant_id,
                'recruiter_id': recruiter_id,
                'recruiter_name': performance_period.get('recruiter_name'),
                'period_start': performance_period.get('start_date'),
                'period_end': performance_period.get('end_date'),
                'processes_handled': performance_period.get('processes_count', 0),
                'clients_served': performance_period.get('clients_count', 0),
                'success_rate': performance_period.get('success_rate', 0),
                'avg_time_to_fill': performance_period.get('avg_time_to_fill', 0),
                'client_satisfaction_avg': performance_period.get('client_satisfaction', 0)
            }
            
            # Obtener plantilla de preguntas
            questions = self.feedback_templates[FeedbackType.CONSULTANT_PERFORMANCE].copy()
            
            # Personalizar preguntas con contexto
            for question in questions:
                question.question = self._personalize_question(question.question, context)
            
            # Crear solicitud de feedback
            feedback_request = FeedbackRequest(
                id=str(uuid.uuid4()),
                feedback_type=FeedbackType.CONSULTANT_PERFORMANCE,
                stage=FeedbackStage.FINAL_PROCESS,
                requester_id='system',
                respondent_id=consultant_id,
                respondent_type='consultant',
                context=context,
                questions=questions,
                status=FeedbackStatus.PENDING,
                priority=priority,
                expires_at=datetime.now() + timedelta(hours=self.feedback_config[FeedbackType.CONSULTANT_PERFORMANCE]['expiry_hours'])
            )
            
            # Registrar solicitud
            self.feedback_requests[feedback_request.id] = feedback_request
            
            # Enviar solicitud
            await self._send_feedback_request(feedback_request)
            
            # Programar recordatorios
            await self._schedule_reminders(feedback_request)
            
            logger.info(f"✅ Feedback de consultor solicitado - ID: {feedback_request.id}")
            return feedback_request.id
            
        except Exception as e:
            logger.error(f"❌ Error solicitando feedback de consultor: {e}")
            raise
    
    async def request_super_admin_system_feedback(self,
                                                 system_period: Dict[str, Any],
                                                 super_admin_id: str,
                                                 priority: FeedbackPriority = FeedbackPriority.HIGH) -> str:
        """
        Solicita feedback del súper administrador sobre el sistema
        """
        try:
            logger.info(f"💬 Solicitando feedback de súper admin para sistema")
            
            # Crear contexto del sistema
            context = {
                'super_admin_id': super_admin_id,
                'period_start': system_period.get('start_date'),
                'period_end': system_period.get('end_date'),
                'total_users': system_period.get('total_users', 0),
                'active_processes': system_period.get('active_processes', 0),
                'system_uptime': system_period.get('uptime_percentage', 0),
                'performance_score': system_period.get('performance_score', 0),
                'user_satisfaction': system_period.get('user_satisfaction', 0),
                'feature_requests': system_period.get('feature_requests_count', 0),
                'bug_reports': system_period.get('bug_reports_count', 0),
                'support_tickets': system_period.get('support_tickets_count', 0)
            }
            
            # Obtener plantilla de preguntas
            questions = self.feedback_templates[FeedbackType.SUPER_ADMIN_SYSTEM].copy()
            
            # Personalizar preguntas con contexto
            for question in questions:
                question.question = self._personalize_question(question.question, context)
            
            # Crear solicitud de feedback
            feedback_request = FeedbackRequest(
                id=str(uuid.uuid4()),
                feedback_type=FeedbackType.SUPER_ADMIN_SYSTEM,
                stage=FeedbackStage.FINAL_PROCESS,
                requester_id='system',
                respondent_id=super_admin_id,
                respondent_type='super_admin',
                context=context,
                questions=questions,
                status=FeedbackStatus.PENDING,
                priority=priority,
                expires_at=datetime.now() + timedelta(hours=self.feedback_config[FeedbackType.SUPER_ADMIN_SYSTEM]['expiry_hours'])
            )
            
            # Registrar solicitud
            self.feedback_requests[feedback_request.id] = feedback_request
            
            # Enviar solicitud
            await self._send_feedback_request(feedback_request)
            
            # Programar recordatorios
            await self._schedule_reminders(feedback_request)
            
            logger.info(f"✅ Feedback de súper admin solicitado - ID: {feedback_request.id}")
            return feedback_request.id
            
        except Exception as e:
            logger.error(f"❌ Error solicitando feedback de súper admin: {e}")
            raise
    
    async def request_recruiter_client_feedback(self,
                                              client_id: str,
                                              recruiter_id: str,
                                              collaboration_period: Dict[str, Any],
                                              priority: FeedbackPriority = FeedbackPriority.MEDIUM) -> str:
        """
        Solicita feedback del recruiter sobre el cliente
        """
        try:
            logger.info(f"💬 Solicitando feedback de recruiter sobre cliente {client_id}")
            
            # Crear contexto de la colaboración
            context = {
                'client_id': client_id,
                'recruiter_id': recruiter_id,
                'client_name': collaboration_period.get('client_name'),
                'recruiter_name': collaboration_period.get('recruiter_name'),
                'collaboration_start': collaboration_period.get('start_date'),
                'collaboration_end': collaboration_period.get('end_date'),
                'processes_together': collaboration_period.get('processes_count', 0),
                'successful_placements': collaboration_period.get('successful_placements', 0),
                'avg_response_time': collaboration_period.get('avg_response_time', 0),
                'communication_frequency': collaboration_period.get('communication_frequency', 'regular')
            }
            
            # Obtener plantilla de preguntas
            questions = self.feedback_templates[FeedbackType.RECRUITER_CLIENT].copy()
            
            # Personalizar preguntas con contexto
            for question in questions:
                question.question = self._personalize_question(question.question, context)
            
            # Crear solicitud de feedback
            feedback_request = FeedbackRequest(
                id=str(uuid.uuid4()),
                feedback_type=FeedbackType.RECRUITER_CLIENT,
                stage=FeedbackStage.FINAL_PROCESS,
                requester_id='system',
                respondent_id=recruiter_id,
                respondent_type='recruiter',
                context=context,
                questions=questions,
                status=FeedbackStatus.PENDING,
                priority=priority,
                expires_at=datetime.now() + timedelta(hours=self.feedback_config[FeedbackType.RECRUITER_CLIENT]['expiry_hours'])
            )
            
            # Registrar solicitud
            self.feedback_requests[feedback_request.id] = feedback_request
            
            # Enviar solicitud
            await self._send_feedback_request(feedback_request)
            
            # Programar recordatorios
            await self._schedule_reminders(feedback_request)
            
            logger.info(f"✅ Feedback de recruiter sobre cliente solicitado - ID: {feedback_request.id}")
            return feedback_request.id
            
        except Exception as e:
            logger.error(f"❌ Error solicitando feedback de recruiter sobre cliente: {e}")
            raise
    
    def _personalize_question(self, question: str, context: Dict[str, Any]) -> str:
        """Personaliza preguntas con datos del contexto"""
        personalized = question
        
        # Reemplazar variables comunes
        replacements = {
            '{candidate_name}': context.get('candidate_name', 'el candidato'),
            '{job_title}': context.get('job_title', 'la posición'),
            '{company_name}': context.get('company_name', 'la empresa'),
            '{recruiter_name}': context.get('recruiter_name', 'el recruiter'),
            '{client_name}': context.get('client_name', 'el cliente'),
            '{consultant_name}': context.get('consultant_name', 'el consultor'),
            '{processes_count}': str(context.get('processes_handled', context.get('processes_count', 0))),
            '{success_rate}': f"{context.get('success_rate', 0):.1f}%",
            '{period_days}': str(context.get('period_days', 'N/A')),
            '{system_uptime}': f"{context.get('system_uptime', 0):.1f}%",
            '{total_users}': str(context.get('total_users', 0)),
            '{collaboration_duration}': str(context.get('collaboration_duration', 'N/A'))
        }
        
        for placeholder, value in replacements.items():
            if placeholder in personalized:
                personalized = personalized.replace(placeholder, str(value))
        
        return personalized
    
    async def _send_feedback_request(self, feedback_request: FeedbackRequest):
        """Envía solicitud de feedback"""
        logger.info(f"📤 Enviando solicitud de feedback a {feedback_request.respondent_type}")
        
        # Actualizar estado
        feedback_request.status = FeedbackStatus.SENT
        feedback_request.sent_at = datetime.now()
        
        # En producción, aquí se enviaría por email/notificación
        # Por ahora, simular envío
        await asyncio.sleep(0.1)
        
        logger.info(f"✅ Solicitud enviada exitosamente")
    
    async def _schedule_reminders(self, feedback_request: FeedbackRequest):
        """Programa recordatorios para feedback"""
        config = self.feedback_config[feedback_request.feedback_type]
        reminder_hours = config['reminder_hours']
        
        for hours in reminder_hours:
            reminder_time = datetime.now() + timedelta(hours=hours)
            logger.info(f"📅 Recordatorio programado para {reminder_time}")
            
            # En producción, usar scheduler como Celery
            # Por ahora, solo logging
    
    async def submit_feedback(self,
                            feedback_request_id: str,
                            responses: Dict[str, Any],
                            respondent_notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesa respuestas de feedback
        """
        try:
            feedback_request = self.feedback_requests.get(feedback_request_id)
            if not feedback_request:
                raise ValueError(f"Feedback request {feedback_request_id} no encontrado")
            
            if feedback_request.status != FeedbackStatus.SENT:
                raise ValueError(f"Feedback request no está en estado válido para respuestas")
            
            logger.info(f"📝 Procesando respuestas de feedback {feedback_request_id}")
            
            # Procesar respuestas
            processed_responses = []
            
            for question in feedback_request.questions:
                response_value = responses.get(question.id)
                if question.required and response_value is None:
                    raise ValueError(f"Respuesta requerida faltante para pregunta {question.id}")
                
                if response_value is not None:
                    processed_response = FeedbackResponse(
                        question_id=question.id,
                        response=response_value
                    )
                    
                    # Calcular score si es aplicable
                    if question.type in ['scale', 'rating']:
                        processed_response.score = self._normalize_score(response_value, question)
                    
                    # Análisis de sentimiento para respuestas de texto
                    if question.type == 'text' and isinstance(response_value, str):
                        sentiment_analysis = self._analyze_sentiment(response_value)
                        processed_response.sentiment = sentiment_analysis['sentiment']
                        processed_response.keywords = sentiment_analysis['keywords']
                    
                    processed_responses.append(processed_response)
            
            # Actualizar feedback request
            feedback_request.responses = processed_responses
            feedback_request.status = FeedbackStatus.COMPLETED
            feedback_request.completed_at = datetime.now()
            
            # Calcular score general
            overall_score = self._calculate_overall_score(feedback_request)
            feedback_request.overall_score = overall_score
            
            # Análisis de sentimientos general
            sentiment_analysis = self._analyze_overall_sentiment(feedback_request)
            feedback_request.sentiment_analysis = sentiment_analysis
            
            # Generar action items
            action_items = await self._generate_action_items(feedback_request)
            feedback_request.action_items = action_items
            
            # Actualizar analytics
            await self._update_analytics(feedback_request)
            
            logger.info(f"✅ Feedback procesado - Score: {overall_score:.1%}")
            
            return {
                'feedback_request_id': feedback_request_id,
                'overall_score': overall_score,
                'sentiment': sentiment_analysis['overall_sentiment'],
                'action_items': action_items,
                'completed_at': feedback_request.completed_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando feedback: {e}")
            raise
    
    def _normalize_score(self, value: Any, question: FeedbackQuestion) -> float:
        """Normaliza score a escala 0-1"""
        try:
            numeric_value = float(value)
            
            if question.min_value is not None and question.max_value is not None:
                # Normalizar basado en rango
                normalized = (numeric_value - question.min_value) / (question.max_value - question.min_value)
                return max(0.0, min(1.0, normalized))
            else:
                # Asumir escala 1-10 por defecto
                return max(0.0, min(1.0, (numeric_value - 1) / 9))
                
        except (ValueError, TypeError):
            return 0.5  # Score neutro si no se puede convertir
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analiza sentimiento de texto"""
        text_lower = text.lower()
        
        positive_count = sum(1 for keyword in self.sentiment_keywords['positive'] if keyword in text_lower)
        negative_count = sum(1 for keyword in self.sentiment_keywords['negative'] if keyword in text_lower)
        neutral_count = sum(1 for keyword in self.sentiment_keywords['neutral'] if keyword in text_lower)
        
        # Determinar sentimiento dominante
        if positive_count > negative_count and positive_count > neutral_count:
            sentiment = 'positive'
        elif negative_count > positive_count and negative_count > neutral_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Identificar keywords encontradas
        found_keywords = []
        for category, keywords in self.sentiment_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
        
        return {
            'sentiment': sentiment,
            'confidence': max(positive_count, negative_count, neutral_count) / max(1, len(text.split())),
            'keywords': found_keywords,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count
        }
    
    def _calculate_overall_score(self, feedback_request: FeedbackRequest) -> float:
        """Calcula score general del feedback"""
        weighted_score = 0.0
        total_weight = 0.0
        
        for response in feedback_request.responses:
            question = next((q for q in feedback_request.questions if q.id == response.question_id), None)
            if question and response.score is not None:
                weighted_score += response.score * question.weight
                total_weight += question.weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _analyze_overall_sentiment(self, feedback_request: FeedbackRequest) -> Dict[str, Any]:
        """Analiza sentimiento general del feedback"""
        text_responses = [
            response.response for response in feedback_request.responses
            if isinstance(response.response, str)
        ]
        
        if not text_responses:
            return {'overall_sentiment': 'neutral', 'confidence': 0.0}
        
        # Combinar todo el texto
        combined_text = ' '.join(text_responses)
        sentiment_analysis = self._analyze_sentiment(combined_text)
        
        return {
            'overall_sentiment': sentiment_analysis['sentiment'],
            'confidence': sentiment_analysis['confidence'],
            'key_themes': sentiment_analysis['keywords'][:10],  # Top 10 keywords
            'text_responses_count': len(text_responses)
        }
    
    async def _generate_action_items(self, feedback_request: FeedbackRequest) -> List[str]:
        """Genera action items basados en el feedback"""
        action_items = []
        
        # Action items basados en scores bajos
        for response in feedback_request.responses:
            question = next((q for q in feedback_request.questions if q.id == response.question_id), None)
            if question and response.score is not None and response.score < 0.6:
                action_items.append(f"Mejorar {question.category}: Score bajo ({response.score:.1%})")
        
        # Action items basados en sentimiento negativo
        negative_responses = [
            response for response in feedback_request.responses
            if response.sentiment == 'negative'
        ]
        
        if negative_responses:
            action_items.append(f"Revisar {len(negative_responses)} respuestas con sentimiento negativo")
        
        # Action items específicos por tipo de feedback
        if feedback_request.feedback_type == FeedbackType.CLIENT_INTERVIEW:
            action_items.extend(await self._generate_client_action_items(feedback_request))
        elif feedback_request.feedback_type == FeedbackType.CANDIDATE_PROCESS:
            action_items.extend(await self._generate_candidate_action_items(feedback_request))
        
        return action_items
    
    async def _generate_client_action_items(self, feedback_request: FeedbackRequest) -> List[str]:
        """Genera action items específicos para feedback de cliente"""
        action_items = []
        
        # Revisar recomendación de próximos pasos
        next_steps_response = next(
            (r for r in feedback_request.responses if r.question_id == 'next_steps'), None
        )
        
        if next_steps_response:
            if next_steps_response.response == "No continuar":
                action_items.append("URGENTE: Cliente no recomienda continuar - Revisar razones")
            elif next_steps_response.response == "Segunda entrevista":
                action_items.append("Programar segunda entrevista según feedback del cliente")
            elif next_steps_response.response == "Solicitar más información":
                action_items.append("Proporcionar información adicional solicitada por el cliente")
        
        return action_items
    
    async def _generate_candidate_action_items(self, feedback_request: FeedbackRequest) -> List[str]:
        """Genera action items específicos para feedback de candidato"""
        action_items = []
        
        # Revisar satisfacción general
        satisfaction_response = next(
            (r for r in feedback_request.responses if r.question_id == 'overall_satisfaction'), None
        )
        
        if satisfaction_response and satisfaction_response.score and satisfaction_response.score < 0.5:
            action_items.append("ATENCIÓN: Baja satisfacción del candidato - Revisar proceso")
        
        # Revisar sugerencias de mejora
        improvement_response = next(
            (r for r in feedback_request.responses if r.question_id == 'improvement_suggestions'), None
        )
        
        if improvement_response and improvement_response.response:
            action_items.append("Revisar sugerencias de mejora del candidato")
        
        return action_items
    
    async def _update_analytics(self, feedback_request: FeedbackRequest):
        """Actualiza analytics con nuevo feedback"""
        feedback_type = feedback_request.feedback_type.value
        
        # Actualizar tasas de respuesta
        if feedback_type not in self.analytics['response_rates']:
            self.analytics['response_rates'][feedback_type] = {'sent': 0, 'completed': 0}
        
        self.analytics['response_rates'][feedback_type]['completed'] += 1
        
        # Actualizar scores de satisfacción
        if feedback_type not in self.analytics['satisfaction_scores']:
            self.analytics['satisfaction_scores'][feedback_type] = []
        
        if feedback_request.overall_score:
            self.analytics['satisfaction_scores'][feedback_type].append(feedback_request.overall_score)
        
        # Actualizar tendencias de sentimiento
        if feedback_request.sentiment_analysis:
            sentiment = feedback_request.sentiment_analysis['overall_sentiment']
            if feedback_type not in self.analytics['sentiment_trends']:
                self.analytics['sentiment_trends'][feedback_type] = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            self.analytics['sentiment_trends'][feedback_type][sentiment] += 1
    
    async def get_feedback_summary(self, feedback_request_id: str) -> Dict[str, Any]:
        """Obtiene resumen de feedback"""
        feedback_request = self.feedback_requests.get(feedback_request_id)
        if not feedback_request:
            return {'status': 'not_found'}
        
        return {
            'id': feedback_request.id,
            'type': feedback_request.feedback_type.value,
            'stage': feedback_request.stage.value,
            'respondent_type': feedback_request.respondent_type,
            'status': feedback_request.status.value,
            'overall_score': feedback_request.overall_score,
            'sentiment': feedback_request.sentiment_analysis.get('overall_sentiment') if feedback_request.sentiment_analysis else None,
            'action_items': feedback_request.action_items,
            'created_at': feedback_request.created_at.isoformat(),
            'completed_at': feedback_request.completed_at.isoformat() if feedback_request.completed_at else None,
            'responses_count': len(feedback_request.responses),
            'context': feedback_request.context
        }
    
    async def get_feedback_analytics(self, 
                                   date_range: Tuple[datetime, datetime],
                                   feedback_type: Optional[FeedbackType] = None) -> Dict[str, Any]:
        """Genera analytics de feedback"""
        start_date, end_date = date_range
        
        # Filtrar feedback requests
        filtered_requests = [
            req for req in self.feedback_requests.values()
            if start_date <= req.created_at <= end_date
        ]
        
        if feedback_type:
            filtered_requests = [req for req in filtered_requests if req.feedback_type == feedback_type]
        
        if not filtered_requests:
            return {'status': 'no_data'}
        
        # Métricas generales
        total_sent = len(filtered_requests)
        completed_requests = [req for req in filtered_requests if req.status == FeedbackStatus.COMPLETED]
        completion_rate = len(completed_requests) / total_sent if total_sent > 0 else 0
        
        # Scores promedio
        scores = [req.overall_score for req in completed_requests if req.overall_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Distribución de sentimientos
        sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        for req in completed_requests:
            if req.sentiment_analysis:
                sentiment = req.sentiment_analysis.get('overall_sentiment', 'neutral')
                sentiment_distribution[sentiment] += 1
        
        # Tiempo promedio de respuesta
        response_times = []
        for req in completed_requests:
            if req.sent_at and req.completed_at:
                response_time = (req.completed_at - req.sent_at).total_seconds() / 3600  # horas
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Action items más comunes
        all_action_items = []
        for req in completed_requests:
            all_action_items.extend(req.action_items)
        
        action_item_frequency = {}
        for item in all_action_items:
            action_item_frequency[item] = action_item_frequency.get(item, 0) + 1
        
        top_action_items = sorted(action_item_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'status': 'completed',
            'period': f"{start_date.date()} to {end_date.date()}",
            'summary': {
                'total_sent': total_sent,
                'completed': len(completed_requests),
                'completion_rate': completion_rate,
                'average_score': avg_score,
                'avg_response_time_hours': avg_response_time
            },
            'sentiment_distribution': sentiment_distribution,
            'top_action_items': top_action_items,
            'generated_at': datetime.now().isoformat()
        }

# Instancia global del servicio
advanced_feedback_service = AdvancedFeedbackService()