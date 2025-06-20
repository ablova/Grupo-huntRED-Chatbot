"""
AURA - Advanced Conversational AI (FASE 1)
Sistema de IA conversacional avanzado para huntRED
"""

import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: DESHABILITADO POR DEFECTO
ENABLED = False  # Cambiar a True para habilitar


class ConversationContext(Enum):
    """Contextos de conversación"""
    RECRUITMENT = "recruitment"
    CAREER_GUIDANCE = "career_guidance"
    NETWORKING = "networking"
    SKILL_DEVELOPMENT = "skill_development"
    MARKET_INSIGHTS = "market_insights"
    GENERAL = "general"


class UserIntent(Enum):
    """Intenciones del usuario"""
    JOB_SEARCH = "job_search"
    CAREER_ADVICE = "career_advice"
    NETWORK_EXPANSION = "network_expansion"
    SKILL_IMPROVEMENT = "skill_improvement"
    MARKET_RESEARCH = "market_research"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    GENERAL_QUESTION = "general_question"


@dataclass
class ConversationSession:
    """Sesión de conversación"""
    session_id: str
    user_id: str
    start_time: datetime
    context: ConversationContext
    messages: List[Dict[str, Any]] = field(default_factory=list)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    conversation_flow: List[str] = field(default_factory=list)
    sentiment_history: List[float] = field(default_factory=list)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class AIResponse:
    """Respuesta de la IA"""
    message: str
    confidence: float
    intent: UserIntent
    context: ConversationContext
    suggested_actions: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    emotional_tone: str = "neutral"
    response_type: str = "text"  # text, quick_reply, card, action


class AdvancedConversationalAI:
    """
    Sistema de IA conversacional avanzado para Grupo huntRED
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("AdvancedConversationalAI: DESHABILITADO")
            return
        
        self.active_sessions = {}
        self.conversation_patterns = {}
        self.response_templates = {}
        self.user_profiles = {}
        
        # Configuración de IA
        self.ai_config = {
            "max_context_length": 10,
            "response_timeout": 30,
            "confidence_threshold": 0.7,
            "sentiment_analysis": True,
            "personalization": True,
            "learning_enabled": True
        }
        
        self._initialize_conversation_patterns()
        self._initialize_response_templates()
        logger.info("AdvancedConversationalAI: Inicializado")
    
    def _initialize_conversation_patterns(self):
        """Inicializa patrones de conversación"""
        if not self.enabled:
            return
        
        self.conversation_patterns = {
            UserIntent.JOB_SEARCH: {
                "keywords": ["trabajo", "empleo", "vacante", "oportunidad", "carrera", "buscar trabajo"],
                "context": ConversationContext.RECRUITMENT,
                "priority": 1
            },
            UserIntent.CAREER_ADVICE: {
                "keywords": ["consejo", "carrera", "desarrollo", "crecimiento", "profesional", "futuro"],
                "context": ConversationContext.CAREER_GUIDANCE,
                "priority": 2
            },
            UserIntent.NETWORK_EXPANSION: {
                "keywords": ["red", "networking", "conexiones", "contactos", "relaciones", "expandir"],
                "context": ConversationContext.NETWORKING,
                "priority": 3
            },
            UserIntent.SKILL_IMPROVEMENT: {
                "keywords": ["habilidades", "skills", "aprender", "mejorar", "desarrollo", "capacitación"],
                "context": ConversationContext.SKILL_DEVELOPMENT,
                "priority": 4
            },
            UserIntent.MARKET_RESEARCH: {
                "keywords": ["mercado", "tendencias", "salarios", "demanda", "industria", "sector"],
                "context": ConversationContext.MARKET_INSIGHTS,
                "priority": 5
            }
        }
    
    def _initialize_response_templates(self):
        """Inicializa plantillas de respuesta"""
        if not self.enabled:
            return
        
        self.response_templates = {
            ConversationContext.RECRUITMENT: {
                "greeting": "¡Hola! Soy tu asistente de huntRED®. Veo que estás interesado en oportunidades laborales. ¿En qué sector te gustaría explorar?",
                "job_search": "Perfecto, entiendo que buscas nuevas oportunidades. En huntRED® tenemos acceso a las mejores posiciones del mercado. ¿Podrías contarme un poco sobre tu experiencia y lo que buscas?",
                "follow_up": "Basándome en tu perfil, te sugiero revisar estas oportunidades. ¿Te gustaría que profundice en alguna en particular?"
            },
            ConversationContext.CAREER_GUIDANCE: {
                "greeting": "¡Excelente! Me encanta que quieras desarrollar tu carrera. En huntRED® creemos en el crecimiento profesional. ¿En qué aspecto te gustaría enfocarte?",
                "advice": "Basándome en tu trayectoria, te recomiendo considerar estas opciones de desarrollo. ¿Cuál te parece más interesante?",
                "follow_up": "¿Te gustaría que exploremos más a fondo alguna de estas opciones?"
            },
            ConversationContext.NETWORKING: {
                "greeting": "¡Genial! El networking es clave para el éxito profesional. En huntRED® tenemos una comunidad increíble. ¿Qué tipo de conexiones te interesan más?",
                "expansion": "Perfecto para expandir tu red. Te sugiero estos eventos y grupos profesionales. ¿Cuál te llama más la atención?",
                "follow_up": "¿Te gustaría que te conecte con algunos profesionales de tu sector?"
            },
            ConversationContext.SKILL_DEVELOPMENT: {
                "greeting": "¡Excelente decisión! El desarrollo de habilidades es fundamental. ¿En qué área te gustaría mejorar?",
                "improvement": "Basándome en las tendencias del mercado, estas habilidades están muy demandadas. ¿Cuál te interesa más?",
                "follow_up": "¿Te gustaría que te recomiende recursos específicos para desarrollar esta habilidad?"
            },
            ConversationContext.MARKET_INSIGHTS: {
                "greeting": "¡Perfecto! Mantenerse informado del mercado es crucial. ¿Qué sector te interesa más?",
                "insights": "Basándome en nuestros datos, estas son las tendencias actuales del mercado. ¿Te gustaría profundizar en algún aspecto?",
                "follow_up": "¿Te interesa recibir actualizaciones regulares sobre estas tendencias?"
            }
        }
    
    def start_conversation(self, user_id: str, initial_message: str = None) -> str:
        """
        Inicia una nueva conversación
        """
        if not self.enabled:
            return self._get_mock_session_id(user_id)
        
        try:
            session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
            
            # Detectar contexto inicial
            context = self._detect_conversation_context(initial_message) if initial_message else ConversationContext.GENERAL
            
            # Crear sesión
            session = ConversationSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(),
                context=context
            )
            
            # Cargar perfil del usuario si existe
            session.user_profile = self.user_profiles.get(user_id, {})
            
            self.active_sessions[session_id] = session
            
            logger.info(f"Conversation started: {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            return self._get_mock_session_id(user_id)
    
    def process_message(self, session_id: str, message: str, user_context: Dict[str, Any] = None) -> AIResponse:
        """
        Procesa un mensaje y genera respuesta
        """
        if not self.enabled:
            return self._get_mock_response(message)
        
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Actualizar sesión
            session.messages.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            session.last_activity = datetime.now()
            
            # Analizar mensaje
            intent = self._detect_user_intent(message)
            sentiment = self._analyze_sentiment(message)
            context = self._update_conversation_context(session, intent, message)
            
            # Generar respuesta
            response = self._generate_ai_response(session, intent, context, sentiment, user_context)
            
            # Guardar respuesta en sesión
            session.messages.append({
                "role": "assistant",
                "content": response.message,
                "timestamp": datetime.now().isoformat(),
                "intent": intent.value,
                "confidence": response.confidence
            })
            
            # Actualizar flujo de conversación
            session.conversation_flow.append(intent.value)
            session.sentiment_history.append(sentiment)
            
            # Aprender de la interacción
            if self.ai_config["learning_enabled"]:
                self._learn_from_interaction(session, intent, sentiment)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._get_mock_response(message)
    
    def _detect_user_intent(self, message: str) -> UserIntent:
        """Detecta la intención del usuario"""
        message_lower = message.lower()
        
        # Calcular scores para cada intención
        intent_scores = {}
        for intent, pattern in self.conversation_patterns.items():
            score = 0
            for keyword in pattern["keywords"]:
                if keyword in message_lower:
                    score += 1
            intent_scores[intent] = score
        
        # Retornar intención con mayor score
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[best_intent] > 0:
                return best_intent
        
        return UserIntent.GENERAL_QUESTION
    
    def _analyze_sentiment(self, message: str) -> float:
        """Analiza sentimiento del mensaje"""
        # Palabras positivas y negativas en español
        positive_words = ["excelente", "genial", "perfecto", "me gusta", "bueno", "interesante", "gracias"]
        negative_words = ["malo", "terrible", "horrible", "no me gusta", "problema", "difícil", "frustrado"]
        
        message_lower = message.lower()
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            return 0.7
        elif negative_count > positive_count:
            return -0.3
        else:
            return 0.0
    
    def _update_conversation_context(self, session: ConversationSession, intent: UserIntent, message: str) -> ConversationContext:
        """Actualiza contexto de conversación"""
        if intent in self.conversation_patterns:
            new_context = self.conversation_patterns[intent]["context"]
            if new_context != session.context:
                session.context = new_context
                logger.info(f"Context changed to: {new_context.value}")
        
        return session.context
    
    def _generate_ai_response(self, session: ConversationSession, intent: UserIntent, 
                            context: ConversationContext, sentiment: float, 
                            user_context: Dict[str, Any] = None) -> AIResponse:
        """Genera respuesta de IA"""
        
        # Obtener plantilla base
        templates = self.response_templates.get(context, {})
        
        # Personalizar respuesta basada en contexto
        if context == ConversationContext.RECRUITMENT:
            if intent == UserIntent.JOB_SEARCH:
                message = templates.get("job_search", "Entiendo que buscas oportunidades laborales. ¿En qué sector te gustaría explorar?")
            else:
                message = templates.get("greeting", "¡Hola! ¿En qué puedo ayudarte con tu búsqueda laboral?")
        
        elif context == ConversationContext.CAREER_GUIDANCE:
            if intent == UserIntent.CAREER_ADVICE:
                message = templates.get("advice", "Basándome en tu perfil, te recomiendo estas opciones de desarrollo profesional.")
            else:
                message = templates.get("greeting", "¡Excelente! ¿En qué aspecto de tu carrera te gustaría enfocarte?")
        
        elif context == ConversationContext.NETWORKING:
            if intent == UserIntent.NETWORK_EXPANSION:
                message = templates.get("expansion", "Te sugiero estos eventos y grupos para expandir tu red profesional.")
            else:
                message = templates.get("greeting", "¡Genial! ¿Qué tipo de conexiones profesionales te interesan?")
        
        elif context == ConversationContext.SKILL_DEVELOPMENT:
            if intent == UserIntent.SKILL_IMPROVEMENT:
                message = templates.get("improvement", "Estas habilidades están muy demandadas en el mercado actual.")
            else:
                message = templates.get("greeting", "¡Excelente decisión! ¿En qué área te gustaría mejorar?")
        
        elif context == ConversationContext.MARKET_INSIGHTS:
            if intent == UserIntent.MARKET_RESEARCH:
                message = templates.get("insights", "Basándome en nuestros datos, estas son las tendencias actuales del mercado.")
            else:
                message = templates.get("greeting", "¡Perfecto! ¿Qué sector del mercado te interesa más?")
        
        else:
            message = "¡Hola! Soy tu asistente de huntRED®. ¿En qué puedo ayudarte hoy?"
        
        # Personalizar basado en perfil del usuario
        if session.user_profile and self.ai_config["personalization"]:
            message = self._personalize_response(message, session.user_profile)
        
        # Generar acciones sugeridas
        suggested_actions = self._generate_suggested_actions(context, intent)
        
        # Generar preguntas de seguimiento
        follow_up_questions = self._generate_follow_up_questions(context, intent)
        
        # Determinar tono emocional
        emotional_tone = self._determine_emotional_tone(sentiment)
        
        return AIResponse(
            message=message,
            confidence=0.85,
            intent=intent,
            context=context,
            suggested_actions=suggested_actions,
            follow_up_questions=follow_up_questions,
            emotional_tone=emotional_tone
        )
    
    def _personalize_response(self, message: str, user_profile: Dict[str, Any]) -> str:
        """Personaliza respuesta basada en perfil del usuario"""
        # Agregar nombre si está disponible
        if user_profile.get("name"):
            message = f"¡Hola {user_profile['name']}! " + message
        
        # Agregar contexto específico del sector
        if user_profile.get("industry"):
            message += f" Veo que trabajas en {user_profile['industry']}, lo cual es muy relevante."
        
        return message
    
    def _generate_suggested_actions(self, context: ConversationContext, intent: UserIntent) -> List[str]:
        """Genera acciones sugeridas"""
        actions = {
            ConversationContext.RECRUITMENT: [
                "Ver oportunidades actuales",
                "Actualizar mi perfil",
                "Agendar consulta con recruiter",
                "Recibir alertas de empleo"
            ],
            ConversationContext.CAREER_GUIDANCE: [
                "Evaluación de carrera",
                "Plan de desarrollo",
                "Mentoría profesional",
                "Coaching ejecutivo"
            ],
            ConversationContext.NETWORKING: [
                "Eventos próximos",
                "Grupos profesionales",
                "Conectar con expertos",
                "Comunidad huntRED"
            ],
            ConversationContext.SKILL_DEVELOPMENT: [
                "Cursos recomendados",
                "Certificaciones",
                "Recursos de aprendizaje",
                "Evaluación de habilidades"
            ],
            ConversationContext.MARKET_INSIGHTS: [
                "Reporte de mercado",
                "Tendencias salariales",
                "Análisis de demanda",
                "Newsletter semanal"
            ]
        }
        
        return actions.get(context, ["Contactar soporte"])
    
    def _generate_follow_up_questions(self, context: ConversationContext, intent: UserIntent) -> List[str]:
        """Genera preguntas de seguimiento"""
        questions = {
            ConversationContext.RECRUITMENT: [
                "¿En qué sector específico te gustaría trabajar?",
                "¿Qué nivel de experiencia tienes?",
                "¿Prefieres trabajo remoto o presencial?",
                "¿Cuál es tu expectativa salarial?"
            ],
            ConversationContext.CAREER_GUIDANCE: [
                "¿Cuáles son tus objetivos profesionales a corto plazo?",
                "¿En qué área te gustaría crecer más?",
                "¿Qué te motiva en tu carrera?",
                "¿Qué desafíos enfrentas actualmente?"
            ],
            ConversationContext.NETWORKING: [
                "¿Qué tipo de profesionales te interesa conectar?",
                "¿En qué eventos te gustaría participar?",
                "¿Qué valor puedes aportar a la comunidad?",
                "¿Prefieres networking online o presencial?"
            ]
        }
        
        return questions.get(context, ["¿En qué más puedo ayudarte?"])
    
    def _determine_emotional_tone(self, sentiment: float) -> str:
        """Determina tono emocional basado en sentimiento"""
        if sentiment > 0.5:
            return "enthusiastic"
        elif sentiment > 0:
            return "positive"
        elif sentiment < -0.3:
            return "empathetic"
        else:
            return "neutral"
    
    def _learn_from_interaction(self, session: ConversationSession, intent: UserIntent, sentiment: float):
        """Aprende de la interacción para mejorar respuestas futuras"""
        # Actualizar perfil del usuario
        user_id = session.user_id
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        
        # Actualizar preferencias basadas en intención
        if intent not in self.user_profiles[user_id]:
            self.user_profiles[user_id][intent.value] = 0
        self.user_profiles[user_id][intent.value] += 1
        
        # Actualizar sentimiento promedio
        if "avg_sentiment" not in self.user_profiles[user_id]:
            self.user_profiles[user_id]["avg_sentiment"] = 0
        self.user_profiles[user_id]["avg_sentiment"] = (
            self.user_profiles[user_id]["avg_sentiment"] + sentiment
        ) / 2
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Obtiene historial de conversación"""
        if not self.enabled:
            return []
        
        session = self.active_sessions.get(session_id)
        if not session:
            return []
        
        return session.messages
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Obtiene insights del usuario basado en conversaciones"""
        if not self.enabled:
            return self._get_mock_user_insights(user_id)
        
        try:
            user_profile = self.user_profiles.get(user_id, {})
            
            # Analizar patrones de conversación
            user_sessions = [
                session for session in self.active_sessions.values()
                if session.user_id == user_id
            ]
            
            insights = {
                "user_id": user_id,
                "total_conversations": len(user_sessions),
                "preferred_contexts": {},
                "sentiment_trend": "neutral",
                "engagement_level": "medium",
                "recommendations": []
            }
            
            # Analizar contextos preferidos
            context_counts = {}
            for session in user_sessions:
                context = session.context.value
                context_counts[context] = context_counts.get(context, 0) + 1
            
            insights["preferred_contexts"] = context_counts
            
            # Analizar tendencia de sentimiento
            if user_profile.get("avg_sentiment"):
                avg_sentiment = user_profile["avg_sentiment"]
                if avg_sentiment > 0.3:
                    insights["sentiment_trend"] = "positive"
                elif avg_sentiment < -0.2:
                    insights["sentiment_trend"] = "negative"
            
            # Generar recomendaciones
            insights["recommendations"] = self._generate_user_recommendations(user_profile, context_counts)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting user insights: {e}")
            return self._get_mock_user_insights(user_id)
    
    def _generate_user_recommendations(self, user_profile: Dict[str, Any], 
                                     context_counts: Dict[str, int]) -> List[str]:
        """Genera recomendaciones personalizadas para el usuario"""
        recommendations = []
        
        # Basado en contextos más usados
        if context_counts.get("recruitment", 0) > 2:
            recommendations.append("Considerar actualizar tu perfil profesional")
            recommendations.append("Explorar oportunidades en tu sector")
        
        if context_counts.get("career_guidance", 0) > 2:
            recommendations.append("Agendar sesión de coaching profesional")
            recommendations.append("Crear plan de desarrollo de carrera")
        
        if context_counts.get("networking", 0) > 2:
            recommendations.append("Participar en eventos de networking")
            recommendations.append("Unirse a grupos profesionales")
        
        return recommendations
    
    def _detect_conversation_context(self, message: str) -> ConversationContext:
        """Detecta contexto inicial de conversación"""
        if not message:
            return ConversationContext.GENERAL
        
        intent = self._detect_user_intent(message)
        if intent in self.conversation_patterns:
            return self.conversation_patterns[intent]["context"]
        
        return ConversationContext.GENERAL
    
    def _get_mock_session_id(self, user_id: str) -> str:
        """ID de sesión simulado"""
        return f"mock_session_{user_id}_{int(datetime.now().timestamp())}"
    
    def _get_mock_response(self, message: str) -> AIResponse:
        """Respuesta simulada"""
        return AIResponse(
            message="¡Hola! Soy tu asistente de huntRED®. ¿En qué puedo ayudarte?",
            confidence=0.8,
            intent=UserIntent.GENERAL_QUESTION,
            context=ConversationContext.GENERAL,
            suggested_actions=["Ver oportunidades", "Contactar soporte"],
            follow_up_questions=["¿En qué sector te interesa trabajar?"]
        )
    
    def _get_mock_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Insights simulados"""
        return {
            "user_id": user_id,
            "total_conversations": 5,
            "preferred_contexts": {"recruitment": 3, "career_guidance": 2},
            "sentiment_trend": "positive",
            "engagement_level": "high",
            "recommendations": ["Actualizar perfil", "Explorar oportunidades"]
        }


# Instancia global del sistema conversacional
advanced_chatbot = AdvancedConversationalAI() 