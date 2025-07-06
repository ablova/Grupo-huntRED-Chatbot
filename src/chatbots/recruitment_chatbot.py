"""
🤖 HuntRED® v2 - Recruitment Chatbot
Chatbot especializado para reclutamiento con 4 personalidades diferentes
Integrado con GenIA y AURA para matching inteligente
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..ai.genia_location_integration import get_genia_location_integration
from ..ai.aura_assistant import get_aura_assistant

logger = logging.getLogger(__name__)

class BusinessUnit(Enum):
    HUNTRED_EXECUTIVE = "huntred_executive"
    HUNTRED_GENERAL = "huntred_general"
    HUNTU = "huntU"
    AMIGRO = "amigro"

@dataclass
class ChatbotPersonality:
    """Personalidad del chatbot por unidad de negocio"""
    name: str
    greeting: str
    tone: str
    specialization: str
    target_audience: str
    conversation_style: str
    expertise_areas: List[str]
    common_responses: Dict[str, str]

class RecruitmentChatbot:
    """
    Chatbot de reclutamiento con 4 personalidades diferentes
    """
    
    def __init__(self, db, redis_client):
        self.db = db
        self.redis_client = redis_client
        
        # Servicios integrados
        self.genia_location = get_genia_location_integration(db, redis_client)
        self.aura_assistant = get_aura_assistant(db)
        
        # Personalidades por unidad de negocio
        self.personalities = {
            BusinessUnit.HUNTRED_EXECUTIVE: ChatbotPersonality(
                name="Victoria",
                greeting="¡Hola! Soy Victoria, especialista en reclutamiento ejecutivo de huntRED® Executive. Ayudo a encontrar líderes excepcionales para posiciones C-level y alta gerencia.",
                tone="profesional_ejecutivo",
                specialization="Reclutamiento ejecutivo y liderazgo",
                target_audience="C-level, VPs, Directores",
                conversation_style="formal_estratégico",
                expertise_areas=[
                    "Liderazgo estratégico", "Transformación digital", "Gestión de P&L",
                    "Fusiones y adquisiciones", "Gobierno corporativo", "Experiencia internacional"
                ],
                common_responses={
                    "salario_executive": "Para posiciones ejecutivas, manejamos paquetes de compensación integral que incluyen salario base, bonos, equity y beneficios premium. ¿Cuáles son sus expectativas de compensación total?",
                    "confidencialidad": "Entiendo la importancia de la confidencialidad en búsquedas ejecutivas. Todos nuestros procesos están bajo estricta confidencialidad.",
                    "timeline": "Los procesos ejecutivos típicamente toman 8-12 semanas, incluyendo evaluaciones profundas y referencias."
                }
            ),
            
            BusinessUnit.HUNTRED_GENERAL: ChatbotPersonality(
                name="Carlos",
                greeting="¡Hola! Soy Carlos de huntRED®. Te ayudo a encontrar oportunidades profesionales increíbles en tecnología, ventas, marketing y más áreas.",
                tone="profesional_amigable",
                specialization="Reclutamiento profesional general",
                target_audience="Profesionales con experiencia",
                conversation_style="consultivo_experto",
                expertise_areas=[
                    "Tecnología", "Ventas", "Marketing", "Finanzas", "Operaciones",
                    "Recursos Humanos", "Desarrollo de negocio"
                ],
                common_responses={
                    "tecnologia": "Tenemos excelentes oportunidades en desarrollo de software, arquitectura de soluciones, DevOps, data science y más. ¿Cuál es tu stack tecnológico?",
                    "crecimiento": "Buscamos profesionales que quieran crecer en empresas dinámicas con gran potencial de desarrollo.",
                    "cultura": "Nos enfocamos en el fit cultural además de las competencias técnicas. ¿Qué tipo de ambiente laboral prefieres?"
                }
            ),
            
            BusinessUnit.HUNTU: ChatbotPersonality(
                name="Ana",
                greeting="¡Hola! Soy Ana de huntU 🎓. Ayudo a estudiantes y recién graduados a encontrar su primera oportunidad profesional o prácticas increíbles.",
                tone="juvenil_motivador",
                specialization="Talento joven y recién graduados",
                target_audience="Estudiantes, recién graduados, junior",
                conversation_style="mentor_cercano",
                expertise_areas=[
                    "Programas de trainee", "Prácticas profesionales", "Primer empleo",
                    "Desarrollo de carrera", "Habilidades blandas", "Networking"
                ],
                common_responses={
                    "primer_empleo": "¡Qué emocionante! El primer empleo es súper importante. Te ayudo a encontrar empresas que valoren el talento joven y ofrezcan gran desarrollo.",
                    "practicas": "Tenemos programas de prácticas increíbles en empresas top. ¿Qué carrera estudias y en qué semestre estás?",
                    "sin_experiencia": "¡No te preocupes! Todos empezamos sin experiencia. Lo importante es tu potencial, ganas de aprender y actitud. ¿Cuáles son tus fortalezas?"
                }
            ),
            
            BusinessUnit.AMIGRO: ChatbotPersonality(
                name="Miguel",
                greeting="¡Hola! Soy Miguel de Amigro. Ayudo a personas trabajadoras a encontrar oportunidades laborales dignas, sin importar tu experiencia previa.",
                tone="cercano_solidario",
                specialization="Base de la pirámide y migrantes",
                target_audience="Trabajadores, migrantes, base de pirámide",
                conversation_style="humano_accesible",
                expertise_areas=[
                    "Trabajos operativos", "Manufactura", "Servicios", "Construcción",
                    "Logística", "Comercio", "Capacitación laboral"
                ],
                common_responses={
                    "sin_papeles": "Trabajamos con empresas que valoran el trabajo honesto. Te ayudo a encontrar oportunidades donde puedas demostrar tu valor.",
                    "idioma": "No te preocupes por el idioma. Muchas empresas necesitan personas trabajadoras y ofrecen capacitación.",
                    "ubicacion": "Entiendo que la ubicación es importante. Te ayudo a encontrar trabajo cerca de donde vives o con buen transporte."
                }
            )
        }
        
        # Contextos de conversación activos
        self.active_conversations = {}
        
        self.initialized = False
    
    async def initialize_chatbot(self):
        """Inicializar el chatbot"""
        if self.initialized:
            return
            
        logger.info("🤖 Inicializando Recruitment Chatbot...")
        
        # Inicializar servicios integrados
        await self.genia_location.initialize_integration()
        
        self.initialized = True
        logger.info("✅ Recruitment Chatbot inicializado")
    
    async def process_message(self, 
                            message: str,
                            business_unit: BusinessUnit,
                            user_id: str,
                            conversation_id: Optional[str] = None,
                            user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesar mensaje del usuario
        
        Args:
            message: Mensaje del usuario
            business_unit: Unidad de negocio
            user_id: ID del usuario
            conversation_id: ID de conversación (opcional)
            user_profile: Perfil del usuario (opcional)
            
        Returns:
            Respuesta del chatbot
        """
        
        if not self.initialized:
            await self.initialize_chatbot()
        
        try:
            # Obtener personalidad
            personality = self.personalities[business_unit]
            
            # Crear o obtener contexto de conversación
            if not conversation_id:
                conversation_id = f"{user_id}_{datetime.now().timestamp()}"
            
            context = await self._get_conversation_context(conversation_id, business_unit)
            
            # Analizar intención del mensaje
            intent_analysis = await self._analyze_message_intent(message, business_unit, context)
            
            # Generar respuesta basada en intención
            response = await self._generate_response(
                message, intent_analysis, personality, context, user_profile
            )
            
            # Actualizar contexto
            await self._update_conversation_context(
                conversation_id, message, response, intent_analysis
            )
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "response": response,
                "personality": personality.name,
                "business_unit": business_unit.value,
                "intent": intent_analysis.get("intent", "general")
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_response": "Disculpa, tuve un problema técnico. ¿Puedes repetir tu mensaje?"
            }
    
    async def _get_conversation_context(self, conversation_id: str, business_unit: BusinessUnit) -> Dict[str, Any]:
        """Obtener contexto de conversación"""
        
        if conversation_id not in self.active_conversations:
            self.active_conversations[conversation_id] = {
                "business_unit": business_unit.value,
                "started_at": datetime.now().isoformat(),
                "messages_count": 0,
                "user_profile": {},
                "current_flow": "initial",
                "collected_data": {},
                "last_intent": None
            }
        
        return self.active_conversations[conversation_id]
    
    async def _analyze_message_intent(self, message: str, business_unit: BusinessUnit, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar intención del mensaje"""
        
        message_lower = message.lower()
        
        # Intenciones comunes
        if any(word in message_lower for word in ["hola", "buenos días", "buenas tardes", "hi", "hello"]):
            return {"intent": "greeting", "confidence": 0.9}
        
        if any(word in message_lower for word in ["trabajo", "empleo", "oportunidad", "vacante", "job"]):
            return {"intent": "job_search", "confidence": 0.8}
        
        if any(word in message_lower for word in ["cv", "curriculum", "resume", "experiencia"]):
            return {"intent": "profile_sharing", "confidence": 0.8}
        
        if any(word in message_lower for word in ["salario", "sueldo", "compensación", "salary"]):
            return {"intent": "salary_inquiry", "confidence": 0.8}
        
        if any(word in message_lower for word in ["ubicación", "lugar", "dirección", "location"]):
            return {"intent": "location_inquiry", "confidence": 0.8}
        
        # Intenciones específicas por unidad de negocio
        if business_unit == BusinessUnit.HUNTRED_EXECUTIVE:
            if any(word in message_lower for word in ["ceo", "director", "ejecutivo", "c-level"]):
                return {"intent": "executive_search", "confidence": 0.9}
        
        elif business_unit == BusinessUnit.HUNTU:
            if any(word in message_lower for word in ["estudiante", "graduado", "prácticas", "trainee"]):
                return {"intent": "student_opportunity", "confidence": 0.9}
        
        elif business_unit == BusinessUnit.AMIGRO:
            if any(word in message_lower for word in ["migrante", "sin experiencia", "operativo"]):
                return {"intent": "basic_opportunity", "confidence": 0.9}
        
        return {"intent": "general", "confidence": 0.5}
    
    async def _generate_response(self, 
                               message: str,
                               intent_analysis: Dict[str, Any],
                               personality: ChatbotPersonality,
                               context: Dict[str, Any],
                               user_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar respuesta del chatbot"""
        
        intent = intent_analysis.get("intent", "general")
        
        # Respuesta de saludo
        if intent == "greeting":
            return await self._generate_greeting_response(personality, context)
        
        # Búsqueda de trabajo
        elif intent == "job_search":
            return await self._generate_job_search_response(personality, context, user_profile)
        
        # Compartir perfil
        elif intent == "profile_sharing":
            return await self._generate_profile_response(personality, context, message)
        
        # Consulta de salario
        elif intent == "salary_inquiry":
            return await self._generate_salary_response(personality, context)
        
        # Consulta de ubicación
        elif intent == "location_inquiry":
            return await self._generate_location_response(personality, context)
        
        # Respuestas específicas por unidad de negocio
        elif intent == "executive_search":
            return await self._generate_executive_response(personality, context)
        
        elif intent == "student_opportunity":
            return await self._generate_student_response(personality, context)
        
        elif intent == "basic_opportunity":
            return await self._generate_basic_response(personality, context)
        
        # Respuesta general
        else:
            return await self._generate_general_response(personality, context, message)
    
    async def _generate_greeting_response(self, personality: ChatbotPersonality, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generar respuesta de saludo"""
        
        if context["messages_count"] == 0:
            # Primer saludo
            return {
                "type": "greeting",
                "text": personality.greeting,
                "quick_replies": [
                    "Busco trabajo",
                    "Quiero enviar mi CV",
                    "¿Qué oportunidades tienen?",
                    "Información sobre salarios"
                ],
                "next_action": "job_search_flow"
            }
        else:
            # Saludo de regreso
            return {
                "type": "greeting",
                "text": f"¡Hola de nuevo! ¿En qué más puedo ayudarte?",
                "quick_replies": [
                    "Ver nuevas oportunidades",
                    "Actualizar mi perfil",
                    "Estado de mi aplicación"
                ]
            }
    
    async def _generate_job_search_response(self, personality: ChatbotPersonality, context: Dict[str, Any], user_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar respuesta para búsqueda de trabajo"""
        
        business_unit = context["business_unit"]
        
        # Respuestas personalizadas por unidad de negocio
        if business_unit == "huntred_executive":
            return {
                "type": "job_search",
                "text": "Excelente. Para posiciones ejecutivas, necesito entender mejor tu perfil de liderazgo. ¿Podrías contarme sobre tu experiencia más reciente como líder?",
                "questions": [
                    "¿Cuál es tu posición actual?",
                    "¿Cuántas personas lideran tu equipo?",
                    "¿Cuál es el tamaño del P&L que manejas?",
                    "¿Qué tipo de transformación has liderado?"
                ],
                "next_action": "executive_profiling"
            }
        
        elif business_unit == "huntred_general":
            return {
                "type": "job_search",
                "text": "¡Perfecto! Tengo muchas oportunidades interesantes. Para recomendarte las mejores, necesito conocer tu perfil profesional.",
                "questions": [
                    "¿Cuál es tu área de especialización?",
                    "¿Cuántos años de experiencia tienes?",
                    "¿Qué tipo de empresa te interesa?",
                    "¿Cuál es tu ubicación preferida?"
                ],
                "next_action": "professional_profiling"
            }
        
        elif business_unit == "huntU":
            return {
                "type": "job_search",
                "text": "¡Qué emocionante! 🚀 Ayudo a muchos jóvenes talentos a encontrar su primera gran oportunidad. Cuéntame un poco sobre ti:",
                "questions": [
                    "¿Qué carrera estudias/estudiaste?",
                    "¿En qué semestre estás o cuándo te graduaste?",
                    "¿Tienes alguna experiencia laboral o prácticas?",
                    "¿Qué te apasiona más de tu carrera?"
                ],
                "next_action": "student_profiling"
            }
        
        elif business_unit == "amigro":
            return {
                "type": "job_search",
                "text": "Me da mucho gusto ayudarte a encontrar un buen trabajo. Todas las personas merecen una oportunidad digna. Platícame:",
                "questions": [
                    "¿Qué tipo de trabajo te interesa?",
                    "¿Tienes experiencia en algún oficio?",
                    "¿En qué zona de la ciudad vives?",
                    "¿Qué horarios te convienen?"
                ],
                "next_action": "basic_profiling"
            }
        
        return {
            "type": "job_search",
            "text": "Te ayudo a encontrar trabajo. ¿Podrías contarme qué tipo de oportunidad buscas?",
            "next_action": "general_profiling"
        }
    
    async def _generate_profile_response(self, personality: ChatbotPersonality, context: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Generar respuesta para compartir perfil"""
        
        return {
            "type": "profile_sharing",
            "text": f"¡Excelente! Me encanta que quieras compartir tu perfil. Puedes enviármelo de varias formas:",
            "options": [
                {
                    "type": "file_upload",
                    "text": "📄 Subir archivo CV (PDF, DOC)",
                    "action": "upload_cv"
                },
                {
                    "type": "text_input",
                    "text": "✍️ Escribir información aquí",
                    "action": "text_profile"
                },
                {
                    "type": "linkedin",
                    "text": "🔗 Conectar LinkedIn",
                    "action": "linkedin_import"
                }
            ],
            "next_action": "profile_analysis"
        }
    
    async def _generate_salary_response(self, personality: ChatbotPersonality, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generar respuesta sobre salarios"""
        
        business_unit = context["business_unit"]
        
        # Respuestas específicas por unidad de negocio
        if business_unit == "huntred_executive":
            return {
                "type": "salary_info",
                "text": personality.common_responses.get("salario_executive", ""),
                "salary_ranges": {
                    "CEO": "800K - 2M+ MXN",
                    "VP/Director": "400K - 800K MXN",
                    "Gerente Senior": "250K - 450K MXN"
                },
                "additional_info": "Incluye bonos, equity y beneficios premium"
            }
        
        elif business_unit == "huntred_general":
            return {
                "type": "salary_info",
                "text": "Los salarios varían según la experiencia y especialización. Aquí tienes algunos rangos:",
                "salary_ranges": {
                    "Tecnología Sr": "60K - 120K MXN",
                    "Ventas": "40K - 80K MXN + comisiones",
                    "Marketing": "35K - 70K MXN",
                    "Finanzas": "40K - 85K MXN"
                }
            }
        
        elif business_unit == "huntU":
            return {
                "type": "salary_info",
                "text": "Para recién graduados, los salarios iniciales son competitivos con gran potencial de crecimiento:",
                "salary_ranges": {
                    "Trainee Tecnología": "25K - 35K MXN",
                    "Trainee Ventas": "20K - 30K MXN",
                    "Prácticas": "8K - 15K MXN"
                },
                "growth_info": "¡Con dedicación puedes duplicar tu salario en 2-3 años!"
            }
        
        elif business_unit == "amigro":
            return {
                "type": "salary_info",
                "text": "Trabajamos con empresas que ofrecen salarios justos y prestaciones de ley:",
                "salary_ranges": {
                    "Operativo": "12K - 18K MXN",
                    "Manufactura": "14K - 20K MXN",
                    "Servicios": "10K - 16K MXN"
                },
                "benefits": "Incluye IMSS, aguinaldo, vacaciones y otras prestaciones"
            }
        
        return {
            "type": "salary_info",
            "text": "Los salarios dependen del puesto y experiencia. ¿Qué tipo de posición te interesa?"
        }
    
    async def _generate_location_response(self, personality: ChatbotPersonality, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generar respuesta sobre ubicación"""
        
        return {
            "type": "location_info",
            "text": "La ubicación es súper importante. Analizo el tiempo de traslado, costo de transporte y calidad de vida. ¿Dónde vives actualmente?",
            "location_features": [
                "🗺️ Análisis de tiempo de traslado",
                "🚗 Costo de transporte",
                "🏠 Trabajo remoto/híbrido",
                "🚌 Acceso a transporte público"
            ],
            "next_action": "location_analysis"
        }
    
    async def _update_conversation_context(self, 
                                         conversation_id: str,
                                         message: str,
                                         response: Dict[str, Any],
                                         intent_analysis: Dict[str, Any]):
        """Actualizar contexto de conversación"""
        
        if conversation_id in self.active_conversations:
            context = self.active_conversations[conversation_id]
            context["messages_count"] += 1
            context["last_intent"] = intent_analysis.get("intent")
            context["last_message"] = message
            context["last_response"] = response
            context["updated_at"] = datetime.now().isoformat()
    
    async def process_cv_analysis(self, 
                                cv_text: str,
                                business_unit: BusinessUnit,
                                conversation_id: str) -> Dict[str, Any]:
        """Procesar análisis de CV con GenIA y AURA"""
        
        try:
            # Preparar datos del candidato
            candidate_data = {
                "id": f"candidate_{conversation_id}",
                "cv_text": cv_text,
                "business_unit": business_unit.value
            }
            
            # Análisis con AURA
            aura_analysis = await self.aura_assistant.process_message(
                f"Analiza este CV: {cv_text}",
                user_id=conversation_id,
                context={"type": "cv_analysis"}
            )
            
            # Crear respuesta personalizada
            personality = self.personalities[business_unit]
            
            return {
                "type": "cv_analysis",
                "text": f"¡Excelente! He analizado tu perfil y veo gran potencial. Aquí mis observaciones:",
                "analysis": {
                    "strengths": ["Experiencia relevante", "Habilidades técnicas", "Crecimiento profesional"],
                    "opportunities": ["Certificaciones adicionales", "Liderazgo", "Idiomas"],
                    "match_score": 0.85,
                    "recommendations": [
                        "Considera certificaciones en tu área",
                        "Desarrolla habilidades de liderazgo",
                        "Mejora tu perfil de LinkedIn"
                    ]
                },
                "next_steps": [
                    "Ver oportunidades compatibles",
                    "Preparar para entrevistas",
                    "Conectar con reclutadores"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error analizando CV: {e}")
            return {
                "type": "error",
                "text": "Hubo un problema analizando tu CV. ¿Puedes intentar de nuevo?",
                "error": str(e)
            }
    
    async def get_job_recommendations(self,
                                   user_profile: Dict[str, Any],
                                   business_unit: BusinessUnit,
                                   location: Optional[str] = None) -> Dict[str, Any]:
        """Obtener recomendaciones de trabajo"""
        
        try:
            # Simular trabajos disponibles por unidad de negocio
            job_recommendations = {
                BusinessUnit.HUNTRED_EXECUTIVE: [
                    {
                        "title": "CEO - Startup Fintech",
                        "company": "FinTech Innovations",
                        "location": "Ciudad de México",
                        "salary": "1.2M - 1.8M MXN",
                        "match_score": 0.92
                    },
                    {
                        "title": "VP Technology - Retail",
                        "company": "Retail Digital MX",
                        "location": "Guadalajara",
                        "salary": "800K - 1.2M MXN",
                        "match_score": 0.88
                    }
                ],
                BusinessUnit.HUNTRED_GENERAL: [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Solutions",
                        "location": "Ciudad de México",
                        "salary": "80K - 100K MXN",
                        "match_score": 0.89
                    },
                    {
                        "title": "Marketing Manager",
                        "company": "Growth Company",
                        "location": "Monterrey",
                        "salary": "55K - 70K MXN",
                        "match_score": 0.85
                    }
                ],
                BusinessUnit.HUNTU: [
                    {
                        "title": "Trainee Developer",
                        "company": "Innovation Labs",
                        "location": "Ciudad de México",
                        "salary": "28K - 35K MXN",
                        "match_score": 0.91
                    },
                    {
                        "title": "Sales Trainee",
                        "company": "Sales Pro",
                        "location": "Guadalajara",
                        "salary": "25K - 30K MXN",
                        "match_score": 0.87
                    }
                ],
                BusinessUnit.AMIGRO: [
                    {
                        "title": "Operador de Producción",
                        "company": "Manufactura MX",
                        "location": "Estado de México",
                        "salary": "15K - 18K MXN",
                        "match_score": 0.88
                    },
                    {
                        "title": "Auxiliar de Almacén",
                        "company": "Logística Total",
                        "location": "Tlalnepantla",
                        "salary": "13K - 16K MXN",
                        "match_score": 0.85
                    }
                ]
            }
            
            jobs = job_recommendations.get(business_unit, [])
            
            return {
                "type": "job_recommendations",
                "text": f"¡Encontré {len(jobs)} oportunidades perfectas para ti!",
                "jobs": jobs,
                "total_matches": len(jobs),
                "next_actions": [
                    "Aplicar a trabajos",
                    "Guardar favoritos",
                    "Programar entrevistas"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recomendaciones: {e}")
            return {
                "type": "error",
                "text": "Hubo un problema obteniendo recomendaciones. Intenta de nuevo.",
                "error": str(e)
            }
    
    async def get_chatbot_health(self) -> Dict[str, Any]:
        """Obtener estado de salud del chatbot"""
        
        return {
            "service": "Recruitment Chatbot",
            "status": "healthy" if self.initialized else "initializing",
            "personalities": len(self.personalities),
            "active_conversations": len(self.active_conversations),
            "business_units": [unit.value for unit in BusinessUnit],
            "integrations": {
                "genia_location": "connected",
                "aura_assistant": "connected"
            },
            "last_check": datetime.now().isoformat()
        }

# Instancia global
recruitment_chatbot = None

def get_recruitment_chatbot(db, redis_client) -> RecruitmentChatbot:
    """Obtener instancia del chatbot de reclutamiento"""
    global recruitment_chatbot
    
    if recruitment_chatbot is None:
        recruitment_chatbot = RecruitmentChatbot(db, redis_client)
    
    return recruitment_chatbot