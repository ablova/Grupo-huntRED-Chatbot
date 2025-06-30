"""
Orquestador Global del Sistema huntRED®
Coordina todos los módulos de app/ats/ con el sistema ML (AURA/GenIA)
para evitar sobrecargas y optimizar recursos del servidor.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from django.core.cache import cache
from django.conf import settings

# Importar orquestador de AURA
try:
    from app.ml.aura.integration.aura_orchestrator import AuraOrchestrator, aura_orchestrator
    AURA_AVAILABLE = True
except ImportError:
    AURA_AVAILABLE = False
    aura_orchestrator = None

logger = logging.getLogger(__name__)

class ModuleType(Enum):
    """Tipos de módulos del sistema"""
    PUBLISH = "publish"
    PAYMENTS = "payments"
    CHATBOT = "chatbot"
    NOTIFICATIONS = "notifications"
    FEEDBACK = "feedback"
    INTEGRATIONS = "integrations"
    ML_SYSTEM = "ml_system"
    API = "api"
    ADMIN = "admin"

class SystemLoad(Enum):
    """Niveles de carga del sistema"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OperationPriority(Enum):
    """Prioridades de operaciones"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5

@dataclass
class ModuleStatus:
    """Estado de un módulo"""
    module_type: ModuleType
    enabled: bool = True
    last_activity: Optional[datetime] = None
    active_operations: int = 0
    error_count: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)

@dataclass
class OperationRequest:
    """Solicitud de operación global"""
    operation_id: str
    module_type: ModuleType
    operation_type: str
    priority: OperationPriority
    estimated_duration: int  # segundos
    estimated_memory: int    # MB
    estimated_cpu: float     # porcentaje
    dependencies: List[str]
    created_at: datetime
    timeout: int = 300
    requires_ml: bool = False

class GlobalOrchestrator:
    """
    Orquestador global que coordina todos los módulos del sistema huntRED®
    """
    
    def __init__(self):
        self.modules: Dict[ModuleType, ModuleStatus] = {}
        self.active_operations: Dict[str, OperationRequest] = {}
        self.operation_queue: List[OperationRequest] = []
        self.system_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'active_connections': 0,
            'queue_length': 0,
            'last_update': datetime.now()
        }
        
        # Límites de tasa globales (más conservadores que individuales)
        self.global_rate_limits = {
            'email': {'limit': 300, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'whatsapp': {'limit': 80, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'telegram': {'limit': 150, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'api_calls': {'limit': 800, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'database_queries': {'limit': 4000, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'ml_operations': {'limit': 50, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'file_operations': {'limit': 200, 'window': 60, 'current': 0, 'reset_time': time.time() + 60}
        }
        
        # Intervalos adaptativos por módulo
        self.adaptive_intervals = {
            ModuleType.PUBLISH: {
                'notifications': 600,      # 10 minutos base
                'campaigns': 1200,         # 20 minutos base
                'insights': 3600,          # 1 hora base
                'cleanup': 7200,           # 2 horas base
                'reports': 14400           # 4 horas base
            },
            ModuleType.NOTIFICATIONS: {
                'strategic': 900,          # 15 minutos base
                'campaign': 600,           # 10 minutos base
                'insights': 1800,          # 30 minutos base
                'metrics': 300,            # 5 minutos base
                'cleanup': 3600            # 1 hora base
            },
            ModuleType.CHATBOT: {
                'session_cleanup': 300,    # 5 minutos base
                'model_updates': 3600,     # 1 hora base
                'analytics': 1800,         # 30 minutos base
                'training': 7200           # 2 horas base
            },
            ModuleType.PAYMENTS: {
                'webhook_processing': 60,  # 1 minuto base
                'invoice_generation': 300, # 5 minutos base
                'reconciliation': 1800,    # 30 minutos base
                'reports': 3600            # 1 hora base
            },
            ModuleType.FEEDBACK: {
                'reminder_processing': 300, # 5 minutos base
                'analysis': 1800,          # 30 minutos base
                'reporting': 3600          # 1 hora base
            },
            ModuleType.ML_SYSTEM: {
                'aura_operations': 300,    # 5 minutos base
                'model_inference': 60,     # 1 minuto base
                'training': 7200,          # 2 horas base
                'analytics': 1800          # 30 minutos base
            }
        }
        
        # Configuración de coordinación
        self.coordination_config = {
            'max_concurrent_operations': 20,
            'max_queue_size': 100,
            'operation_timeout': 300,
            'health_check_interval': 30,
            'metrics_update_interval': 60,
            'emergency_threshold': 0.9,  # 90% de carga
            'high_load_threshold': 0.7,  # 70% de carga
            'medium_load_threshold': 0.4  # 40% de carga
        }
        
        self._initialize_modules()
        self._start_monitoring()
        
        logger.info("GlobalOrchestrator: Inicializado")
    
    def _initialize_modules(self):
        """Inicializa todos los módulos del sistema"""
        for module_type in ModuleType:
            self.modules[module_type] = ModuleStatus(
                module_type=module_type,
                enabled=True,
                last_activity=datetime.now()
            )
    
    def _start_monitoring(self):
        """Inicia el monitoreo del sistema"""
        asyncio.create_task(self._monitor_system_health())
        asyncio.create_task(self._update_system_metrics())
    
    async def get_system_load(self) -> SystemLoad:
        """Determina la carga actual del sistema global"""
        try:
            # Obtener métricas del sistema
            cpu_usage = cache.get('system_cpu_usage', 0.0)
            memory_usage = cache.get('system_memory_usage', 0.0)
            active_connections = cache.get('system_active_connections', 0)
            
            # Calcular carga considerando operaciones activas
            active_ops_factor = len(self.active_operations) / self.coordination_config['max_concurrent_operations']
            queue_factor = len(self.operation_queue) / self.coordination_config['max_queue_size']
            
            # Calcular carga total
            load_score = (
                cpu_usage * 0.3 +
                memory_usage * 0.25 +
                (active_connections / 1000) * 0.2 +
                active_ops_factor * 0.15 +
                queue_factor * 0.1
            )
            
            if load_score < self.coordination_config['medium_load_threshold']:
                return SystemLoad.LOW
            elif load_score < self.coordination_config['high_load_threshold']:
                return SystemLoad.MEDIUM
            elif load_score < self.coordination_config['emergency_threshold']:
                return SystemLoad.HIGH
            else:
                return SystemLoad.CRITICAL
                
        except Exception as e:
            logger.error(f"Error obteniendo carga del sistema: {str(e)}")
            return SystemLoad.MEDIUM
    
    async def can_execute_operation(self, operation: OperationRequest) -> bool:
        """Verifica si se puede ejecutar una operación globalmente"""
        current_load = await self.get_system_load()
        
        # Verificar límites de concurrencia
        if len(self.active_operations) >= self.coordination_config['max_concurrent_operations']:
            return False
        
        # Verificar tamaño de cola
        if len(self.operation_queue) >= self.coordination_config['max_queue_size']:
            return False
        
        # Reglas de ejecución basadas en carga
        if current_load == SystemLoad.CRITICAL:
            return operation.priority == OperationPriority.CRITICAL
        
        elif current_load == SystemLoad.HIGH:
            return operation.priority in [OperationPriority.CRITICAL, OperationPriority.HIGH]
        
        elif current_load == SystemLoad.MEDIUM:
            return operation.priority in [OperationPriority.CRITICAL, OperationPriority.HIGH, OperationPriority.MEDIUM]
        
        else:  # LOW
            return True
    
    async def check_global_rate_limit(self, operation_type: str, amount: int = 1) -> bool:
        """Verifica límites de tasa globales"""
        if operation_type not in self.global_rate_limits:
            return True
            
        limit_info = self.global_rate_limits[operation_type]
        current_time = time.time()
        
        # Resetear contador si ha pasado la ventana
        if current_time > limit_info['reset_time']:
            limit_info['current'] = 0
            limit_info['reset_time'] = current_time + limit_info['window']
        
        # Verificar si podemos agregar más operaciones
        if limit_info['current'] + amount <= limit_info['limit']:
            limit_info['current'] += amount
            return True
        
        return False
    
    async def get_adaptive_interval(self, module_type: ModuleType, operation_type: str) -> int:
        """Obtiene intervalo adaptativo basado en carga del sistema"""
        module_intervals = self.adaptive_intervals.get(module_type, {})
        base_interval = module_intervals.get(operation_type, 300)
        current_load = await self.get_system_load()
        
        # Ajustar intervalo según carga
        if current_load == SystemLoad.CRITICAL:
            return base_interval * 4  # 4x más lento
        elif current_load == SystemLoad.HIGH:
            return base_interval * 2  # 2x más lento
        elif current_load == SystemLoad.MEDIUM:
            return base_interval  # Intervalo normal
        else:  # LOW
            return max(base_interval // 2, 60)  # 2x más rápido, mínimo 1 minuto
    
    async def schedule_global_operation(self, operation: OperationRequest) -> bool:
        """Programa una operación global"""
        try:
            # Verificar si se puede ejecutar
            if not await self.can_execute_operation(operation):
                # Agregar a cola si no se puede ejecutar inmediatamente
                self.operation_queue.append(operation)
                self.operation_queue.sort(key=lambda x: x.priority.value)
                logger.info(f"Operación global {operation.operation_id} agregada a cola")
                return False
            
            # Verificar límites de tasa globales
            if not await self.check_global_rate_limit(operation.operation_type):
                logger.warning(f"Rate limit global alcanzado para {operation.operation_type}")
                return False
            
            # Si requiere ML, verificar disponibilidad de AURA
            if operation.requires_ml and not AURA_AVAILABLE:
                logger.warning(f"Operación {operation.operation_id} requiere ML pero AURA no está disponible")
                return False
            
            # Ejecutar operación
            self.active_operations[operation.operation_id] = operation
            
            # Actualizar estado del módulo
            module_status = self.modules[operation.module_type]
            module_status.active_operations += 1
            module_status.last_activity = datetime.now()
            
            logger.info(f"Ejecutando operación global {operation.operation_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error programando operación global {operation.operation_id}: {str(e)}")
            return False
    
    async def execute_coordinated_notification_batch(self, notifications: List[Dict]) -> Dict[str, Any]:
        """Ejecuta un lote de notificaciones con coordinación global"""
        results = {
            'total': len(notifications),
            'sent': 0,
            'queued': 0,
            'failed': 0,
            'errors': []
        }
        
        # Agrupar por canal para optimizar envíos
        by_channel = {}
        for notification in notifications:
            channel = notification.get('channel', 'email')
            if channel not in by_channel:
                by_channel[channel] = []
            by_channel[channel].append(notification)
        
        # Procesar por canal con límites de tasa globales
        for channel, channel_notifications in by_channel.items():
            # Verificar límite de tasa global para el canal
            if not await self.check_global_rate_limit(channel, len(channel_notifications)):
                # Agregar a cola si excede límite
                results['queued'] += len(channel_notifications)
                continue
            
            # Enviar notificaciones del canal
            for notification in channel_notifications:
                try:
                    # Simular envío (aquí iría la lógica real)
                    await asyncio.sleep(0.1)  # Simular tiempo de envío
                    results['sent'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(str(e))
        
        return results
    
    async def coordinate_ml_operation(self, operation_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordina operaciones con el sistema ML (AURA/GenIA)"""
        if not AURA_AVAILABLE:
            return {
                'success': False,
                'error': 'ML system not available',
                'data': {}
            }
        
        try:
            # Verificar límite de tasa para ML
            if not await self.check_global_rate_limit('ml_operations'):
                return {
                    'success': False,
                    'error': 'ML rate limit exceeded',
                    'data': {}
                }
            
            # Ejecutar operación ML según el tipo
            if operation_type == 'aura_analysis':
                # Usar AURA para análisis
                result = await aura_orchestrator.execute_integration_flow(
                    user_id=data.get('user_id'),
                    flow_type=data.get('flow_type'),
                    custom_data=data.get('custom_data', {})
                )
                return {
                    'success': result.success,
                    'data': result.results,
                    'recommendations': result.recommendations,
                    'next_actions': result.next_actions
                }
            
            elif operation_type == 'genia_processing':
                # Usar GenIA para procesamiento
                # Aquí iría la integración con GenIA
                return {
                    'success': True,
                    'data': {'genia_result': 'processed'},
                    'recommendations': [],
                    'next_actions': []
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown ML operation type: {operation_type}',
                    'data': {}
                }
                
        except Exception as e:
            logger.error(f"Error en operación ML {operation_type}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
    
    async def optimize_global_performance(self):
        """Optimiza el rendimiento global del sistema"""
        current_load = await self.get_system_load()
        
        if current_load == SystemLoad.CRITICAL:
            await self._emergency_mode()
        elif current_load == SystemLoad.HIGH:
            await self._high_load_mode()
        else:
            await self._normal_mode()
    
    async def _emergency_mode(self):
        """Modo de emergencia cuando la carga es crítica"""
        logger.warning("Sistema en modo de emergencia global - solo operaciones críticas")
        
        # Cancelar operaciones no críticas
        non_critical = [
            op_id for op_id, op in self.active_operations.items()
            if op.priority != OperationPriority.CRITICAL
        ]
        
        for op_id in non_critical:
            del self.active_operations[op_id]
        
        # Limpiar cola de operaciones no críticas
        self.operation_queue = [
            op for op in self.operation_queue
            if op.priority == OperationPriority.CRITICAL
        ]
        
        # Deshabilitar módulos no críticos
        for module_type, status in self.modules.items():
            if module_type not in [ModuleType.PAYMENTS, ModuleType.NOTIFICATIONS]:
                status.enabled = False
    
    async def _high_load_mode(self):
        """Modo de alta carga"""
        logger.info("Sistema en modo de alta carga global - optimizando recursos")
        
        # Aumentar intervalos de operaciones
        for module_type, intervals in self.adaptive_intervals.items():
            for operation_type in intervals:
                intervals[operation_type] = int(intervals[operation_type] * 1.5)
    
    async def _normal_mode(self):
        """Modo normal de operación"""
        # Restaurar intervalos normales
        self.adaptive_intervals = {
            ModuleType.PUBLISH: {
                'notifications': 600,
                'campaigns': 1200,
                'insights': 3600,
                'cleanup': 7200,
                'reports': 14400
            },
            ModuleType.NOTIFICATIONS: {
                'strategic': 900,
                'campaign': 600,
                'insights': 1800,
                'metrics': 300,
                'cleanup': 3600
            },
            ModuleType.CHATBOT: {
                'session_cleanup': 300,
                'model_updates': 3600,
                'analytics': 1800,
                'training': 7200
            },
            ModuleType.PAYMENTS: {
                'webhook_processing': 60,
                'invoice_generation': 300,
                'reconciliation': 1800,
                'reports': 3600
            },
            ModuleType.FEEDBACK: {
                'reminder_processing': 300,
                'analysis': 1800,
                'reporting': 3600
            },
            ModuleType.ML_SYSTEM: {
                'aura_operations': 300,
                'model_inference': 60,
                'training': 7200,
                'analytics': 1800
            }
        }
        
        # Habilitar todos los módulos
        for status in self.modules.values():
            status.enabled = True
    
    async def _monitor_system_health(self):
        """Monitorea la salud del sistema"""
        while True:
            try:
                await self.optimize_global_performance()
                await asyncio.sleep(self.coordination_config['health_check_interval'])
            except Exception as e:
                logger.error(f"Error en monitoreo de salud: {str(e)}")
                await asyncio.sleep(60)
    
    async def _update_system_metrics(self):
        """Actualiza métricas del sistema"""
        while True:
            try:
                # Actualizar métricas del sistema
                self.system_metrics.update({
                    'queue_length': len(self.operation_queue),
                    'last_update': datetime.now()
                })
                
                # Guardar en cache para otros componentes
                cache.set('global_orchestrator_metrics', self.system_metrics, 300)
                
                await asyncio.sleep(self.coordination_config['metrics_update_interval'])
            except Exception as e:
                logger.error(f"Error actualizando métricas: {str(e)}")
                await asyncio.sleep(60)
    
    async def get_global_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema global"""
        current_load = await self.get_system_load()
        
        return {
            'system_load': current_load.value,
            'active_operations': len(self.active_operations),
            'queue_length': len(self.operation_queue),
            'global_rate_limits': self.global_rate_limits,
            'adaptive_intervals': {
                module_type.value: intervals
                for module_type, intervals in self.adaptive_intervals.items()
            },
            'module_status': {
                module_type.value: {
                    'enabled': status.enabled,
                    'active_operations': status.active_operations,
                    'last_activity': status.last_activity.isoformat() if status.last_activity else None,
                    'error_count': status.error_count,
                    'success_rate': status.success_rate
                }
                for module_type, status in self.modules.items()
            },
            'system_metrics': self.system_metrics,
            'ml_system_available': AURA_AVAILABLE,
            'timestamp': datetime.now().isoformat()
        }

# Instancia global del orquestador
global_orchestrator = GlobalOrchestrator() 