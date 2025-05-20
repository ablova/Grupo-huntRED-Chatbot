# /home/pablo/app/com/chatbot/chat_state_manager.py
from typing import Dict, Any, Optional, List, Tuple, Set
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from aioredis import Redis
import aioredis
from app.com.chatbot.metrics import ChatBotMetrics
from app.models import (
    Person, BusinessUnit, ChatState, IntentPattern,
    StateTransition, IntentTransition, )
from app.com.chatbot.utils import ChatbotUtils
# Importaciones directas siguiendo estándares de Django - v2025.05.20
from app.com.chatbot.integrations.whatsapp import WhatsAppHandler
from app.com.chatbot.integrations.telegram import TelegramHandler
from app.com.chatbot.integrations.slack import SlackHandler
from app.com.chatbot.workflow.workflow_manager import WorkflowManager
from app.com.chatbot.core.values import ValuesIntegrator, ValuesPrinciples


# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator

# FIXED: Modelo ContextCondition agregado localmente - v2025.05.19
class ContextCondition:
    """Modelo local para mantener compatibilidad."""
    KEY = 'key'
    VALUE = 'value'
    OPERATOR = 'operator'
    
    OPERATORS = {
        'eq': 'equal',
        'neq': 'not_equal',
        'gt': 'greater_than',
        'lt': 'less_than',
        'contains': 'contains',
        'not_contains': 'not_contains'
    }
    
    def __init__(self, key, value, operator='eq'):
        self.key = key
        self.value = value
        self.operator = operator
# Nota: Ahora importamos las clases directamente, ya no necesitamos getters
# Las importaciones están en la parte superior del archivo
import asyncio
import logging
import json
from functools import lru_cache
from collections import defaultdict

logger = logging.getLogger(__name__)

# Cache configuration
STATE_CACHE_KEY = 'chat_state_{}_{}_{}'
STATE_CACHE_TIMEOUT = 300  # 5 minutes
INTENT_CACHE_KEY = 'intent_cache_{}'
INTENT_CACHE_TIMEOUT = 60  # 1 minute

# Channel configuration
CHANNEL_HANDLERS = {
    'whatsapp': WhatsAppHandler,
    'telegram': TelegramHandler,
    'slack': SlackHandler
}

# Intent priority levels
INTENT_PRIORITY = {
    'CRITICAL': 5,
    'HIGH': 4,
    'MEDIUM': 3,
    'LOW': 2,
    'NONE': 1
}

class ChatStateManager:
    """
    Manager for handling chatbot conversation states with Redis caching.
    """
    def __init__(self, user: Person, business_unit: BusinessUnit, channel: str):
        self.user = user
        self.business_unit = business_unit
        self.channel = channel
        self.channel_handler = CHANNEL_HANDLERS.get(channel.lower())
        self.current_state = None
        self.last_intent = None
        self.conversation_history = []
        self.context = {}
        self.context_stack = []  # Stack for context management
        self.metrics = ChatBotMetrics()
        self.cache_key = STATE_CACHE_KEY.format(user.id, business_unit.id, channel)
        self.fallback_states = []
        self.error_count = 0
        self.max_retries = 3
        self.redis_client = None
        self._initialize_redis()
        
        # Importación a nivel de método para evitar dependencias circulares
        from app.com.chatbot.workflow.context import WorkflowContext
        self.workflow_context = WorkflowContext()
        logger.info("ChatStateManager initialized")

    def _initialize_redis(self):
        """
        Initialize Redis client with retry mechanism.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Successfully connected to Redis")
                return
            except aioredis.ConnectionError as e:
                logger.error(f"Redis connection attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.critical("Failed to connect to Redis after retries")
                    raise
                asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def get_state(self) -> Dict[str, Any]:
        """
        Retrieve the current state for the chat session.

        Returns:
            dict: Current state of the chat, or empty dict if not found.
        """
        for attempt in range(3):
            try:
                state_json = self.redis_client.get(self.cache_key)
                if state_json:
                    return json.loads(state_json)
                return {}
            except (aioredis.RedisError, json.JSONDecodeError) as e:
                logger.error(f"Error retrieving state for chat {self.user.id}, attempt {attempt + 1}/3: {str(e)}")
                if attempt == 2:
                    logger.critical(f"Failed to retrieve state for chat {self.user.id} after retries")
                    return {}
                asyncio.sleep(1)

    async def set_state(self, state: Dict[str, Any], ttl: int = None):
        """
        Set the current state for the chat session.

        Args:
            state (dict): State data to store.
            ttl (int, optional): Time to live in seconds for the state data.
        """
        for attempt in range(3):
            try:
                state_json = json.dumps(state)
                if ttl:
                    self.redis_client.setex(self.cache_key, ttl, state_json)
                else:
                    self.redis_client.set(self.cache_key, state_json)
                logger.info(f"State set for chat {self.user.id}")
                return
            except (aioredis.RedisError, json.JSONEncodeError) as e:
                logger.error(f"Error setting state for chat {self.user.id}, attempt {attempt + 1}/3: {str(e)}")
                if attempt == 2:
                    logger.critical(f"Failed to set state for chat {self.user.id} after retries")
                    raise
                asyncio.sleep(1)

    async def update_state_field(self, field: str, value: Any):
        """
        Update a specific field in the state for the chat session.

        Args:
            field (str): Field to update.
            value (any): Value to set for the field.
        """
        state = await self.get_state()
        state[field] = value
        await self.set_state(state)
        logger.info(f"Updated field {field} for chat {self.user.id}")

    async def clear_state(self):
        """
        Clear the state for the chat session.
        """
        for attempt in range(3):
            try:
                self.redis_client.delete(self.cache_key)
                logger.info(f"State cleared for chat {self.user.id}")
                return
            except aioredis.RedisError as e:
                logger.error(f"Error clearing state for chat {self.user.id}, attempt {attempt + 1}/3: {str(e)}")
                if attempt == 2:
                    logger.critical(f"Failed to clear state for chat {self.user.id} after retries")
                    raise
                asyncio.sleep(1)

    async def initialize(self):
        """Inicializa el estado del chat para un usuario con soporte Redis."""
        try:
            logger.info(f"Initializing chat state for user {self.user.id} on channel {self.channel}")
            # Try to get from Redis cache first
            state = await self.get_state()
            if state:
                self.current_state = state['state']
                self.last_intent = state['last_intent']
                self.conversation_history = state['history']
                self.context = state['context']
                self.context_stack = state.get('context_stack', [])
                self.metrics = ChatBotMetrics.from_dict(state.get('metrics', {}))
                logger.info(f"Chat state successfully loaded for user {self.user.id}")
                return True
            else:
                logger.debug(f"No cached state found for user {self.user.id}, initializing new state")
                # Get or create the chat state
                chat_state, created = await ChatState.objects.aget_or_create(
                    person=self.user,
                    business_unit=self.business_unit,
                    defaults={'state': 'INITIAL'}
                )
                
                if created:
                    self.metrics.increment('new_conversation')
                else:
                    self.metrics.increment('existing_conversation')

                self.current_state = chat_state.state
                self.last_intent = None
                self.conversation_history = []
                self.context = {}
                self.context_stack = []
                
                # Save initial state to Redis
                await self.set_state({
                    'state': self.current_state,
                    'last_intent': self.last_intent,
                    'history': self.conversation_history,
                    'context': self.context,
                    'context_stack': self.context_stack,
                    'metrics': dict(self.metrics)
                })
                return True
        except Exception as e:
            logger.error(f"Error initializing chat state: {str(e)}")
            raise

    async def update_state(self, new_state: str, intent: Optional[str] = None):
        """Actualiza el estado actual con soporte asíncrono y métricas."""
        try:
            logger.info(f"Updating state for user {self.user.id} from {self.current_state} to {new_state}, intent: {intent or 'None'}")
            if self.current_state != new_state:
                if await self._is_valid_transition(self.current_state, new_state):
                    self.current_state = new_state
                    if intent:
                        self.last_intent = intent
                        self.metrics.increment(f'intent_{intent}')
                    self.metrics.increment('state_transitions')
                    logger.debug(f"State transition successful for user {self.user.id} to {new_state}")
                else:
                    logger.warning(f"Invalid state transition attempted for user {self.user.id}: {self.current_state} -> {new_state}")
                    self.metrics.increment('invalid_transitions')
                    return False
            else:
                logger.debug(f"State unchanged for user {self.user.id}: {new_state}")
            await self.set_state({
                'state': self.current_state,
                'last_intent': self.last_intent,
                'history': self.conversation_history,
                'context': self.context,
                'context_stack': self.context_stack,
                'metrics': dict(self.metrics)
            })
            logger.info(f"State updated for user {self.user.id} to {new_state}")
            return True
        except Exception as e:
            logger.error(f"Error updating state for user {self.user.id}: {str(e)}", exc_info=True)
            self.error_count += 1
            self.metrics.increment('state_update_errors')
            return False

    async def process_message(self, message: str) -> Dict[str, Any]:
        """Procesa un mensaje y actualiza el estado del chat."""
        try:
            # Primero analizamos los valores fundamentales presentes en el mensaje
            values_metadata = await ValuesIntegrator.process_incoming_message(
                message, 
                {'user': self.user, 'bu': self.business_unit}
            )
            
            # Almacenamos los metadatos de valores en el contexto
            if not 'values' in self.context:
                self.context['values'] = {}
                
            self.context['values'].update({
                'emotional_context': values_metadata.get('emotional_context', 'neutral'),
                'career_stage': values_metadata.get('career_stage', 'exploring'),
                'value_opportunities': values_metadata.get('value_opportunities', []),
                'last_updated': timezone.now().isoformat()
            })
            
            # Analyze the message for intents, entities, sentiment
            analysis = await ChatbotUtils.analyze_text(message, self.business_unit)
            intent = await self._get_intent(analysis)
            
            # Update analytics
            self.metrics.increment('messages_processed')
            self.conversation_history.append({
                'text': message,
                'timestamp': timezone.now().isoformat(),
                'intent': intent,
                'values': self.context.get('values', {})
            })
            
            # If we have a valid intent, update the state
            if intent:
                self.metrics.increment(f'intent_{intent}')
                # Get all transitions for this intent
                transitions = await IntentTransition.objects.filter(
                    intent__name=intent,
                    business_unit=self.business_unit
                ).select_related('target_state').async_all()
                
                # Find valid transition
                for transition in transitions:
                    # Check conditions
                    if await self._check_conditions(transition.conditions):
                        # Update state
                        new_state = transition.target_state.name
                        await self.update_state(new_state, intent)
                        return
            
            logger.info(f"No valid transition found for intent: {intent}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.error_count += 1

    async def _is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """Verifica si una transición de estado es válida."""
        try:
            # Get all possible transitions
            transitions = await StateTransition.objects.filter(
                current_state=current_state,
                next_state=new_state,
                business_unit=self.business_unit
            ).values('id', 'priority', 'conditions')
            
            if not transitions:
                return False
            
            # Check if any transition meets the conditions
            for transition in transitions:
                if await self._check_transition_conditions(transition['conditions']):
                    return True
            
            # Check channel-specific restrictions
            if self.channel_handler:
                return await self.channel_handler.is_valid_transition(
                    current_state=current_state,
                    new_state=new_state,
                    context=self.context
                )
            
            return False
        except Exception as e:
            logger.error(f"Error verificando transición: {str(e)}")
            raise
    
    async def _get_intent(self, analysis: Dict[str, Any]) -> Optional[IntentPattern]:
        """Obtiene el intent más probable para un análisis."""
        try:
            # Check cache first
            cache_key = get_intent_cache_key(self.user.id)
            cached_intent = cache.get(cache_key)
            if cached_intent:
                return cached_intent
            
            # Get available intents with priority
            intents = await self.get_available_intents()
            
            # Group intents by priority
            intents_by_priority = defaultdict(list)
            for intent in intents:
                priority = INTENT_PRIORITY.get(intent.priority, 1)
                intents_by_priority[priority].append(intent)
            
            # Evaluate intents starting from highest priority
            best_intent = None
            best_score = 0
            
            for priority in sorted(intents_by_priority.keys(), reverse=True):
                for intent in intents_by_priority[priority]:
                    score = await self._evaluate_intent(intent, analysis)
                    if score > settings.INTENT_THRESHOLD and score > best_score:
                        best_intent = intent
                        best_score = score
            
            # Cache the best intent
            if best_intent:
                cache.set(cache_key, best_intent, INTENT_CACHE_TIMEOUT)
                return best_intent
            
            return None
        except Exception as e:
            logger.error(f"Error getting intent: {str(e)}")
            return None
    
    async def _evaluate_intent(self, intent: IntentPattern, analysis: Dict[str, Any]) -> float:
        """Evalúa la probabilidad de que un intent sea el correcto."""
        try:
            # Verificar patrones de texto
            text_match = 0
            for pattern in intent.get_patterns_list():
                if re.search(pattern, analysis.get('text', ''), re.IGNORECASE):
                    text_match += 1
            
            # Calculate similarity score
            score = 0
            for pattern in intent.patterns:
                similarity = await ChatbotUtils.analyze_text(
                    pattern,
                    analysis['text'],
                    method='similarity'
                )
                score = max(score, similarity)
            
            # Apply channel-specific adjustments
            if self.channel_handler:
                score = self.channel_handler.adjust_intent_score(
                    intent=intent,
                    score=score,
                    context=self.context
                )
            
            return score
        except Exception as e:
            logger.error(f"Error evaluating intent: {str(e)}")
            return 0
    
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
            # Check context conditions
            if condition.get('context'):
                for ctx_key, ctx_value in condition['context'].items():
                    if ctx_key not in self.context or self.context[ctx_key] != ctx_value:
                        return False
            
            # Check state conditions
            if condition.get('state') and condition['state'] != self.current_state:
                return False
            
            # Check intent conditions
            if condition.get('intent') and condition['intent'] != self.last_intent:
                return False
            
            # Check channel-specific conditions
            if self.channel_handler:
                return await self.channel_handler.check_condition(
                    condition=condition,
                    context=self.context
                )
            
            return True
        except Exception as e:
            logger.error(f"Error checking condition: {str(e)}")
            return False
    
    async def get_context(self, key: str, default=None):
        """Obtiene un valor del contexto con soporte asíncrono y validación."""
        value = self.context.get(key, default)
        if value is None:
            self.metrics.increment('context_misses')
        else:
            self.metrics.increment('context_hits')
        return value

    async def set_context(self, key: str, value: Any):
        """Establece un valor en el contexto con soporte asíncrono."""
        self.context[key] = value
        await self.set_state({
            'state': self.current_state,
            'last_intent': self.last_intent,
            'history': self.conversation_history,
            'context': self.context,
            'context_stack': self.context_stack,
            'metrics': dict(self.metrics)
        })
        self.metrics.increment('context_updates')

    async def push_context(self, context: Dict[str, Any]):
        """Guarda el contexto actual y establece uno nuevo."""
        self.context_stack.append(self.context.copy())
        self.context = context
        await self.set_state({
            'state': self.current_state,
            'last_intent': self.last_intent,
            'history': self.conversation_history,
            'context': self.context,
            'context_stack': self.context_stack,
            'metrics': dict(self.metrics)
        })
        self.metrics.increment('context_stack_push')

    async def pop_context(self):
        """Restaura el contexto anterior."""
        if self.context_stack:
            self.context = self.context_stack.pop()
            await self.set_state({
                'state': self.current_state,
                'last_intent': self.last_intent,
                'history': self.conversation_history,
                'context': self.context,
                'context_stack': self.context_stack,
                'metrics': dict(self.metrics)
            })
            self.metrics.increment('context_stack_pop')
        return self.context_stack
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene las métricas del chat."""
        return {
            'messages_processed': self.metrics.get('messages_processed', 0),
            'state_transitions': self.metrics.get('state_transitions', 0),
            'response_time_avg': self.metrics.get('response_time', 0) / max(1, self.metrics.get('messages_processed', 1)),
            'intent_distribution': {
                intent: self.metrics.get(f'intent_{intent}', 0)
                for intent in self.metrics
                if intent.startswith('intent_')
            }
        }
