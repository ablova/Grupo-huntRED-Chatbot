"""
Orquestador central del sistema de publicación y notificaciones.
Coordina todas las operaciones para evitar sobrecarga del servidor.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

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
class OperationRequest:
    """Solicitud de operación"""
    operation_id: str
    operation_type: str
    priority: OperationPriority
    estimated_duration: int  # segundos
    estimated_memory: int    # MB
    estimated_cpu: float     # porcentaje
    dependencies: List[str]
    created_at: datetime
    timeout: int = 300

class SystemOrchestrator:
    """
    Orquestador central que coordina todas las operaciones del sistema.
    Evita sobrecargas y optimiza el uso de recursos.
    """
    
    def __init__(self):
        self.active_operations: Dict[str, OperationRequest] = {}
        self.operation_queue: List[OperationRequest] = []
        self.system_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'active_connections': 0,
            'queue_length': 0,
            'last_update': datetime.now()
        }
        self.rate_limits = {
            'email': {'limit': 350, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'whatsapp': {'limit': 100, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'telegram': {'limit': 200, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'api_calls': {'limit': 1000, 'window': 60, 'current': 0, 'reset_time': time.time() + 60},
            'database_queries': {'limit': 5000, 'window': 60, 'current': 0, 'reset_time': time.time() + 60}
        }
        self.adaptive_intervals = {
            'notifications': 300,  # 5 minutos base
            'campaigns': 600,      # 10 minutos base
            'insights': 1800,      # 30 minutos base
            'cleanup': 3600,       # 1 hora base
            'reports': 7200        # 2 horas base
        }
        
    async def get_system_load(self) -> SystemLoad:
        """Determina la carga actual del sistema"""
        try:
            # Obtener métricas del sistema desde cache
            cpu_usage = cache.get('system_cpu_usage', 0.0)
            memory_usage = cache.get('system_memory_usage', 0.0)
            active_connections = cache.get('system_active_connections', 0)
            
            # Calcular carga basada en múltiples factores
            load_score = (
                cpu_usage * 0.4 +
                memory_usage * 0.3 +
                (active_connections / 1000) * 0.3
            )
            
            if load_score < 0.3:
                return SystemLoad.LOW
            elif load_score < 0.6:
                return SystemLoad.MEDIUM
            elif load_score < 0.8:
                return SystemLoad.HIGH
            else:
                return SystemLoad.CRITICAL
                
        except Exception as e:
            logger.error(f"Error obteniendo carga del sistema: {str(e)}")
            return SystemLoad.MEDIUM
    
    async def can_execute_operation(self, operation: OperationRequest) -> bool:
        """Verifica si se puede ejecutar una operación"""
        current_load = await self.get_system_load()
        
        # Reglas de ejecución basadas en carga
        if current_load == SystemLoad.CRITICAL:
            return operation.priority == OperationPriority.CRITICAL
        
        elif current_load == SystemLoad.HIGH:
            return operation.priority in [OperationPriority.CRITICAL, OperationPriority.HIGH]
        
        elif current_load == SystemLoad.MEDIUM:
            return operation.priority in [OperationPriority.CRITICAL, OperationPriority.HIGH, OperationPriority.MEDIUM]
        
        else:  # LOW
            return True
    
    async def check_rate_limit(self, operation_type: str, amount: int = 1) -> bool:
        """Verifica límites de tasa para operaciones"""
        if operation_type not in self.rate_limits:
            return True
            
        limit_info = self.rate_limits[operation_type]
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
    
    async def get_adaptive_interval(self, operation_type: str) -> int:
        """Obtiene intervalo adaptativo basado en carga del sistema"""
        base_interval = self.adaptive_intervals.get(operation_type, 300)
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
    
    async def schedule_operation(self, operation: OperationRequest) -> bool:
        """Programa una operación para ejecución"""
        try:
            # Verificar si se puede ejecutar
            if not await self.can_execute_operation(operation):
                # Agregar a cola si no se puede ejecutar inmediatamente
                self.operation_queue.append(operation)
                self.operation_queue.sort(key=lambda x: x.priority.value)
                logger.info(f"Operación {operation.operation_id} agregada a cola")
                return False
            
            # Verificar límites de tasa
            if not await self.check_rate_limit(operation.operation_type):
                logger.warning(f"Rate limit alcanzado para {operation.operation_type}")
                return False
            
            # Ejecutar operación
            self.active_operations[operation.operation_id] = operation
            logger.info(f"Ejecutando operación {operation.operation_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error programando operación {operation.operation_id}: {str(e)}")
            return False
    
    async def execute_notification_batch(self, notifications: List[Dict]) -> Dict[str, Any]:
        """Ejecuta un lote de notificaciones con control inteligente"""
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
        
        # Procesar por canal con límites de tasa
        for channel, channel_notifications in by_channel.items():
            # Verificar límite de tasa para el canal
            if not await self.check_rate_limit(channel, len(channel_notifications)):
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
    
    async def optimize_system_performance(self):
        """Optimiza el rendimiento del sistema"""
        current_load = await self.get_system_load()
        
        if current_load == SystemLoad.CRITICAL:
            # Modo de emergencia: solo operaciones críticas
            await self._emergency_mode()
        elif current_load == SystemLoad.HIGH:
            # Modo de alta carga: reducir operaciones no esenciales
            await self._high_load_mode()
        else:
            # Modo normal: optimizar recursos
            await self._normal_mode()
    
    async def _emergency_mode(self):
        """Modo de emergencia cuando la carga es crítica"""
        logger.warning("Sistema en modo de emergencia - solo operaciones críticas")
        
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
    
    async def _high_load_mode(self):
        """Modo de alta carga"""
        logger.info("Sistema en modo de alta carga - optimizando recursos")
        
        # Aumentar intervalos de operaciones
        for op_type in self.adaptive_intervals:
            self.adaptive_intervals[op_type] = int(self.adaptive_intervals[op_type] * 1.5)
    
    async def _normal_mode(self):
        """Modo normal de operación"""
        # Restaurar intervalos normales
        self.adaptive_intervals = {
            'notifications': 300,
            'campaigns': 600,
            'insights': 1800,
            'cleanup': 3600,
            'reports': 7200
        }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema"""
        current_load = await self.get_system_load()
        
        return {
            'system_load': current_load.value,
            'active_operations': len(self.active_operations),
            'queue_length': len(self.operation_queue),
            'rate_limits': self.rate_limits,
            'adaptive_intervals': self.adaptive_intervals,
            'system_metrics': self.system_metrics,
            'timestamp': datetime.now().isoformat()
        }

# Instancia global del orquestador
orchestrator = SystemOrchestrator() 