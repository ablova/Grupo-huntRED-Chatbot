"""
AURA - Monitoring and Analytics System
Sistema de monitoreo y analytics para todos los componentes de AURA
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import psutil
import threading

logger = logging.getLogger(__name__)

# CONFIGURACIÓN: DESHABILITADO POR DEFECTO
ENABLED = False  # Cambiar a True para habilitar


class MetricType(Enum):
    """Tipos de métricas"""
    PERFORMANCE = "performance"
    USAGE = "usage"
    ERROR = "error"
    BUSINESS = "business"
    SYSTEM = "system"


class AlertLevel(Enum):
    """Niveles de alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """Datos de métrica"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    component: str
    metric_type: MetricType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alerta del sistema"""
    id: str
    level: AlertLevel
    message: str
    component: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """Estado de salud de un componente"""
    component: str
    status: str  # 'healthy', 'warning', 'error', 'disabled'
    last_check: datetime
    response_time_ms: float
    error_count: int
    success_rate: float
    uptime_seconds: float


class AuraMonitor:
    """
    Sistema de monitoreo y analytics para AURA
    """
    
    def __init__(self):
        self.enabled = ENABLED
        if not self.enabled:
            logger.info("AuraMonitor: DESHABILITADO")
            return
        
        self.metrics_history = []
        self.active_alerts = {}
        self.component_health = {}
        self.performance_data = {}
        
        # Configuración de monitoreo
        self.monitor_config = {
            "metrics_retention_hours": 24,
            "alert_check_interval_seconds": 60,
            "health_check_interval_seconds": 30,
            "performance_thresholds": {
                "response_time_ms": 1000,
                "error_rate_percent": 5.0,
                "memory_usage_percent": 80.0,
                "cpu_usage_percent": 70.0
            },
            "business_thresholds": {
                "daily_active_users": 100,
                "conversations_per_hour": 50,
                "predictions_accuracy": 0.8,
                "user_satisfaction": 0.7
            }
        }
        
        # Componentes a monitorear
        self.monitored_components = [
            "career_predictor",
            "market_predictor", 
            "sentiment_analyzer",
            "executive_analytics",
            "advanced_chatbot",
            "achievement_system",
            "strategic_competitions",
            "multi_platform_connector",
            "ar_network_viewer",
            "multi_language_system",
            "compliance_manager",
            "intelligent_cache",
            "aura_orchestrator"
        ]
        
        self._initialize_component_health()
        self._start_monitoring_thread()
        logger.info("AuraMonitor: Inicializado")
    
    def _initialize_component_health(self):
        """Inicializa estado de salud de componentes"""
        if not self.enabled:
            return
        
        for component in self.monitored_components:
            self.component_health[component] = ComponentHealth(
                component=component,
                status="disabled",
                last_check=datetime.now(),
                response_time_ms=0.0,
                error_count=0,
                success_rate=1.0,
                uptime_seconds=0.0
            )
    
    def _start_monitoring_thread(self):
        """Inicia thread de monitoreo continuo"""
        if not self.enabled:
            return
        
        def monitoring_loop():
            while self.enabled:
                try:
                    self._collect_system_metrics()
                    self._check_component_health()
                    self._check_alerts()
                    time.sleep(self.monitor_config["health_check_interval_seconds"])
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Monitoring thread started")
    
    def record_metric(self, name: str, value: float, unit: str, component: str, 
                     metric_type: MetricType, metadata: Dict[str, Any] = None):
        """
        Registra una métrica
        """
        if not self.enabled:
            return
        
        try:
            metric = MetricData(
                name=name,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                component=component,
                metric_type=metric_type,
                metadata=metadata or {}
            )
            
            self.metrics_history.append(metric)
            
            # Limpiar métricas antiguas
            self._cleanup_old_metrics()
            
            # Verificar umbrales
            self._check_metric_thresholds(metric)
            
        except Exception as e:
            logger.error(f"Error recording metric: {e}")
    
    def record_performance_metric(self, component: str, operation: str, 
                                response_time_ms: float, success: bool):
        """
        Registra métrica de rendimiento
        """
        if not self.enabled:
            return
        
        try:
            # Actualizar salud del componente
            if component in self.component_health:
                health = self.component_health[component]
                health.last_check = datetime.now()
                health.response_time_ms = response_time_ms
                
                if not success:
                    health.error_count += 1
                
                # Calcular tasa de éxito
                total_operations = health.error_count + (health.success_rate * 100)
                if total_operations > 0:
                    health.success_rate = (total_operations - health.error_count) / total_operations
                
                # Determinar estado
                if health.success_rate < 0.9:
                    health.status = "error"
                elif health.response_time_ms > self.monitor_config["performance_thresholds"]["response_time_ms"]:
                    health.status = "warning"
                else:
                    health.status = "healthy"
            
            # Registrar métrica
            self.record_metric(
                name=f"{component}_{operation}_response_time",
                value=response_time_ms,
                unit="ms",
                component=component,
                metric_type=MetricType.PERFORMANCE,
                metadata={"operation": operation, "success": success}
            )
            
        except Exception as e:
            logger.error(f"Error recording performance metric: {e}")
    
    def record_business_metric(self, metric_name: str, value: float, 
                             component: str = "system"):
        """
        Registra métrica de negocio
        """
        if not self.enabled:
            return
        
        self.record_metric(
            name=metric_name,
            value=value,
            unit="count",
            component=component,
            metric_type=MetricType.BUSINESS
        )
    
    def record_error(self, component: str, error_message: str, 
                    error_type: str = "general", severity: AlertLevel = AlertLevel.ERROR):
        """
        Registra error del sistema
        """
        if not self.enabled:
            return
        
        try:
            # Crear alerta
            alert_id = f"error_{component}_{int(datetime.now().timestamp())}"
            alert = Alert(
                id=alert_id,
                level=severity,
                message=error_message,
                component=component,
                timestamp=datetime.now(),
                metadata={"error_type": error_type}
            )
            
            self.active_alerts[alert_id] = alert
            
            # Registrar métrica de error
            self.record_metric(
                name=f"{component}_errors",
                value=1,
                unit="count",
                component=component,
                metric_type=MetricType.ERROR,
                metadata={"error_type": error_type, "severity": severity.value}
            )
            
            logger.error(f"Error recorded: {component} - {error_message}")
            
        except Exception as e:
            logger.error(f"Error recording error: {e}")
    
    def _collect_system_metrics(self):
        """Recolecta métricas del sistema"""
        if not self.enabled:
            return
        
        try:
            # Métricas de CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric(
                name="system_cpu_usage",
                value=cpu_percent,
                unit="percent",
                component="system",
                metric_type=MetricType.SYSTEM
            )
            
            # Métricas de memoria
            memory = psutil.virtual_memory()
            self.record_metric(
                name="system_memory_usage",
                value=memory.percent,
                unit="percent",
                component="system",
                metric_type=MetricType.SYSTEM
            )
            
            # Métricas de disco
            disk = psutil.disk_usage('/')
            self.record_metric(
                name="system_disk_usage",
                value=(disk.used / disk.total) * 100,
                unit="percent",
                component="system",
                metric_type=MetricType.SYSTEM
            )
            
            # Métricas de red
            network = psutil.net_io_counters()
            self.record_metric(
                name="system_network_bytes_sent",
                value=network.bytes_sent,
                unit="bytes",
                component="system",
                metric_type=MetricType.SYSTEM
            )
            
            self.record_metric(
                name="system_network_bytes_recv",
                value=network.bytes_recv,
                unit="bytes",
                component="system",
                metric_type=MetricType.SYSTEM
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _check_component_health(self):
        """Verifica salud de componentes"""
        if not self.enabled:
            return
        
        for component, health in self.component_health.items():
            try:
                # Verificar si el componente está habilitado
                if not self._is_component_enabled(component):
                    health.status = "disabled"
                    continue
                
                # Simular verificación de salud
                health_check_result = self._perform_health_check(component)
                
                if health_check_result["healthy"]:
                    health.status = "healthy"
                    health.uptime_seconds += self.monitor_config["health_check_interval_seconds"]
                else:
                    health.status = "error"
                    self.record_error(component, health_check_result["error"], "health_check")
                
            except Exception as e:
                health.status = "error"
                self.record_error(component, str(e), "health_check")
    
    def _is_component_enabled(self, component: str) -> bool:
        """Verifica si un componente está habilitado"""
        # En implementación real, verificar configuración
        return True  # Simulado
    
    def _perform_health_check(self, component: str) -> Dict[str, Any]:
        """Realiza verificación de salud de un componente"""
        # Simulación de health check
        import random
        
        if random.random() > 0.95:  # 5% de probabilidad de fallo
            return {
                "healthy": False,
                "error": f"Component {component} health check failed"
            }
        
        return {
            "healthy": True,
            "response_time": random.uniform(10, 100)
        }
    
    def _check_metric_thresholds(self, metric: MetricData):
        """Verifica umbrales de métricas"""
        if not self.enabled:
            return
        
        try:
            thresholds = self.monitor_config["performance_thresholds"]
            
            # Verificar umbrales de rendimiento
            if metric.metric_type == MetricType.PERFORMANCE:
                if "response_time" in metric.name and metric.value > thresholds["response_time_ms"]:
                    self._create_alert(
                        AlertLevel.WARNING,
                        f"High response time for {metric.component}: {metric.value}ms",
                        metric.component
                    )
            
            # Verificar umbrales de sistema
            elif metric.metric_type == MetricType.SYSTEM:
                if "cpu_usage" in metric.name and metric.value > thresholds["cpu_usage_percent"]:
                    self._create_alert(
                        AlertLevel.WARNING,
                        f"High CPU usage: {metric.value}%",
                        "system"
                    )
                
                elif "memory_usage" in metric.name and metric.value > thresholds["memory_usage_percent"]:
                    self._create_alert(
                        AlertLevel.WARNING,
                        f"High memory usage: {metric.value}%",
                        "system"
                    )
            
            # Verificar umbrales de negocio
            elif metric.metric_type == MetricType.BUSINESS:
                business_thresholds = self.monitor_config["business_thresholds"]
                
                if "user_satisfaction" in metric.name and metric.value < business_thresholds["user_satisfaction"]:
                    self._create_alert(
                        AlertLevel.WARNING,
                        f"Low user satisfaction: {metric.value}",
                        "business"
                    )
                
                elif "predictions_accuracy" in metric.name and metric.value < business_thresholds["predictions_accuracy"]:
                    self._create_alert(
                        AlertLevel.WARNING,
                        f"Low prediction accuracy: {metric.value}",
                        "business"
                    )
            
        except Exception as e:
            logger.error(f"Error checking metric thresholds: {e}")
    
    def _create_alert(self, level: AlertLevel, message: str, component: str):
        """Crea una nueva alerta"""
        if not self.enabled:
            return
        
        try:
            alert_id = f"alert_{component}_{int(datetime.now().timestamp())}"
            alert = Alert(
                id=alert_id,
                level=level,
                message=message,
                component=component,
                timestamp=datetime.now()
            )
            
            self.active_alerts[alert_id] = alert
            logger.warning(f"Alert created: {level.value} - {message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    def _check_alerts(self):
        """Verifica y gestiona alertas activas"""
        if not self.enabled:
            return
        
        try:
            current_time = datetime.now()
            alerts_to_resolve = []
            
            for alert_id, alert in self.active_alerts.items():
                # Resolver alertas antiguas de INFO
                if alert.level == AlertLevel.INFO:
                    if (current_time - alert.timestamp).total_seconds() > 3600:  # 1 hora
                        alerts_to_resolve.append(alert_id)
                
                # Resolver alertas de WARNING después de 24 horas
                elif alert.level == AlertLevel.WARNING:
                    if (current_time - alert.timestamp).total_seconds() > 86400:  # 24 horas
                        alerts_to_resolve.append(alert_id)
            
            # Resolver alertas
            for alert_id in alerts_to_resolve:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = current_time
                logger.info(f"Alert resolved: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _cleanup_old_metrics(self):
        """Limpia métricas antiguas"""
        if not self.enabled:
            return
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.monitor_config["metrics_retention_hours"])
            self.metrics_history = [
                metric for metric in self.metrics_history
                if metric.timestamp > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Obtiene datos para el dashboard de monitoreo
        """
        if not self.enabled:
            return self._get_mock_dashboard_data()
        
        try:
            # Métricas recientes
            recent_metrics = self._get_recent_metrics()
            
            # Estado de componentes
            component_status = {
                component: {
                    "status": health.status,
                    "response_time_ms": health.response_time_ms,
                    "success_rate": health.success_rate,
                    "uptime_hours": health.uptime_seconds / 3600
                }
                for component, health in self.component_health.items()
            }
            
            # Alertas activas
            active_alerts = [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "message": alert.message,
                    "component": alert.component,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in self.active_alerts.values()
                if not alert.resolved
            ]
            
            # Resumen del sistema
            system_summary = self._generate_system_summary()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_summary": system_summary,
                "component_status": component_status,
                "recent_metrics": recent_metrics,
                "active_alerts": active_alerts,
                "performance_trends": self._get_performance_trends()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self._get_mock_dashboard_data()
    
    def _get_recent_metrics(self) -> List[Dict[str, Any]]:
        """Obtiene métricas recientes"""
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_metrics = [
            metric for metric in self.metrics_history
            if metric.timestamp > recent_cutoff
        ]
        
        return [
            {
                "name": metric.name,
                "value": metric.value,
                "unit": metric.unit,
                "component": metric.component,
                "type": metric.metric_type.value,
                "timestamp": metric.timestamp.isoformat()
            }
            for metric in recent_metrics[-100:]  # Últimas 100 métricas
        ]
    
    def _generate_system_summary(self) -> Dict[str, Any]:
        """Genera resumen del sistema"""
        try:
            # Calcular estadísticas
            total_components = len(self.component_health)
            healthy_components = sum(1 for h in self.component_health.values() if h.status == "healthy")
            warning_components = sum(1 for h in self.component_health.values() if h.status == "warning")
            error_components = sum(1 for h in self.component_health.values() if h.status == "error")
            
            # Alertas por nivel
            alert_counts = {
                "info": sum(1 for a in self.active_alerts.values() if a.level == AlertLevel.INFO and not a.resolved),
                "warning": sum(1 for a in self.active_alerts.values() if a.level == AlertLevel.WARNING and not a.resolved),
                "error": sum(1 for a in self.active_alerts.values() if a.level == AlertLevel.ERROR and not a.resolved),
                "critical": sum(1 for a in self.active_alerts.values() if a.level == AlertLevel.CRITICAL and not a.resolved)
            }
            
            return {
                "total_components": total_components,
                "healthy_components": healthy_components,
                "warning_components": warning_components,
                "error_components": error_components,
                "health_percentage": (healthy_components / total_components * 100) if total_components > 0 else 0,
                "active_alerts": alert_counts,
                "total_alerts": sum(alert_counts.values())
            }
            
        except Exception as e:
            logger.error(f"Error generating system summary: {e}")
            return {}
    
    def _get_performance_trends(self) -> Dict[str, Any]:
        """Obtiene tendencias de rendimiento"""
        try:
            # Obtener métricas de la última hora
            hour_ago = datetime.now() - timedelta(hours=1)
            recent_metrics = [
                metric for metric in self.metrics_history
                if metric.timestamp > hour_ago and metric.metric_type == MetricType.PERFORMANCE
            ]
            
            # Agrupar por componente
            component_trends = {}
            for metric in recent_metrics:
                if metric.component not in component_trends:
                    component_trends[metric.component] = []
                component_trends[metric.component].append(metric.value)
            
            # Calcular promedios
            trends = {}
            for component, values in component_trends.items():
                if values:
                    trends[component] = {
                        "average_response_time": sum(values) / len(values),
                        "max_response_time": max(values),
                        "min_response_time": min(values),
                        "data_points": len(values)
                    }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {}
    
    def _get_mock_dashboard_data(self) -> Dict[str, Any]:
        """Datos simulados del dashboard"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_summary": {
                "total_components": 13,
                "healthy_components": 10,
                "warning_components": 2,
                "error_components": 1,
                "health_percentage": 76.9,
                "active_alerts": {"info": 0, "warning": 2, "error": 1, "critical": 0},
                "total_alerts": 3
            },
            "component_status": {
                "career_predictor": {"status": "healthy", "response_time_ms": 150, "success_rate": 0.95, "uptime_hours": 24.5},
                "market_predictor": {"status": "healthy", "response_time_ms": 200, "success_rate": 0.92, "uptime_hours": 24.3}
            },
            "recent_metrics": [],
            "active_alerts": [],
            "performance_trends": {}
        }


# Instancia global del monitor
aura_monitor = AuraMonitor() 