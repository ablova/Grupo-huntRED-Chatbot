"""
NLP AVANZADO - Grupo huntRED®
Sistema de procesamiento de lenguaje natural con contexto persistente, análisis de sentimientos y corrección automática
"""

import logging
import json
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from textblob import TextBlob
import spacy
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

@dataclass
class NLPContext:
    """Contexto persistente para NLP"""
    user_id: str
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_intent: str = ""
    confidence_score: float = 0.0
    sentiment_history: List[float] = field(default_factory=list)
    entities: Dict[str, Any] = field(default_factory=dict)
    last_interaction: datetime = field(default_factory=timezone.now)
    context_window: int = 10

@dataclass
class IntentDetection:
    """Resultado de detección de intent"""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    context_relevant: bool
    suggested_response: str

@dataclass
class SentimentAnalysis:
    """Análisis de sentimientos"""
    polarity: float  # -1 a 1
    subjectivity: float  # 0 a 1
    emotion: str
    confidence: float
    keywords: List[str]

class AdvancedNLP:
    """
    Sistema NLP avanzado con múltiples capacidades
    """
    
    def __init__(self):
        # Cargar modelo spaCy
        try:
            self.nlp = spacy.load("es_core_news_sm")
            logger.info("✅ Modelo spaCy cargado exitosamente")
        except:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("✅ Modelo spaCy inglés cargado como fallback")
            except:
                logger.warning("⚠️ spaCy no disponible, usando procesamiento básico")
                self.nlp = None
        
        # Configuración
        self.context_cache = {}
        self.intent_patterns = self._load_intent_patterns()
        self.sentiment_models = self._initialize_sentiment_models()
        self.correction_rules = self._load_correction_rules()
        
        # Métricas
        self.metrics = {
            'intent_detections': 0,
            'sentiment_analyses': 0,
            'corrections_made': 0,
            'context_updates': 0,
            'avg_confidence': 0.0,
            'processing_time': 0.0
        }
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Carga patrones de intents"""
        return {
            'greeting': [
                r'\b(hola|buenos días|buenas tardes|buenas noches|saludos)\b',
                r'\b(hey|hi|hello|good morning|good afternoon|good evening)\b'
            ],
            'farewell': [
                r'\b(adiós|hasta luego|nos vemos|chao|bye|goodbye)\b',
                r'\b(see you|take care|have a good day)\b'
            ],
            'job_search': [
                r'\b(buscar trabajo|empleo|vacante|oportunidad laboral)\b',
                r'\b(job search|employment|vacancy|job opportunity)\b',
                r'\b(quiero trabajar|necesito trabajo|busco empleo)\b'
            ],
            'profile_update': [
                r'\b(actualizar perfil|modificar datos|cambiar información)\b',
                r'\b(update profile|modify data|change information)\b',
                r'\b(editar perfil|completar perfil|mejorar perfil)\b'
            ],
            'application_status': [
                r'\b(estado de aplicación|status|progreso)\b',
                r'\b(application status|progress|tracking)\b',
                r'\b(cómo va mi aplicación|dónde estoy)\b'
            ],
            'interview_schedule': [
                r'\b(entrevista|agendar|cita|programar)\b',
                r'\b(interview|schedule|appointment|book)\b',
                r'\b(cuándo es mi entrevista|confirmar entrevista)\b'
            ],
            'salary_question': [
                r'\b(salario|sueldo|remuneración|pago)\b',
                r'\b(salary|wage|compensation|payment)\b',
                r'\b(cuánto pagan|rango salarial|beneficios)\b'
            ],
            'help_request': [
                r'\b(ayuda|soporte|asistencia|problema)\b',
                r'\b(help|support|assistance|issue)\b',
                r'\b(no entiendo|confundido|perdido)\b'
            ]
        }
    
    def _initialize_sentiment_models(self) -> Dict[str, Any]:
        """Inicializa modelos de sentimientos"""
        return {
            'textblob': TextBlob,
            'custom_keywords': {
                'positive': ['excelente', 'genial', 'perfecto', 'fantástico', 'maravilloso', 'increíble'],
                'negative': ['terrible', 'horrible', 'pésimo', 'malo', 'frustrante', 'molesto'],
                'neutral': ['normal', 'regular', 'aceptable', 'bien', 'ok']
            }
        }
    
    def _load_correction_rules(self) -> Dict[str, str]:
        """Carga reglas de corrección automática"""
        return {
            'ke': 'que',
            'q': 'que',
            'xq': 'porque',
            'pq': 'porque',
            'tb': 'también',
            'tmb': 'también',
            'xfa': 'por favor',
            'pls': 'por favor',
            'plz': 'por favor',
            'grax': 'gracias',
            'grasias': 'gracias',
            'trabajo': 'trabajo',
            'trabajo': 'trabajo',
            'entrevista': 'entrevista',
            'entrevista': 'entrevista'
        }
    
    async def process_message(self, user_id: str, message: str, 
                            business_unit: str = None) -> Dict[str, Any]:
        """
        Procesa mensaje completo con todas las capacidades NLP
        """
        start_time = timezone.now()
        
        try:
            # Obtener contexto del usuario
            context = await self._get_user_context(user_id)
            
            # Corregir texto
            corrected_message = self._correct_text(message)
            
            # Detectar intent
            intent_result = await self._detect_intent(corrected_message, context)
            
            # Analizar sentimientos
            sentiment_result = await self._analyze_sentiment(corrected_message)
            
            # Extraer entidades
            entities = await self._extract_entities(corrected_message)
            
            # Actualizar contexto
            await self._update_context(user_id, context, corrected_message, 
                                     intent_result, sentiment_result, entities)
            
            # Calcular métricas
            processing_time = (timezone.now() - start_time).total_seconds()
            self._update_metrics(processing_time)
            
            return {
                'original_message': message,
                'corrected_message': corrected_message,
                'intent': intent_result,
                'sentiment': sentiment_result,
                'entities': entities,
                'context_updated': True,
                'processing_time': processing_time,
                'business_unit': business_unit
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje: {e}")
            return {
                'original_message': message,
                'error': str(e),
                'processing_time': 0.0
            }
    
    async def _get_user_context(self, user_id: str) -> NLPContext:
        """Obtiene contexto del usuario"""
        try:
            # Intentar obtener de cache
            cache_key = f"nlp_context:{user_id}"
            cached_context = cache.get(cache_key)
            
            if cached_context:
                return NLPContext(**cached_context)
            
            # Crear nuevo contexto
            context = NLPContext(user_id=user_id)
            cache.set(cache_key, context.__dict__, 3600)  # 1 hora
            return context
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo contexto: {e}")
            return NLPContext(user_id=user_id)
    
    def _correct_text(self, text: str) -> str:
        """Corrige texto automáticamente"""
        try:
            corrected = text.lower()
            
            # Aplicar reglas de corrección
            for wrong, correct in self.correction_rules.items():
                corrected = re.sub(r'\b' + wrong + r'\b', correct, corrected)
            
            # Corregir errores comunes
            corrected = re.sub(r'\bke\b', 'que', corrected)
            corrected = re.sub(r'\bq\b', 'que', corrected)
            corrected = re.sub(r'\bxq\b', 'porque', corrected)
            corrected = re.sub(r'\bpq\b', 'porque', corrected)
            
            # Capitalizar primera letra
            if corrected:
                corrected = corrected[0].upper() + corrected[1:]
            
            self.metrics['corrections_made'] += 1
            return corrected
            
        except Exception as e:
            logger.error(f"❌ Error corrigiendo texto: {e}")
            return text
    
    async def _detect_intent(self, message: str, context: NLPContext) -> IntentDetection:
        """Detecta intent con contexto"""
        try:
            best_intent = "unknown"
            best_confidence = 0.0
            detected_entities = {}
            
            # Detectar por patrones
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, message.lower())
                    if matches:
                        confidence = len(matches) / len(message.split())
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent
            
            # Usar spaCy si está disponible
            if self.nlp:
                doc = self.nlp(message)
                
                # Extraer entidades
                for ent in doc.ents:
                    detected_entities[ent.label_] = ent.text
                
                # Mejorar detección con spaCy
                if best_confidence < 0.3:
                    # Análisis más profundo
                    for token in doc:
                        if token.pos_ in ['VERB', 'NOUN']:
                            # Buscar intents basados en tokens
                            if token.lemma_ in ['buscar', 'encontrar', 'trabajo']:
                                best_intent = 'job_search'
                                best_confidence = max(best_confidence, 0.6)
                            elif token.lemma_ in ['actualizar', 'cambiar', 'modificar']:
                                best_intent = 'profile_update'
                                best_confidence = max(best_confidence, 0.6)
            
            # Considerar contexto histórico
            context_relevant = self._is_context_relevant(best_intent, context)
            
            # Generar respuesta sugerida
            suggested_response = self._generate_suggested_response(best_intent, context)
            
            self.metrics['intent_detections'] += 1
            
            return IntentDetection(
                intent=best_intent,
                confidence=min(best_confidence, 1.0),
                entities=detected_entities,
                context_relevant=context_relevant,
                suggested_response=suggested_response
            )
            
        except Exception as e:
            logger.error(f"❌ Error detectando intent: {e}")
            return IntentDetection(
                intent="unknown",
                confidence=0.0,
                entities={},
                context_relevant=False,
                suggested_response=""
            )
    
    async def _analyze_sentiment(self, message: str) -> SentimentAnalysis:
        """Analiza sentimientos con múltiples modelos"""
        try:
            # TextBlob
            blob = TextBlob(message)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Análisis por palabras clave
            keyword_score = self._analyze_keywords(message)
            
            # Combinar resultados
            final_polarity = (polarity + keyword_score) / 2
            
            # Determinar emoción
            emotion = self._classify_emotion(final_polarity, subjectivity)
            
            # Extraer palabras clave
            keywords = self._extract_sentiment_keywords(message)
            
            self.metrics['sentiment_analyses'] += 1
            
            return SentimentAnalysis(
                polarity=final_polarity,
                subjectivity=subjectivity,
                emotion=emotion,
                confidence=abs(final_polarity),
                keywords=keywords
            )
            
        except Exception as e:
            logger.error(f"❌ Error analizando sentimientos: {e}")
            return SentimentAnalysis(
                polarity=0.0,
                subjectivity=0.5,
                emotion="neutral",
                confidence=0.0,
                keywords=[]
            )
    
    def _analyze_keywords(self, message: str) -> float:
        """Analiza sentimientos por palabras clave"""
        try:
            message_lower = message.lower()
            score = 0.0
            total_words = len(message.split())
            
            if total_words == 0:
                return 0.0
            
            # Palabras positivas
            for word in self.sentiment_models['custom_keywords']['positive']:
                if word in message_lower:
                    score += 0.3
            
            # Palabras negativas
            for word in self.sentiment_models['custom_keywords']['negative']:
                if word in message_lower:
                    score -= 0.3
            
            return score / total_words
            
        except Exception as e:
            logger.error(f"❌ Error analizando keywords: {e}")
            return 0.0
    
    def _classify_emotion(self, polarity: float, subjectivity: float) -> str:
        """Clasifica emoción basada en polaridad y subjetividad"""
        if polarity > 0.3:
            if subjectivity > 0.6:
                return "excited"
            else:
                return "positive"
        elif polarity < -0.3:
            if subjectivity > 0.6:
                return "frustrated"
            else:
                return "negative"
        else:
            if subjectivity > 0.6:
                return "uncertain"
            else:
                return "neutral"
    
    def _extract_sentiment_keywords(self, message: str) -> List[str]:
        """Extrae palabras clave de sentimiento"""
        try:
            keywords = []
            message_lower = message.lower()
            
            # Buscar palabras de sentimiento
            all_sentiment_words = (
                self.sentiment_models['custom_keywords']['positive'] +
                self.sentiment_models['custom_keywords']['negative'] +
                self.sentiment_models['custom_keywords']['neutral']
            )
            
            for word in all_sentiment_words:
                if word in message_lower:
                    keywords.append(word)
            
            return keywords[:5]  # Máximo 5 palabras clave
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo keywords: {e}")
            return []
    
    async def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extrae entidades nombradas"""
        try:
            entities = {}
            
            if self.nlp:
                doc = self.nlp(message)
                
                for ent in doc.ents:
                    if ent.label_ not in entities:
                        entities[ent.label_] = []
                    entities[ent.label_].append(ent.text)
            
            # Extraer entidades específicas del dominio
            entities.update(self._extract_domain_entities(message))
            
            return entities
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo entidades: {e}")
            return {}
    
    def _extract_domain_entities(self, message: str) -> Dict[str, Any]:
        """Extrae entidades específicas del dominio de reclutamiento"""
        try:
            entities = {}
            message_lower = message.lower()
            
            # Fechas
            date_patterns = [
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',
                r'\b\d{1,2}-\d{1,2}-\d{4}\b',
                r'\b(mañana|hoy|ayer|próxima semana)\b'
            ]
            
            dates = []
            for pattern in date_patterns:
                dates.extend(re.findall(pattern, message_lower))
            
            if dates:
                entities['DATE'] = dates
            
            # Salarios
            salary_patterns = [
                r'\b\d{1,3}(?:,\d{3})*\s*(?:pesos|dólares|euros)\b',
                r'\b\$\d{1,3}(?:,\d{3})*\b'
            ]
            
            salaries = []
            for pattern in salary_patterns:
                salaries.extend(re.findall(pattern, message_lower))
            
            if salaries:
                entities['SALARY'] = salaries
            
            # Ubicaciones
            location_patterns = [
                r'\b(remoto|presencial|híbrido|home office)\b',
                r'\b(ciudad de méxico|cdmx|guadalajara|monterrey)\b'
            ]
            
            locations = []
            for pattern in location_patterns:
                locations.extend(re.findall(pattern, message_lower))
            
            if locations:
                entities['LOCATION'] = locations
            
            return entities
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo entidades del dominio: {e}")
            return {}
    
    def _is_context_relevant(self, intent: str, context: NLPContext) -> bool:
        """Determina si el intent es relevante al contexto"""
        try:
            if not context.conversation_history:
                return True
            
            # Verificar si el intent continúa la conversación
            last_intent = context.current_intent
            
            # Pares de intents relacionados
            related_intents = {
                'job_search': ['application_status', 'interview_schedule'],
                'profile_update': ['job_search', 'application_status'],
                'application_status': ['interview_schedule', 'salary_question'],
                'interview_schedule': ['salary_question', 'help_request']
            }
            
            if last_intent in related_intents:
                return intent in related_intents[last_intent]
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verificando relevancia de contexto: {e}")
            return True
    
    def _generate_suggested_response(self, intent: str, context: NLPContext) -> str:
        """Genera respuesta sugerida basada en intent y contexto"""
        try:
            responses = {
                'greeting': [
                    "¡Hola! Soy tu asistente de reclutamiento. ¿En qué puedo ayudarte hoy?",
                    "¡Bienvenido! ¿Estás buscando nuevas oportunidades laborales?"
                ],
                'job_search': [
                    "Perfecto, te ayudo a encontrar las mejores oportunidades. ¿Qué tipo de trabajo buscas?",
                    "Excelente decisión. ¿En qué área te gustaría trabajar?"
                ],
                'profile_update': [
                    "Claro, actualicemos tu perfil. ¿Qué información te gustaría modificar?",
                    "Perfecto para mejorar tus oportunidades. ¿Qué sección quieres actualizar?"
                ],
                'application_status': [
                    "Te ayudo a revisar el estado de tus aplicaciones. ¿A qué posición te refieres?",
                    "Claro, revisemos el progreso de tu aplicación. ¿Cuál es la empresa?"
                ],
                'interview_schedule': [
                    "Te ayudo con la programación de entrevistas. ¿Cuándo prefieres?",
                    "Perfecto, programemos tu entrevista. ¿Qué horario te funciona mejor?"
                ],
                'salary_question': [
                    "Te ayudo con información sobre salarios. ¿Qué rango buscas?",
                    "Claro, hablemos de remuneración. ¿Cuál es tu expectativa salarial?"
                ],
                'help_request': [
                    "No te preocupes, te ayudo. ¿Qué necesitas saber específicamente?",
                    "Estoy aquí para ayudarte. ¿En qué parte del proceso tienes dudas?"
                ],
                'farewell': [
                    "¡Ha sido un placer ayudarte! ¡Que tengas un excelente día!",
                    "¡Gracias por usar nuestro servicio! ¡Hasta pronto!"
                ]
            }
            
            intent_responses = responses.get(intent, ["Entiendo, ¿cómo puedo ayudarte?"])
            return np.random.choice(intent_responses)
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta sugerida: {e}")
            return "¿En qué puedo ayudarte?"
    
    async def _update_context(self, user_id: str, context: NLPContext, 
                            message: str, intent_result: IntentDetection,
                            sentiment_result: SentimentAnalysis, entities: Dict[str, Any]):
        """Actualiza contexto del usuario"""
        try:
            # Agregar mensaje al historial
            context.conversation_history.append({
                'message': message,
                'intent': intent_result.intent,
                'confidence': intent_result.confidence,
                'sentiment': sentiment_result.polarity,
                'timestamp': timezone.now().isoformat(),
                'entities': entities
            })
            
            # Mantener solo los últimos mensajes
            if len(context.conversation_history) > context.context_window:
                context.conversation_history = context.conversation_history[-context.context_window:]
            
            # Actualizar estado actual
            context.current_intent = intent_result.intent
            context.confidence_score = intent_result.confidence
            context.sentiment_history.append(sentiment_result.polarity)
            context.entities.update(entities)
            context.last_interaction = timezone.now()
            
            # Guardar en cache
            cache_key = f"nlp_context:{user_id}"
            cache.set(cache_key, context.__dict__, 3600)
            
            self.metrics['context_updates'] += 1
            
        except Exception as e:
            logger.error(f"❌ Error actualizando contexto: {e}")
    
    def _update_metrics(self, processing_time: float):
        """Actualiza métricas de rendimiento"""
        try:
            self.metrics['processing_time'] = (
                (self.metrics['processing_time'] + processing_time) / 2
            )
            
            # Actualizar confianza promedio
            total_detections = self.metrics['intent_detections']
            if total_detections > 0:
                self.metrics['avg_confidence'] = (
                    (self.metrics['avg_confidence'] * (total_detections - 1) + 0.8) / total_detections
                )
            
        except Exception as e:
            logger.error(f"❌ Error actualizando métricas: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema NLP"""
        try:
            return {
                'intent_detections': self.metrics['intent_detections'],
                'sentiment_analyses': self.metrics['sentiment_analyses'],
                'corrections_made': self.metrics['corrections_made'],
                'context_updates': self.metrics['context_updates'],
                'avg_confidence': round(self.metrics['avg_confidence'], 3),
                'avg_processing_time': round(self.metrics['processing_time'], 4),
                'spacy_available': self.nlp is not None,
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas NLP: {e}")
            return {}

# Instancia global
advanced_nlp = AdvancedNLP() 