from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from app.models import (
    Person, BusinessUnit, ChatState, IntentPattern,
    StateTransition, IntentTransition, ContextCondition
)
from app.chatbot.utils import analyze_text, get_nlp_processor
import asyncio
import logging

logger = logging.getLogger(__name__)

class ChatStateManager:
    """Manejador de estados de chat para el chatbot."""
    
    def __init__(self, user: Person, business_unit: BusinessUnit):
        self.user = user
        self.business_unit = business_unit
        self.current_state = None
        self.last_intent = None
        self.conversation_history = []
        self.context = {}
        
    async def initialize(self):
        """Inicializa el estado del chat para un usuario."""
        try:
            # Obtener o crear el estado del chat
            chat_state, created = await ChatState.objects.aget_or_create(
                person=self.user,
                business_unit=self.business_unit,
                defaults={'state': 'INITIAL'}
            )
            
            self.current_state = chat_state.state
            self.last_intent = chat_state.last_intent
            self.conversation_history = chat_state.conversation_history
            
            return chat_state
        except Exception as e:
            logger.error(f"Error inicializando chat state: {str(e)}")
            raise
    
    async def update_state(self, new_state: str, intent: IntentPattern = None):
        """Actualiza el estado del chat."""
        try:
            chat_state = await ChatState.objects.aget(
                person=self.user,
                business_unit=self.business_unit
            )
            
            # Verificar transición válida
            valid_transition = await self._is_valid_transition(
                current_state=chat_state.state,
                new_state=new_state
            )
            
            if not valid_transition:
                logger.warning(f"Transición no válida: {chat_state.state} -> {new_state}")
                return False
            
            chat_state.state = new_state
            chat_state.last_intent = intent
            chat_state.last_transition = timezone.now()
            await chat_state.asave()
            
            self.current_state = new_state
            self.last_intent = intent
            
            return True
        except Exception as e:
            logger.error(f"Error actualizando estado: {str(e)}")
            raise
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Procesa un mensaje y actualiza el estado del chat."""
        try:
            # Analizar el texto
            analysis = await analyze_text(message)
            
            # Obtener intent y actualizar contexto
            intent = await self._get_intent(analysis)
            
            if intent:
                # Actualizar estado basado en el intent
                await self.update_state(
                    new_state=await self._get_next_state(intent),
                    intent=intent
                )
                
                # Actualizar contexto
                await self._update_context(analysis)
                
                # Agregar al historial de conversación
                await self._add_to_history(message, intent)
                
                return {
                    'intent': intent.name,
                    'state': self.current_state,
                    'analysis': analysis,
                    'context': self.context
                }
            else:
                logger.warning("No se pudo determinar el intent del mensaje")
                return {
                    'intent': None,
                    'state': self.current_state,
                    'analysis': analysis,
                    'context': self.context
                }
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            raise
    
    async def _is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """Verifica si una transición de estado es válida."""
        try:
            transition = await StateTransition.objects.aget(
                current_state=current_state,
                next_state=new_state,
                business_unit=self.business_unit
            )
            
            # Verificar condiciones
            return await self._check_conditions(transition.conditions)
        except StateTransition.DoesNotExist:
            return False
    
    async def _get_intent(self, analysis: Dict[str, Any]) -> Optional[IntentPattern]:
        """Obtiene el intent más probable para un análisis."""
        try:
            # Obtener todos los intents disponibles
            intents = await IntentPattern.objects.filter(
                business_units=self.business_unit,
                enabled=True
            ).aall()
            
            # Evaluar cada intent
            best_match = None
            highest_score = 0
            
            for intent in intents:
                score = await self._evaluate_intent(intent, analysis)
                if score > highest_score:
                    highest_score = score
                    best_match = intent
            
            return best_match if highest_score > 0.5 else None
        except Exception as e:
            logger.error(f"Error obteniendo intent: {str(e)}")
            return None
    
    async def _evaluate_intent(self, intent: IntentPattern, analysis: Dict[str, Any]) -> float:
        """Evalúa la probabilidad de que un intent sea el correcto."""
        try:
            # Verificar patrones de texto
            text_match = 0
            for pattern in intent.get_patterns_list():
                if re.search(pattern, analysis.get('text', ''), re.IGNORECASE):
                    text_match += 1
            
            # Verificar entidades
            entity_match = 0
            for entity in analysis.get('entities', []):
                if entity['label'] in intent.entities:
                    entity_match += 1
            
            # Verificar contexto
            context_match = 0
            for condition in intent.conditions:
                if await self._check_condition(condition):
                    context_match += 1
            
            # Calcular puntuación total
            score = (
                (text_match / len(intent.get_patterns_list())) * 0.5 +
                (entity_match / len(intent.entities)) * 0.3 +
                (context_match / len(intent.conditions)) * 0.2
            )
            
            return score
        except Exception as e:
            logger.error(f"Error evaluando intent: {str(e)}")
            return 0
    
    async def _get_next_state(self, intent: IntentPattern) -> str:
        """Obtiene el siguiente estado basado en el intent actual."""
        try:
            transition = await IntentTransition.objects.aget(
                current_intent=intent,
                business_unit=self.business_unit
            )
            
            # Verificar condiciones
            if await self._check_conditions(transition.conditions):
                return transition.next_intent.name
            else:
                return self.current_state
        except IntentTransition.DoesNotExist:
            return self.current_state
    
    async def _update_context(self, analysis: Dict[str, Any]):
        """Actualiza el contexto de la conversación."""
        try:
            # Extraer información relevante
            entities = analysis.get('entities', [])
            sentiment = analysis.get('sentiment', {})
            
            # Actualizar contexto
            self.context.update({
                'entities': entities,
                'sentiment': sentiment,
                'timestamp': timezone.now().isoformat()
            })
            
            # Guardar en base de datos
            chat_state = await ChatState.objects.aget(
                person=self.user,
                business_unit=self.business_unit
            )
            chat_state.context = self.context
            await chat_state.asave()
        except Exception as e:
            logger.error(f"Error actualizando contexto: {str(e)}")
    
    async def _add_to_history(self, message: str, intent: IntentPattern):
        """Agrega un mensaje al historial de conversación."""
        try:
            chat_state = await ChatState.objects.aget(
                person=self.user,
                business_unit=self.business_unit
            )
            
            chat_state.conversation_history.append({
                'message': message,
                'intent': intent.name,
                'timestamp': timezone.now().isoformat(),
                'analysis': await analyze_text(message)
            })
            
            # Mantener solo los últimos 10 mensajes
            if len(chat_state.conversation_history) > 10:
                chat_state.conversation_history.pop(0)
            
            await chat_state.asave()
        except Exception as e:
            logger.error(f"Error agregando a historial: {str(e)}")
    
    async def _check_conditions(self, conditions: List[Dict]) -> bool:
        """Verifica si se cumplen las condiciones para una transición."""
        try:
            for condition in conditions:
                if not await self._check_condition(condition):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error verificando condiciones: {str(e)}")
            return False
    
    async def _check_condition(self, condition: Dict) -> bool:
        """Verifica si se cumple una condición específica."""
        try:
            condition_type = condition.get('type')
            value = condition.get('value')
            
            if condition_type == 'PROFILE_COMPLETE':
                return await self.user.is_profile_complete()
            elif condition_type == 'HAS_APPLIED':
                return await Application.objects.filter(
                    user=self.user,
                    status='applied'
                ).aexists()
            elif condition_type == 'HAS_INTERVIEW':
                return await Interview.objects.filter(
                    person=self.user,
                    interview_date__gte=timezone.now()
                ).aexists()
            elif condition_type == 'HAS_OFFER':
                return await Application.objects.filter(
                    user=self.user,
                    status='hired'
                ).aexists()
            elif condition_type == 'HAS_PROFILE':
                return await self.user.is_profile_complete()
            elif condition_type == 'HAS_CV':
                return bool(self.user.cv_file)
            elif condition_type == 'HAS_TEST':
                return bool(self.user.personality_data)
            
            return False
        except Exception as e:
            logger.error(f"Error verificando condición: {str(e)}")
            return False
    
    async def get_available_intents(self) -> List[IntentPattern]:
        """Obtiene los intents disponibles según el estado actual."""
        try:
            # Obtener transiciones válidas desde el estado actual
            transitions = await StateTransition.objects.filter(
                current_state=self.current_state,
                business_unit=self.business_unit
            ).aall()
            
            # Obtener intents disponibles
            available_intents = await IntentPattern.objects.filter(
                business_units=self.business_unit,
                enabled=True
            ).aall()
            
            # Filtrar por condiciones
            filtered_intents = []
            for intent in available_intents:
                transitions = await IntentTransition.objects.filter(
                    current_intent=intent,
                    business_unit=self.business_unit
                ).aall()
                
                for transition in transitions:
                    if await self._check_conditions(transition.conditions):
                        filtered_intents.append(intent)
                        break
            
            return filtered_intents
        except Exception as e:
            logger.error(f"Error obteniendo intents disponibles: {str(e)}")
            return []
