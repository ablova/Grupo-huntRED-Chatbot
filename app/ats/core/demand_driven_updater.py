"""
Sistema de Actualizaciones Bajo Demanda
Reemplaza las actualizaciones automáticas cada 30 segundos con un sistema inteligente
que solo actualiza cuando es necesario.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from django.core.cache import cache
from django.conf import settings

from .global_orchestrator import global_orchestrator, ModuleType, OperationPriority, OperationRequest

logger = logging.getLogger(__name__)

class UpdateTrigger(Enum):
    """Tipos de triggers para actualizaciones"""
    USER_REQUEST = "user_request"
    DATA_CHANGE = "data_change"
    TIME_BASED = "time_based"
    SYSTEM_EVENT = "system_event"
    PERFORMANCE_ALERT = "performance_alert"
    ML_INSIGHT = "ml_insight"

class UpdatePriority(Enum):
    """Prioridades de actualización"""
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"

@dataclass
class UpdateRequest:
    """Solicitud de actualización"""
    request_id: str
    module_type: ModuleType
    update_type: str
    trigger: UpdateTrigger
    priority: UpdatePriority
    data: Dict[str, Any]
    callback: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    timeout: int = 300

@dataclass
class UpdateCache:
    """Cache de actualizaciones"""
    last_update: datetime
    data_hash: str
    update_count: int = 0
    last_trigger: Optional[UpdateTrigger] = None

class DemandDrivenUpdater:
    """
    Sistema de actualizaciones bajo demanda que evita sobrecargas del servidor
    """
    
    def __init__(self):
        self.update_cache: Dict[str, UpdateCache] = {}
        self.pending_updates: Dict[str, UpdateRequest] = {}
        self.update_history: List[UpdateRequest] = []
        self.update_callbacks: Dict[str, Callable] = {}
        
        # Configuración de actualizaciones
        self.update_config = {
            'min_interval_seconds': 60,  # Mínimo 1 minuto entre actualizaciones
            'max_concurrent_updates': 5,
            'cache_timeout_hours': 24,
            'data_change_threshold': 0.1,  # 10% de cambio mínimo
            'performance_threshold': 0.8,  # 80% de carga
            'ml_insight_cooldown': 300,  # 5 minutos entre insights ML
        }
        
        # Triggers específicos por módulo
        self.module_triggers = {
            ModuleType.PUBLISH: {
                'campaign_created': UpdateTrigger.DATA_CHANGE,
                'campaign_launched': UpdateTrigger.SYSTEM_EVENT,
                'performance_alert': UpdateTrigger.PERFORMANCE_ALERT,
                'ml_insight': UpdateTrigger.ML_INSIGHT,
                'user_dashboard': UpdateTrigger.USER_REQUEST,
            },
            ModuleType.NOTIFICATIONS: {
                'new_notification': UpdateTrigger.DATA_CHANGE,
                'notification_sent': UpdateTrigger.SYSTEM_EVENT,
                'rate_limit_reached': UpdateTrigger.PERFORMANCE_ALERT,
                'strategic_insight': UpdateTrigger.ML_INSIGHT,
                'user_preferences': UpdateTrigger.USER_REQUEST,
            },
            ModuleType.CHATBOT: {
                'new_message': UpdateTrigger.DATA_CHANGE,
                'session_started': UpdateTrigger.SYSTEM_EVENT,
                'model_update': UpdateTrigger.ML_INSIGHT,
                'user_query': UpdateTrigger.USER_REQUEST,
            },
            ModuleType.PAYMENTS: {
                'payment_received': UpdateTrigger.DATA_CHANGE,
                'invoice_generated': UpdateTrigger.SYSTEM_EVENT,
                'webhook_received': UpdateTrigger.SYSTEM_EVENT,
                'user_payment': UpdateTrigger.USER_REQUEST,
            },
            ModuleType.FEEDBACK: {
                'feedback_submitted': UpdateTrigger.DATA_CHANGE,
                'reminder_sent': UpdateTrigger.SYSTEM_EVENT,
                'analysis_complete': UpdateTrigger.ML_INSIGHT,
                'user_feedback': UpdateTrigger.USER_REQUEST,
            }
        }
        
        # Inicializar cache
        self._initialize_cache()
        
        logger.info("DemandDrivenUpdater: Inicializado")
    
    def _initialize_cache(self):
        """Inicializa el cache de actualizaciones"""
        for module_type in ModuleType:
            for update_type in self.module_triggers.get(module_type, {}):
                cache_key = f"{module_type.value}_{update_type}"
                self.update_cache[cache_key] = UpdateCache(
                    last_update=datetime.now() - timedelta(hours=1),
                    data_hash="",
                    update_count=0
                )
    
    async def request_update(
        self,
        module_type: ModuleType,
        update_type: str,
        trigger: UpdateTrigger,
        data: Dict[str, Any],
        priority: UpdatePriority = UpdatePriority.NORMAL,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        Solicita una actualización bajo demanda
        """
        try:
            # Generar ID único
            request_id = f"update_{module_type.value}_{update_type}_{int(time.time())}"
            
            # Verificar si realmente necesitamos actualizar
            if not await self._needs_update(module_type, update_type, trigger, data):
                logger.info(f"Actualización no necesaria para {module_type.value}.{update_type}")
                return False
            
            # Crear solicitud de actualización
            update_request = UpdateRequest(
                request_id=request_id,
                module_type=module_type,
                update_type=update_type,
                trigger=trigger,
                priority=priority,
                data=data,
                callback=callback
            )
            
            # Programar operación global
            operation = OperationRequest(
                operation_id=request_id,
                module_type=module_type,
                operation_type=f"update_{update_type}",
                priority=self._map_priority(priority),
                estimated_duration=30,  # 30 segundos estimados
                estimated_memory=50,    # 50 MB estimados
                estimated_cpu=5.0,      # 5% CPU estimado
                dependencies=[],
                created_at=datetime.now(),
                requires_ml=trigger == UpdateTrigger.ML_INSIGHT
            )
            
            # Programar con el orquestador global
            scheduled = await global_orchestrator.schedule_global_operation(operation)
            
            if scheduled:
                self.pending_updates[request_id] = update_request
                if callback:
                    self.update_callbacks[request_id] = callback
                
                logger.info(f"Actualización programada: {request_id}")
                return True
            else:
                logger.warning(f"Actualización no pudo ser programada: {request_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error solicitando actualización: {str(e)}")
            return False
    
    async def _needs_update(
        self,
        module_type: ModuleType,
        update_type: str,
        trigger: UpdateTrigger,
        data: Dict[str, Any]
    ) -> bool:
        """
        Determina si realmente necesitamos actualizar
        """
        cache_key = f"{module_type.value}_{update_type}"
        cache_entry = self.update_cache.get(cache_key)
        
        if not cache_entry:
            return True
        
        current_time = datetime.now()
        time_since_last = (current_time - cache_entry.last_update).total_seconds()
        
        # Reglas de actualización por trigger
        if trigger == UpdateTrigger.USER_REQUEST:
            # Usuario solicita actualización - siempre actualizar
            return True
        
        elif trigger == UpdateTrigger.DATA_CHANGE:
            # Cambio de datos - verificar si hay cambios significativos
            data_hash = self._calculate_data_hash(data)
            if data_hash != cache_entry.data_hash:
                # Verificar umbral de cambio mínimo
                change_percentage = self._calculate_change_percentage(data, cache_entry.data_hash)
                return change_percentage >= self.update_config['data_change_threshold']
            return False
        
        elif trigger == UpdateTrigger.SYSTEM_EVENT:
            # Evento del sistema - verificar intervalo mínimo
            return time_since_last >= self.update_config['min_interval_seconds']
        
        elif trigger == UpdateTrigger.PERFORMANCE_ALERT:
            # Alerta de rendimiento - verificar carga del sistema
            system_load = await global_orchestrator.get_system_load()
            if system_load.value in ['high', 'critical']:
                return False  # No actualizar si el sistema está sobrecargado
            return time_since_last >= self.update_config['min_interval_seconds']
        
        elif trigger == UpdateTrigger.ML_INSIGHT:
            # Insight de ML - verificar cooldown
            return time_since_last >= self.update_config['ml_insight_cooldown']
        
        elif trigger == UpdateTrigger.TIME_BASED:
            # Basado en tiempo - verificar intervalo específico
            return time_since_last >= self._get_time_based_interval(module_type, update_type)
        
        return False
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calcula hash de los datos para detectar cambios"""
        import hashlib
        import json
        
        # Ordenar datos para hash consistente
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def _calculate_change_percentage(self, new_data: Dict[str, Any], old_hash: str) -> float:
        """Calcula el porcentaje de cambio entre datos"""
        new_hash = self._calculate_data_hash(new_data)
        
        if old_hash == new_hash:
            return 0.0
        
        # Simulación de cálculo de cambio
        # En implementación real, compararía campos específicos
        return 0.15  # 15% de cambio simulado
    
    def _get_time_based_interval(self, module_type: ModuleType, update_type: str) -> int:
        """Obtiene intervalo basado en tiempo para actualizaciones"""
        # Intervalos específicos por módulo y tipo
        intervals = {
            ModuleType.PUBLISH: {
                'campaign_metrics': 300,    # 5 minutos
                'performance_report': 1800, # 30 minutos
                'ml_insights': 3600,        # 1 hora
            },
            ModuleType.NOTIFICATIONS: {
                'strategic_alerts': 600,    # 10 minutos
                'campaign_status': 300,     # 5 minutos
                'user_notifications': 60,   # 1 minuto
            },
            ModuleType.CHATBOT: {
                'session_metrics': 300,     # 5 minutos
                'model_performance': 1800,  # 30 minutos
                'user_interactions': 60,    # 1 minuto
            },
            ModuleType.PAYMENTS: {
                'transaction_status': 60,   # 1 minuto
                'invoice_status': 300,      # 5 minutos
                'payment_analytics': 1800,  # 30 minutos
            },
            ModuleType.FEEDBACK: {
                'feedback_metrics': 600,    # 10 minutos
                'sentiment_analysis': 1800, # 30 minutos
                'user_satisfaction': 3600,  # 1 hora
            }
        }
        
        return intervals.get(module_type, {}).get(update_type, 300)
    
    def _map_priority(self, update_priority: UpdatePriority) -> OperationPriority:
        """Mapea prioridad de actualización a prioridad de operación"""
        mapping = {
            UpdatePriority.IMMEDIATE: OperationPriority.CRITICAL,
            UpdatePriority.HIGH: OperationPriority.HIGH,
            UpdatePriority.NORMAL: OperationPriority.MEDIUM,
            UpdatePriority.LOW: OperationPriority.LOW,
            UpdatePriority.BACKGROUND: OperationPriority.BACKGROUND
        }
        return mapping.get(update_priority, OperationPriority.MEDIUM)
    
    async def execute_update(self, request_id: str) -> bool:
        """
        Ejecuta una actualización específica
        """
        try:
            update_request = self.pending_updates.get(request_id)
            if not update_request:
                logger.warning(f"Actualización no encontrada: {request_id}")
                return False
            
            # Ejecutar actualización específica
            success = await self._execute_module_update(update_request)
            
            if success:
                # Actualizar cache
                cache_key = f"{update_request.module_type.value}_{update_request.update_type}"
                cache_entry = self.update_cache.get(cache_key)
                
                if cache_entry:
                    cache_entry.last_update = datetime.now()
                    cache_entry.data_hash = self._calculate_data_hash(update_request.data)
                    cache_entry.update_count += 1
                    cache_entry.last_trigger = update_request.trigger
                
                # Ejecutar callback si existe
                if update_request.callback:
                    try:
                        await update_request.callback(update_request.data)
                    except Exception as e:
                        logger.error(f"Error en callback de actualización: {str(e)}")
                
                # Limpiar
                del self.pending_updates[request_id]
                self.update_callbacks.pop(request_id, None)
                
                # Agregar al historial
                self.update_history.append(update_request)
                
                logger.info(f"Actualización ejecutada exitosamente: {request_id}")
                return True
            else:
                logger.error(f"Error ejecutando actualización: {request_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error en execute_update: {str(e)}")
            return False
    
    async def _execute_module_update(self, update_request: UpdateRequest) -> bool:
        """
        Ejecuta actualización específica del módulo
        """
        try:
            module_type = update_request.module_type
            update_type = update_request.update_type
            data = update_request.data
            
            # Ejecutar actualización según el módulo
            if module_type == ModuleType.PUBLISH:
                return await self._execute_publish_update(update_type, data)
            
            elif module_type == ModuleType.NOTIFICATIONS:
                return await self._execute_notification_update(update_type, data)
            
            elif module_type == ModuleType.CHATBOT:
                return await self._execute_chatbot_update(update_type, data)
            
            elif module_type == ModuleType.PAYMENTS:
                return await self._execute_payment_update(update_type, data)
            
            elif module_type == ModuleType.FEEDBACK:
                return await self._execute_feedback_update(update_type, data)
            
            else:
                logger.warning(f"Tipo de módulo no soportado: {module_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando actualización de módulo: {str(e)}")
            return False
    
    async def _execute_publish_update(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Ejecuta actualización del módulo publish"""
        try:
            if update_type == 'campaign_metrics':
                # Actualizar métricas de campaña
                await asyncio.sleep(1)  # Simular procesamiento
                return True
            
            elif update_type == 'performance_report':
                # Generar reporte de rendimiento
                await asyncio.sleep(2)  # Simular procesamiento
                return True
            
            elif update_type == 'ml_insights':
                # Obtener insights de ML
                ml_result = await global_orchestrator.coordinate_ml_operation(
                    'aura_analysis',
                    {'flow_type': 'market_research', 'custom_data': data}
                )
                return ml_result.get('success', False)
            
            return False
            
        except Exception as e:
            logger.error(f"Error en actualización publish: {str(e)}")
            return False
    
    async def _execute_notification_update(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Ejecuta actualización del módulo notifications"""
        try:
            if update_type == 'strategic_alerts':
                # Procesar alertas estratégicas
                await asyncio.sleep(1)
                return True
            
            elif update_type == 'campaign_status':
                # Actualizar estado de campañas
                await asyncio.sleep(1)
                return True
            
            elif update_type == 'user_notifications':
                # Procesar notificaciones de usuario
                await asyncio.sleep(0.5)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error en actualización notifications: {str(e)}")
            return False
    
    async def _execute_chatbot_update(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Ejecuta actualización del módulo chatbot"""
        try:
            if update_type == 'session_metrics':
                # Actualizar métricas de sesión
                await asyncio.sleep(1)
                return True
            
            elif update_type == 'model_performance':
                # Actualizar rendimiento del modelo
                await asyncio.sleep(2)
                return True
            
            elif update_type == 'user_interactions':
                # Procesar interacciones de usuario
                await asyncio.sleep(0.5)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error en actualización chatbot: {str(e)}")
            return False
    
    async def _execute_payment_update(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Ejecuta actualización del módulo payments"""
        try:
            if update_type == 'transaction_status':
                # Actualizar estado de transacciones
                await asyncio.sleep(1)
                return True
            
            elif update_type == 'invoice_status':
                # Actualizar estado de facturas
                await asyncio.sleep(1)
                return True
            
            elif update_type == 'payment_analytics':
                # Generar analytics de pagos
                await asyncio.sleep(2)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error en actualización payments: {str(e)}")
            return False
    
    async def _execute_feedback_update(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Ejecuta actualización del módulo feedback"""
        try:
            if update_type == 'feedback_metrics':
                # Actualizar métricas de feedback
                await asyncio.sleep(1)
                return True
            
            elif update_type == 'sentiment_analysis':
                # Análisis de sentimiento
                ml_result = await global_orchestrator.coordinate_ml_operation(
                    'aura_analysis',
                    {'flow_type': 'career_analysis', 'custom_data': data}
                )
                return ml_result.get('success', False)
            
            elif update_type == 'user_satisfaction':
                # Actualizar satisfacción del usuario
                await asyncio.sleep(1)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error en actualización feedback: {str(e)}")
            return False
    
    async def get_update_status(self) -> Dict[str, Any]:
        """Obtiene el estado del sistema de actualizaciones"""
        return {
            'pending_updates': len(self.pending_updates),
            'update_history_count': len(self.update_history),
            'cache_entries': len(self.update_cache),
            'recent_updates': [
                {
                    'module': req.module_type.value,
                    'type': req.update_type,
                    'trigger': req.trigger.value,
                    'priority': req.priority.value,
                    'created_at': req.created_at.isoformat()
                }
                for req in list(self.update_history)[-10:]  # Últimas 10 actualizaciones
            ],
            'cache_status': {
                key: {
                    'last_update': entry.last_update.isoformat(),
                    'update_count': entry.update_count,
                    'last_trigger': entry.last_trigger.value if entry.last_trigger else None
                }
                for key, entry in self.update_cache.items()
            },
            'timestamp': datetime.now().isoformat()
        }

# Instancia global del actualizador
demand_driven_updater = DemandDrivenUpdater() 