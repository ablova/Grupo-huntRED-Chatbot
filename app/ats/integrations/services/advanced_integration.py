"""
INTEGRACIÓN AVANZADA - Grupo huntRED®
Sistema de integración con APIs, webhooks, sincronización en tiempo real y gestión de errores
"""

import logging
import json
import asyncio
import aiohttp
import websockets
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac
import base64

from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Tipos de integración"""
    API = "api"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    FILE_SYNC = "file_sync"
    DATABASE = "database"

class IntegrationStatus(Enum):
    """Estados de integración"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"
    MAINTENANCE = "maintenance"

@dataclass
class IntegrationConfig:
    """Configuración de integración"""
    name: str
    type: IntegrationType
    endpoint: str
    api_key: str = ""
    secret_key: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    webhook_url: str = ""
    webhook_secret: str = ""
    sync_interval: int = 300  # 5 minutos
    enabled: bool = True

@dataclass
class IntegrationEvent:
    """Evento de integración"""
    id: str
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    status: str = "pending"
    retry_count: int = 0
    error_message: str = ""

@dataclass
class WebhookPayload:
    """Payload de webhook"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    signature: str = ""
    source: str = ""

class AdvancedIntegration:
    """
    Sistema de integración avanzado
    """
    
    def __init__(self):
        self.integrations = {}
        self.webhook_handlers = {}
        self.websocket_connections = {}
        self.event_queue = asyncio.Queue()
        self.sync_tasks = {}
        self.metrics = {
            'api_calls': 0,
            'webhook_events': 0,
            'websocket_messages': 0,
            'sync_operations': 0,
            'errors': 0,
            'success_rate': 0.0
        }
        
        # Configurar integraciones por defecto
        self._setup_default_integrations()
        
        # Iniciar procesamiento de eventos
        asyncio.create_task(self._process_event_queue())
    
    def _setup_default_integrations(self):
        """Configura integraciones por defecto"""
        default_integrations = {
            'google_calendar': IntegrationConfig(
                name='Google Calendar',
                type=IntegrationType.API,
                endpoint='https://www.googleapis.com/calendar/v3',
                sync_interval=300
            ),
            'linkedin_jobs': IntegrationConfig(
                name='LinkedIn Jobs',
                type=IntegrationType.API,
                endpoint='https://api.linkedin.com/v2',
                sync_interval=600
            ),
            'indeed_jobs': IntegrationConfig(
                name='Indeed Jobs',
                type=IntegrationType.API,
                endpoint='https://api.indeed.com',
                sync_interval=600
            ),
            'slack_notifications': IntegrationConfig(
                name='Slack Notifications',
                type=IntegrationType.WEBHOOK,
                webhook_url='https://hooks.slack.com/services/',
                sync_interval=60
            ),
            'email_service': IntegrationConfig(
                name='Email Service',
                type=IntegrationType.API,
                endpoint='https://api.sendgrid.com/v3',
                sync_interval=120
            )
        }
        
        for key, config in default_integrations.items():
            self.add_integration(key, config)
    
    def add_integration(self, key: str, config: IntegrationConfig):
        """Agrega una nueva integración"""
        try:
            self.integrations[key] = {
                'config': config,
                'status': IntegrationStatus.INACTIVE,
                'last_sync': None,
                'error_count': 0,
                'success_count': 0
            }
            
            logger.info(f"✅ Integración agregada: {config.name}")
            
            # Iniciar sincronización si está habilitada
            if config.enabled:
                self.start_integration(key)
                
        except Exception as e:
            logger.error(f"❌ Error agregando integración {key}: {e}")
    
    def start_integration(self, key: str):
        """Inicia una integración"""
        try:
            integration = self.integrations.get(key)
            if not integration:
                return False
            
            config = integration['config']
            
            if config.type == IntegrationType.API:
                # Iniciar sincronización periódica
                task = asyncio.create_task(self._sync_api_integration(key))
                self.sync_tasks[key] = task
                
            elif config.type == IntegrationType.WEBHOOK:
                # Configurar webhook
                self._setup_webhook(key)
                
            elif config.type == IntegrationType.WEBSOCKET:
                # Iniciar conexión WebSocket
                asyncio.create_task(self._connect_websocket(key))
            
            integration['status'] = IntegrationStatus.ACTIVE
            logger.info(f"🚀 Integración iniciada: {config.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando integración {key}: {e}")
            return False
    
    def stop_integration(self, key: str):
        """Detiene una integración"""
        try:
            integration = self.integrations.get(key)
            if not integration:
                return False
            
            # Cancelar tarea de sincronización
            if key in self.sync_tasks:
                self.sync_tasks[key].cancel()
                del self.sync_tasks[key]
            
            integration['status'] = IntegrationStatus.INACTIVE
            logger.info(f"⏹️ Integración detenida: {integration['config'].name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deteniendo integración {key}: {e}")
            return False
    
    async def _sync_api_integration(self, key: str):
        """Sincroniza integración API"""
        integration = self.integrations[key]
        config = integration['config']
        
        while True:
            try:
                logger.info(f"🔄 Sincronizando {config.name}")
                
                # Realizar llamada API
                data = await self._make_api_call(key)
                
                if data:
                    # Procesar datos
                    await self._process_integration_data(key, data)
                    
                    # Actualizar métricas
                    integration['success_count'] += 1
                    integration['last_sync'] = timezone.now()
                    self.metrics['sync_operations'] += 1
                    
                    logger.info(f"✅ Sincronización exitosa: {config.name}")
                
                # Esperar intervalo
                await asyncio.sleep(config.sync_interval)
                
            except asyncio.CancelledError:
                logger.info(f"🛑 Sincronización cancelada: {config.name}")
                break
            except Exception as e:
                logger.error(f"❌ Error en sincronización {config.name}: {e}")
                integration['error_count'] += 1
                self.metrics['errors'] += 1
                
                # Esperar antes de reintentar
                await asyncio.sleep(config.retry_delay)
    
    async def _make_api_call(self, key: str) -> Optional[Dict[str, Any]]:
        """Realiza llamada API"""
        try:
            integration = self.integrations[key]
            config = integration['config']
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'huntRED-Integration/1.0'
            }
            
            # Agregar headers personalizados
            headers.update(config.headers)
            
            # Agregar autenticación si existe
            if config.api_key:
                headers['Authorization'] = f'Bearer {config.api_key}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    config.endpoint,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        self.metrics['api_calls'] += 1
                        return data
                    else:
                        logger.error(f"❌ API error {response.status}: {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Error en llamada API {key}: {e}")
            return None
    
    async def _process_integration_data(self, key: str, data: Dict[str, Any]):
        """Procesa datos de integración"""
        try:
            # Crear evento de integración
            event = IntegrationEvent(
                id=f"{key}_{int(timezone.now().timestamp())}",
                type=f"{key}_sync",
                data=data,
                timestamp=timezone.now(),
                source=key
            )
            
            # Agregar a cola de eventos
            await self.event_queue.put(event)
            
            # Cachear datos
            cache_key = f"integration_data:{key}"
            cache.set(cache_key, data, 3600)  # 1 hora
            
        except Exception as e:
            logger.error(f"❌ Error procesando datos de integración {key}: {e}")
    
    def _setup_webhook(self, key: str):
        """Configura webhook"""
        try:
            integration = self.integrations[key]
            config = integration['config']
            
            # Registrar handler de webhook
            self.webhook_handlers[key] = {
                'url': config.webhook_url,
                'secret': config.webhook_secret,
                'config': config
            }
            
            logger.info(f"🔗 Webhook configurado: {config.name}")
            
        except Exception as e:
            logger.error(f"❌ Error configurando webhook {key}: {e}")
    
    async def handle_webhook(self, key: str, payload: WebhookPayload) -> bool:
        """Maneja webhook entrante"""
        try:
            handler = self.webhook_handlers.get(key)
            if not handler:
                return False
            
            # Verificar firma si existe
            if handler['secret'] and not self._verify_webhook_signature(payload, handler['secret']):
                logger.warning(f"⚠️ Firma de webhook inválida: {key}")
                return False
            
            # Crear evento
            event = IntegrationEvent(
                id=f"webhook_{int(timezone.now().timestamp())}",
                type=payload.event_type,
                data=payload.data,
                timestamp=payload.timestamp,
                source=key
            )
            
            # Agregar a cola
            await self.event_queue.put(event)
            
            self.metrics['webhook_events'] += 1
            logger.info(f"📥 Webhook procesado: {key} - {payload.event_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error procesando webhook {key}: {e}")
            return False
    
    def _verify_webhook_signature(self, payload: WebhookPayload, secret: str) -> bool:
        """Verifica firma de webhook"""
        try:
            if not payload.signature:
                return False
            
            # Crear firma esperada
            message = f"{payload.event_type}.{json.dumps(payload.data)}.{payload.timestamp.isoformat()}"
            expected_signature = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(payload.signature, expected_signature)
            
        except Exception as e:
            logger.error(f"❌ Error verificando firma: {e}")
            return False
    
    async def _connect_websocket(self, key: str):
        """Conecta WebSocket"""
        try:
            integration = self.integrations[key]
            config = integration['config']
            
            uri = config.endpoint.replace('https://', 'wss://').replace('http://', 'ws://')
            
            async with websockets.connect(uri) as websocket:
                self.websocket_connections[key] = websocket
                
                logger.info(f"🔌 WebSocket conectado: {config.name}")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        # Procesar mensaje
                        await self._process_websocket_message(key, data)
                        
                        self.metrics['websocket_messages'] += 1
                        
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ Mensaje WebSocket inválido: {key}")
                    except Exception as e:
                        logger.error(f"❌ Error procesando mensaje WebSocket: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error conectando WebSocket {key}: {e}")
            # Reintentar conexión
            await asyncio.sleep(5)
            asyncio.create_task(self._connect_websocket(key))
    
    async def _process_websocket_message(self, key: str, data: Dict[str, Any]):
        """Procesa mensaje WebSocket"""
        try:
            event = IntegrationEvent(
                id=f"ws_{int(timezone.now().timestamp())}",
                type=f"{key}_message",
                data=data,
                timestamp=timezone.now(),
                source=key
            )
            
            await self.event_queue.put(event)
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje WebSocket {key}: {e}")
    
    async def _process_event_queue(self):
        """Procesa cola de eventos"""
        while True:
            try:
                event = await self.event_queue.get()
                
                # Procesar evento según tipo
                if event.type.endswith('_sync'):
                    await self._handle_sync_event(event)
                elif event.type.endswith('_message'):
                    await self._handle_message_event(event)
                else:
                    await self._handle_generic_event(event)
                
                # Marcar como completado
                event.status = "completed"
                
            except Exception as e:
                logger.error(f"❌ Error procesando evento: {e}")
                if event:
                    event.status = "error"
                    event.error_message = str(e)
    
    async def _handle_sync_event(self, event: IntegrationEvent):
        """Maneja evento de sincronización"""
        try:
            # Actualizar datos en el sistema
            await self._update_system_data(event.source, event.data)
            
            # Notificar cambios
            await self._notify_data_changes(event.source, event.data)
            
            logger.info(f"🔄 Evento de sincronización procesado: {event.source}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando evento de sincronización: {e}")
    
    async def _handle_message_event(self, event: IntegrationEvent):
        """Maneja evento de mensaje"""
        try:
            # Procesar mensaje según tipo
            message_type = event.data.get('type', 'unknown')
            
            if message_type == 'notification':
                await self._handle_notification(event.data)
            elif message_type == 'update':
                await self._handle_update(event.data)
            elif message_type == 'alert':
                await self._handle_alert(event.data)
            else:
                logger.info(f"📨 Mensaje recibido: {message_type}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando evento de mensaje: {e}")
    
    async def _handle_generic_event(self, event: IntegrationEvent):
        """Maneja evento genérico"""
        try:
            logger.info(f"📋 Evento genérico procesado: {event.type}")
            
            # Implementar lógica específica según el tipo de evento
            if 'job' in event.type:
                await self._handle_job_event(event)
            elif 'candidate' in event.type:
                await self._handle_candidate_event(event)
            elif 'interview' in event.type:
                await self._handle_interview_event(event)
            
        except Exception as e:
            logger.error(f"❌ Error manejando evento genérico: {e}")
    
    async def _update_system_data(self, source: str, data: Dict[str, Any]):
        """Actualiza datos en el sistema"""
        try:
            # Implementar actualización según la fuente
            if source == 'google_calendar':
                await self._update_calendar_data(data)
            elif source == 'linkedin_jobs':
                await self._update_job_data(data)
            elif source == 'indeed_jobs':
                await self._update_job_data(data)
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos del sistema: {e}")
    
    async def _notify_data_changes(self, source: str, data: Dict[str, Any]):
        """Notifica cambios de datos"""
        try:
            # Enviar notificaciones a usuarios relevantes
            notification_data = {
                'type': 'integration_update',
                'source': source,
                'data': data,
                'timestamp': timezone.now().isoformat()
            }
            
            # Aquí se integraría con el sistema de notificaciones
            logger.info(f"🔔 Notificación enviada: {source}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
    
    async def _handle_notification(self, data: Dict[str, Any]):
        """Maneja notificación"""
        try:
            # Procesar notificación
            logger.info(f"📢 Notificación procesada: {data.get('message', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando notificación: {e}")
    
    async def _handle_update(self, data: Dict[str, Any]):
        """Maneja actualización"""
        try:
            # Procesar actualización
            logger.info(f"🔄 Actualización procesada: {data.get('entity', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando actualización: {e}")
    
    async def _handle_alert(self, data: Dict[str, Any]):
        """Maneja alerta"""
        try:
            # Procesar alerta
            logger.warning(f"🚨 Alerta procesada: {data.get('message', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando alerta: {e}")
    
    async def _handle_job_event(self, event: IntegrationEvent):
        """Maneja evento de trabajo"""
        try:
            # Procesar evento de trabajo
            job_data = event.data
            
            # Actualizar base de datos
            # await Job.objects.update_or_create(...)
            
            logger.info(f"💼 Evento de trabajo procesado: {job_data.get('title', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando evento de trabajo: {e}")
    
    async def _handle_candidate_event(self, event: IntegrationEvent):
        """Maneja evento de candidato"""
        try:
            # Procesar evento de candidato
            candidate_data = event.data
            
            # Actualizar base de datos
            # await Candidate.objects.update_or_create(...)
            
            logger.info(f"👤 Evento de candidato procesado: {candidate_data.get('name', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando evento de candidato: {e}")
    
    async def _handle_interview_event(self, event: IntegrationEvent):
        """Maneja evento de entrevista"""
        try:
            # Procesar evento de entrevista
            interview_data = event.data
            
            # Actualizar base de datos
            # await Interview.objects.update_or_create(...)
            
            logger.info(f"🎯 Evento de entrevista procesado: {interview_data.get('id', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error manejando evento de entrevista: {e}")
    
    async def _update_calendar_data(self, data: Dict[str, Any]):
        """Actualiza datos de calendario"""
        try:
            # Procesar eventos de calendario
            events = data.get('items', [])
            
            for event in events:
                # Actualizar eventos en el sistema
                logger.info(f"📅 Evento de calendario: {event.get('summary', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos de calendario: {e}")
    
    async def _update_job_data(self, data: Dict[str, Any]):
        """Actualiza datos de trabajos"""
        try:
            # Procesar trabajos
            jobs = data.get('jobs', [])
            
            for job in jobs:
                # Actualizar trabajos en el sistema
                logger.info(f"💼 Trabajo actualizado: {job.get('title', '')}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos de trabajos: {e}")
    
    def get_integration_status(self, key: str) -> Dict[str, Any]:
        """Obtiene estado de una integración"""
        try:
            integration = self.integrations.get(key)
            if not integration:
                return {}
            
            config = integration['config']
            
            return {
                'name': config.name,
                'type': config.type.value,
                'status': integration['status'].value,
                'last_sync': integration['last_sync'].isoformat() if integration['last_sync'] else None,
                'error_count': integration['error_count'],
                'success_count': integration['success_count'],
                'enabled': config.enabled
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de integración: {e}")
            return {}
    
    def get_all_integrations(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todas las integraciones"""
        try:
            return {
                key: self.get_integration_status(key)
                for key in self.integrations.keys()
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo integraciones: {e}")
            return {}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema de integración"""
        try:
            total_operations = (
                self.metrics['api_calls'] + 
                self.metrics['webhook_events'] + 
                self.metrics['websocket_messages'] + 
                self.metrics['sync_operations']
            )
            
            success_rate = (
                (total_operations - self.metrics['errors']) / max(total_operations, 1) * 100
            )
            
            return {
                'api_calls': self.metrics['api_calls'],
                'webhook_events': self.metrics['webhook_events'],
                'websocket_messages': self.metrics['websocket_messages'],
                'sync_operations': self.metrics['sync_operations'],
                'errors': self.metrics['errors'],
                'success_rate': round(success_rate, 2),
                'active_integrations': len([i for i in self.integrations.values() if i['status'] == IntegrationStatus.ACTIVE]),
                'total_integrations': len(self.integrations),
                'last_updated': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas: {e}")
            return {}

# Instancia global
advanced_integration = AdvancedIntegration() 