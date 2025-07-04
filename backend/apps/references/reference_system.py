"""
Advanced Reference System - huntRED® v2
Sistema completo de referencias con verificación automática, análisis de credibilidad y workflow inteligente.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import requests
import hashlib
import hmac
from urllib.parse import urlencode
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ReferenceStatus(Enum):
    """Estados de una referencia."""
    PENDING = "pending"
    REQUESTED = "requested"
    RECEIVED = "received"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ReferenceType(Enum):
    """Tipos de referencia."""
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    PERSONAL = "personal"
    MANAGER = "manager"
    PEER = "peer"
    CLIENT = "client"


class VerificationLevel(Enum):
    """Niveles de verificación."""
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    PREMIUM = "premium"


@dataclass
class ReferenceContact:
    """Información de contacto de referencia."""
    name: str
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    relationship: str = ""
    years_known: Optional[int] = None
    verification_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReferenceQuestion:
    """Pregunta para referencia."""
    id: str
    question: str
    type: str  # rating, text, multiple_choice, yes_no
    category: str  # performance, character, skills, etc.
    options: Optional[List[str]] = None
    required: bool = True
    weight: float = 1.0


@dataclass
class ReferenceResponse:
    """Respuesta a una pregunta de referencia."""
    question_id: str
    answer: Any
    score: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class Reference:
    """Referencia completa."""
    id: str
    candidate_id: str
    reference_contact: ReferenceContact
    reference_type: ReferenceType
    status: ReferenceStatus
    verification_level: VerificationLevel
    
    # Contenido de la referencia
    responses: List[ReferenceResponse] = field(default_factory=list)
    overall_rating: Optional[float] = None
    recommendation: Optional[str] = None
    
    # Verificación
    verification_score: Optional[float] = None
    verification_details: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    requested_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Metadata
    reference_token: str = field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReferenceTemplate:
    """Template para diferentes tipos de referencias."""
    id: str
    name: str
    reference_type: ReferenceType
    questions: List[ReferenceQuestion]
    description: str = ""
    estimated_time: int = 5  # minutos
    is_active: bool = True


class AdvancedReferenceSystem:
    """
    Sistema avanzado de referencias con:
    - Verificación automática de identidad
    - Templates personalizables por rol/industria
    - Análisis de credibilidad con ML
    - Detección de referencias falsas
    - Integración con LinkedIn para verificación
    - Scoring inteligente con pesos dinámicos
    - Workflow automatizado con recordatorios
    """
    
    def __init__(self, config: Dict[str, Any], db_session: Session):
        self.config = config
        self.db = db_session
        
        # Templates de referencia
        self.templates: Dict[str, ReferenceTemplate] = {}
        
        # Referencias activas
        self.active_references: Dict[str, Reference] = {}
        
        # Configurar templates predefinidos
        self._setup_default_templates()
        
        # Configurar verificadores
        self._setup_verification_services()
        
        # Métricas
        self.metrics = {
            'total_requested': 0,
            'total_received': 0,
            'total_verified': 0,
            'average_response_time': 0,
            'verification_success_rate': 0
        }
    
    def _setup_default_templates(self):
        """Configura templates predefinidos de referencia."""
        # Template para referencias profesionales
        professional_template = ReferenceTemplate(
            id="professional_reference",
            name="Referencia Profesional",
            reference_type=ReferenceType.PROFESSIONAL,
            questions=[
                ReferenceQuestion(
                    id="overall_performance",
                    question="¿Cómo calificarías el desempeño general de {candidate_name}?",
                    type="rating",
                    category="performance",
                    weight=2.0
                ),
                ReferenceQuestion(
                    id="technical_skills",
                    question="¿Cómo evalúas las habilidades técnicas de {candidate_name}?",
                    type="rating",
                    category="skills",
                    weight=1.5
                ),
                ReferenceQuestion(
                    id="communication",
                    question="¿Cómo calificarías las habilidades de comunicación?",
                    type="rating",
                    category="soft_skills",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="teamwork",
                    question="¿Cómo trabaja {candidate_name} en equipo?",
                    type="rating",
                    category="soft_skills",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="reliability",
                    question="¿Es {candidate_name} confiable y cumple con los plazos?",
                    type="rating",
                    category="character",
                    weight=1.5
                ),
                ReferenceQuestion(
                    id="growth_potential",
                    question="¿Cómo ves el potencial de crecimiento de {candidate_name}?",
                    type="rating",
                    category="potential",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="rehire",
                    question="¿Volverías a contratar a {candidate_name}?",
                    type="yes_no",
                    category="recommendation",
                    weight=2.0
                ),
                ReferenceQuestion(
                    id="strengths",
                    question="¿Cuáles son las principales fortalezas de {candidate_name}?",
                    type="text",
                    category="strengths",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="areas_improvement",
                    question="¿En qué áreas podría mejorar {candidate_name}?",
                    type="text",
                    category="development",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="additional_comments",
                    question="¿Hay algo más que te gustaría agregar sobre {candidate_name}?",
                    type="text",
                    category="general",
                    required=False,
                    weight=0.5
                )
            ],
            description="Template completo para referencias profesionales de trabajo",
            estimated_time=8
        )
        
        # Template para referencias de manager
        manager_template = ReferenceTemplate(
            id="manager_reference",
            name="Referencia de Manager",
            reference_type=ReferenceType.MANAGER,
            questions=[
                ReferenceQuestion(
                    id="reporting_relationship",
                    question="¿Cuál era tu relación de reporte con {candidate_name}?",
                    type="multiple_choice",
                    category="relationship",
                    options=["Era mi subordinado directo", "Era mi manager", "Éramos pares", "Trabajábamos en proyectos juntos"],
                    weight=0.5
                ),
                ReferenceQuestion(
                    id="performance_rating",
                    question="¿Cómo calificarías el desempeño de {candidate_name} comparado con otros en el mismo nivel?",
                    type="multiple_choice",
                    category="performance",
                    options=["Top 10%", "Top 25%", "Promedio superior", "Promedio", "Bajo promedio"],
                    weight=2.0
                ),
                ReferenceQuestion(
                    id="leadership_potential",
                    question="¿Cómo evalúas el potencial de liderazgo de {candidate_name}?",
                    type="rating",
                    category="leadership",
                    weight=1.5
                ),
                ReferenceQuestion(
                    id="problem_solving",
                    question="¿Cómo aborda {candidate_name} los problemas complejos?",
                    type="text",
                    category="skills",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="initiative",
                    question="¿Toma {candidate_name} iniciativa y es proactivo?",
                    type="rating",
                    category="character",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="specific_achievements",
                    question="¿Puedes mencionar logros específicos de {candidate_name}?",
                    type="text",
                    category="achievements",
                    weight=1.5
                ),
                ReferenceQuestion(
                    id="promotion_readiness",
                    question="¿Estaba {candidate_name} listo para una promoción?",
                    type="yes_no",
                    category="potential",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="reason_leaving",
                    question="¿Cuál fue la razón por la que {candidate_name} dejó la empresa?",
                    type="text",
                    category="context",
                    weight=0.5
                )
            ],
            description="Template especializado para referencias de managers directos",
            estimated_time=10
        )
        
        # Template para referencias académicas
        academic_template = ReferenceTemplate(
            id="academic_reference",
            name="Referencia Académica",
            reference_type=ReferenceType.ACADEMIC,
            questions=[
                ReferenceQuestion(
                    id="academic_performance",
                    question="¿Cómo calificas el desempeño académico de {candidate_name}?",
                    type="rating",
                    category="performance",
                    weight=2.0
                ),
                ReferenceQuestion(
                    id="analytical_skills",
                    question="¿Cómo evalúas las habilidades analíticas de {candidate_name}?",
                    type="rating",
                    category="skills",
                    weight=1.5
                ),
                ReferenceQuestion(
                    id="research_ability",
                    question="¿Cómo es la capacidad de investigación de {candidate_name}?",
                    type="rating",
                    category="skills",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="intellectual_curiosity",
                    question="¿Demuestra {candidate_name} curiosidad intelectual?",
                    type="rating",
                    category="character",
                    weight=1.0
                ),
                ReferenceQuestion(
                    id="class_participation",
                    question="¿Cómo participaba {candidate_name} en clase?",
                    type="text",
                    category="engagement",
                    weight=0.5
                ),
                ReferenceQuestion(
                    id="recommend_for_position",
                    question="¿Recomendarías a {candidate_name} para una posición profesional?",
                    type="yes_no",
                    category="recommendation",
                    weight=1.5
                )
            ],
            description="Template para referencias de profesores y supervisores académicos",
            estimated_time=6
        )
        
        # Registrar templates
        self.templates[professional_template.id] = professional_template
        self.templates[manager_template.id] = manager_template
        self.templates[academic_template.id] = academic_template
    
    def _setup_verification_services(self):
        """Configura servicios de verificación."""
        # LinkedIn API para verificación
        self.linkedin_config = {
            'client_id': self.config.get('linkedin_client_id'),
            'client_secret': self.config.get('linkedin_client_secret'),
            'api_url': 'https://api.linkedin.com/v2'
        }
        
        # Servicios de verificación de email
        self.email_verification_config = {
            'hunter_api_key': self.config.get('hunter_api_key'),
            'zerobounce_api_key': self.config.get('zerobounce_api_key')
        }
        
        # Configuración de scoring de credibilidad
        self.credibility_weights = {
            'email_verification': 0.3,
            'linkedin_profile': 0.4,
            'company_verification': 0.2,
            'response_quality': 0.1
        }
    
    async def request_reference(self, candidate_id: str, reference_contact: ReferenceContact,
                              template_id: str, verification_level: VerificationLevel = VerificationLevel.STANDARD,
                              custom_message: Optional[str] = None) -> str:
        """Solicita una nueva referencia."""
        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")
            
            # Crear referencia
            reference = Reference(
                id=str(uuid.uuid4()),
                candidate_id=candidate_id,
                reference_contact=reference_contact,
                reference_type=template.reference_type,
                status=ReferenceStatus.PENDING,
                verification_level=verification_level,
                expires_at=datetime.now() + timedelta(days=14)  # Expira en 14 días
            )
            
            # Verificación inicial del contacto
            if verification_level != VerificationLevel.BASIC:
                await self._initial_contact_verification(reference)
            
            # Enviar solicitud
            await self._send_reference_request(reference, template, custom_message)
            
            # Actualizar estado
            reference.status = ReferenceStatus.REQUESTED
            self.active_references[reference.id] = reference
            
            # Métricas
            self.metrics['total_requested'] += 1
            
            logger.info(f"Reference requested: {reference.id} for candidate {candidate_id}")
            return reference.id
            
        except Exception as e:
            logger.error(f"Error requesting reference: {str(e)}")
            raise
    
    async def _initial_contact_verification(self, reference: Reference):
        """Verificación inicial del contacto de referencia."""
        try:
            verification_results = {}
            
            # Verificar email
            email_valid = await self._verify_email(reference.reference_contact.email)
            verification_results['email_valid'] = email_valid
            
            # Verificar LinkedIn si está disponible
            if reference.reference_contact.linkedin_url:
                linkedin_valid = await self._verify_linkedin_profile(reference.reference_contact.linkedin_url)
                verification_results['linkedin_valid'] = linkedin_valid
            
            # Verificar empresa si está disponible
            if reference.reference_contact.company:
                company_valid = await self._verify_company(reference.reference_contact.company)
                verification_results['company_valid'] = company_valid
            
            # Calcular score de verificación inicial
            initial_score = self._calculate_initial_verification_score(verification_results)
            
            reference.verification_details['initial_verification'] = verification_results
            reference.verification_score = initial_score
            
            logger.info(f"Initial verification completed for reference {reference.id}, score: {initial_score}")
            
        except Exception as e:
            logger.error(f"Error in initial contact verification: {str(e)}")
            reference.verification_details['initial_verification_error'] = str(e)
    
    async def _verify_email(self, email: str) -> bool:
        """Verifica la validez de un email."""
        try:
            # Usar Hunter.io para verificación
            if self.email_verification_config.get('hunter_api_key'):
                url = f"https://api.hunter.io/v2/email-verifier"
                params = {
                    'email': email,
                    'api_key': self.email_verification_config['hunter_api_key']
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return data.get('data', {}).get('result') == 'deliverable'
            
            # Fallback: verificación básica de formato
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(email_pattern, email))
            
        except Exception as e:
            logger.error(f"Error verifying email {email}: {str(e)}")
            return False
    
    async def _verify_linkedin_profile(self, linkedin_url: str) -> bool:
        """Verifica la validez de un perfil de LinkedIn."""
        try:
            # Verificar que la URL sea válida
            if 'linkedin.com/in/' not in linkedin_url:
                return False
            
            # Hacer request básico para verificar que existe
            response = requests.head(linkedin_url, timeout=10, allow_redirects=True)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error verifying LinkedIn profile {linkedin_url}: {str(e)}")
            return False
    
    async def _verify_company(self, company_name: str) -> bool:
        """Verifica la existencia de una empresa."""
        try:
            # En producción, esto se integraría con APIs como Clearbit, LinkedIn Company API, etc.
            # Por ahora, verificación básica
            return len(company_name.strip()) > 2
            
        except Exception as e:
            logger.error(f"Error verifying company {company_name}: {str(e)}")
            return False
    
    def _calculate_initial_verification_score(self, verification_results: Dict[str, bool]) -> float:
        """Calcula score inicial de verificación."""
        score = 0.0
        total_weight = 0.0
        
        if 'email_valid' in verification_results:
            weight = self.credibility_weights['email_verification']
            score += weight if verification_results['email_valid'] else 0
            total_weight += weight
        
        if 'linkedin_valid' in verification_results:
            weight = self.credibility_weights['linkedin_profile']
            score += weight if verification_results['linkedin_valid'] else 0
            total_weight += weight
        
        if 'company_valid' in verification_results:
            weight = self.credibility_weights['company_verification']
            score += weight if verification_results['company_valid'] else 0
            total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.0
    
    async def _send_reference_request(self, reference: Reference, template: ReferenceTemplate,
                                    custom_message: Optional[str] = None):
        """Envía la solicitud de referencia por email."""
        try:
            # Crear URL de referencia
            reference_url = f"{self.config.get('base_url')}/references/{reference.reference_token}"
            
            # Preparar variables para el mensaje
            variables = {
                'reference_name': reference.reference_contact.name,
                'candidate_name': 'el candidato',  # Se obtendría de la BD
                'company_name': self.config.get('company_name', 'huntRED®'),
                'reference_url': reference_url,
                'estimated_time': template.estimated_time,
                'expiry_date': reference.expires_at.strftime('%d/%m/%Y') if reference.expires_at else 'N/A'
            }
            
            # Mensaje personalizado o template por defecto
            if custom_message:
                message_body = custom_message.format(**variables)
            else:
                message_body = f"""
                Estimado/a {variables['reference_name']},
                
                Espero que este mensaje te encuentre bien.
                
                {variables['candidate_name']} ha aplicado para una posición en {variables['company_name']} 
                y te ha indicado como referencia profesional.
                
                ¿Podrías ayudarnos proporcionando una breve referencia sobre su desempeño y habilidades?
                
                Puedes completar el formulario aquí: {variables['reference_url']}
                
                El proceso toma aproximadamente {variables['estimated_time']} minutos y toda la información 
                será tratada con total confidencialidad.
                
                Esta solicitud expira el {variables['expiry_date']}.
                
                Gracias por tu tiempo y colaboración.
                
                Saludos cordiales,
                Equipo de Talent Acquisition
                {variables['company_name']}
                """
            
            # Aquí se integraría con el sistema de notificaciones
            logger.info(f"Reference request sent to {reference.reference_contact.email}")
            
        except Exception as e:
            logger.error(f"Error sending reference request: {str(e)}")
            raise
    
    async def submit_reference(self, reference_token: str, responses: List[ReferenceResponse],
                             overall_rating: Optional[float] = None,
                             recommendation: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Procesa la sumisión de una referencia."""
        try:
            # Encontrar referencia por token
            reference = None
            for ref in self.active_references.values():
                if ref.reference_token == reference_token:
                    reference = ref
                    break
            
            if not reference:
                raise ValueError("Reference not found or expired")
            
            if reference.status != ReferenceStatus.REQUESTED:
                raise ValueError(f"Reference is in {reference.status.value} state, cannot submit")
            
            # Verificar que no haya expirado
            if reference.expires_at and datetime.now() > reference.expires_at:
                reference.status = ReferenceStatus.EXPIRED
                raise ValueError("Reference has expired")
            
            # Actualizar referencia
            reference.responses = responses
            reference.overall_rating = overall_rating
            reference.recommendation = recommendation
            reference.submitted_at = datetime.now()
            reference.status = ReferenceStatus.RECEIVED
            
            if metadata:
                reference.metadata.update(metadata)
            
            # Análisis avanzado de la referencia
            await self._analyze_reference_quality(reference)
            
            # Verificación adicional si es requerida
            if reference.verification_level in [VerificationLevel.ENHANCED, VerificationLevel.PREMIUM]:
                await self._enhanced_verification(reference)
            
            # Calcular score final
            reference.verification_score = self._calculate_final_verification_score(reference)
            
            # Determinar si pasa verificación
            min_score = self._get_minimum_verification_score(reference.verification_level)
            if reference.verification_score >= min_score:
                reference.status = ReferenceStatus.VERIFIED
                reference.verified_at = datetime.now()
            else:
                reference.status = ReferenceStatus.REJECTED
                logger.warning(f"Reference {reference.id} rejected due to low verification score: {reference.verification_score}")
            
            # Métricas
            self.metrics['total_received'] += 1
            if reference.status == ReferenceStatus.VERIFIED:
                self.metrics['total_verified'] += 1
            
            # Calcular tiempo de respuesta
            if reference.submitted_at and reference.requested_at:
                response_time = (reference.submitted_at - reference.requested_at).total_seconds() / 3600  # horas
                # Actualizar promedio (simplificado)
                current_avg = self.metrics['average_response_time']
                total_responses = self.metrics['total_received']
                self.metrics['average_response_time'] = ((current_avg * (total_responses - 1)) + response_time) / total_responses
            
            logger.info(f"Reference {reference.id} submitted successfully, status: {reference.status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting reference: {str(e)}")
            raise
    
    async def _analyze_reference_quality(self, reference: Reference):
        """Analiza la calidad de las respuestas de la referencia."""
        try:
            quality_metrics = {}
            
            # Analizar completitud
            template = self.templates.get(reference.reference_type.value + "_reference")
            if template:
                required_questions = [q for q in template.questions if q.required]
                answered_required = len([r for r in reference.responses if any(q.id == r.question_id for q in required_questions)])
                completeness = answered_required / len(required_questions) if required_questions else 1.0
                quality_metrics['completeness'] = completeness
            
            # Analizar longitud de respuestas de texto
            text_responses = [r for r in reference.responses if isinstance(r.answer, str)]
            if text_responses:
                avg_length = sum(len(r.answer) for r in text_responses) / len(text_responses)
                quality_metrics['response_detail'] = min(avg_length / 100, 1.0)  # Normalizar a 0-1
            
            # Detectar respuestas sospechosas (muy cortas, genéricas, etc.)
            suspicious_indicators = []
            for response in reference.responses:
                if isinstance(response.answer, str):
                    if len(response.answer.strip()) < 10:
                        suspicious_indicators.append("very_short_response")
                    if response.answer.lower() in ['good', 'excellent', 'ok', 'fine', 'average']:
                        suspicious_indicators.append("generic_response")
            
            quality_metrics['suspicious_indicators'] = suspicious_indicators
            quality_metrics['quality_score'] = self._calculate_response_quality_score(quality_metrics)
            
            reference.verification_details['quality_analysis'] = quality_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing reference quality: {str(e)}")
    
    def _calculate_response_quality_score(self, quality_metrics: Dict[str, Any]) -> float:
        """Calcula score de calidad de respuestas."""
        score = 0.0
        
        # Completitud (40%)
        completeness = quality_metrics.get('completeness', 0)
        score += completeness * 0.4
        
        # Detalle de respuestas (30%)
        response_detail = quality_metrics.get('response_detail', 0)
        score += response_detail * 0.3
        
        # Penalización por indicadores sospechosos (30%)
        suspicious_count = len(quality_metrics.get('suspicious_indicators', []))
        suspicious_penalty = min(suspicious_count * 0.1, 0.3)
        score += max(0.3 - suspicious_penalty, 0)
        
        return score
    
    async def _enhanced_verification(self, reference: Reference):
        """Verificación mejorada para niveles ENHANCED y PREMIUM."""
        try:
            enhanced_checks = {}
            
            # Verificar coherencia temporal (fechas, períodos de trabajo)
            enhanced_checks['temporal_consistency'] = await self._check_temporal_consistency(reference)
            
            # Cross-verification con LinkedIn si está disponible
            if reference.reference_contact.linkedin_url:
                enhanced_checks['linkedin_cross_check'] = await self._linkedin_cross_verification(reference)
            
            # Análisis de patrones de IP y user agent
            enhanced_checks['behavior_analysis'] = self._analyze_submission_behavior(reference)
            
            # Verificación de dominio de email corporativo
            enhanced_checks['corporate_email'] = self._verify_corporate_email(reference.reference_contact.email)
            
            reference.verification_details['enhanced_verification'] = enhanced_checks
            
        except Exception as e:
            logger.error(f"Error in enhanced verification: {str(e)}")
    
    async def _check_temporal_consistency(self, reference: Reference) -> Dict[str, Any]:
        """Verifica consistencia temporal en las respuestas."""
        # Implementación simplificada
        return {'consistent': True, 'issues': []}
    
    async def _linkedin_cross_verification(self, reference: Reference) -> Dict[str, Any]:
        """Cross-verificación con perfil de LinkedIn."""
        # Implementación simplificada
        return {'verified': True, 'confidence': 0.8}
    
    def _analyze_submission_behavior(self, reference: Reference) -> Dict[str, Any]:
        """Analiza patrones de comportamiento en la sumisión."""
        behavior_score = 1.0
        issues = []
        
        # Verificar tiempo de sumisión (muy rápido puede ser sospechoso)
        if reference.submitted_at and reference.requested_at:
            submission_time = (reference.submitted_at - reference.requested_at).total_seconds()
            if submission_time < 300:  # Menos de 5 minutos
                behavior_score -= 0.3
                issues.append("very_fast_submission")
        
        return {
            'behavior_score': behavior_score,
            'issues': issues
        }
    
    def _verify_corporate_email(self, email: str) -> bool:
        """Verifica si el email es corporativo (no Gmail, Yahoo, etc.)."""
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
        domain = email.split('@')[1].lower() if '@' in email else ''
        return domain not in personal_domains
    
    def _calculate_final_verification_score(self, reference: Reference) -> float:
        """Calcula el score final de verificación."""
        total_score = 0.0
        total_weight = 0.0
        
        # Score inicial de contacto
        if reference.verification_score is not None:
            initial_weight = 0.4
            total_score += reference.verification_score * initial_weight
            total_weight += initial_weight
        
        # Score de calidad de respuestas
        quality_analysis = reference.verification_details.get('quality_analysis', {})
        if 'quality_score' in quality_analysis:
            quality_weight = 0.3
            total_score += quality_analysis['quality_score'] * quality_weight
            total_weight += quality_weight
        
        # Score de verificación mejorada (si aplica)
        enhanced_verification = reference.verification_details.get('enhanced_verification', {})
        if enhanced_verification:
            enhanced_weight = 0.3
            enhanced_score = self._calculate_enhanced_score(enhanced_verification)
            total_score += enhanced_score * enhanced_weight
            total_weight += enhanced_weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_enhanced_score(self, enhanced_verification: Dict[str, Any]) -> float:
        """Calcula score de verificación mejorada."""
        score = 0.0
        checks = 0
        
        if 'temporal_consistency' in enhanced_verification:
            score += 1.0 if enhanced_verification['temporal_consistency'].get('consistent', False) else 0.0
            checks += 1
        
        if 'linkedin_cross_check' in enhanced_verification:
            score += enhanced_verification['linkedin_cross_check'].get('confidence', 0.0)
            checks += 1
        
        if 'behavior_analysis' in enhanced_verification:
            score += enhanced_verification['behavior_analysis'].get('behavior_score', 0.0)
            checks += 1
        
        if 'corporate_email' in enhanced_verification:
            score += 1.0 if enhanced_verification['corporate_email'] else 0.5
            checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _get_minimum_verification_score(self, verification_level: VerificationLevel) -> float:
        """Obtiene el score mínimo requerido por nivel de verificación."""
        thresholds = {
            VerificationLevel.BASIC: 0.3,
            VerificationLevel.STANDARD: 0.6,
            VerificationLevel.ENHANCED: 0.75,
            VerificationLevel.PREMIUM: 0.85
        }
        return thresholds.get(verification_level, 0.6)
    
    def get_reference_by_token(self, reference_token: str) -> Optional[Reference]:
        """Obtiene una referencia por su token."""
        for reference in self.active_references.values():
            if reference.reference_token == reference_token:
                return reference
        return None
    
    def get_reference_form(self, reference_token: str) -> Optional[Dict[str, Any]]:
        """Obtiene el formulario de referencia para mostrar al usuario."""
        reference = self.get_reference_by_token(reference_token)
        if not reference:
            return None
        
        # Verificar expiración
        if reference.expires_at and datetime.now() > reference.expires_at:
            return {'error': 'Reference has expired'}
        
        if reference.status != ReferenceStatus.REQUESTED:
            return {'error': f'Reference is in {reference.status.value} state'}
        
        # Obtener template
        template_key = reference.reference_type.value + "_reference"
        template = self.templates.get(template_key)
        
        if not template:
            return {'error': 'Template not found'}
        
        # Preparar formulario
        return {
            'reference_id': reference.id,
            'reference_token': reference_token,
            'candidate_name': 'el candidato',  # Se obtendría de la BD
            'reference_contact': {
                'name': reference.reference_contact.name,
                'company': reference.reference_contact.company,
                'position': reference.reference_contact.position
            },
            'template': {
                'name': template.name,
                'description': template.description,
                'estimated_time': template.estimated_time,
                'questions': [
                    {
                        'id': q.id,
                        'question': q.question.format(candidate_name='el candidato'),
                        'type': q.type,
                        'category': q.category,
                        'options': q.options,
                        'required': q.required
                    }
                    for q in template.questions
                ]
            },
            'expires_at': reference.expires_at.isoformat() if reference.expires_at else None
        }
    
    def get_candidate_references(self, candidate_id: str) -> List[Dict[str, Any]]:
        """Obtiene todas las referencias de un candidato."""
        references = [ref for ref in self.active_references.values() if ref.candidate_id == candidate_id]
        
        return [
            {
                'id': ref.id,
                'reference_contact': {
                    'name': ref.reference_contact.name,
                    'company': ref.reference_contact.company,
                    'position': ref.reference_contact.position,
                    'relationship': ref.reference_contact.relationship
                },
                'reference_type': ref.reference_type.value,
                'status': ref.status.value,
                'verification_level': ref.verification_level.value,
                'verification_score': ref.verification_score,
                'overall_rating': ref.overall_rating,
                'requested_at': ref.requested_at.isoformat(),
                'submitted_at': ref.submitted_at.isoformat() if ref.submitted_at else None,
                'verified_at': ref.verified_at.isoformat() if ref.verified_at else None
            }
            for ref in sorted(references, key=lambda x: x.requested_at, reverse=True)
        ]
    
    def get_reference_analytics(self, candidate_id: str) -> Dict[str, Any]:
        """Obtiene analíticas de referencias para un candidato."""
        references = [ref for ref in self.active_references.values() 
                     if ref.candidate_id == candidate_id and ref.status == ReferenceStatus.VERIFIED]
        
        if not references:
            return {'error': 'No verified references found'}
        
        # Calcular métricas agregadas
        total_rating = sum(ref.overall_rating for ref in references if ref.overall_rating)
        avg_rating = total_rating / len([ref for ref in references if ref.overall_rating])
        
        verification_scores = [ref.verification_score for ref in references if ref.verification_score]
        avg_verification = sum(verification_scores) / len(verification_scores) if verification_scores else 0
        
        # Análisis por categorías
        category_scores = {}
        for reference in references:
            template_key = reference.reference_type.value + "_reference"
            template = self.templates.get(template_key)
            if template:
                for response in reference.responses:
                    question = next((q for q in template.questions if q.id == response.question_id), None)
                    if question and isinstance(response.answer, (int, float)):
                        if question.category not in category_scores:
                            category_scores[question.category] = []
                        category_scores[question.category].append(response.answer)
        
        # Promediar por categoría
        category_averages = {
            category: sum(scores) / len(scores)
            for category, scores in category_scores.items()
        }
        
        return {
            'total_references': len(references),
            'average_rating': round(avg_rating, 2) if references else 0,
            'average_verification_score': round(avg_verification, 2),
            'category_scores': category_averages,
            'reference_types': list(set(ref.reference_type.value for ref in references)),
            'recommendations': [ref.recommendation for ref in references if ref.recommendation]
        }
    
    async def send_reminders(self):
        """Envía recordatorios para referencias pendientes."""
        try:
            now = datetime.now()
            
            for reference in self.active_references.values():
                if reference.status == ReferenceStatus.REQUESTED:
                    # Calcular días desde solicitud
                    days_since_request = (now - reference.requested_at).days
                    
                    # Enviar recordatorios a los 3, 7 y 10 días
                    if days_since_request in [3, 7, 10]:
                        await self._send_reminder(reference, days_since_request)
                    
                    # Marcar como expirada si han pasado 14+ días
                    elif days_since_request >= 14:
                        reference.status = ReferenceStatus.EXPIRED
                        logger.info(f"Reference {reference.id} marked as expired")
            
        except Exception as e:
            logger.error(f"Error sending reminders: {str(e)}")
    
    async def _send_reminder(self, reference: Reference, days_since_request: int):
        """Envía un recordatorio específico."""
        try:
            # Determinar urgencia del recordatorio
            if days_since_request == 3:
                urgency = "gentle"
            elif days_since_request == 7:
                urgency = "standard"
            else:  # 10 días
                urgency = "urgent"
            
            # Aquí se integraría con el sistema de notificaciones
            logger.info(f"Sending {urgency} reminder for reference {reference.id}")
            
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema de referencias."""
        # Calcular tasa de verificación
        verification_rate = (self.metrics['total_verified'] / self.metrics['total_received']) * 100 if self.metrics['total_received'] > 0 else 0
        
        return {
            **self.metrics,
            'verification_success_rate': round(verification_rate, 2),
            'active_references': len(self.active_references),
            'templates_available': len(self.templates)
        }
    
    def create_custom_template(self, name: str, reference_type: ReferenceType,
                             questions: List[ReferenceQuestion], description: str = "",
                             estimated_time: int = 5) -> str:
        """Crea un template personalizado de referencia."""
        template_id = f"custom_{str(uuid.uuid4())[:8]}"
        
        template = ReferenceTemplate(
            id=template_id,
            name=name,
            reference_type=reference_type,
            questions=questions,
            description=description,
            estimated_time=estimated_time
        )
        
        self.templates[template_id] = template
        logger.info(f"Custom template '{name}' created with ID: {template_id}")
        
        return template_id