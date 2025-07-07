"""
HuntRED® v2 - Complete Recruitment Chatbot System
Chatbot especializado para las 4 business units con IA avanzada
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import uuid
import re
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BusinessUnit(Enum):
    HUNTRED_EXECUTIVE = "huntred_executive"
    HUNTRED_GENERAL = "huntred_general"
    HUNTU = "huntu"
    AMIGRO = "amigro"

class ConversationState(Enum):
    GREETING = "greeting"
    PROFILE_COLLECTION = "profile_collection"
    SKILL_ASSESSMENT = "skill_assessment"
    POSITION_MATCHING = "position_matching"
    INTERVIEW_SCHEDULING = "interview_scheduling"
    DOCUMENT_COLLECTION = "document_collection"
    FOLLOW_UP = "follow_up"
    COMPLETED = "completed"

class CandidateProfile(Enum):
    EXECUTIVE = "executive"
    SENIOR_PROFESSIONAL = "senior_professional"
    MID_LEVEL = "mid_level"
    JUNIOR = "junior"
    STUDENT = "student"
    RECENT_GRADUATE = "recent_graduate"
    MIGRANT_NATIONAL = "migrant_national"
    MIGRANT_FOREIGN = "migrant_foreign"
    BASE_PYRAMID = "base_pyramid"

@dataclass
class CandidateData:
    """Datos completos del candidato"""
    candidate_id: str
    business_unit: BusinessUnit
    full_name: str
    email: str
    phone: str
    location: str
    experience_years: int
    education_level: str
    current_position: str
    desired_position: str
    salary_expectation: Optional[int]
    skills: List[str]
    languages: List[str]
    profile_type: CandidateProfile
    visa_status: Optional[str]
    availability: str
    preferred_contact: str
    conversation_state: ConversationState
    assessment_score: Optional[float]
    matched_positions: List[Dict[str, Any]]
    interview_scheduled: Optional[datetime]
    documents_uploaded: List[str]
    notes: List[str]
    created_at: datetime
    updated_at: datetime

class RecruitmentBotBase(ABC):
    """Base class para todos los chatbots de recruitment"""
    
    def __init__(self, business_unit: BusinessUnit, config: Dict[str, Any]):
        self.business_unit = business_unit
        self.config = config
        self.conversation_flows = self._initialize_conversation_flows()
        self.assessment_engine = self._initialize_assessment_engine()
    
    @abstractmethod
    def _initialize_conversation_flows(self) -> Dict[str, Any]:
        """Inicializa flujos de conversación específicos por BU"""
        pass
    
    @abstractmethod
    def _initialize_assessment_engine(self) -> Dict[str, Any]:
        """Inicializa engine de assessment específico por BU"""
        pass
    
    @abstractmethod
    async def _conduct_specialized_assessment(self, candidate: CandidateData) -> Dict[str, Any]:
        """Realiza assessment especializado según la BU"""
        pass

class HuntREDExecutiveBot(RecruitmentBotBase):
    """Chatbot especializado para posiciones C-level y senior management"""
    
    def _initialize_conversation_flows(self) -> Dict[str, Any]:
        return {
            "greeting": {
                "message": "👔 ¡Bienvenido a huntRED® Executive! Soy ALEX, su consultor especializado en posiciones de alta dirección.\n\n¿En qué tipo de posición ejecutiva está interesado?",
                "options": [
                    "CEO/President",
                    "CTO/VP Technology", 
                    "CFO/VP Finance",
                    "CMO/VP Marketing",
                    "CHRO/VP Human Resources",
                    "COO/VP Operations",
                    "Board Member",
                    "Otra posición ejecutiva"
                ],
                "next_state": "profile_collection"
            },
            "profile_collection": {
                "questions": [
                    "¿Cuántos años de experiencia ejecutiva tiene?",
                    "¿Cuál es el tamaño de presupuesto/equipo que ha manejado?",
                    "¿En qué industrias ha ejercido liderazgo?",
                    "¿Tiene experiencia internacional?",
                    "¿Qué idiomas domina a nivel ejecutivo?"
                ]
            },
            "executive_assessment": {
                "leadership_scenarios": [
                    "Cómo manejaría una crisis de 50M+ impacto",
                    "Estrategia para transformación digital organizacional",
                    "Manejo de stakeholders y board relations"
                ]
            }
        }
    
    def _initialize_assessment_engine(self) -> Dict[str, Any]:
        return {
            "leadership_competencies": [
                "strategic_vision",
                "decision_making", 
                "crisis_management",
                "stakeholder_management",
                "financial_acumen",
                "digital_transformation",
                "global_mindset",
                "board_interaction"
            ],
            "required_experience": {
                "min_years": 15,
                "budget_managed": 10000000,  # 10M+
                "team_size": 100,
                "industries": ["technology", "finance", "healthcare", "manufacturing"]
            }
        }
    
    async def _conduct_specialized_assessment(self, candidate: CandidateData) -> Dict[str, Any]:
        """Assessment específico para ejecutivos"""
        
        assessment_results = {
            "executive_readiness": 0.0,
            "leadership_score": 0.0,
            "strategic_thinking": 0.0,
            "industry_expertise": 0.0,
            "cultural_fit": 0.0,
            "compensation_range": {"min": 2000000, "max": 8000000},  # Executive range
            "recommendations": []
        }
        
        # Evaluar experiencia ejecutiva
        if candidate.experience_years >= 20:
            assessment_results["executive_readiness"] += 0.4
        elif candidate.experience_years >= 15:
            assessment_results["executive_readiness"] += 0.3
        
        # Evaluar liderazgo basado en respuestas
        leadership_indicators = [
            "board", "strategy", "transformation", "crisis", "m&a", 
            "stakeholder", "global", "vision", "ceo", "president"
        ]
        
        text_responses = " ".join(candidate.notes).lower()
        leadership_matches = sum(1 for indicator in leadership_indicators if indicator in text_responses)
        assessment_results["leadership_score"] = min(leadership_matches / len(leadership_indicators), 1.0)
        
        # Score final
        final_score = (
            assessment_results["executive_readiness"] * 0.4 +
            assessment_results["leadership_score"] * 0.3 +
            assessment_results["strategic_thinking"] * 0.2 +
            assessment_results["industry_expertise"] * 0.1
        )
        
        assessment_results["final_score"] = final_score
        
        # Recomendaciones
        if final_score >= 0.8:
            assessment_results["recommendations"] = [
                "Candidato PREMIUM para posiciones C-level",
                "Agendar entrevista con Managing Partner",
                "Considerar para posiciones de Board Member"
            ]
        elif final_score >= 0.6:
            assessment_results["recommendations"] = [
                "Candidato sólido para VP/SVP positions",
                "Potencial para growth hacia C-level",
                "Requerir assessment adicional"
            ]
        
        return assessment_results

class HuntREDGeneralBot(RecruitmentBotBase):
    """Chatbot para recruitment profesional general"""
    
    def _initialize_conversation_flows(self) -> Dict[str, Any]:
        return {
            "greeting": {
                "message": "🚀 ¡Hola! Soy SOPHIA de huntRED®, tu consultora especializada en posiciones profesionales.\n\n¿Qué tipo de oportunidad profesional buscas?",
                "options": [
                    "Technology & Engineering",
                    "Finance & Accounting", 
                    "Marketing & Sales",
                    "Operations & Supply Chain",
                    "Human Resources",
                    "Legal & Compliance",
                    "Project Management",
                    "Consulting"
                ],
                "next_state": "profile_collection"
            },
            "skill_assessment": {
                "technical_categories": [
                    "programming_languages",
                    "frameworks_tools",
                    "certifications", 
                    "project_experience",
                    "methodologies"
                ]
            }
        }
    
    def _initialize_assessment_engine(self) -> Dict[str, Any]:
        return {
            "skill_categories": {
                "technology": ["python", "java", "javascript", "sql", "aws", "docker"],
                "finance": ["excel", "sap", "financial_modeling", "cfa", "frm"],
                "marketing": ["digital_marketing", "analytics", "crm", "social_media"],
                "operations": ["lean", "six_sigma", "supply_chain", "logistics"]
            },
            "experience_levels": {
                "senior": {"min_years": 8, "salary_range": [800000, 2000000]},
                "mid": {"min_years": 4, "salary_range": [400000, 800000]},
                "junior": {"min_years": 1, "salary_range": [250000, 400000]}
            }
        }
    
    async def _conduct_specialized_assessment(self, candidate: CandidateData) -> Dict[str, Any]:
        """Assessment para profesionales generales"""
        
        assessment_results = {
            "technical_score": 0.0,
            "experience_score": 0.0, 
            "cultural_score": 0.0,
            "growth_potential": 0.0,
            "salary_range": {"min": 250000, "max": 500000},
            "matched_roles": [],
            "development_areas": []
        }
        
        # Evaluar skills técnicos
        relevant_skills = self.assessment_engine["skill_categories"].get("technology", [])
        skill_matches = len([skill for skill in candidate.skills if skill.lower() in relevant_skills])
        assessment_results["technical_score"] = min(skill_matches / len(relevant_skills), 1.0)
        
        # Evaluar experiencia
        exp_score = min(candidate.experience_years / 10, 1.0)
        assessment_results["experience_score"] = exp_score
        
        # Determinar nivel y salary range
        if candidate.experience_years >= 8:
            level = "senior"
            assessment_results["salary_range"] = {"min": 800000, "max": 2000000}
        elif candidate.experience_years >= 4:
            level = "mid"
            assessment_results["salary_range"] = {"min": 400000, "max": 800000}
        else:
            level = "junior"
            assessment_results["salary_range"] = {"min": 250000, "max": 400000}
        
        # Score final
        final_score = (
            assessment_results["technical_score"] * 0.4 +
            assessment_results["experience_score"] * 0.3 +
            assessment_results["cultural_score"] * 0.2 +
            assessment_results["growth_potential"] * 0.1
        )
        
        assessment_results["final_score"] = final_score
        
        return assessment_results

class HuntUBot(RecruitmentBotBase):
    """Chatbot especializado para estudiantes y recién graduados"""
    
    def _initialize_conversation_flows(self) -> Dict[str, Any]:
        return {
            "greeting": {
                "message": "🎓 ¡Hola! Soy MAYA de huntU, tu mentora especializada en oportunidades para estudiantes y recién graduados.\n\n¿En qué etapa de tu carrera estás?",
                "options": [
                    "Estudiante universitario (activo)",
                    "Recién graduado (< 1 año)",
                    "Graduado junior (1-2 años)",
                    "Buscando prácticas profesionales", 
                    "Primer empleo profesional",
                    "Cambio de carrera temprano"
                ],
                "next_state": "academic_profile"
            },
            "academic_profile": {
                "questions": [
                    "¿Qué carrera estudiaste/estudias?",
                    "¿En qué universidad?",
                    "¿Cuál es tu promedio académico?",
                    "¿Has realizado prácticas profesionales?",
                    "¿Tienes proyectos académicos destacados?"
                ]
            },
            "potential_assessment": {
                "categories": [
                    "academic_performance",
                    "practical_experience", 
                    "soft_skills",
                    "learning_agility",
                    "career_clarity"
                ]
            }
        }
    
    def _initialize_assessment_engine(self) -> Dict[str, Any]:
        return {
            "academic_factors": {
                "gpa_excellent": 9.0,
                "gpa_good": 8.0,
                "gpa_acceptable": 7.0
            },
            "entry_level_skills": {
                "technology": ["python", "javascript", "sql", "excel", "office"],
                "business": ["excel", "powerpoint", "project_management", "analytics"],
                "creative": ["adobe", "design", "content_creation", "social_media"]
            },
            "internship_value": 0.3,  # 30% boost for internship experience
            "salary_ranges": {
                "intern": {"min": 8000, "max": 15000},  # Monthly
                "entry": {"min": 180000, "max": 300000},  # Annual
                "junior": {"min": 250000, "max": 400000}  # Annual
            }
        }
    
    async def _conduct_specialized_assessment(self, candidate: CandidateData) -> Dict[str, Any]:
        """Assessment especializado para estudiantes/graduados"""
        
        assessment_results = {
            "academic_score": 0.0,
            "potential_score": 0.0,
            "readiness_score": 0.0,
            "learning_agility": 0.0,
            "recommended_path": "",
            "mentorship_areas": [],
            "salary_range": {"min": 180000, "max": 300000},
            "growth_timeline": "6-12 meses para primer promoción"
        }
        
        # Evaluar performance académico (simulado basado en notas)
        academic_keywords = ["excelente", "destacado", "9.", "8.", "honor", "cum laude"]
        academic_mentions = sum(1 for keyword in academic_keywords 
                              if any(keyword in note.lower() for note in candidate.notes))
        assessment_results["academic_score"] = min(academic_mentions / 3, 1.0)
        
        # Evaluar experiencia práctica
        practical_keywords = ["práctica", "internship", "proyecto", "freelance", "voluntario"]
        practical_experience = sum(1 for keyword in practical_keywords 
                                 if any(keyword in note.lower() for note in candidate.notes))
        assessment_results["readiness_score"] = min(practical_experience / 2, 1.0)
        
        # Evaluar potencial basado en skills técnicos
        relevant_skills = self.assessment_engine["entry_level_skills"].get("technology", [])
        skill_matches = len([skill for skill in candidate.skills if skill.lower() in relevant_skills])
        assessment_results["potential_score"] = min(skill_matches / 3, 1.0)
        
        # Determinar path recomendado
        if assessment_results["academic_score"] >= 0.8 and assessment_results["potential_score"] >= 0.6:
            assessment_results["recommended_path"] = "Fast-track Graduate Program"
            assessment_results["salary_range"] = {"min": 250000, "max": 400000}
        elif assessment_results["readiness_score"] >= 0.5:
            assessment_results["recommended_path"] = "Junior Professional Track"
            assessment_results["salary_range"] = {"min": 200000, "max": 320000}
        else:
            assessment_results["recommended_path"] = "Internship-to-Hire Program"
            assessment_results["salary_range"] = {"min": 12000, "max": 18000}  # Monthly internship
        
        # Áreas de mentoría
        if assessment_results["potential_score"] < 0.5:
            assessment_results["mentorship_areas"].append("Desarrollo de skills técnicos")
        if assessment_results["readiness_score"] < 0.5:
            assessment_results["mentorship_areas"].append("Experiencia práctica")
        
        assessment_results["mentorship_areas"].extend([
            "Networking profesional",
            "Preparación para entrevistas",
            "Planificación de carrera"
        ])
        
        final_score = (
            assessment_results["academic_score"] * 0.3 +
            assessment_results["potential_score"] * 0.4 +
            assessment_results["readiness_score"] * 0.3
        )
        
        assessment_results["final_score"] = final_score
        
        return assessment_results

class AmigroBot(RecruitmentBotBase):
    """Chatbot especializado para base de pirámide y migrantes"""
    
    def _initialize_conversation_flows(self) -> Dict[str, Any]:
        return {
            "greeting": {
                "message": "🤝 ¡Bienvenido a Amigro! Soy CARLOS, tu aliado para encontrar oportunidades laborales.\n\n¿Cuál describe mejor tu situación?",
                "options": [
                    "Mexicano regresando del extranjero",
                    "Extranjero buscando trabajo en México",
                    "Busco trabajo sin experiencia formal",
                    "Tengo skills pero sin certificar",
                    "Necesito trabajo inmediato",
                    "Quiero mejorar mi situación laboral"
                ],
                "next_state": "situation_assessment"
            },
            "situation_assessment": {
                "questions": [
                    "¿Tienes documentos en regla para trabajar?",
                    "¿Qué tipo de trabajo has hecho antes?", 
                    "¿Tienes algún skill especial?",
                    "¿Necesitas apoyo con documentación?",
                    "¿Qué tan urgente es encontrar trabajo?"
                ]
            },
            "skill_identification": {
                "categories": [
                    "manual_skills",
                    "service_skills", 
                    "basic_technical",
                    "language_skills",
                    "soft_skills"
                ]
            }
        }
    
    def _initialize_assessment_engine(self) -> Dict[str, Any]:
        return {
            "entry_opportunities": {
                "manufacturing": {"requirements": "basic", "salary": [180, 280]},  # Daily
                "services": {"requirements": "customer_service", "salary": [200, 350]},
                "construction": {"requirements": "physical", "salary": [250, 400]},
                "logistics": {"requirements": "organization", "salary": [220, 320]},
                "hospitality": {"requirements": "service_attitude", "salary": [180, 300]}
            },
            "skill_development": [
                "basic_computer_literacy",
                "spanish_improvement", 
                "customer_service",
                "safety_certifications",
                "basic_accounting"
            ],
            "support_services": [
                "document_assistance",
                "language_training",
                "skill_certification",
                "financial_planning",
                "legal_orientation"
            ]
        }
    
    async def _conduct_specialized_assessment(self, candidate: CandidateData) -> Dict[str, Any]:
        """Assessment especializado para base de pirámide y migrantes"""
        
        assessment_results = {
            "immediate_employability": 0.0,
            "skill_potential": 0.0,
            "adaptation_score": 0.0,
            "support_needed": [],
            "immediate_opportunities": [],
            "salary_range": {"min": 180, "max": 280, "period": "daily"},
            "development_plan": [],
            "urgency_level": "medium"
        }
        
        # Evaluar empleabilidad inmediata
        immediate_factors = ["documentos", "experiencia", "disponible", "urgente"]
        immediate_score = sum(1 for factor in immediate_factors 
                            if any(factor in note.lower() for note in candidate.notes))
        assessment_results["immediate_employability"] = min(immediate_score / 4, 1.0)
        
        # Evaluar potencial de skills
        skill_indicators = ["construcción", "cocina", "limpieza", "venta", "cuidado", "manejo"]
        skill_mentions = sum(1 for skill in skill_indicators 
                           if any(skill in note.lower() for note in candidate.notes))
        assessment_results["skill_potential"] = min(skill_mentions / 3, 1.0)
        
        # Determinar nivel de urgencia
        urgency_keywords = ["urgente", "inmediato", "necesito ya", "sin dinero"]
        if any(keyword in " ".join(candidate.notes).lower() for keyword in urgency_keywords):
            assessment_results["urgency_level"] = "high"
            assessment_results["immediate_opportunities"] = [
                "Trabajo de manufactura - inicio inmediato",
                "Servicios de limpieza - pago diario", 
                "Construcción - pago semanal",
                "Delivery/mensajería - pago diario"
            ]
        
        # Identificar soporte necesario
        if "documentos" in " ".join(candidate.notes).lower():
            assessment_results["support_needed"].append("Asistencia con documentación")
        if "idioma" in " ".join(candidate.notes).lower() or candidate.visa_status:
            assessment_results["support_needed"].append("Clases de español")
        
        assessment_results["support_needed"].extend([
            "Orientación laboral básica",
            "Apertura de cuenta bancaria",
            "Registro en seguridad social"
        ])
        
        # Plan de desarrollo
        assessment_results["development_plan"] = [
            "Mes 1-2: Estabilización laboral básica",
            "Mes 3-6: Desarrollo de skills específicos", 
            "Mes 6-12: Certificaciones y mejores oportunidades",
            "Año 2+: Promoción a posiciones de supervisor"
        ]
        
        # Ajustar salary range basado en skills y urgencia
        if assessment_results["skill_potential"] >= 0.7:
            assessment_results["salary_range"] = {"min": 250, "max": 400, "period": "daily"}
        elif assessment_results["urgency_level"] == "high":
            assessment_results["salary_range"] = {"min": 180, "max": 250, "period": "daily"}
        
        final_score = (
            assessment_results["immediate_employability"] * 0.5 +
            assessment_results["skill_potential"] * 0.3 +
            assessment_results["adaptation_score"] * 0.2
        )
        
        assessment_results["final_score"] = final_score
        
        return assessment_results

class RecruitmentChatbotManager:
    """Manager principal para todos los chatbots de recruitment"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bots = {
            BusinessUnit.HUNTRED_EXECUTIVE: HuntREDExecutiveBot(BusinessUnit.HUNTRED_EXECUTIVE, config),
            BusinessUnit.HUNTRED_GENERAL: HuntREDGeneralBot(BusinessUnit.HUNTRED_GENERAL, config),
            BusinessUnit.HUNTU: HuntUBot(BusinessUnit.HUNTU, config),
            BusinessUnit.AMIGRO: AmigroBot(BusinessUnit.AMIGRO, config)
        }
        self.active_conversations: Dict[str, CandidateData] = {}
    
    async def route_conversation(self, user_id: str, message: str, 
                               platform: str = "whatsapp") -> Dict[str, Any]:
        """Rutea la conversación al bot apropiado"""
        
        try:
            # Si no hay conversación activa, determinar business unit
            if user_id not in self.active_conversations:
                business_unit = await self._determine_business_unit(message)
                
                candidate = CandidateData(
                    candidate_id=str(uuid.uuid4()),
                    business_unit=business_unit,
                    full_name="",
                    email="",
                    phone=user_id,
                    location="",
                    experience_years=0,
                    education_level="",
                    current_position="",
                    desired_position="",
                    salary_expectation=None,
                    skills=[],
                    languages=[],
                    profile_type=CandidateProfile.JUNIOR,
                    visa_status=None,
                    availability="",
                    preferred_contact=platform,
                    conversation_state=ConversationState.GREETING,
                    assessment_score=None,
                    matched_positions=[],
                    interview_scheduled=None,
                    documents_uploaded=[],
                    notes=[message],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                self.active_conversations[user_id] = candidate
            else:
                candidate = self.active_conversations[user_id]
                candidate.notes.append(message)
                candidate.updated_at = datetime.now()
            
            # Procesar mensaje con el bot apropiado
            bot = self.bots[candidate.business_unit]
            response = await self._process_message_with_bot(bot, candidate, message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return {
                "success": False,
                "message": "Lo siento, ocurrió un error. Por favor intenta de nuevo.",
                "error": str(e)
            }
    
    async def _determine_business_unit(self, initial_message: str) -> BusinessUnit:
        """Determina la business unit apropiada basada en el mensaje inicial"""
        
        message_lower = initial_message.lower()
        
        # Keywords para cada business unit
        executive_keywords = [
            "ceo", "director", "gerente general", "ejecutivo", "c-level", 
            "presidente", "vicepresidente", "board", "consejo"
        ]
        
        student_keywords = [
            "estudiante", "universidad", "graduado", "recién", "primer empleo",
            "práctica", "internship", "carrera", "titulado"
        ]
        
        migrant_keywords = [
            "migrante", "extranjero", "regresé", "visa", "documentos",
            "sin experiencia", "trabajo inmediato", "urgente", "primer trabajo"
        ]
        
        # Verificar coincidencias
        if any(keyword in message_lower for keyword in executive_keywords):
            return BusinessUnit.HUNTRED_EXECUTIVE
        elif any(keyword in message_lower for keyword in student_keywords):
            return BusinessUnit.HUNTU
        elif any(keyword in message_lower for keyword in migrant_keywords):
            return BusinessUnit.AMIGRO
        else:
            return BusinessUnit.HUNTRED_GENERAL  # Default
    
    async def _process_message_with_bot(self, bot: RecruitmentBotBase, 
                                      candidate: CandidateData, 
                                      message: str) -> Dict[str, Any]:
        """Procesa mensaje con el bot específico"""
        
        current_state = candidate.conversation_state
        
        if current_state == ConversationState.GREETING:
            return await self._handle_greeting(bot, candidate, message)
        elif current_state == ConversationState.PROFILE_COLLECTION:
            return await self._handle_profile_collection(bot, candidate, message)
        elif current_state == ConversationState.SKILL_ASSESSMENT:
            return await self._handle_skill_assessment(bot, candidate, message)
        elif current_state == ConversationState.POSITION_MATCHING:
            return await self._handle_position_matching(bot, candidate, message)
        else:
            return await self._handle_general_conversation(bot, candidate, message)
    
    async def _handle_greeting(self, bot: RecruitmentBotBase, 
                             candidate: CandidateData, message: str) -> Dict[str, Any]:
        """Maneja el saludo inicial"""
        
        greeting_flow = bot.conversation_flows["greeting"]
        candidate.conversation_state = ConversationState.PROFILE_COLLECTION
        
        return {
            "success": True,
            "message": greeting_flow["message"],
            "options": greeting_flow.get("options", []),
            "next_action": "collect_profile"
        }
    
    async def _handle_profile_collection(self, bot: RecruitmentBotBase,
                                       candidate: CandidateData, message: str) -> Dict[str, Any]:
        """Maneja recolección de perfil"""
        
        # Extraer información del mensaje
        await self._extract_profile_info(candidate, message)
        
        # Determinar si hay suficiente información
        if self._has_sufficient_profile_info(candidate):
            candidate.conversation_state = ConversationState.SKILL_ASSESSMENT
            
            return {
                "success": True,
                "message": "Perfecto! Ahora vamos a evaluar tus habilidades. ¿Podrías contarme sobre tu experiencia y skills principales?",
                "next_action": "skill_assessment"
            }
        else:
            return {
                "success": True,
                "message": "Gracias por la información. ¿Podrías contarme un poco más sobre tu experiencia profesional?",
                "next_action": "continue_profile"
            }
    
    async def _handle_skill_assessment(self, bot: RecruitmentBotBase,
                                     candidate: CandidateData, message: str) -> Dict[str, Any]:
        """Maneja el assessment de skills"""
        
        # Extraer skills del mensaje
        skills = self._extract_skills_from_message(message)
        candidate.skills.extend(skills)
        
        # Realizar assessment especializado
        assessment_results = await bot._conduct_specialized_assessment(candidate)
        candidate.assessment_score = assessment_results["final_score"]
        candidate.conversation_state = ConversationState.POSITION_MATCHING
        
        # Generar respuesta personalizada
        response_message = self._generate_assessment_response(candidate.business_unit, assessment_results)
        
        return {
            "success": True,
            "message": response_message,
            "assessment_results": assessment_results,
            "next_action": "position_matching"
        }
    
    async def _handle_position_matching(self, bot: RecruitmentBotBase,
                                      candidate: CandidateData, message: str) -> Dict[str, Any]:
        """Maneja el matching de posiciones"""
        
        # Simular búsqueda de posiciones
        matched_positions = await self._find_matching_positions(candidate)
        candidate.matched_positions = matched_positions
        
        if matched_positions:
            positions_text = "\n".join([
                f"• {pos['title']} - {pos['company']} - {pos['salary_range']}"
                for pos in matched_positions[:3]
            ])
            
            message = f"¡Excelente! Encontré estas oportunidades que podrían interesarte:\n\n{positions_text}\n\n¿Te gustaría que programe una entrevista para alguna de estas posiciones?"
        else:
            message = "Estoy trabajando en encontrar las mejores oportunidades para ti. Te contactaré pronto con opciones personalizadas."
        
        candidate.conversation_state = ConversationState.INTERVIEW_SCHEDULING
        
        return {
            "success": True,
            "message": message,
            "matched_positions": matched_positions,
            "next_action": "schedule_interview"
        }
    
    async def _handle_general_conversation(self, bot: RecruitmentBotBase,
                                         candidate: CandidateData, message: str) -> Dict[str, Any]:
        """Maneja conversación general"""
        
        return {
            "success": True,
            "message": "Gracias por tu mensaje. ¿Hay algo específico en lo que pueda ayudarte con tu búsqueda laboral?",
            "next_action": "continue_conversation"
        }
    
    # Métodos auxiliares
    
    async def _extract_profile_info(self, candidate: CandidateData, message: str):
        """Extrae información del perfil del mensaje"""
        
        message_lower = message.lower()
        
        # Extraer años de experiencia
        exp_match = re.search(r'(\d+)\s*año', message_lower)
        if exp_match:
            candidate.experience_years = int(exp_match.group(1))
        
        # Extraer educación
        education_keywords = ["universidad", "licenciatura", "ingeniería", "maestría", "doctorado"]
        for keyword in education_keywords:
            if keyword in message_lower:
                candidate.education_level = keyword
                break
        
        # Extraer ubicación
        location_keywords = ["cdmx", "guadalajara", "monterrey", "méxico", "ciudad"]
        for keyword in location_keywords:
            if keyword in message_lower:
                candidate.location = keyword
                break
    
    def _has_sufficient_profile_info(self, candidate: CandidateData) -> bool:
        """Verifica si hay suficiente información del perfil"""
        
        return (
            len(candidate.notes) >= 2 and
            (candidate.experience_years > 0 or candidate.education_level)
        )
    
    def _extract_skills_from_message(self, message: str) -> List[str]:
        """Extrae skills del mensaje"""
        
        common_skills = [
            "python", "java", "javascript", "sql", "excel", "powerpoint",
            "marketing", "ventas", "liderazgo", "análisis", "gestión",
            "inglés", "comunicación", "trabajo en equipo"
        ]
        
        message_lower = message.lower()
        found_skills = [skill for skill in common_skills if skill in message_lower]
        
        return found_skills
    
    def _generate_assessment_response(self, business_unit: BusinessUnit, 
                                    assessment_results: Dict[str, Any]) -> str:
        """Genera respuesta personalizada del assessment"""
        
        score = assessment_results["final_score"]
        
        if business_unit == BusinessUnit.HUNTRED_EXECUTIVE:
            if score >= 0.8:
                return f"🌟 Excelente! Tu perfil ejecutivo es excepcional (score: {score:.1%}). Tienes el potencial para posiciones C-level de alto impacto."
            elif score >= 0.6:
                return f"👔 Muy buen perfil ejecutivo (score: {score:.1%}). Recomiendo posiciones VP/SVP como siguiente paso en tu carrera."
            else:
                return f"📈 Tu perfil tiene potencial (score: {score:.1%}). Te ayudo a desarrollar las competencias ejecutivas necesarias."
        
        elif business_unit == BusinessUnit.HUNTU:
            if score >= 0.7:
                return f"🚀 ¡Increíble! Tu potencial es muy alto (score: {score:.1%}). Te conectaré con los mejores graduate programs."
            else:
                return f"🎓 Buen perfil académico (score: {score:.1%}). Te ayudo a potenciar tus habilidades para mejores oportunidades."
        
        elif business_unit == BusinessUnit.AMIGRO:
            return f"🤝 He evaluado tu situación (score: {score:.1%}). Te voy a ayudar a encontrar oportunidades inmediatas y a desarrollar un plan de crecimiento."
        
        else:  # HUNTRED_GENERAL
            if score >= 0.7:
                return f"✨ Excelente perfil profesional (score: {score:.1%}). Tienes acceso a las mejores oportunidades del mercado."
            else:
                return f"💼 Buen perfil profesional (score: {score:.1%}). Te ayudo a optimizar tu búsqueda laboral."
    
    async def _find_matching_positions(self, candidate: CandidateData) -> List[Dict[str, Any]]:
        """Busca posiciones que coincidan con el candidato"""
        
        # Simulación de posiciones basada en business unit y assessment
        positions = []
        
        if candidate.business_unit == BusinessUnit.HUNTRED_EXECUTIVE:
            positions = [
                {
                    "title": "Chief Technology Officer",
                    "company": "TechCorp Internacional",
                    "salary_range": "$3,000,000 - $5,000,000 MXN",
                    "match_score": 0.9
                },
                {
                    "title": "VP of Operations",
                    "company": "Global Manufacturing",
                    "salary_range": "$2,500,000 - $4,000,000 MXN", 
                    "match_score": 0.85
                }
            ]
        
        elif candidate.business_unit == BusinessUnit.HUNTU:
            positions = [
                {
                    "title": "Graduate Trainee Program",
                    "company": "Banco Internacional",
                    "salary_range": "$250,000 - $350,000 MXN",
                    "match_score": 0.8
                },
                {
                    "title": "Junior Software Developer",
                    "company": "Startup Tech",
                    "salary_range": "$300,000 - $450,000 MXN",
                    "match_score": 0.75
                }
            ]
        
        elif candidate.business_unit == BusinessUnit.AMIGRO:
            positions = [
                {
                    "title": "Operador de Manufactura",
                    "company": "Planta Automotriz",
                    "salary_range": "$250 - $350 MXN/día",
                    "match_score": 0.9
                },
                {
                    "title": "Asistente de Almacén",
                    "company": "Centro Logístico",
                    "salary_range": "$220 - $300 MXN/día",
                    "match_score": 0.8
                }
            ]
        
        else:  # HUNTRED_GENERAL
            positions = [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Solutions",
                    "salary_range": "$800,000 - $1,200,000 MXN",
                    "match_score": 0.85
                },
                {
                    "title": "Marketing Manager",
                    "company": "Consumer Brand",
                    "salary_range": "$600,000 - $900,000 MXN",
                    "match_score": 0.8
                }
            ]
        
        return positions

# Factory function
def get_recruitment_chatbot_manager(config: Dict[str, Any]) -> RecruitmentChatbotManager:
    """Factory para el manager de chatbots de recruitment"""
    return RecruitmentChatbotManager(config)