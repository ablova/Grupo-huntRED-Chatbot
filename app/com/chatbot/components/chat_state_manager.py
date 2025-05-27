# /home/pablo/app/com/chatbot/components/chat_state_manager.py
from typing import Dict, Any, Optional, List, Tuple, TypedDict, Literal, Union, Callable, TypeVar, cast
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
from django.utils.translation import gettext as _
from redis.asyncio import Redis
from redis.exceptions import RedisError
import asyncio
import logging
import json
import re
from functools import lru_cache, wraps
from collections import defaultdict
from asgiref.sync import sync_to_async

# Import models directly to avoid circular imports
from app.models import Person, BusinessUnit, ChatState, IntentPattern, StateTransition, IntentTransition

# Defer importing utility classes
from app.com.chatbot.components.metrics import ChatBotMetrics

# Deferred imports
_chatbot_utils = None
_workflow_manager = None
_channel_handlers = {}

logger = logging.getLogger(__name__)

# Cache configuration
STATE_CACHE_KEY = 'chat_state_{}_{}_{}'
STATE_CACHE_TIMEOUT = 300  # 5 minutes
INTENT_CACHE_KEY = 'intent_cache_{}'
INTENT_CACHE_TIMEOUT = 60  # 1 minute
DESCRIPTION_CACHE_KEY = 'state_desc_{}_{}_{}'
DESCRIPTION_CACHE_TIMEOUT = 3600  # 1 hour

# Intent priority levels
INTENT_PRIORITY = {
    'CRITICAL': 5,
    'HIGH': 4,
    'MEDIUM': 3,
    'LOW': 2,
    'NONE': 1
}

# Type definitions
LanguageCode = Literal['es', 'en']
BusinessUnitName = Literal['amigro', 'huntu', 'huntred', 'default']
StateName = str
StateDescription = Dict[LanguageCode, str]

class StateDescriptionConfig(TypedDict):
    """Estructura de configuración para las descripciones de estados."""
    base: Dict[StateName, StateDescription]
    by_business_unit: Dict[BusinessUnitName, Dict[StateName, StateDescription]]

# Type variables
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

def handle_redis_errors(func: F) -> F:
    """Decorador para manejar errores de Redis."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RedisError as e:
            logger.error(f"Redis error in {func.__name__}: {str(e)}")
            raise ChatStateError(f"Error de almacenamiento: {str(e)}") from e
    return cast(F, wrapper)

# Consolidated ChatStateTransition class
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
    
    def __init__(self, user: Person, business_unit: BusinessUnit, channel: str, redis_client: Optional[Redis] = None):
        self.user = user
        self.business_unit = business_unit
        self.channel = channel.lower()
        self._channel_handler = None
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
        self.redis_client = redis_client or self._get_redis_client()
        self.state_transitions = self._initialize_state_transitions()
        self._initialized = False
        logger.info(f"ChatStateManager initialized for user {user.id}, channel {self.channel}")

    def _get_redis_client(self) -> Redis:
        """Crea y devuelve un cliente Redis configurado."""
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            max_connections=100  # Connection pooling
        )

    def _get_channel_handler(self, channel_type):
        """Get channel handler with lazy loading."""
        global _channel_handlers
        if channel_type not in _channel_handlers:
            if channel_type == 'whatsapp':
                from app.com.chatbot.integrations.services import get_whatsapp_handler
                _channel_handlers[channel_type] = get_whatsapp_handler()
            elif channel_type == 'telegram':
                from app.com.chatbot.integrations.services import get_telegram_handler
                _channel_handlers[channel_type] = get_telegram_handler()
            elif channel_type == 'instagram':
                from app.com.chatbot.integrations.services import get_instagram_handler
                _channel_handlers[channel_type] = get_instagram_handler()
            elif channel_type == 'slack':
                from app.com.chatbot.integrations.services import get_slack_handler
                _channel_handlers[channel_type] = get_slack_handler()
            else:
                raise ValueError(f"Canal no soportado: {channel_type}")
        return _channel_handlers[channel_type]

    async def channel_handler(self):
        """Obtiene el manejador de canal de forma perezosa."""
        if self._channel_handler is None:
            self._channel_handler = self._get_channel_handler(self.channel)
        return self._channel_handler

    @property
    def _state_descriptions(self) -> StateDescriptionConfig:
        """Configuración de descripciones de estados."""
        return {
            "base": {
                "initial": {"es": "Estado inicial", "en": "Initial state"},
                "waiting_for_tos": {"es": "Esperando aceptación de TOS", "en": "Waiting for TOS acceptance"},
                "profile_in_progress": {"es": "Creando perfil", "en": "Creating profile"},
                "profile_complete": {"es": "Perfil completo", "en": "Profile complete"},
                "applied": {"es": "Solicitud enviada", "en": "Application submitted"},
                "scheduled": {"es": "Entrevista programada", "en": "Interview scheduled"},
                "interviewed": {"es": "Entrevista completada", "en": "Interview completed"},
                "offered": {"es": "Oferta recibida", "en": "Offer received"},
                "signed": {"es": "Contrato firmado", "en": "Contract signed"},
                "hired": {"es": "Contratado", "en": "Hired"},
                "idle": {"es": "Inactivo", "en": "Idle"},
            },
            "by_business_unit": {
                "amigro": {
                    "migratory_status": {"es": "Verificando estatus migratorio", "en": "Verifying migratory status"},
                    "document_verification": {"es": "Verificación de documentos", "en": "Document verification"},
                },
                "huntu": {
                    "internship_search": {"es": "Buscando prácticas profesionales", "en": "Looking for internships"},
                    "academic_validation": {"es": "Validación académica", "en": "Academic validation"},
                },
                "huntred": {
                    "executive_search": {"es": "Buscando posiciones ejecutivas", "en": "Looking for executive positions"},
                    "leadership_assessment": {"es": "Evaluación de liderazgo", "en": "Leadership assessment"},
                }
            }
        }

    def _get_business_unit_name(self) -> BusinessUnitName:
        """Obtiene el nombre normalizado de la unidad de negocio."""
        if not self.business_unit or not self.business_unit.name:
            return 'default'
        name = self.business_unit.name.lower()
        return name if name in ['amigro', 'huntu', 'huntred'] else 'default'

    @lru_cache(maxsize=128)
    async def _get_cached_description(
        self, 
        state: str, 
        language: LanguageCode, 
        bu_name: BusinessUnitName
    ) -> str:
        """Obtiene una descripción de estado desde Redis o caché local."""
        cache_key = DESCRIPTION_CACHE_KEY.format(state, language, bu_name)
        try:
            cached_desc = await self.redis_client.get(cache_key)
            if cached_desc:
                return cached_desc

            bu_desc = self._state_descriptions["by_business_unit"].get(bu_name, {})
            if state in bu_desc:
                desc = bu_desc[state].get(language, bu_desc[state]['es'])
            else:
                base_desc = self._state_descriptions["base"].get(state, {})
                desc = base_desc.get(language, base_desc['es']) if base_desc else _("Estado desconocido: %(state)s") % {'state': state}

            await self.redis_client.setex(cache_key, DESCRIPTION_CACHE_TIMEOUT, desc)
            return desc
        except RedisError as e:
            logger.warning(f"Redis error in _get_cached_description: {str(e)}, falling back to local cache")
            bu_desc = self._state_descriptions["by_business_unit"].get(bu_name, {})
            if state in bu_desc:
                return bu_desc[state].get(language, bu_desc[state]['es'])
            base_desc = self._state_descriptions["base"].get(state, {})
            return base_desc.get(language, base_desc['es']) if base_desc else _("Estado desconocido: %(state)s") % {'state': state}

    def get_state_description(self, state: Optional[str] = None) -> str:
        """Obtiene la descripción de un estado con soporte multilingüe."""
        state = state or self.current_state
        if not state:
            return _("Estado no especificado")
        language: LanguageCode = self.context.get('language', 'es')
        bu_name: BusinessUnitName = self._get_business_unit_name()
        return self._get_cached_description(state, language, bu_name)

    def _initialize_state_transitions(self) -> Dict[str, List[ChatStateTransition]]:
        """Initialize business-unit-specific state transitions."""
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

        if self._get_business_unit_name() == "amigro":
            transitions["initial"].append(
                ChatStateTransition("initial", "migratory_status", {"has_migration_docs": True})
            )
            transitions["migratory_status"] = [
                ChatStateTransition("migratory_status", "document_verification", {"has_migration_docs": True}),
                ChatStateTransition("migratory_status", "initial")
            ]
        elif self._get_business_unit_name() == "huntu":
            transitions["profile_complete"].append(
                ChatStateTransition("profile_complete", "internship_search", {"is_student": True})
            )
            transitions["internship_search"] = [
                ChatStateTransition("internship_search", "academic_validation", {"has_profile": True}),
                ChatStateTransition("internship_search", "profile_complete")
            ]
        elif self._get_business_unit_name() == "huntred":
            transitions["profile_complete"].append(
                ChatStateTransition("profile_complete", "executive_search", {"has_executive_experience": True})
            )
            transitions["executive_search"] = [
                ChatStateTransition("executive_search", "leadership_assessment", {"has_profile": True}),
                ChatStateTransition("executive_search", "profile_complete")
            ]

        return transitions

    @handle_redis_errors
    async def get_state(self) -> Dict[str, Any]:
        """Retrieve the current state from Redis or database."""
        for attempt in range(self.max_retries):
            try:
                state_json = await self.redis_client.get(self.cache_key)
                if state_json:
                    return json.loads(state_json)
                return {}
            except RedisError as e:
                logger.error(f"Error retrieving state for user {self.user.id}, attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.critical(f"Failed to retrieve state for user {self.user.id}")
                    return {}
                await asyncio.sleep(1)

    @handle_redis_errors
    async def set_state(self, state: Dict[str, Any], ttl: int = None):
        """Set the current state in Redis."""
        for attempt in range(self.max_retries):
            try:
                state_json = json.dumps(state)
                if ttl:
                    await self.redis_client.setex(self.cache_key, ttl, state_json)
                else:
                    await self.redis_client.set(self.cache_key, state_json)
                logger.debug(f"State set for user {self.user.id}")
                return
            except RedisError as e:
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
        logger.debug(f"Updated field {field} for user {self.user.id}")

    @handle_redis_errors
    async def clear_state(self):
        """Clear the state from Redis."""
        for attempt in range(self.max_retries):
            try:
                await self.redis_client.delete(self.cache_key)
                logger.debug(f"State cleared for user {self.user.id}")
                return
            except RedisError as e:
                logger.error(f"Error clearing state for user {self.user.id}, attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.critical(f"Failed to clear state for user {self.user.id}")
                    raise
                await asyncio.sleep(1)

    @handle_redis_errors
    async def initialize(self):
        """Initialize chat state for a user."""
        if self._initialized:
            return
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
                logger.debug(f"Chat state loaded for user {self.user.id}")
                self._initialized = True
                return

            chat_state, created = await ChatState.objects.aget_or_create(
                person=self.user,
                business_unit=self.business_unit,
                defaults={'state': 'initial'}
            )
            
            self.metrics.increment('new_conversation' if created else 'existing_conversation')
            self.current_state = chat_state.state
            self.last_intent = None
            self.conversation_history = []
            self.context = {'language': 'es'}
            self.context_stack = []
            
            await self.set_state({
                'state': self.current_state,
                'last_intent': self.last_intent,
                'history': self.conversation_history,
                'context': self.context,
                'context_stack': self.context_stack,
                'metrics': dict(self.metrics),
                'created_at': timezone.now().isoformat(),
                'updated_at': timezone.now().isoformat()
            })
            self._initialized = True
        except Exception as e:
            logger.error(f"Error initializing chat state: {str(e)}")
            raise ChatStateError(f"Error initializing chat state: {str(e)}")

    async def update_state(self, new_state: str, intent: Optional[str] = None):
        """Update the current state with async support and metrics."""
        try:
            logger.info(f"Updating state for user {self.user.id} from {self.current_state} to {new_state}, intent: {intent or 'None'}")
            if self.current_state != new_state:
                if await self._is_valid_transition(self.current_state, new_state):
                    old_state = self.current_state
                    self.current_state = new_state
                    if intent:
                        self.last_intent = intent
                        self.metrics.increment(f'intent_{intent}')
                    self.metrics.increment('state_transitions')

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
                    raise StateTransitionError(f"Invalid transition from {self.current_state} to {new_state}")

            await self.set_state({
                'state': self.current_state,
                'last_intent': self.last_intent,
                'history': self.conversation_history,
                'context': self.context,
                'context_stack': self.context_stack,
                'metrics': dict(self.metrics),
                'updated_at': timezone.now().isoformat()
            })
            logger.debug(f"State updated for user {self.user.id} to {new_state}")
        except Exception as e:
            logger.error(f"Error updating state for user {self.user.id}: {str(e)}")
            self.error_count += 1
            self.metrics.increment('state_update_errors')
            raise ChatStateError(f"Error updating state: {str(e)}")

    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and update the chat state."""
        start_time = timezone.now()
        try:
            global _chatbot_utils, _workflow_manager
            if _chatbot_utils is None:
                from app.com.chatbot.utils import ChatbotUtils
                _chatbot_utils = ChatbotUtils
            if _workflow_manager is None:
                from app.com.chatbot.workflow.core.workflow_manager import WorkflowManager
                _workflow_manager = WorkflowManager

            self.metrics.increment('messages_processed')
            self.conversation_history.append({
                'text': message,
                'timestamp': start_time.isoformat(),
                'intent': None,
                'values': self.context.get('values', {})
            })

            analysis = await _chatbot_utils.analyze_text(message, self.business_unit)
            intent = await self._get_intent(analysis)
            self.last_intent = intent
            self.conversation_history[-1]['intent'] = intent

            if 'entities' in analysis:
                for entity, value in analysis['entities'].items():
                    await self.set_context(entity, value)

            workflow = _workflow_manager(self._get_business_unit_name())
            new_state = await workflow.process_intent(self, intent, analysis)

            if not new_state:
                transitions = await IntentTransition.objects.filter(
                    intent__name=intent,
                    business_unit=self.business_unit
                ).select_related('target_state').prefetch_related('conditions').all()

                for transition in transitions:
                    if await self._check_conditions(transition.conditions):
                        new_state = transition.target_state.name
                        break

                if not new_state:
                    available_transitions = await self.get_available_transitions()
                    new_state = available_transitions[0] if available_transitions else self.current_state

            old_state = self.current_state
            if new_state and new_state != old_state:
                await self.update_state(new_state, intent)

            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            self.metrics.add('response_time', response_time)

            await self.set_state({
                'state': self.current_state,
                'last_intent': self.last_intent,
                'history': self.conversation_history,
                'context': self.context,
                'context_stack': self.context_stack,
                'metrics': dict(self.metrics),
                'updated_at': timezone.now().isoformat()
            })

            logger.debug(f"Processed message for user {self.user.id}, intent: {intent}, state: {self.current_state}")
            return {'state': self.current_state, 'intent': intent}
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.error_count += 1
            self.metrics.increment('message_processing_errors')
            return {'state': self.current_state, 'intent': None}

    async def _is_valid_transition(self, current_state: str, new_state: str) -> bool:
        """Verify if a state transition is valid."""
        try:
            person = await sync_to_async(lambda: self.user)()
            transitions = self.state_transitions.get(current_state, [])
            valid_transitions = [t for t in transitions if t.next_state == new_state]
            for transition in valid_transitions:
                if await transition.is_valid_transition(person, self.context):
                    return True

            db_transitions = await StateTransition.objects.filter(
                current_state=current_state,
                next_state=new_state,
                business_unit=self.business_unit
            ).prefetch_related('conditions').values('id', 'priority', 'conditions')
            
            for transition in db_transitions:
                if await self._check_conditions(transition['conditions']):
                    return True

            handler = await self.channel_handler()
            if handler:
                return await handler.is_valid_transition(
                    current_state=current_state,
                    new_state=new_state,
                    context=self.context
                )

            return False
        except (ValueError, TypeError) as e:
            logger.error(f"Error verifying transition: {str(e)}")
            return False

    @handle_redis_errors
    async def _get_intent(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Get the most likely intent from analysis using Redis caching."""
        try:
            cache_key = f"{INTENT_CACHE_KEY}_{self.user.id}"
            cached_intent = await self.redis_client.get(cache_key)
            if cached_intent:
                return cached_intent

            intents = await IntentPattern.objects.filter(
                business_unit=self.business_unit
            ).prefetch_related('patterns').all()
            
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
                await self.redis_client.setex(cache_key, INTENT_CACHE_TIMEOUT, best_intent)
                return best_intent
            
            return None
        except RedisError as e:
            logger.error(f"Error getting intent: {str(e)}")
            return None

    @handle_redis_errors
    async def _evaluate_intent(self, intent: IntentPattern, analysis: Dict[str, Any]) -> float:
        """Evaluate the likelihood of an intent with caching."""
        try:
            cache_key = f"intent_eval_{intent.id}_{hash(str(analysis))}"
            cached_score = await self.redis_client.get(cache_key)
            if cached_score:
                return float(cached_score)

            patterns = intent.get_patterns_list()
            score = 0
            for pattern in patterns:
                similarity = await _chatbot_utils.analyze_text(
                    pattern, analysis['text'], method='similarity'
                )
                score = max(score, similarity)
            
            handler = await self.channel_handler()
            if handler:
                score = await handler.adjust_intent_score(
                    intent=intent, score=score, context=self.context
                )
            
            await self.redis_client.setex(cache_key, INTENT_CACHE_TIMEOUT, str(score))
            return score
        except RedisError as e:
            logger.error(f"Error evaluating intent: {str(e)}")
            return 0

    async def _check_conditions(self, conditions: List[Dict]) -> bool:
        """Check if transition conditions are met."""
        try:
            for condition in conditions:
                if not await self._check_condition(condition):
                    return False
            return True
        except (ValueError, TypeError) as e:
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
            
            handler = await self.channel_handler()
            if handler:
                return await handler.check_condition(
                    condition=condition, context=self.context
                )
                
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"Error checking condition: {str(e)}")
            return False

    async def get_context(self, key: str, default=None):
        """Get a value from the context."""
        value = self.context.get(key, default)
        self.metrics.increment('context_access')
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
            'metrics': dict(self.metrics),
            'updated_at': timezone.now().isoformat()
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
            'metrics': dict(self.metrics),
            'updated_at': timezone.now().isoformat()
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
                'metrics': dict(self.metrics),
                'updated_at': timezone.now().isoformat()
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
        person = await sync_to_async(lambda: self.user)()
        available_transitions = []
        
        for transition in transitions:
            if await transition.is_valid_transition(person, self.context):
                available_transitions.append(transition.next_state)
                
        return available_transitions

    async def close(self) -> None:
        """Limpia los recursos del manejador de estado."""
        if hasattr(self, 'redis_client') and self.redis_client:
            await self.redis_client.aclose()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# Custom exceptions
class ChatStateError(Exception):
    """Excepción base para errores de estado del chat."""
    pass

class StateTransitionError(ChatStateError):
    """Excepción para transiciones de estado no válidas."""
    pass