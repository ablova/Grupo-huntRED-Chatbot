# /home/pablo/app/com/chatbot/components/chat_state_manager.py
from typing import Dict, Any, Optional, List, Tuple
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from redis.asyncio import Redis
import asyncio
import logging
import json
import re
from functools import lru_cache
from collections import defaultdict
from asgiref.sync import sync_to_async

from app.models import Person, BusinessUnit, ChatState, IntentPattern, StateTransition, IntentTransition
from app.com.chatbot.components.metrics import ChatBotMetrics
from app.com.chatbot.utils import ChatbotUtils
from app.com.chatbot.workflow.core.workflow_manager import WorkflowManager
from app.com.chatbot.workflow.common.context import WorkflowContext
from app.com.chatbot.integrations.services import (
    get_whatsapp_handler,
    get_telegram_handler,
    get_instagram_handler,
    get_slack_handler
)

logger = logging.getLogger(__name__)

# Cache configuration
STATE_CACHE_KEY = 'chat_state_{}_{}_{}'
STATE_CACHE_TIMEOUT = 300  # 5 minutes
INTENT_CACHE_KEY = 'intent_cache_{}'
INTENT_CACHE_TIMEOUT = 60  # 1 minute

# Channel configuration is now handled by channel_handlers module

# Intent priority levels
INTENT_PRIORITY = {
    'CRITICAL': 5,
    'HIGH': 4,
    'MEDIUM': 3,
    'LOW': 2,
    'NONE': 1
}

# Consolidated ContextCondition class (removed redundant definitions)
class ContextCondition:
    """Modelo para condiciones de contexto."""
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

# Consolidated ChatStateTransition class from state_manager.py
class ChatStateTransition:
    """Clase para definir transiciones de estado con condiciones."""
    def __init__(self, current_state: str, next_state: str, conditions: Dict[str, Any] = None):
        self.current_state = current_state
        self.next_state = next_state
        self.conditions = conditions or {}

    async def is_valid_transition(self, person: Person, context: Dict[str, Any]) -> bool:
        """Verifica si la transición es válida según las condiciones."""
        for key, value in self.conditions.items():
            if key == 'min_experience':
                if person.experience_years < value:
                    return False
            elif key == 'min_salary':
                if person.salary_data.get('current_salary', 0) < value:
                    return False
            elif key == 'has_cv':
                if not person.cv_file:
                    return False
            elif key == 'has_profile':
                if not await sync_to_async(person.is_profile_complete)():
                    return False
            elif key == 'has_test':
                if not await sync_to_async(person.has_completed_test)():
                    return False
            elif key == 'has_tos_accepted':
                if not context.get('tos_accepted', False):
                    return False
            elif key == 'has_applied':
                if not context.get('has_applied', False):
                    return False
            elif key == 'has_interview_scheduled':
                if not context.get('interview_scheduled', False):
                    return False
            elif key == 'has_completed_interview':
                if not context.get('interview_completed', False):
                    return False
            elif key == 'has_offer':
                if not context.get('offer_received', False):
                    return False
            elif key == 'has_signed_contract':
                if not context.get('contract_signed', False):
                    return False
            elif key == 'has_started_job':
                if not context.get('job_started', False):
                    return False
            elif key == 'has_completed_probation':
                if not context.get('probation_completed', False):
                    return False
            elif key == 'has_updated_profile':
                if not context.get('profile_updated', False):
                    return False
            elif key == 'has_migration_docs':
                if not context.get('migration_docs', False):
                    return False
            elif key == 'is_student':
                if not person.is_student:
                    return False
            elif key == 'has_executive_experience':
                if not person.executive_experience:
                    return False
        return True

class ChatStateManager:
    """Manager for handling chatbot conversation states with Redis caching and business-unit-specific transitions."""
    
    def __init__(self, user: Person, business_unit: BusinessUnit, channel: str):
        self.user = user
        self.business_unit = business_unit
        self.channel = channel.lower()
        self._channel_handler = None  # Inicializado de forma perezosa
        self.current_state = None
        self.last_intent = None
        self.conversation_history = []
        self.context = {}
        self.context_stack = []
        self.metrics = ChatBotMetrics()
        self.cache_key = STATE_CACHE_KEY.format(user.id, business_unit.id, self.channel)
        self.fallback_states = []
        self.error_count = 0
        self.max_retries = 3
        self.redis_client = None
        self.workflow_context = WorkflowContext()
        self.state_transitions = self._initialize_state_transitions()
        self._initialize_redis()
        logger.info(f"ChatStateManager initialized for user {user.id}, channel {self.channel}")
    
    @property
    def channel_handler(self):
        """Obtiene el manejador de canal de forma perezosa."""
        if self._channel_handler is None:
            handler_map = {
                'whatsapp': get_whatsapp_handler(),
                'telegram': get_telegram_handler()[0],  # get_telegram_handler retorna (TelegramHandler, fetch_telegram_user_data)
                'messenger': get_instagram_handler()[0],  # Asumiendo que get_instagram_handler es similar
                'instagram': get_instagram_handler()[0],
                'slack': get_slack_handler()
            }
            self._channel_handler = handler_map.get(self.channel)
        return self._channel_handler

    def _initialize_redis(self):
        """Initialize Redis client with retry mechanism."""
        max_retries = self.max_retries
        for attempt in range(max_retries):
            try:
                self.redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("Successfully connected to Redis")
                return
            except Exception as e:
                logger.error(f"Redis connection attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt == max_retries - 1:
                    logger.critical("Failed to connect to Redis after retries")
                    raise
                asyncio.sleep(2 ** attempt)

    def _initialize_state_transitions(self) -> Dict[str, List[ChatStateTransition]]:
        """Initialize business-unit-specific state transitions (from state_manager.py)."""
        transitions = {
            "initial": [
                ChatStateTransition("initial", "waiting_for_tos"),
                ChatStateTransition("initial", "profile_in_progress", {"has_cv": True}),
            ],
            "waiting_for_tos": [
                ChatStateTransition("waiting_for_tos", "profile_in_progress", {"has_tos_accepted": True}),
                ChatStateTransition("waiting_for_tos", "initial"),
            ],
            "profile_in_progress": [
                ChatStateTransition("profile_in_progress", "profile_complete", {"has_profile": True}),
                ChatStateTransition("profile_in_progress", "initial"),
            ],
            "profile_complete": [
                ChatStateTransition("profile_complete", "applied", {"has_applied": True}),
                ChatStateTransition("profile_complete", "profile_in_progress"),
            ],
            "applied": [
                ChatStateTransition("applied", "scheduled", {"has_interview_scheduled": True}),
                ChatStateTransition("applied", "profile_complete"),
            ],
            "scheduled": [
                ChatStateTransition("scheduled", "interviewed", {"has_completed_interview": True}),
                ChatStateTransition("scheduled", "applied"),
            ],
            "interviewed": [
                ChatStateTransition("interviewed", "offered", {"has_offer": True}),
                ChatStateTransition("interviewed", "applied"),
            ],
            "offered": [
                ChatStateTransition("offered", "signed", {"has_signed_contract": True}),
                ChatStateTransition("offered", "interviewed"),
            ],
            "signed": [
                ChatStateTransition("signed", "hired", {"has_started_job": True}),
                ChatStateTransition("signed", "offered"),
            ],
            "hired": [
                ChatStateTransition("hired", "idle", {"has_completed_probation": True}),
                ChatStateTransition("hired", "signed"),
            ],
            "idle": [
                ChatStateTransition("idle", "profile_complete", {"has_updated_profile": True}),
                ChatStateTransition("idle", "initial"),
            ],
        }

        # Business-unit-specific transitions
        if self.business_unit.name.lower() == "amigro":
            transitions["initial"].append(
                ChatStateTransition("initial", "migratory_status", {"has_migration_docs": True})
            )
        elif self.business_unit.name.lower() == "huntu":
            transitions["profile_complete"].append(
                ChatStateTransition("profile_complete", "internship_search", {"is_student": True})
            )
        elif self.business_unit.name.lower() == "huntred":
            transitions["profile_complete"].append(
                ChatStateTransition("profile_complete", "executive_search", {"has_executive_experience": True})
            )

        return transitions

    async def get_state(self) -> Dict[str, Any]:
        """Retrieve the current state from Redis or database."""
        for attempt in range(self.max_retries):
            try:
                state_json = await self.redis_client.get(self.cache_key)
                if state_json:
                    return json.loads(state_json)
                return {}
            except Exception as e:
                logger.error(f"Error retrieving state for user {self.user.id}, attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.critical(f"Failed to retrieve state for user {self.user.id}")
                    return {}
                await asyncio.sleep(1)

    async def set_state(self, state: Dict[str, Any], ttl: int = None):
        """Set the current state in Redis."""
        for attempt in range(self.max_retries):
            try:
                state_json = json.dumps(state)
                if ttl:
                    await self.redis_client.setex(self.cache_key, ttl, state_json)
                else:
                    await self.redis_client.set(self.cache_key, state_json)
                logger.info(f"State set for user {self.user.id}")
                return
            except Exception as e:
                logger.error(f"Error setting state for user {self.user.id}, attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.critical(f"Failed to set state for user {self.user.id}")
                    raise
                await asyncio.sleep(1)

    async def update_state_field(self, field: str, value: Any):
        """Update a specific field in the state."""
        state = await self.get_state()
        state[field] = value
        await self.set_state(state)
        logger.info(f"Updated field {field} for user {self.user.id}")

    async def clear_state(self):
        """Clear the state from Redis."""
        for attempt in range(self.max_retries):
            try:
                await self.redis_client.delete(self.cache_key)
                logger.info(f"State cleared for user {self.user.id}")
                return
            except Exception as e:
                logger.error(f"Error clearing state for user {self.user.id}, attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.critical(f"Failed to clear state for user {self.user.id}")
                    raise
                await asyncio.sleep(1)

    async def initialize(self):
        """Initialize chat state for a user."""
        try:
            logger.info(f"Initializing chat state for user {self.user.id} on channel {self.channel}")
            state = await self.get_state()
            if state:
                self.current_state = state['state']
                self.last_intent = state['last_intent']
                self.conversation_history = state['history']
                self.context = state['context']
                self.context_stack = state.get('context_stack', [])
                self.metrics = ChatBotMetrics.from_dict(state.get('metrics', {}))
                logger.info(f"Chat state loaded for user {self.user.id}")
                return True

            chat_state, created = await ChatState.objects.aget_or_create(
                person=self.user,
                business_unit=self.business_unit,
                defaults={'state': 'initial'}
            )
            
            self.metrics.increment('new_conversation' if created else 'existing_conversation')
            self.current_state = chat_state.state
            self.last_intent = None
            self.conversation_history = []
            self.context = {}
            self.context_stack = []
            
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
        """Update the current state with async support and metrics."""
        try:
            logger.info(f"Updating state for user {self.user.id} from {self.current_state} to {new_state}, intent: {intent or 'None'}")
            if self.current_state != new_state:
                if await self._is_valid_transition(self.current_state, new_state):
                    self.current_state = new_state
                    if intent:
                        self.last_intent = intent
                        self.metrics.increment(f'intent_{intent}')
                    self.metrics.increment('state_transitions')

                    # Persist to database with transaction
                    async with transaction.atomic():
                        chat_state = await ChatState.objects.aget(
                            person=self.user, business_unit=self.business_unit
                        )
                        chat_state.state = new_state
                        chat_state.last_transition = timezone.now()
                        await sync_to_async(chat_state.save)()

                    logger.debug(f"State transition successful for user {self.user.id} to {new_state}")
                else:
                    logger.warning(f"Invalid state transition for user {self.user.id}: {self.current_state} -> {new_state}")
                    self.metrics.increment('invalid_transitions')
                    return False

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
            logger.error(f"Error updating state for user {self.user.id}: {str(e)}")
            self.error_count += 1
            self.metrics.increment('state_update_errors')
            return False

    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and update the chat state."""
        try:
            values_metadata = await ValuesIntegrator.process_incoming_message(
                message, {'user': self.user, 'bu': self.business_unit}
            )
            self.context.setdefault('values', {}).update({
                'emotional_context': values_metadata.get('emotional_context', 'neutral'),
                'career_stage': values_metadata.get('career_stage', 'exploring'),
                'value_opportunities': values_metadata.get('value_opportunities', []),
                'last_updated': timezone.now().isoformat()
            })

            analysis = await ChatbotUtils.analyze_text(message, self.business_unit)
            intent = await self._get_intent(analysis)
            self.metrics.increment('messages_processed')
            self.conversation_history.append({
                'text': message,
                'timestamp': timezone.now().isoformat(),
                'intent': intent,
                'values': self.context.get('values', {})
            })

            if intent:
                self.metrics.increment(f'intent_{intent}')
                transitions = await IntentTransition.objects.filter(
                    intent__name=intent,
                    business_unit=self.business_unit
                ).select_related('target_state').all()

                for transition in transitions:
                    if await self._check_conditions(transition.conditions):
                        new_state = transition.target_state.name
                        await self.update_state(new_state, intent)
                        return {'state': new_state, 'intent': intent}

            # Fallback to predefined transitions
            available_transitions = await self.get_available_transitions()
            if available_transitions:
                new_state = available_transitions[0]  # Pick the first valid transition
                await self.update_state(new_state, intent)
                return {'state': new_state, 'intent': intent}

            logger.info(f"No valid transition found for intent: {intent}")
            return {'state': self.current_state, 'intent': intent}
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.error_count += 1
            self.metrics.increment('message_processing_errors')
            return {'state': self.current_state, 'intent': None}

    async def _is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """Verify if a state transition is valid."""
        try:
            # Check predefined transitions (from state_manager.py)
            transitions = self.state_transitions.get(current_state, [])
            valid_transitions = [t for t in transitions if t.next_state == new_state]
            person = await sync_to_async(self.user.refresh_from_db)()
            for transition in valid_transitions:
                if await transition.is_valid_transition(person, self.context):
                    return True

            # Check database transitions (from chat_state_manager.py)
            db_transitions = await StateTransition.objects.filter(
                current_state=current_state,
                next_state=new_state,
                business_unit=self.business_unit
            ).values('id', 'priority', 'conditions')
            
            for transition in db_transitions:
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
            logger.error(f"Error verifying transition: {str(e)}")
            return False

    async def _get_intent(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Get the most likely intent from analysis."""
        try:
            cache_key = f"{INTENT_CACHE_KEY}_{self.user.id}"
            cached_intent = cache.get(cache_key)
            if cached_intent:
                return cached_intent

            intents = await IntentPattern.objects.filter(
                business_unit=self.business_unit
            ).all()
            
            intents_by_priority = defaultdict(list)
            for intent in intents:
                priority = INTENT_PRIORITY.get(intent.priority, 1)
                intents_by_priority[priority].append(intent)
            
            best_intent = None
            best_score = 0
            
            for priority in sorted(intents_by_priority.keys(), reverse=True):
                for intent in intents_by_priority[priority]:
                    score = await self._evaluate_intent(intent, analysis)
                    if score > settings.INTENT_THRESHOLD and score > best_score:
                        best_intent = intent.name
                        best_score = score
            
            if best_intent:
                cache.set(cache_key, best_intent, INTENT_CACHE_TIMEOUT)
                return best_intent
            
            return None
        except Exception as e:
            logger.error(f"Error getting intent: {str(e)}")
            return None

    async def _evaluate_intent(self, intent: IntentPattern, analysis: Dict[str, Any]) -> float:
        """Evaluate the likelihood of an intent."""
        try:
            text_match = 0
            patterns = intent.get_patterns_list()
            for pattern in patterns:
                if re.search(pattern, analysis.get('text', ''), re.IGNORECASE):
                    text_match += 1
            
            score = 0
            for pattern in patterns:
                similarity = await ChatbotUtils.analyze_text(
                    pattern, analysis['text'], method='similarity'
                )
                score = max(score, similarity)
            
            if self.channel_handler:
                score = await self.channel_handler.adjust_intent_score(
                    intent=intent, score=score, context=self.context
                )
            
            return score
        except Exception as e:
            logger.error(f"Error evaluating intent: {str(e)}")
            return 0

    async def _check_conditions(self, conditions: List[Dict]) -> bool:
        """Check if transition conditions are met."""
        try:
            for condition in conditions:
                if not await self._check_condition(condition):
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking conditions: {str(e)}")
            return False

    async def _check_condition(self, condition: Dict) -> bool:
        """Check a specific condition."""
        try:
            if condition.get('context'):
                for ctx_key, ctx_value in condition['context'].items():
                    if ctx_key not in self.context or self.context[ctx_key] != ctx_value:
                        return False
            
            if condition.get('state') and condition['state'] != self.current_state:
                return False
            
            if condition.get('intent') and condition['intent'] != self.last_intent:
                return False
            
            if self.channel_handler:
                return await self.channel_handler.check_condition(
                    condition=condition, context=self.context
                )
            
            return True
        except Exception as e:
            logger.error(f"Error checking condition: {str(e)}")
            return False

    async def get_context(self, key: str, default=None):
        """Get a value from the context."""
        value = self.context.get(key, default)
        self.metrics.increment('context_misses' if value is None else 'context_hits')
        return value

    async def set_context(self, key: str, value: Any):
        """Set a value in the context."""
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
        """Push the current context and set a new one."""
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
        """Restore the previous context."""
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
        return self.context

    async def get_metrics(self) -> Dict[str, Any]:
        """Get chat metrics."""
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

    async def get_available_transitions(self) -> List[str]:
        """Get available transitions from the current state."""
        transitions = self.state_transitions.get(self.current_state, [])
        person = await sync_to_async(self.user.refresh_from_db)()
        available_transitions = []
        
        for transition in transitions:
            if await transition.is_valid_transition(person, self.context):
                available_transitions.append(transition.next_state)
                
        return available_transitions

    async def get_state_description(self, state: str) -> str:
        """Get the description of a state."""
        descriptions = {
            "initial": "Estado inicial",
            "waiting_for_tos": "Esperando aceptación de TOS",
            "profile_in_progress": "Creando perfil",
            "profile_complete": "Perfil completo",
            "applied": "Solicitud enviada",
            "scheduled": "Entrevista programada",
            "interviewed": "Entrevista completada",
            "offered": "Oferta recibida",
            "signed": "Contrato firmado",
            "hired": "Contratado",
            "idle": "Inactivo",
        }
        
        if self.business_unit.name.lower() == "amigro":
            descriptions["migratory_status"] = "Verificando estatus migratorio"
        elif self.business_unit.name.lower() == "huntu":
            descriptions["internship_search"] = "Buscando internships"
        elif self.business_unit.name.lower() == "huntred":
            descriptions["executive_search"] = "Buscando posiciones ejecutivas"
        
        return descriptions.get(state, "Estado desconocido")