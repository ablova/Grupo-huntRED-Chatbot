# app/ml/aura/chatbot/advanced_chatbot.py
"""
Implementación del chatbot avanzado para AURA.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import json

from app.ml.aura.core.ethics_engine import EthicsEngine
from app.ml.aura.core.bias_detection import BiasDetectionEngine
from app.ml.aura.truth.truth_analyzer import TruthAnalyzer

logger = logging.getLogger(__name__)

class AdvancedChatbot:
    """
    Chatbot avanzado con capacidades de procesamiento de lenguaje natural,
    detección de intenciones, y generación de respuestas contextuales.
    
    Integra componentes de AURA para proporcionar respuestas éticas,
    imparciales y verificadas.
    """
    
    def __init__(self, 
                 config: Optional[Dict[str, Any]] = None,
                 ethics_engine: Optional[EthicsEngine] = None,
                 bias_engine: Optional[BiasDetectionEngine] = None,
                 truth_analyzer: Optional[TruthAnalyzer] = None):
        """
        Inicializa el chatbot avanzado.
        
        Args:
            config: Configuración del chatbot
            ethics_engine: Motor de ética opcional
            bias_engine: Motor de detección de sesgos opcional
            truth_analyzer: Analizador de veracidad opcional
        """
        self.config = config or {}
        self.conversation_history = []
        self.context = {}
        self.language = self.config.get('language', 'es')
        self.ethics_engine = ethics_engine or EthicsEngine()
        self.bias_engine = bias_engine or BiasDetectionEngine()
        self.truth_analyzer = truth_analyzer or TruthAnalyzer()
        
        # Cargar modelos y recursos
        self._load_resources()
        
        logger.info("AdvancedChatbot inicializado correctamente")
    
    def _load_resources(self) -> None:
        """
        Carga los modelos y recursos necesarios para el chatbot.
        """
        try:
            # Implementación real cargaría modelos NLP, embeddings, etc.
            self.intent_model = None
            self.entity_model = None
            self.response_model = None
            
            # Cargar diccionarios de respuestas
            self.responses = self.config.get('responses', {})
            
            # Cargar configuración de idiomas
            self.language_config = self.config.get('languages', {})
            
            logger.debug("Recursos del chatbot cargados correctamente")
        except Exception as e:
            logger.error(f"Error al cargar recursos del chatbot: {str(e)}")
            # Fallback a configuración mínima
            self.responses = {}
            self.language_config = {}
    
    def process_message(self, 
                        message: str, 
                        user_id: str, 
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        
        Args:
            message: Mensaje del usuario
            user_id: Identificador del usuario
            context: Contexto adicional para la conversación
            
        Returns:
            Diccionario con la respuesta y metadatos
        """
        try:
            # Actualizar contexto
            self.context.update(context or {})
            
            # Guardar mensaje en el historial
            self.conversation_history.append({
                'user_id': user_id,
                'message': message,
                'timestamp': self.context.get('timestamp', None)
            })
            
            # Detectar intención
            intent, confidence = self._detect_intent(message)
            
            # Extraer entidades
            entities = self._extract_entities(message)
            
            # Verificar ética y sesgos
            ethics_result = self._check_ethics(message)
            
            # Generar respuesta
            response = self._generate_response(message, intent, entities)
            
            # Guardar respuesta en el historial
            self.conversation_history.append({
                'user_id': 'system',
                'message': response['text'],
                'timestamp': self.context.get('timestamp', None)
            })
            
            return {
                'text': response['text'],
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'ethics': ethics_result,
                'metadata': response.get('metadata', {})
            }
        
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {str(e)}")
            return {
                'text': "Lo siento, ha ocurrido un error al procesar tu mensaje.",
                'intent': 'error',
                'confidence': 0.0,
                'entities': [],
                'ethics': {},
                'metadata': {'error': str(e)}
            }
    
    def _detect_intent(self, message: str) -> Tuple[str, float]:
        """
        Detecta la intención del mensaje del usuario.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple con la intención detectada y el nivel de confianza
        """
        # Implementación simplificada
        # En una implementación real, se usaría un modelo de NLP
        
        message = message.lower()
        
        if 'ayuda' in message or 'help' in message:
            return 'help', 0.9
        elif 'gracias' in message or 'thank' in message:
            return 'thanks', 0.9
        elif 'hola' in message or 'hello' in message or 'hi' in message:
            return 'greeting', 0.9
        elif 'adiós' in message or 'bye' in message:
            return 'goodbye', 0.9
        else:
            return 'unknown', 0.5
    
    def _extract_entities(self, message: str) -> List[Dict[str, Any]]:
        """
        Extrae entidades del mensaje del usuario.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Lista de entidades detectadas
        """
        # Implementación simplificada
        # En una implementación real, se usaría un modelo de NER
        entities = []
        
        # Ejemplo de detección simple
        if 'mañana' in message.lower():
            entities.append({
                'type': 'time',
                'value': 'tomorrow',
                'text': 'mañana'
            })
            
        return entities
    
    def _check_ethics(self, message: str) -> Dict[str, Any]:
        """
        Verifica aspectos éticos del mensaje.
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Resultado del análisis ético
        """
        try:
            # Usar el motor de ética para analizar el mensaje
            ethics_result = self.ethics_engine.analyze_text(message)
            
            # Verificar sesgos
            bias_result = self.bias_engine.detect_bias(message)
            
            # Verificar veracidad (si aplica)
            truth_result = {}
            if self.truth_analyzer and any(claim in message.lower() for claim in ['es verdad', 'es cierto', 'es real']):
                truth_result = self.truth_analyzer.analyze(message)
            
            return {
                'ethics': ethics_result,
                'bias': bias_result,
                'truth': truth_result
            }
        except Exception as e:
            logger.warning(f"Error en verificación ética: {str(e)}")
            return {}
    
    def _generate_response(self, 
                          message: str, 
                          intent: str, 
                          entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera una respuesta basada en la intención y entidades.
        
        Args:
            message: Mensaje del usuario
            intent: Intención detectada
            entities: Entidades detectadas
            
        Returns:
            Respuesta generada con metadatos
        """
        # Implementación simplificada
        # En una implementación real, se usaría un modelo generativo
        
        # Buscar respuesta predefinida por intención
        if intent in self.responses:
            responses = self.responses[intent]
            if isinstance(responses, list) and responses:
                # Seleccionar una respuesta de la lista
                import random
                response_text = random.choice(responses)
            else:
                response_text = str(responses)
        else:
            # Respuesta por defecto
            response_text = "Entiendo tu mensaje. ¿En qué más puedo ayudarte?"
        
        # Personalizar la respuesta con entidades si es necesario
        for entity in entities:
            if entity['type'] == 'time' and entity['value'] == 'tomorrow':
                response_text += " ¿Necesitas programar algo para mañana?"
        
        return {
            'text': response_text,
            'metadata': {
                'intent': intent,
                'entities': [e['type'] for e in entities]
            }
        }
    
    def get_conversation_history(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de conversación.
        
        Args:
            user_id: ID de usuario opcional para filtrar
            
        Returns:
            Lista de mensajes en el historial
        """
        if user_id:
            return [msg for msg in self.conversation_history if msg['user_id'] == user_id]
        return self.conversation_history
    
    def clear_history(self, user_id: Optional[str] = None) -> None:
        """
        Limpia el historial de conversación.
        
        Args:
            user_id: ID de usuario opcional para filtrar
        """
        if user_id:
            self.conversation_history = [msg for msg in self.conversation_history if msg['user_id'] != user_id]
        else:
            self.conversation_history = []
    
    def set_language(self, language_code: str) -> bool:
        """
        Establece el idioma del chatbot.
        
        Args:
            language_code: Código de idioma (es, en, fr, etc.)
            
        Returns:
            True si el cambio fue exitoso, False en caso contrario
        """
        if language_code in self.language_config:
            self.language = language_code
            return True
        return False
    
    def get_supported_languages(self) -> List[str]:
        """
        Obtiene la lista de idiomas soportados.
        
        Returns:
            Lista de códigos de idioma soportados
        """
        return list(self.language_config.keys())
