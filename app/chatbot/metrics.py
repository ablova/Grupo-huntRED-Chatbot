import asyncio
import time
from typing import Dict, Any, Optional
import logging
from app.chatbot.channel_config import ChannelConfig

logger = logging.getLogger(__name__)

class ChatBotMetrics:
    def __init__(self):
        self.metrics = {
            'delivery_rate': {},
            'response_time': {},
            'error_rate': {},
            'active_users': {},
            'messages_sent': {},
            'messages_received': {}
        }
        self.last_collection = time.time()
        self.collection_interval = 60  # 1 minuto

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
        """Registra una métrica de mensaje."""
        if channel not in self.metrics['messages_sent']:
            self.metrics['messages_sent'][channel] = 0
            self.metrics['messages_received'][channel] = 0
            self.metrics['response_time'][channel] = []
            self.metrics['error_rate'][channel] = 0

        if action == 'sent':
            self.metrics['messages_sent'][channel] += 1
        elif action == 'received':
            self.metrics['messages_received'][channel] += 1
            if response_time:
                self.metrics['response_time'][channel].append(response_time)

        if not success:
            self.metrics['error_rate'][channel] += 1

    def track_user_activity(self, channel: str, user_id: str):
        """Registra actividad de usuario."""
        if channel not in self.metrics['active_users']:
            self.metrics['active_users'][channel] = set()
        self.metrics['active_users'][channel].add(user_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene las métricas actuales."""
        return self.metrics

# Instancia global
chatbot_metrics = ChatBotMetrics()

# Iniciar recolección de métricas
async def start_metrics_collection():
    await chatbot_metrics.collect_metrics()
