"""
🚀 HUNTRED® V2 - SYSTEM ORCHESTRATOR
===================================

Coordinador maestro de todos los módulos del sistema.
Maneja el estado global, flujos de trabajo integrados y health monitoring.

Autor: GHUNTRED V2 Team
Fecha: Diciembre 2024
Versión: 1.0.0
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
import json
import redis
from sqlalchemy.orm import Session

# Core imports
from ..database.models import *
from ..auth.auth_service import AuthService
from ..config.settings import get_settings

# Services imports
from ..services.advanced_notifications_service import AdvancedNotificationsService
from ..services.advanced_references_service import AdvancedReferencesService
from ..services.advanced_feedback_service import AdvancedFeedbackService
from ..services.proposals_service import ProposalsService
from ..services.payments_service import PaymentsService
from ..services.referrals_service import ReferralsService
from ..services.onboarding_service import OnboardingService
from ..services.workflows_service import WorkflowsService
from ..services.business_units_service import BusinessUnitsService
from ..services.dashboards_service import DashboardsService
from ..services.employee_service import EmployeeService
from ..services.real_payroll_service import RealPayrollService
from ..services.attendance_service import AttendanceService
from ..services.reports_service import ReportsService

# AI imports
from ..ai.aura_assistant import AURAAssistant
from ..ml.genia_matchmaking import GeniaMatchmaking
from ..ml.sentiment_analysis import SentimentAnalysis
from ..ml.turnover_prediction import TurnoverPrediction

# Utils
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class SystemStatus(Enum):
    """Estados del sistema"""
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"

class ModuleStatus(Enum):
    """Estados de los módulos"""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"

@dataclass
class ModuleHealth:
    """Información de salud de un módulo"""
    name: str
    status: ModuleStatus
    last_check: datetime
    response_time: float
    error_count: int = 0
    success_rate: float = 100.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemMetrics:
    """Métricas del sistema"""
    uptime: timedelta
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    peak_response_time: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    active_users: int = 0
    cache_hit_ratio: float = 0.0

class SystemOrchestrator:
    """
    🧠 COORDINADOR MAESTRO DEL SISTEMA HUNTRED® V2
    
    Responsabilidades:
    - Inicialización y coordinación de todos los módulos
    - Monitoring de salud del sistema
    - Gestión de flujos de trabajo integrados
    - Cache y estado global
    - Performance optimization
    - Error handling y recovery
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.start_time = datetime.utcnow()
        self.status = SystemStatus.STARTING
        
        # Estado del sistema
        self.modules: Dict[str, Any] = {}
        self.module_health: Dict[str, ModuleHealth] = {}
        self.metrics = SystemMetrics(uptime=timedelta(0))
        
        # Services registry
        self.services = {}
        
        # Event callbacks
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        logger.info("🚀 Iniciando System Orchestrator...")
        
    async def initialize(self) -> bool:
        """Inicializa todos los módulos del sistema"""
        try:
            logger.info("🔄 Iniciando inicialización completa del sistema...")
            
            # 1. Inicializar servicios core
            await self._initialize_core_services()
            
            # 2. Inicializar servicios de negocio
            await self._initialize_business_services()
            
            # 3. Inicializar servicios de IA
            await self._initialize_ai_services()
            
            # 4. Inicializar monitoring
            await self._initialize_monitoring()
            
            # 5. Verificar integridad del sistema
            system_healthy = await self._verify_system_integrity()
            
            if system_healthy:
                self.status = SystemStatus.HEALTHY
                logger.info("✅ Sistema inicializado exitosamente!")
                await self._emit_event("system_ready", {"timestamp": datetime.utcnow()})
                return True
            else:
                self.status = SystemStatus.DEGRADED
                logger.warning("⚠️ Sistema inicializado con algunos problemas")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error crítico en inicialización: {e}")
            self.status = SystemStatus.CRITICAL
            return False
    
    async def _initialize_core_services(self):
        """Inicializa servicios core del sistema"""
        logger.info("🔧 Inicializando servicios core...")
        
        # Auth Service
        self.services['auth'] = AuthService()
        await self._register_module('auth', self.services['auth'])
        
        # Employee Service
        self.services['employee'] = EmployeeService(self.db)
        await self._register_module('employee', self.services['employee'])
        
        # Payroll Service
        self.services['payroll'] = RealPayrollService(self.db)
        await self._register_module('payroll', self.services['payroll'])
        
        # Attendance Service
        self.services['attendance'] = AttendanceService(self.db)
        await self._register_module('attendance', self.services['attendance'])
        
        # Reports Service
        self.services['reports'] = ReportsService(self.db)
        await self._register_module('reports', self.services['reports'])
        
        logger.info("✅ Servicios core inicializados")
    
    async def _initialize_business_services(self):
        """Inicializa servicios de negocio"""
        logger.info("💼 Inicializando servicios de negocio...")
        
        # Advanced Notifications
        self.services['notifications'] = AdvancedNotificationsService(self.db)
        await self._register_module('notifications', self.services['notifications'])
        
        # Advanced References
        self.services['references'] = AdvancedReferencesService(self.db)
        await self._register_module('references', self.services['references'])
        
        # Advanced Feedback
        self.services['feedback'] = AdvancedFeedbackService(self.db)
        await self._register_module('feedback', self.services['feedback'])
        
        # Proposals Service
        self.services['proposals'] = ProposalsService(self.db)
        await self._register_module('proposals', self.services['proposals'])
        
        # Payments Service
        self.services['payments'] = PaymentsService(self.db)
        await self._register_module('payments', self.services['payments'])
        
        # Referrals Service
        self.services['referrals'] = ReferralsService(self.db)
        await self._register_module('referrals', self.services['referrals'])
        
        # Onboarding Service
        self.services['onboarding'] = OnboardingService(self.db)
        await self._register_module('onboarding', self.services['onboarding'])
        
        # Workflows Service
        self.services['workflows'] = WorkflowsService(self.db)
        await self._register_module('workflows', self.services['workflows'])
        
        # Business Units Service
        self.services['business_units'] = BusinessUnitsService(self.db)
        await self._register_module('business_units', self.services['business_units'])
        
        # Dashboards Service
        self.services['dashboards'] = DashboardsService(self.db)
        await self._register_module('dashboards', self.services['dashboards'])
        
        logger.info("✅ Servicios de negocio inicializados")
    
    async def _initialize_ai_services(self):
        """Inicializa servicios de IA"""
        logger.info("🤖 Inicializando servicios de IA...")
        
        # AURA Assistant
        self.services['aura'] = AURAAssistant()
        await self._register_module('aura', self.services['aura'])
        
        # GenIA Matchmaking
        self.services['genia'] = GeniaMatchmaking()
        await self._register_module('genia', self.services['genia'])
        
        # Sentiment Analysis
        self.services['sentiment'] = SentimentAnalysis()
        await self._register_module('sentiment', self.services['sentiment'])
        
        # Turnover Prediction
        self.services['turnover'] = TurnoverPrediction()
        await self._register_module('turnover', self.services['turnover'])
        
        logger.info("✅ Servicios de IA inicializados")
    
    async def _initialize_monitoring(self):
        """Inicializa sistema de monitoring"""
        logger.info("📊 Inicializando monitoring...")
        
        # Background task para health checks
        asyncio.create_task(self._health_check_loop())
        
        # Background task para métricas
        asyncio.create_task(self._metrics_collection_loop())
        
        logger.info("✅ Monitoring inicializado")
    
    async def _register_module(self, name: str, module: Any):
        """Registra un módulo en el sistema"""
        try:
            start_time = time.time()
            
            # Verificar si el módulo tiene método de health check
            if hasattr(module, 'health_check'):
                await module.health_check()
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            self.modules[name] = module
            self.module_health[name] = ModuleHealth(
                name=name,
                status=ModuleStatus.READY,
                last_check=datetime.utcnow(),
                response_time=response_time
            )
            
            logger.info(f"✅ Módulo '{name}' registrado ({response_time:.2f}ms)")
            
        except Exception as e:
            logger.error(f"❌ Error registrando módulo '{name}': {e}")
            self.module_health[name] = ModuleHealth(
                name=name,
                status=ModuleStatus.ERROR,
                last_check=datetime.utcnow(),
                response_time=0,
                error_count=1
            )
    
    async def _verify_system_integrity(self) -> bool:
        """Verifica la integridad del sistema"""
        logger.info("🔍 Verificando integridad del sistema...")
        
        total_modules = len(self.modules)
        healthy_modules = sum(1 for health in self.module_health.values() 
                            if health.status == ModuleStatus.READY)
        
        health_ratio = healthy_modules / total_modules if total_modules > 0 else 0
        
        logger.info(f"📈 Salud del sistema: {healthy_modules}/{total_modules} módulos OK ({health_ratio:.1%})")
        
        return health_ratio >= 0.8  # 80% de módulos deben estar saludables
    
    async def _health_check_loop(self):
        """Loop de health checks cada 30 segundos"""
        while True:
            try:
                await asyncio.sleep(30)
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"Error en health check loop: {e}")
    
    async def _perform_health_checks(self):
        """Ejecuta health checks en todos los módulos"""
        for name, module in self.modules.items():
            try:
                start_time = time.time()
                
                if hasattr(module, 'health_check'):
                    await module.health_check()
                
                response_time = (time.time() - start_time) * 1000
                
                # Actualizar health
                if name in self.module_health:
                    self.module_health[name].last_check = datetime.utcnow()
                    self.module_health[name].response_time = response_time
                    self.module_health[name].status = ModuleStatus.READY
                
            except Exception as e:
                logger.warning(f"Health check fallido para '{name}': {e}")
                if name in self.module_health:
                    self.module_health[name].status = ModuleStatus.ERROR
                    self.module_health[name].error_count += 1
    
    async def _metrics_collection_loop(self):
        """Loop de recolección de métricas cada 60 segundos"""
        while True:
            try:
                await asyncio.sleep(60)
                await self._collect_metrics()
            except Exception as e:
                logger.error(f"Error en metrics collection loop: {e}")
    
    async def _collect_metrics(self):
        """Recolecta métricas del sistema"""
        self.metrics.uptime = datetime.utcnow() - self.start_time
        
        # Calcular success rate general
        total_requests = self.metrics.total_requests
        if total_requests > 0:
            success_rate = (self.metrics.successful_requests / total_requests) * 100
        else:
            success_rate = 100.0
        
        # Guardar métricas en Redis para dashboards
        metrics_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.status.value,
            "uptime_seconds": self.metrics.uptime.total_seconds(),
            "total_requests": self.metrics.total_requests,
            "success_rate": success_rate,
            "avg_response_time": self.metrics.avg_response_time,
            "modules_status": {
                name: health.status.value 
                for name, health in self.module_health.items()
            }
        }
        
        self.redis_client.setex(
            "huntred:system:metrics", 
            300,  # 5 minutos TTL
            json.dumps(metrics_data)
        )
    
    # =============================================================================
    # FLUJOS DE TRABAJO INTEGRADOS
    # =============================================================================
    
    async def execute_recruitment_workflow(self, job_id: str, client_id: str) -> Dict[str, Any]:
        """Ejecuta el flujo completo de reclutamiento"""
        try:
            logger.info(f"🎯 Iniciando workflow de reclutamiento para job {job_id}")
            
            workflow_data = {
                "job_id": job_id,
                "client_id": client_id,
                "started_at": datetime.utcnow(),
                "steps": []
            }
            
            # Paso 1: GenIA Matchmaking
            step_start = time.time()
            candidates = await self.services['genia'].find_candidates(job_id)
            workflow_data['steps'].append({
                "step": "matchmaking",
                "duration": time.time() - step_start,
                "candidates_found": len(candidates),
                "status": "completed"
            })
            
            # Paso 2: Notificaciones automáticas
            step_start = time.time()
            for candidate in candidates[:10]:  # Top 10
                await self.services['notifications'].send_candidate_notification(
                    candidate['id'], job_id, "new_opportunity"
                )
            workflow_data['steps'].append({
                "step": "candidate_notifications",
                "duration": time.time() - step_start,
                "notifications_sent": min(10, len(candidates)),
                "status": "completed"
            })
            
            # Paso 3: Crear propuesta para cliente
            step_start = time.time()
            proposal = await self.services['proposals'].create_job_proposal(
                client_id, job_id, candidates
            )
            workflow_data['steps'].append({
                "step": "proposal_creation",
                "duration": time.time() - step_start,
                "proposal_id": proposal['id'],
                "status": "completed"
            })
            
            # Paso 4: Notificar cliente
            step_start = time.time()
            await self.services['notifications'].send_client_notification(
                client_id, "proposal_ready", {"proposal_id": proposal['id']}
            )
            workflow_data['steps'].append({
                "step": "client_notification",
                "duration": time.time() - step_start,
                "status": "completed"
            })
            
            workflow_data['completed_at'] = datetime.utcnow()
            workflow_data['total_duration'] = sum(s['duration'] for s in workflow_data['steps'])
            workflow_data['status'] = 'completed'
            
            await self._emit_event('recruitment_workflow_completed', workflow_data)
            
            logger.info(f"✅ Workflow completado en {workflow_data['total_duration']:.2f}s")
            return workflow_data
            
        except Exception as e:
            logger.error(f"❌ Error en workflow de reclutamiento: {e}")
            workflow_data['status'] = 'failed'
            workflow_data['error'] = str(e)
            return workflow_data
    
    async def execute_onboarding_workflow(self, employee_id: str) -> Dict[str, Any]:
        """Ejecuta el flujo completo de onboarding"""
        try:
            logger.info(f"👋 Iniciando workflow de onboarding para empleado {employee_id}")
            
            # Obtener información del empleado
            employee = self.services['employee'].get_employee(employee_id)
            if not employee:
                raise ValueError(f"Empleado {employee_id} no encontrado")
            
            workflow_data = {
                "employee_id": employee_id,
                "started_at": datetime.utcnow(),
                "steps": []
            }
            
            # Paso 1: Crear proceso de onboarding
            step_start = time.time()
            onboarding = await self.services['onboarding'].create_onboarding_process(
                employee_id, employee['role']
            )
            workflow_data['steps'].append({
                "step": "create_onboarding",
                "duration": time.time() - step_start,
                "onboarding_id": onboarding['id'],
                "status": "completed"
            })
            
            # Paso 2: Notificación de bienvenida
            step_start = time.time()
            await self.services['notifications'].send_welcome_notification(
                employee_id, onboarding['id']
            )
            workflow_data['steps'].append({
                "step": "welcome_notification",
                "duration": time.time() - step_start,
                "status": "completed"
            })
            
            # Paso 3: Configurar accesos
            step_start = time.time()
            # Aquí iría integración con sistemas de accesos
            workflow_data['steps'].append({
                "step": "access_setup",
                "duration": time.time() - step_start,
                "status": "completed"
            })
            
            # Paso 4: Programar seguimientos
            step_start = time.time()
            await self.services['workflows'].schedule_onboarding_followups(
                employee_id, onboarding['id']
            )
            workflow_data['steps'].append({
                "step": "schedule_followups",
                "duration": time.time() - step_start,
                "status": "completed"
            })
            
            workflow_data['completed_at'] = datetime.utcnow()
            workflow_data['total_duration'] = sum(s['duration'] for s in workflow_data['steps'])
            workflow_data['status'] = 'completed'
            
            await self._emit_event('onboarding_workflow_completed', workflow_data)
            
            logger.info(f"✅ Onboarding workflow completado en {workflow_data['total_duration']:.2f}s")
            return workflow_data
            
        except Exception as e:
            logger.error(f"❌ Error en workflow de onboarding: {e}")
            workflow_data['status'] = 'failed'
            workflow_data['error'] = str(e)
            return workflow_data
    
    # =============================================================================
    # GESTIÓN DE EVENTOS
    # =============================================================================
    
    def on(self, event: str, handler: Callable):
        """Registra un handler para un evento"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, data: Any):
        """Emite un evento a todos los handlers registrados"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"Error en event handler para '{event}': {e}")
    
    # =============================================================================
    # API PÚBLICA
    # =============================================================================
    
    def get_service(self, name: str) -> Optional[Any]:
        """Obtiene un servicio por nombre"""
        return self.services.get(name)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema"""
        return {
            "status": self.status.value,
            "uptime": self.metrics.uptime.total_seconds(),
            "modules": {
                name: {
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "response_time": health.response_time,
                    "error_count": health.error_count
                }
                for name, health in self.module_health.items()
            },
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "avg_response_time": self.metrics.avg_response_time,
                "active_users": self.metrics.active_users
            }
        }
    
    def get_module_health(self, module_name: str) -> Optional[ModuleHealth]:
        """Obtiene la salud de un módulo específico"""
        return self.module_health.get(module_name)
    
    async def shutdown(self):
        """Apaga el sistema ordenadamente"""
        logger.info("🛑 Iniciando shutdown del sistema...")
        self.status = SystemStatus.SHUTDOWN
        
        # Notificar a todos los módulos
        for name, module in self.modules.items():
            try:
                if hasattr(module, 'shutdown'):
                    await module.shutdown()
                logger.info(f"✅ Módulo '{name}' apagado")
            except Exception as e:
                logger.error(f"❌ Error apagando módulo '{name}': {e}")
        
        logger.info("✅ Sistema apagado completamente")


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_orchestrator_instance: Optional[SystemOrchestrator] = None

async def get_system_orchestrator(db_session: Session) -> SystemOrchestrator:
    """Factory function para obtener la instancia del orchestrator"""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = SystemOrchestrator(db_session)
        await _orchestrator_instance.initialize()
    
    return _orchestrator_instance

async def initialize_system(db_session: Session) -> bool:
    """Inicializa el sistema completo"""
    orchestrator = await get_system_orchestrator(db_session)
    return orchestrator.status == SystemStatus.HEALTHY