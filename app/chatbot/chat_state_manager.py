from typing import Dict, Any, Optional, List, Tuple, Set
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from aioredis import Redis
import aioredis
from app.chatbot.metrics import StateMetrics
from app.models import (
    Person, BusinessUnit, ChatState, IntentPattern,
    StateTransition, IntentTransition, ContextCondition,
    ChannelPreference
)
from app.chatbot.utils import analyze_text, get_nlp_processor
from app.chatbot.workflow.common import get_workflow_context
from app.chatbot.channels import WhatsAppHandler, TelegramHandler, SlackHandler
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

async def get_redis_connection() -> Redis:
    """Get Redis connection with connection pooling"""
    if not hasattr(get_redis_connection, 'pool'):
        get_redis_connection.pool = await aioredis.create_redis_pool(
            settings.REDIS_URL,
            minsize=5,
            maxsize=10
        )
    return get_redis_connection.pool

async def get_cached_state_key(user_id: int, bu_id: int, channel: str) -> str:
    """Get cache key for chat state with Redis support"""
    redis_key = REDIS_STATE_CACHE_KEY.format(user_id, bu_id, channel)
    return redis_key

@lru_cache(maxsize=1000)
def get_intent_cache_key(user_id: int) -> str:
    """Get cache key for intent analysis"""
    return INTENT_CACHE_KEY.format(user_id)

logger = logging.getLogger(__name__)

# Cache configuration
STATE_CACHE_KEY = 'chat_state_{}_{}'
STATE_CACHE_TIMEOUT = 300  # 5 minutes

@lru_cache(maxsize=1000)
def get_cached_state_key(user_id: int, bu_id: int) -> str:
    """Get cache key for chat state"""
    return STATE_CACHE_KEY.format(user_id, bu_id)

class ChatStateManager:
    """Manejador de estados de chat para el chatbot.
    
    Optimizado para:
    - Manejo asíncrono de estados
    - Caching con Redis
    - Seguimiento de métricas en tiempo real
    - Manejo de contexto mejorado
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
        self.metrics = StateMetrics()
        self.cache_key = get_cached_state_key(user.id, business_unit.id, channel)
        self.fallback_states = []
        self.error_count = 0
        self.max_retries = 3
        
    async def initialize(self):
        """Inicializa el estado del chat para un usuario con soporte Redis."""
        try:
            # Try to get from Redis cache first
            redis = await get_redis_connection()
            cached_state = await redis.get(self.cache_key)
            if cached_state:
                cached_state = json.loads(cached_state)
                logger.debug(f"Loaded chat state from Redis for user {self.user.id}")
                self.current_state = cached_state['state']
                self.last_intent = cached_state['last_intent']
                self.conversation_history = cached_state['history']
                self.context = cached_state['context']
                self.context_stack = cached_state.get('context_stack', [])
                self.metrics = StateMetrics.from_dict(cached_state.get('metrics', {}))
                return True

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
            await self._save_to_redis()
            return True
            
            # Get or create the chat state
            chat_state, created = await ChatState.objects.aget_or_create(
                person=self.user,
                business_unit=self.business_unit,
                defaults={'state': 'INITIAL'}
            )
            
            self.current_state = chat_state.state
            self.last_intent = chat_state.last_intent
            self.conversation_history = chat_state.conversation_history or []
            self.context = get_workflow_context(self.business_unit)
            
            # Initialize channel-specific context
            if self.channel_handler:
                self.context.update(self.channel_handler.get_initial_context())
            
            # Cache the state
            cache.set(
                self.cache_key,
                {
                    'state': self.current_state,
                    'last_intent': self.last_intent,
                    'history': self.conversation_history,
                    'context': self.context,
                    'context_stack': self.context_stack,
                    'metrics': dict(self.metrics)
                },
                STATE_CACHE_TIMEOUT
            )
            
            return chat_state
        except Exception as e:
            logger.error(f"Error initializing chat state: {str(e)}")
            raise
    
    async def update_state(self, new_state: str, intent: Optional[str] = None):
        """Actualiza el estado actual con soporte asíncrono y métricas."""
        try:
            self.last_intent = intent
            self.current_state = new_state
            
            # Add to conversation history
            history_entry = {
                'timestamp': timezone.now().isoformat(),
                'state': new_state,
                'intent': intent
            }
            self.conversation_history.append(history_entry)
            
            # Update metrics
            self.metrics.increment('state_transitions')
            self.metrics.track_transition(self.current_state, new_state)
            
            # Save to Redis
            await self._save_to_redis()
            
            # Check for fallback conditions
            if self.error_count >= self.max_retries:
                await self._handle_fallback()
                
            return True
        except Exception as e:
            logger.error(f"Error updating state: {str(e)}")
            self.error_count += 1
            self.metrics.increment('state_update_errors')
            return False
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Procesa un mensaje y actualiza el estado del chat."""
        try:
            # Get or initialize state
            if not self.current_state:
                await self.initialize()
            
            # Analyze message
            analysis = await analyze_text(message, method='nlp')
            
            # Get intent
            intent = await self._get_intent(analysis)
            
            # Update metrics
            self.metrics.increment('messages_processed')
            self.metrics.track_transition(self.current_state, intent)
            
            # Update state based on intent
            if intent:
                new_state = await self._get_next_state(intent)
                if new_state:
                    await self.update_state(new_state, intent)
            
            # Update context
            self.context.update(analysis.get('context', {}))
            
            # Cache state
            cache.set(
                self.cache_key,
                {
                    'state': self.current_state,
                    'last_intent': self.last_intent,
                    'history': self.conversation_history,
                    'context': self.context,
                    'context_stack': self.context_stack,
                    'metrics': dict(self.metrics)
                },
                STATE_CACHE_TIMEOUT
            )
            
            return {
                'state': self.current_state,
                'intent': intent,
                'analysis': analysis
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise
    
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
                similarity = await analyze_text(
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
        await self._save_to_redis()
        self.metrics.increment('context_updates')

    async def push_context(self, context: Dict[str, Any]):
        """Guarda el contexto actual y establece uno nuevo."""
        self.context_stack.append(self.context.copy())
        self.context = context
        await self._save_to_redis()
        self.metrics.increment('context_stack_push')

    async def pop_context(self):
        """Restaura el contexto anterior."""
        if self.context_stack:
            self.context = self.context_stack.pop()
            await self._save_to_redis()
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
