"""
📋 ADVANCED REFERENCES SERVICE - GHUNTRED V2
Sistema avanzado de referencias con dos momentos específicos:
1. Referencias iniciales al inicio del proceso
2. Referencias profundas en etapa avanzada
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid
import re

logger = logging.getLogger(__name__)

class ReferenceStage(Enum):
    """Etapas de referencias"""
    INITIAL = "initial"          # Al inicio del proceso
    ADVANCED = "advanced"        # En etapa avanzada
    FINAL = "final"             # Antes de la oferta
    POST_OFFER = "post_offer"   # Después de la oferta

class ReferenceType(Enum):
    """Tipos de referencias"""
    PROFESSIONAL = "professional"
    MANAGER = "manager"
    PEER = "peer"
    SUBORDINATE = "subordinate"
    CLIENT = "client"
    VENDOR = "vendor"
    ACADEMIC = "academic"
    PERSONAL = "personal"

class ReferenceStatus(Enum):
    """Estados de referencias"""
    PENDING = "pending"
    CONTACTED = "contacted"
    COMPLETED = "completed"
    DECLINED = "declined"
    UNREACHABLE = "unreachable"
    INVALID = "invalid"

class ReferenceMethod(Enum):
    """Métodos de contacto para referencias"""
    PHONE = "phone"
    EMAIL = "email"
    VIDEO_CALL = "video_call"
    IN_PERSON = "in_person"
    LINKEDIN = "linkedin"
    FORM = "form"

@dataclass
class ReferenceContact:
    """Contacto de referencia"""
    id: str
    name: str
    position: str
    company: str
    relationship: str
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    years_known: Optional[int] = None
    relationship_context: Optional[str] = None
    preferred_contact_method: ReferenceMethod = ReferenceMethod.PHONE
    best_contact_times: List[str] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class ReferenceQuestion:
    """Pregunta de referencia"""
    id: str
    question: str
    category: str
    weight: float
    required: bool
    stage: ReferenceStage
    reference_type: ReferenceType
    response_type: str  # scale, text, boolean, multiple_choice
    options: List[str] = field(default_factory=list)

@dataclass
class ReferenceResponse:
    """Respuesta de referencia"""
    question_id: str
    response: Any
    score: Optional[float] = None
    notes: Optional[str] = None
    confidence_level: Optional[float] = None

@dataclass
class ReferenceCheck:
    """Verificación de referencia"""
    id: str
    candidate_id: str
    job_id: str
    reference_contact: ReferenceContact
    stage: ReferenceStage
    reference_type: ReferenceType
    status: ReferenceStatus
    method: ReferenceMethod
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    conducted_by: Optional[str] = None
    responses: List[ReferenceResponse] = field(default_factory=list)
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    red_flags: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    areas_for_development: List[str] = field(default_factory=list)
    rehire_eligible: Optional[bool] = None
    additional_notes: Optional[str] = None
    duration_minutes: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ReferenceTemplate:
    """Plantilla de referencias por etapa y tipo"""
    id: str
    name: str
    stage: ReferenceStage
    reference_type: ReferenceType
    questions: List[ReferenceQuestion]
    estimated_duration: int  # minutos
    introduction_script: str
    closing_script: str
    required_questions: List[str]
    optional_questions: List[str]

class AdvancedReferencesService:
    """
    Servicio avanzado de referencias con dos momentos específicos
    """
    
    def __init__(self):
        self.reference_templates = {}
        self.reference_checks = {}
        self.reference_questions = {}
        self.candidates_references = {}
        self.analytics = {}
        
        # Configuración por etapa
        self.stage_config = {
            ReferenceStage.INITIAL: {
                'required_references': 2,
                'reference_types': [ReferenceType.PROFESSIONAL, ReferenceType.MANAGER],
                'depth_level': 'basic',
                'estimated_time': 15,  # minutos por referencia
                'focus_areas': ['work_performance', 'reliability', 'basic_skills']
            },
            ReferenceStage.ADVANCED: {
                'required_references': 3,
                'reference_types': [ReferenceType.MANAGER, ReferenceType.PEER, ReferenceType.SUBORDINATE],
                'depth_level': 'comprehensive',
                'estimated_time': 30,  # minutos por referencia
                'focus_areas': ['leadership', 'cultural_fit', 'growth_potential', 'detailed_performance']
            }
        }
        
        self.initialized = False
    
    async def initialize_service(self):
        """Inicializa el servicio de referencias"""
        if self.initialized:
            return
            
        logger.info("📋 Inicializando Advanced References Service...")
        
        # Cargar plantillas de referencias
        await self._load_reference_templates()
        
        # Configurar preguntas por etapa
        await self._setup_reference_questions()
        
        # Inicializar sistema de analytics
        await self._initialize_analytics()
        
        self.initialized = True
        logger.info("✅ Advanced References Service inicializado")
    
    async def _load_reference_templates(self):
        """Carga plantillas de referencias"""
        logger.info("📋 Cargando plantillas de referencias...")
        
        # Plantilla para Referencias Iniciales
        initial_template = ReferenceTemplate(
            id="initial_professional_reference",
            name="Referencias Profesionales Iniciales",
            stage=ReferenceStage.INITIAL,
            reference_type=ReferenceType.PROFESSIONAL,
            questions=[],  # Se cargarán después
            estimated_duration=15,
            introduction_script="""
            Buenos días/tardes {reference_name},
            
            Mi nombre es {recruiter_name} de {company_name}. Estoy contactándolo porque {candidate_name} 
            ha aplicado para una posición en nuestra empresa y nos ha proporcionado su nombre como referencia profesional.
            
            ¿Tendría unos 10-15 minutos para hablar sobre su experiencia trabajando con {candidate_name}?
            Esta información nos ayudará a tomar una mejor decisión de contratación.
            
            Toda la información que comparta será tratada de manera confidencial.
            """,
            closing_script="""
            Muchas gracias por su tiempo y por compartir esta información valiosa sobre {candidate_name}.
            
            ¿Hay algo más que considere importante que debería saber sobre {candidate_name}?
            
            Si necesito aclarar algún punto, ¿estaría disponible para una breve llamada de seguimiento?
            
            Que tenga un excelente día.
            """,
            required_questions=["work_performance", "reliability", "teamwork", "recommendation"],
            optional_questions=["strengths", "areas_improvement", "rehire_eligible"]
        )
        
        # Plantilla para Referencias Avanzadas
        advanced_template = ReferenceTemplate(
            id="advanced_comprehensive_reference",
            name="Referencias Comprehensivas Avanzadas",
            stage=ReferenceStage.ADVANCED,
            reference_type=ReferenceType.MANAGER,
            questions=[],  # Se cargarán después
            estimated_duration=30,
            introduction_script="""
            Buenos días/tardes {reference_name},
            
            Mi nombre es {recruiter_name} de {company_name}. Estoy contactándolo porque {candidate_name} 
            está en la etapa final de nuestro proceso de selección para una posición de {job_title}.
            
            Dado que está muy cerca de recibir una oferta, necesitamos hacer una verificación más profunda 
            de referencias. ¿Tendría unos 25-30 minutos para una conversación detallada sobre su experiencia 
            trabajando con {candidate_name}?
            
            Sus insights serán fundamentales para nuestra decisión final.
            """,
            closing_script="""
            Muchas gracias por dedicar este tiempo y por proporcionar información tan detallada sobre {candidate_name}.
            
            Basado en nuestra conversación, ¿recomendaría contratar a {candidate_name} para esta posición?
            
            ¿Hay algún consejo específico sobre cómo maximizar el éxito de {candidate_name} en esta nueva posición?
            
            Aprecio mucho su tiempo y perspectiva profesional.
            """,
            required_questions=["detailed_performance", "leadership_style", "cultural_fit", "growth_potential", 
                              "decision_making", "stress_management", "team_dynamics", "final_recommendation"],
            optional_questions=["development_areas", "motivation_factors", "retention_risk", "management_style"]
        )
        
        # Registrar plantillas
        self.reference_templates[initial_template.id] = initial_template
        self.reference_templates[advanced_template.id] = advanced_template
        
        logger.info(f"✅ {len(self.reference_templates)} plantillas de referencias cargadas")
    
    async def _setup_reference_questions(self):
        """Configura preguntas por etapa y tipo"""
        logger.info("❓ Configurando preguntas de referencias...")
        
        # Preguntas para Referencias Iniciales
        initial_questions = [
            ReferenceQuestion(
                id="work_performance",
                question="¿Cómo calificaría el desempeño laboral general de {candidate_name}?",
                category="performance",
                weight=0.25,
                required=True,
                stage=ReferenceStage.INITIAL,
                reference_type=ReferenceType.PROFESSIONAL,
                response_type="scale",
                options=["1-Deficiente", "2-Bajo", "3-Promedio", "4-Bueno", "5-Excelente"]
            ),
            ReferenceQuestion(
                id="reliability",
                question="¿Qué tan confiable era {candidate_name} en términos de puntualidad, cumplimiento de deadlines y responsabilidades?",
                category="reliability",
                weight=0.20,
                required=True,
                stage=ReferenceStage.INITIAL,
                reference_type=ReferenceType.PROFESSIONAL,
                response_type="scale",
                options=["1-Muy poco confiable", "2-Poco confiable", "3-Moderadamente confiable", "4-Confiable", "5-Muy confiable"]
            ),
            ReferenceQuestion(
                id="teamwork",
                question="¿Cómo era {candidate_name} trabajando en equipo?",
                category="soft_skills",
                weight=0.15,
                required=True,
                stage=ReferenceStage.INITIAL,
                reference_type=ReferenceType.PROFESSIONAL,
                response_type="text"
            ),
            ReferenceQuestion(
                id="strengths",
                question="¿Cuáles considera que son las principales fortalezas de {candidate_name}?",
                category="strengths",
                weight=0.15,
                required=False,
                stage=ReferenceStage.INITIAL,
                reference_type=ReferenceType.PROFESSIONAL,
                response_type="text"
            ),
            ReferenceQuestion(
                id="areas_improvement",
                question="¿En qué áreas podría mejorar {candidate_name}?",
                category="development",
                weight=0.10,
                required=False,
                stage=ReferenceStage.INITIAL,
                reference_type=ReferenceType.PROFESSIONAL,
                response_type="text"
            ),
            ReferenceQuestion(
                id="recommendation",
                question="¿Recomendaría contratar a {candidate_name}?",
                category="recommendation",
                weight=0.15,
                required=True,
                stage=ReferenceStage.INITIAL,
                reference_type=ReferenceType.PROFESSIONAL,
                response_type="boolean"
            )
        ]
        
        # Preguntas para Referencias Avanzadas
        advanced_questions = [
            ReferenceQuestion(
                id="detailed_performance",
                question="Describa en detalle el desempeño de {candidate_name} en los proyectos más importantes que manejó.",
                category="performance",
                weight=0.20,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="text"
            ),
            ReferenceQuestion(
                id="leadership_style",
                question="¿Cómo describiría el estilo de liderazgo de {candidate_name}? ¿Fue efectivo?",
                category="leadership",
                weight=0.18,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="text"
            ),
            ReferenceQuestion(
                id="cultural_fit",
                question="¿Cómo se adaptó {candidate_name} a la cultura de la empresa? ¿Hubo algún desafío?",
                category="culture",
                weight=0.15,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="text"
            ),
            ReferenceQuestion(
                id="growth_potential",
                question="¿Cuál es el potencial de crecimiento de {candidate_name}? ¿Está listo para mayores responsabilidades?",
                category="growth",
                weight=0.15,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="text"
            ),
            ReferenceQuestion(
                id="decision_making",
                question="¿Cómo toma decisiones {candidate_name}? ¿Puede manejar decisiones complejas bajo presión?",
                category="decision_making",
                weight=0.12,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="text"
            ),
            ReferenceQuestion(
                id="stress_management",
                question="¿Cómo maneja {candidate_name} el estrés y la presión? ¿Ha visto algún comportamiento preocupante?",
                category="stress_management",
                weight=0.10,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="text"
            ),
            ReferenceQuestion(
                id="team_dynamics",
                question="¿Cómo afectó {candidate_name} la dinámica del equipo? ¿Fue un influencia positiva o negativa?",
                category="team_dynamics",
                weight=0.10,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="text"
            ),
            ReferenceQuestion(
                id="final_recommendation",
                question="En una escala del 1 al 10, ¿qué tan fuertemente recomendaría a {candidate_name} para esta posición?",
                category="final_recommendation",
                weight=0.20,
                required=True,
                stage=ReferenceStage.ADVANCED,
                reference_type=ReferenceType.MANAGER,
                response_type="scale",
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
            )
        ]
        
        # Registrar preguntas
        all_questions = initial_questions + advanced_questions
        for question in all_questions:
            self.reference_questions[question.id] = question
        
        logger.info(f"✅ {len(all_questions)} preguntas de referencias configuradas")
    
    async def _initialize_analytics(self):
        """Inicializa sistema de analytics"""
        logger.info("📊 Inicializando analytics de referencias...")
        
        self.analytics = {
            'completion_rates': {},
            'response_times': {},
            'score_distributions': {},
            'red_flag_patterns': {},
            'reference_quality_metrics': {}
        }
        
        logger.info("✅ Analytics de referencias inicializado")
    
    async def initiate_reference_check(self, 
                                     candidate_id: str,
                                     job_id: str,
                                     stage: ReferenceStage,
                                     reference_contacts: List[ReferenceContact],
                                     priority: str = "normal") -> List[str]:
        """
        Inicia proceso de verificación de referencias
        """
        if not self.initialized:
            await self.initialize_service()
        
        try:
            logger.info(f"📋 Iniciando verificación de referencias {stage.value} para candidato {candidate_id}")
            
            # Validar etapa y configuración
            stage_config = self.stage_config.get(stage)
            if not stage_config:
                raise ValueError(f"Configuración no encontrada para etapa {stage.value}")
            
            # Validar número de referencias
            required_refs = stage_config['required_references']
            if len(reference_contacts) < required_refs:
                raise ValueError(f"Se requieren al menos {required_refs} referencias para etapa {stage.value}")
            
            # Crear checks de referencia
            reference_check_ids = []
            
            for contact in reference_contacts:
                # Determinar tipo de referencia
                reference_type = self._determine_reference_type(contact, stage)
                
                # Crear check de referencia
                reference_check = ReferenceCheck(
                    id=str(uuid.uuid4()),
                    candidate_id=candidate_id,
                    job_id=job_id,
                    reference_contact=contact,
                    stage=stage,
                    reference_type=reference_type,
                    status=ReferenceStatus.PENDING,
                    method=contact.preferred_contact_method
                )
                
                # Registrar check
                self.reference_checks[reference_check.id] = reference_check
                reference_check_ids.append(reference_check.id)
                
                logger.info(f"   • Referencia creada: {contact.name} ({contact.company})")
            
            # Registrar referencias del candidato
            if candidate_id not in self.candidates_references:
                self.candidates_references[candidate_id] = {}
            
            self.candidates_references[candidate_id][stage.value] = reference_check_ids
            
            # Programar contacto inicial
            await self._schedule_reference_contacts(reference_check_ids, priority)
            
            logger.info(f"✅ {len(reference_check_ids)} referencias iniciadas para etapa {stage.value}")
            return reference_check_ids
            
        except Exception as e:
            logger.error(f"❌ Error iniciando verificación de referencias: {e}")
            raise
    
    def _determine_reference_type(self, contact: ReferenceContact, stage: ReferenceStage) -> ReferenceType:
        """Determina el tipo de referencia basado en la relación"""
        
        relationship_lower = contact.relationship.lower()
        
        if any(word in relationship_lower for word in ['manager', 'supervisor', 'boss', 'jefe']):
            return ReferenceType.MANAGER
        elif any(word in relationship_lower for word in ['peer', 'colleague', 'compañero', 'colega']):
            return ReferenceType.PEER
        elif any(word in relationship_lower for word in ['subordinate', 'team member', 'subordinado']):
            return ReferenceType.SUBORDINATE
        elif any(word in relationship_lower for word in ['client', 'customer', 'cliente']):
            return ReferenceType.CLIENT
        elif any(word in relationship_lower for word in ['vendor', 'supplier', 'proveedor']):
            return ReferenceType.VENDOR
        else:
            return ReferenceType.PROFESSIONAL
    
    async def _schedule_reference_contacts(self, reference_check_ids: List[str], priority: str):
        """Programa contactos con referencias"""
        logger.info(f"📞 Programando contactos con {len(reference_check_ids)} referencias")
        
        for check_id in reference_check_ids:
            check = self.reference_checks[check_id]
            
            # Determinar tiempo de contacto
            if priority == "urgent":
                contact_delay = 0  # Inmediato
            elif priority == "high":
                contact_delay = 1  # 1 hora
            else:
                contact_delay = 4  # 4 horas
            
            # Programar contacto
            scheduled_time = datetime.now() + timedelta(hours=contact_delay)
            check.scheduled_date = scheduled_time
            
            logger.info(f"   • Contacto programado con {check.reference_contact.name} para {scheduled_time}")
            
            # En producción, aquí se programaría el contacto real
            # Por ahora, simular programación
            await self._simulate_reference_contact_scheduling(check)
    
    async def _simulate_reference_contact_scheduling(self, check: ReferenceCheck):
        """Simula programación de contacto con referencia"""
        # En producción, esto se integraría con sistema de calendario/CRM
        logger.info(f"📅 Contacto programado con {check.reference_contact.name}")
    
    async def conduct_reference_check(self, 
                                    reference_check_id: str,
                                    conducted_by: str,
                                    responses: Dict[str, Any],
                                    duration_minutes: int,
                                    additional_notes: str = None) -> Dict[str, Any]:
        """
        Conduce una verificación de referencia
        """
        try:
            check = self.reference_checks.get(reference_check_id)
            if not check:
                raise ValueError(f"Reference check {reference_check_id} no encontrado")
            
            logger.info(f"📋 Conduciendo verificación de referencia con {check.reference_contact.name}")
            
            # Actualizar estado
            check.status = ReferenceStatus.COMPLETED
            check.completed_date = datetime.now()
            check.conducted_by = conducted_by
            check.duration_minutes = duration_minutes
            check.additional_notes = additional_notes
            
            # Procesar respuestas
            processed_responses = await self._process_reference_responses(check, responses)
            check.responses = processed_responses
            
            # Calcular score general
            overall_score = await self._calculate_reference_score(check)
            check.overall_score = overall_score
            
            # Generar análisis
            analysis = await self._analyze_reference_responses(check)
            check.recommendation = analysis['recommendation']
            check.red_flags = analysis['red_flags']
            check.strengths = analysis['strengths']
            check.areas_for_development = analysis['areas_for_development']
            check.rehire_eligible = analysis['rehire_eligible']
            
            logger.info(f"✅ Verificación completada - Score: {overall_score:.1%}")
            
            return {
                'reference_check_id': reference_check_id,
                'overall_score': overall_score,
                'recommendation': check.recommendation,
                'red_flags': check.red_flags,
                'strengths': check.strengths,
                'areas_for_development': check.areas_for_development,
                'rehire_eligible': check.rehire_eligible
            }
            
        except Exception as e:
            logger.error(f"❌ Error conduciendo verificación de referencia: {e}")
            raise
    
    async def _process_reference_responses(self, check: ReferenceCheck, responses: Dict[str, Any]) -> List[ReferenceResponse]:
        """Procesa respuestas de referencia"""
        processed_responses = []
        
        for question_id, response_value in responses.items():
            question = self.reference_questions.get(question_id)
            if not question:
                continue
            
            # Crear respuesta procesada
            processed_response = ReferenceResponse(
                question_id=question_id,
                response=response_value
            )
            
            # Calcular score si es aplicable
            if question.response_type == "scale":
                if isinstance(response_value, str) and response_value.isdigit():
                    score = float(response_value) / 10.0  # Normalizar a 0-1
                elif isinstance(response_value, (int, float)):
                    score = float(response_value) / 10.0
                else:
                    score = 0.5  # Score neutro
                processed_response.score = score
            
            elif question.response_type == "boolean":
                processed_response.score = 1.0 if response_value else 0.0
            
            # Evaluar confianza basada en longitud y detalle de respuesta
            if question.response_type == "text":
                confidence = self._assess_response_confidence(response_value)
                processed_response.confidence_level = confidence
            
            processed_responses.append(processed_response)
        
        return processed_responses
    
    def _assess_response_confidence(self, response_text: str) -> float:
        """Evalúa confianza de respuesta basada en contenido"""
        if not response_text or len(response_text.strip()) < 10:
            return 0.2
        
        # Factores que aumentan confianza
        confidence_factors = 0.5
        
        # Longitud de respuesta
        if len(response_text) > 50:
            confidence_factors += 0.2
        if len(response_text) > 100:
            confidence_factors += 0.1
        
        # Presencia de ejemplos específicos
        if any(word in response_text.lower() for word in ['ejemplo', 'instance', 'ocasión', 'vez']):
            confidence_factors += 0.1
        
        # Detalles específicos (números, fechas, nombres)
        if re.search(r'\d+', response_text):
            confidence_factors += 0.1
        
        return min(1.0, confidence_factors)
    
    async def _calculate_reference_score(self, check: ReferenceCheck) -> float:
        """Calcula score general de la referencia"""
        if not check.responses:
            return 0.0
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for response in check.responses:
            question = self.reference_questions.get(response.question_id)
            if not question or response.score is None:
                continue
            
            weighted_score += response.score * question.weight
            total_weight += question.weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_score / total_weight
    
    async def _analyze_reference_responses(self, check: ReferenceCheck) -> Dict[str, Any]:
        """Analiza respuestas y genera insights"""
        
        red_flags = []
        strengths = []
        areas_for_development = []
        rehire_eligible = None
        
        # Analizar respuestas por categoría
        for response in check.responses:
            question = self.reference_questions.get(response.question_id)
            if not question:
                continue
            
            response_text = str(response.response).lower()
            
            # Detectar red flags
            red_flag_keywords = [
                'problema', 'conflicto', 'difícil', 'negativo', 'preocupante',
                'no recomiendo', 'no contrataría', 'problemas de actitud',
                'falta de compromiso', 'irresponsable'
            ]
            
            if any(keyword in response_text for keyword in red_flag_keywords):
                red_flags.append(f"Posible red flag en {question.category}: {response.response}")
            
            # Identificar fortalezas
            strength_keywords = [
                'excelente', 'outstanding', 'excepcional', 'sobresaliente',
                'muy bueno', 'talentoso', 'dedicado', 'confiable', 'líder'
            ]
            
            if any(keyword in response_text for keyword in strength_keywords):
                strengths.append(f"Fortaleza en {question.category}: {response.response}")
            
            # Áreas de desarrollo
            development_keywords = [
                'mejorar', 'desarrollar', 'crecer', 'aprender', 'fortalecer'
            ]
            
            if any(keyword in response_text for keyword in development_keywords):
                areas_for_development.append(f"Desarrollo en {question.category}: {response.response}")
            
            # Elegibilidad para rehire
            if question.id == "recommendation" or question.id == "final_recommendation":
                if response.score and response.score >= 0.7:
                    rehire_eligible = True
                elif response.score and response.score < 0.4:
                    rehire_eligible = False
        
        # Generar recomendación general
        overall_score = check.overall_score or 0.0
        
        if overall_score >= 0.8:
            recommendation = "Altamente recomendado"
        elif overall_score >= 0.6:
            recommendation = "Recomendado"
        elif overall_score >= 0.4:
            recommendation = "Recomendado con reservas"
        else:
            recommendation = "No recomendado"
        
        return {
            'recommendation': recommendation,
            'red_flags': red_flags,
            'strengths': strengths,
            'areas_for_development': areas_for_development,
            'rehire_eligible': rehire_eligible
        }
    
    async def get_reference_summary(self, candidate_id: str, stage: ReferenceStage) -> Dict[str, Any]:
        """
        Obtiene resumen de referencias para un candidato y etapa
        """
        try:
            if candidate_id not in self.candidates_references:
                return {'status': 'no_references_found'}
            
            stage_references = self.candidates_references[candidate_id].get(stage.value, [])
            if not stage_references:
                return {'status': 'no_references_for_stage'}
            
            # Obtener todos los checks de la etapa
            checks = [self.reference_checks[check_id] for check_id in stage_references]
            
            # Calcular métricas generales
            completed_checks = [c for c in checks if c.status == ReferenceStatus.COMPLETED]
            pending_checks = [c for c in checks if c.status == ReferenceStatus.PENDING]
            
            if not completed_checks:
                return {
                    'status': 'in_progress',
                    'total_references': len(checks),
                    'completed': 0,
                    'pending': len(pending_checks)
                }
            
            # Calcular score promedio
            scores = [c.overall_score for c in completed_checks if c.overall_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Consolidar red flags y fortalezas
            all_red_flags = []
            all_strengths = []
            all_areas_development = []
            
            for check in completed_checks:
                all_red_flags.extend(check.red_flags)
                all_strengths.extend(check.strengths)
                all_areas_development.extend(check.areas_for_development)
            
            # Determinar recomendación general
            recommendations = [c.recommendation for c in completed_checks if c.recommendation]
            positive_recommendations = len([r for r in recommendations if 'recomendado' in r.lower()])
            recommendation_rate = positive_recommendations / len(recommendations) if recommendations else 0.0
            
            return {
                'status': 'completed',
                'stage': stage.value,
                'total_references': len(checks),
                'completed': len(completed_checks),
                'pending': len(pending_checks),
                'average_score': avg_score,
                'recommendation_rate': recommendation_rate,
                'overall_recommendation': self._determine_overall_recommendation(avg_score, recommendation_rate),
                'red_flags': list(set(all_red_flags)),
                'strengths': list(set(all_strengths)),
                'areas_for_development': list(set(all_areas_development)),
                'reference_details': [
                    {
                        'reference_name': c.reference_contact.name,
                        'reference_company': c.reference_contact.company,
                        'relationship': c.reference_contact.relationship,
                        'score': c.overall_score,
                        'recommendation': c.recommendation,
                        'completed_date': c.completed_date.isoformat() if c.completed_date else None
                    }
                    for c in completed_checks
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen de referencias: {e}")
            raise
    
    def _determine_overall_recommendation(self, avg_score: float, recommendation_rate: float) -> str:
        """Determina recomendación general basada en métricas"""
        
        if avg_score >= 0.8 and recommendation_rate >= 0.8:
            return "Altamente recomendado - Proceder con oferta"
        elif avg_score >= 0.6 and recommendation_rate >= 0.6:
            return "Recomendado - Candidato sólido"
        elif avg_score >= 0.4 and recommendation_rate >= 0.4:
            return "Recomendado con reservas - Revisar áreas de preocupación"
        else:
            return "No recomendado - Considerar otros candidatos"
    
    async def compare_reference_stages(self, candidate_id: str) -> Dict[str, Any]:
        """
        Compara referencias entre etapa inicial y avanzada
        """
        try:
            initial_summary = await self.get_reference_summary(candidate_id, ReferenceStage.INITIAL)
            advanced_summary = await self.get_reference_summary(candidate_id, ReferenceStage.ADVANCED)
            
            if initial_summary['status'] != 'completed' or advanced_summary['status'] != 'completed':
                return {
                    'status': 'incomplete',
                    'initial_status': initial_summary['status'],
                    'advanced_status': advanced_summary['status']
                }
            
            # Comparar scores
            score_improvement = advanced_summary['average_score'] - initial_summary['average_score']
            
            # Comparar consistencia
            consistency_score = 1.0 - abs(score_improvement)  # Más consistente = menos diferencia
            
            # Analizar progresión de fortalezas
            initial_strengths = set(initial_summary['strengths'])
            advanced_strengths = set(advanced_summary['strengths'])
            
            consistent_strengths = initial_strengths & advanced_strengths
            new_strengths = advanced_strengths - initial_strengths
            
            # Analizar red flags
            initial_red_flags = set(initial_summary['red_flags'])
            advanced_red_flags = set(advanced_summary['red_flags'])
            
            persistent_red_flags = initial_red_flags & advanced_red_flags
            new_red_flags = advanced_red_flags - initial_red_flags
            
            return {
                'status': 'completed',
                'comparison_summary': {
                    'initial_score': initial_summary['average_score'],
                    'advanced_score': advanced_summary['average_score'],
                    'score_improvement': score_improvement,
                    'consistency_score': consistency_score,
                    'overall_trend': 'improving' if score_improvement > 0.1 else 'declining' if score_improvement < -0.1 else 'stable'
                },
                'strengths_analysis': {
                    'consistent_strengths': list(consistent_strengths),
                    'new_strengths': list(new_strengths),
                    'total_unique_strengths': len(initial_strengths | advanced_strengths)
                },
                'red_flags_analysis': {
                    'persistent_red_flags': list(persistent_red_flags),
                    'new_red_flags': list(new_red_flags),
                    'total_red_flags': len(initial_red_flags | advanced_red_flags)
                },
                'final_recommendation': self._generate_final_recommendation(
                    initial_summary, advanced_summary, score_improvement, consistency_score
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Error comparando etapas de referencias: {e}")
            raise
    
    def _generate_final_recommendation(self, initial_summary: Dict[str, Any], 
                                     advanced_summary: Dict[str, Any],
                                     score_improvement: float,
                                     consistency_score: float) -> str:
        """Genera recomendación final basada en ambas etapas"""
        
        avg_score = (initial_summary['average_score'] + advanced_summary['average_score']) / 2
        
        # Factores de decisión
        high_performance = avg_score >= 0.7
        consistent_performance = consistency_score >= 0.8
        positive_trend = score_improvement > 0
        low_red_flags = len(advanced_summary['red_flags']) <= 2
        
        if high_performance and consistent_performance and low_red_flags:
            return "PROCEDER CON OFERTA - Candidato excepcional con referencias consistentemente positivas"
        elif high_performance and low_red_flags:
            return "PROCEDER CON OFERTA - Candidato sólido con buenas referencias"
        elif avg_score >= 0.5 and consistent_performance:
            return "PROCEDER CON PRECAUCIÓN - Candidato aceptable, considerar áreas de desarrollo"
        elif positive_trend and low_red_flags:
            return "CONSIDERAR OFERTA - Candidato en mejora, referencias positivas recientes"
        else:
            return "NO PROCEDER - Referencias insuficientes o preocupaciones significativas"
    
    async def get_reference_analytics(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Genera analytics de referencias
        """
        start_date, end_date = date_range
        
        # Filtrar checks en el rango de fechas
        relevant_checks = [
            check for check in self.reference_checks.values()
            if check.created_at >= start_date and check.created_at <= end_date
        ]
        
        if not relevant_checks:
            return {'status': 'no_data', 'period': f"{start_date.date()} to {end_date.date()}"}
        
        # Métricas generales
        total_checks = len(relevant_checks)
        completed_checks = [c for c in relevant_checks if c.status == ReferenceStatus.COMPLETED]
        completion_rate = len(completed_checks) / total_checks if total_checks > 0 else 0
        
        # Métricas por etapa
        stage_metrics = {}
        for stage in ReferenceStage:
            stage_checks = [c for c in relevant_checks if c.stage == stage]
            if stage_checks:
                stage_completed = [c for c in stage_checks if c.status == ReferenceStatus.COMPLETED]
                stage_metrics[stage.value] = {
                    'total': len(stage_checks),
                    'completed': len(stage_completed),
                    'completion_rate': len(stage_completed) / len(stage_checks),
                    'avg_score': sum(c.overall_score for c in stage_completed if c.overall_score) / len(stage_completed) if stage_completed else 0
                }
        
        # Tiempo promedio de respuesta
        response_times = [
            (c.completed_date - c.created_at).total_seconds() / 3600  # horas
            for c in completed_checks if c.completed_date
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Red flags más comunes
        all_red_flags = []
        for check in completed_checks:
            all_red_flags.extend(check.red_flags)
        
        red_flag_frequency = {}
        for flag in all_red_flags:
            red_flag_frequency[flag] = red_flag_frequency.get(flag, 0) + 1
        
        top_red_flags = sorted(red_flag_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'status': 'completed',
            'period': f"{start_date.date()} to {end_date.date()}",
            'summary': {
                'total_reference_checks': total_checks,
                'completed_checks': len(completed_checks),
                'completion_rate': completion_rate,
                'avg_response_time_hours': avg_response_time
            },
            'stage_breakdown': stage_metrics,
            'top_red_flags': top_red_flags,
            'generated_at': datetime.now().isoformat()
        }

# Instancia global del servicio
advanced_references_service = AdvancedReferencesService()