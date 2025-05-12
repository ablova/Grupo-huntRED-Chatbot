import asyncio
import time
from typing import Dict, Any, Optional
import logging
from app.com.chatbot.channel_config import ChannelConfig

logger = logging.getLogger(__name__)

class ChatBotMetrics:
    def __init__(self):
        self.metrics = {
            'delivery_rate': {},
            'response_time': {},
            'error_rate': {},
            'active_users': {},
            'messages_sent': {},
            'messages_received': {},
            'state_transitions': {},
            'context_metrics': {},
            'intent_metrics': {},
            'fallback_metrics': {},
            'redis_metrics': {},
            'intent_processing_time': {},
            'intent_error_rate': {}
        }
        self.last_collection = time.time()
        self.collection_interval = 60  # 1 minuto
        self.state_transitions = {}
        self.intent_counts = {}
        self.context_hits = {}
        self.context_misses = {}
        self.fallback_triggers = {}
        self.redis_operations = {}
        self.error_count = 0
        self.max_error_threshold = 5
        self.cache_timeout = 3600  # 1 hora

    async def collect_metrics(self):
        """Recopila métricas periódicamente."""
        while True:
            await asyncio.sleep(self.collection_interval)
            self._process_metrics()

    def _process_metrics(self):
        """Procesa y registra las métricas."""
        current_time = time.time()
        
        # Calcular métricas por canal
        for channel, config in ChannelConfig.get_config().items():
            if not config['metrics']['enabled']:
                continue
                
            # Delivery rate
            if channel in self.metrics['messages_sent'] and channel in self.metrics['messages_received']:
                sent = self.metrics['messages_sent'][channel]
                received = self.metrics['messages_received'][channel]
                self.metrics['delivery_rate'][channel] = (received / sent) * 100 if sent > 0 else 0
                
            # Response time
            if channel in self.metrics['response_time']:
                avg_response_time = sum(self.metrics['response_time'][channel]) / len(self.metrics['response_time'][channel])
                self.metrics['response_time'][channel] = avg_response_time
                
            # Error rate
            if channel in self.metrics['error_rate']:
                error_rate = (self.metrics['error_rate'][channel] / self.metrics['messages_sent'][channel]) * 100
                self.metrics['error_rate'][channel] = error_rate
                
            # Active users
            if channel in self.metrics['active_users']:
                self.metrics['active_users'][channel] = len(self.metrics['active_users'][channel])

        # Reset counters
        self.metrics['messages_sent'] = {}
        self.metrics['messages_received'] = {}
        self.metrics['response_time'] = {}
        self.metrics['error_rate'] = {}
        self.metrics['active_users'] = {}

    def track_message(self, channel: str, action: str, success: bool = True, response_time: float = None):
        """Registra métricas de mensaje con soporte para estados y contexto."""
        if channel not in self.metrics['messages_sent']:
            self._initialize_channel_metrics(channel)

        if action == 'sent':
            self.metrics['messages_sent'][channel] += 1
        elif action == 'received':
            self.metrics['messages_received'][channel] += 1
            if response_time:
                self.metrics['response_time'][channel].append(response_time)

        if not success:
            self.metrics['error_rate'][channel] += 1
            self.error_count += 1

    def track_state_transition(self, from_state: str, to_state: str):
        """Registra una transición de estado."""
        transition_key = f"{from_state}->{to_state}"
        self.state_transitions[transition_key] += 1
        self.metrics['state_transitions'][transition_key] = self.state_transitions[transition_key]

    def track_intent(self, intent: str):
        """Registra un intent."""
        self.intent_counts[intent] += 1
        self.metrics['intent_metrics'][intent] = self.intent_counts[intent]

    def track_context(self, hit: bool, key: str = None):
        """Registra métricas de contexto."""
        if hit:
            self.context_hits[key] += 1
            self.metrics['context_metrics']['hits'] = sum(self.context_hits.values())
        else:
            self.context_misses[key] += 1
            self.metrics['context_metrics']['misses'] = sum(self.context_misses.values())

    def track_fallback(self, trigger: str):
        """Registra un trigger de fallback."""
        self.fallback_triggers[trigger] += 1
        self.metrics['fallback_metrics'][trigger] = self.fallback_triggers[trigger]

    def track_redis_operation(self, operation: str):
        """Registra operaciones de Redis."""
        self.redis_operations[operation] += 1
        self.metrics['redis_metrics'][operation] = self.redis_operations[operation]

    def _initialize_channel_metrics(self, channel: str):
        """Inicializa métricas para un nuevo canal."""
        self.metrics['messages_sent'][channel] = 0
        self.metrics['messages_received'][channel] = 0
        self.metrics['response_time'][channel] = []
        self.metrics['error_rate'][channel] = 0
        self.metrics['active_users'][channel] = set()

    def track_user_activity(self, channel: str, user_id: str):
        """Registra actividad de usuario."""
        if channel not in self.metrics['active_users']:
            self.metrics['active_users'][channel] = set()
        self.metrics['active_users'][channel].add(user_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas detalladas del chatbot."""
        metrics = {
            'channels': {},
            'states': {},
            'context': {},
            'performance': {},
            'errors': {}
        }

        # Métricas por canal
        for channel in self.metrics['messages_sent']:
            metrics['channels'][channel] = {
                'delivery_rate': self.metrics['delivery_rate'].get(channel, 0),
                'avg_response_time': sum(self.metrics['response_time'][channel]) / 
                                   len(self.metrics['response_time'][channel]) if self.metrics['response_time'][channel] else 0,
                'error_rate': self.metrics['error_rate'][channel],
                'active_users': len(self.metrics['active_users'][channel])
            }

        # Métricas de estados
        metrics['states'] = {
            'transitions': dict(self.state_transitions),
            'total_transitions': sum(self.state_transitions.values())
        }

        # Métricas de contexto
        metrics['context'] = {
            'hits': dict(self.context_hits),
            'misses': dict(self.context_misses),
            'hit_rate': sum(self.context_hits.values()) / 
                      (sum(self.context_hits.values()) + sum(self.context_misses.values())) if 
                      (sum(self.context_hits.values()) + sum(self.context_misses.values())) > 0 else 0
        }

        # Métricas de rendimiento
        metrics['performance'] = {
            'redis_operations': dict(self.redis_operations),
            'intent_counts': dict(self.intent_counts),
            'fallback_triggers': dict(self.fallback_triggers)
        }

        # Métricas de errores
        metrics['errors'] = {
            'total_errors': self.error_count,
            'error_rate': self.error_count / 
                        (sum(self.metrics['messages_sent'].values()) + 1e-6),
            'exceeded_threshold': self.error_count >= self.max_error_threshold
        }

        return metrics

# Instancia global
chatbot_metrics = ChatBotMetrics()

# Iniciar recolección de métricas
async def start_metrics_collection():
    await chatbot_metrics.collect_metrics()
