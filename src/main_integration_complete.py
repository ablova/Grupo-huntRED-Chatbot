"""
HuntRED® v2 - Main Integration Complete
Sistema completamente integrado con todos los módulos funcionando
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
import json
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Core imports
from core.system_orchestrator import SystemOrchestrator
from api.gateway_complete import APIGatewayComplete

# Service imports
from services.publish_service import JobPublishingService, PublishPlatform
from services.virtuous_circle_orchestrator import VirtuousCircleOrchestrator
from services.location_analytics_service import LocationAnalyticsService
from services.advanced_notifications_service import NotificationService
from services.dashboards_service import DashboardsService
from services.business_units_service import BusinessUnitsService
from services.workflows_service import WorkflowsService
from services.onboarding_service import OnboardingService
from services.payments_service import PaymentsService
from services.referrals_service import ReferralsService
from services.proposals_service import ProposalsService

# Scraper imports
from scrapers.enterprise_ats_scraper import EnterpriseATSScraper, ATSPlatform
from scrapers.job_boards_scraper import JobBoardsScraper

# Chatbot imports
from chatbots.recruitment_chatbot_complete import RecruitmentChatbotManager, BusinessUnit

# ML/AI imports
from ml.genia_location_integration import GenIALocationIntegration
from ai.aura_ai_assistant import AURAAssistant
from ai.advanced_neural_engine import AdvancedNeuralEngine
from ai.quantum_consciousness_engine import QuantumConsciousnessEngine

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HuntREDv2MainSystem:
    """Sistema principal completo de HuntRED® v2"""
    
    def __init__(self):
        self.app = FastAPI(
            title="HuntRED® v2 - Complete System",
            description="Sistema integral de gestión de RRHH con IA avanzada",
            version="2.0.0"
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Configuración del sistema
        self.config = {
            "database": {
                "url": "postgresql://huntred:password@localhost:5432/huntred_v2",
                "echo": True
            },
            "redis": {
                "url": "redis://localhost:6379"
            },
            "apis": {
                "openai_key": "sk-test",
                "google_maps_key": "AIza-test",
                "whatsapp_token": "test-token"
            },
            "business_units": {
                "huntred_executive": {"enabled": True, "priority": "high"},
                "huntred_general": {"enabled": True, "priority": "high"},
                "huntu": {"enabled": True, "priority": "medium"},
                "amigro": {"enabled": True, "priority": "high"}
            }
        }
        
        # Inicializar servicios
        self.services = {}
        self.scrapers = {}
        self.chatbots = {}
        self.ai_engines = {}
        
        # Sistema orchestrador
        self.orchestrator = None
        self.api_gateway = None
        
        # Estado del sistema
        self.system_status = {
            "initialized": False,
            "services_running": 0,
            "total_services": 20,
            "last_health_check": None,
            "virtuous_circle_active": False,
            "active_conversations": 0,
            "jobs_scraped_today": 0,
            "proposals_sent_today": 0
        }
    
    async def initialize_system(self):
        """Inicializa todo el sistema completo"""
        
        try:
            logger.info("🚀 Inicializando HuntRED® v2 Complete System...")
            
            # 1. Inicializar servicios core
            await self._initialize_core_services()
            
            # 2. Inicializar scrapers
            await self._initialize_scrapers()
            
            # 3. Inicializar chatbots
            await self._initialize_chatbots()
            
            # 4. Inicializar AI engines
            await self._initialize_ai_engines()
            
            # 5. Inicializar orchestrador
            await self._initialize_orchestrator()
            
            # 6. Inicializar API Gateway
            await self._initialize_api_gateway()
            
            # 7. Configurar endpoints
            self._setup_endpoints()
            
            # 8. Inicializar círculo virtuoso
            await self._start_virtuous_circle()
            
            self.system_status["initialized"] = True
            self.system_status["last_health_check"] = datetime.now()
            
            logger.info("✅ HuntRED® v2 System completamente inicializado!")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema: {e}")
            raise
    
    async def _initialize_core_services(self):
        """Inicializa servicios principales"""
        
        logger.info("📦 Inicializando servicios core...")
        
        # Publishing Service
        self.services["publishing"] = JobPublishingService(self.config)
        
        # Location Analytics
        self.services["location"] = LocationAnalyticsService(self.config)
        
        # Notifications
        self.services["notifications"] = NotificationService(self.config)
        
        # Dashboards
        self.services["dashboards"] = DashboardsService(self.config)
        
        # Business Units
        self.services["business_units"] = BusinessUnitsService(self.config)
        
        # Workflows
        self.services["workflows"] = WorkflowsService(self.config)
        
        # Onboarding
        self.services["onboarding"] = OnboardingService(self.config)
        
        # Payments
        self.services["payments"] = PaymentsService(self.config)
        
        # Referrals
        self.services["referrals"] = ReferralsService(self.config)
        
        # Proposals
        self.services["proposals"] = ProposalsService(self.config)
        
        self.system_status["services_running"] += 10
        logger.info("✅ Servicios core inicializados")
    
    async def _initialize_scrapers(self):
        """Inicializa scrapers"""
        
        logger.info("🕷️ Inicializando scrapers...")
        
        # Enterprise ATS Scraper
        self.scrapers["ats"] = EnterpriseATSScraper(self.config)
        
        # Job Boards Scraper
        self.scrapers["job_boards"] = JobBoardsScraper(self.config)
        
        self.system_status["services_running"] += 2
        logger.info("✅ Scrapers inicializados")
    
    async def _initialize_chatbots(self):
        """Inicializa chatbots"""
        
        logger.info("🤖 Inicializando chatbots...")
        
        # Recruitment Chatbot Manager
        self.chatbots["recruitment"] = RecruitmentChatbotManager(self.config)
        
        self.system_status["services_running"] += 1
        logger.info("✅ Chatbots inicializados")
    
    async def _initialize_ai_engines(self):
        """Inicializa engines de IA"""
        
        logger.info("🧠 Inicializando AI engines...")
        
        # AURA Assistant
        self.ai_engines["aura"] = AURAAssistant(self.config)
        
        # Advanced Neural Engine
        self.ai_engines["neural"] = AdvancedNeuralEngine(self.config)
        
        # Quantum Consciousness Engine
        self.ai_engines["quantum"] = QuantumConsciousnessEngine(self.config)
        
        # GenIA Location Integration
        self.ai_engines["genia_location"] = GenIALocationIntegration(self.config)
        
        self.system_status["services_running"] += 4
        logger.info("✅ AI engines inicializados")
    
    async def _initialize_orchestrator(self):
        """Inicializa orchestrador del sistema"""
        
        logger.info("🎯 Inicializando orchestrador...")
        
        all_services = {
            **self.services,
            **self.scrapers,
            **self.chatbots,
            **self.ai_engines
        }
        
        self.orchestrator = SystemOrchestrator(all_services, self.config)
        await self.orchestrator.start_monitoring()
        
        self.system_status["services_running"] += 1
        logger.info("✅ Orchestrador inicializado")
    
    async def _initialize_api_gateway(self):
        """Inicializa API Gateway"""
        
        logger.info("🌐 Inicializando API Gateway...")
        
        all_services = {
            **self.services,
            **self.scrapers,
            **self.chatbots,
            **self.ai_engines
        }
        
        self.api_gateway = APIGatewayComplete(all_services, self.config)
        
        self.system_status["services_running"] += 1
        logger.info("✅ API Gateway inicializado")
    
    def _setup_endpoints(self):
        """Configura todos los endpoints del sistema"""
        
        logger.info("🔗 Configurando endpoints...")
        
        # Health check
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy" if self.system_status["initialized"] else "initializing",
                "system_status": self.system_status,
                "timestamp": datetime.now().isoformat()
            }
        
        # Sistema status
        @self.app.get("/system/status")
        async def system_status():
            return await self.orchestrator.get_system_health() if self.orchestrator else {"status": "not_initialized"}
        
        # Círculo virtuoso
        @self.app.post("/virtuous-circle/trigger")
        async def trigger_virtuous_circle(background_tasks: BackgroundTasks):
            if not self.services.get("virtuous_circle"):
                raise HTTPException(status_code=404, detail="Virtuous circle not initialized")
            
            background_tasks.add_task(self._run_virtuous_circle_cycle)
            return {"message": "Virtuous circle cycle triggered", "status": "running"}
        
        # Scraping endpoints
        @self.app.post("/scraping/ats")
        async def scrape_ats_platforms(platforms: List[str], companies: List[str]):
            ats_platforms = [ATSPlatform(p) for p in platforms if hasattr(ATSPlatform, p.upper())]
            results = await self.scrapers["ats"].scrape_all_ats_platforms(companies, ats_platforms)
            return results
        
        @self.app.post("/scraping/job-boards")
        async def scrape_job_boards(platforms: List[str], search_terms: List[str]):
            results = await self.scrapers["job_boards"].scrape_multiple_platforms(platforms, search_terms)
            return results
        
        # Publishing endpoints
        @self.app.post("/publishing/multi-platform")
        async def publish_job_multi_platform(job_data: Dict[str, Any], platforms: List[str]):
            publish_platforms = [PublishPlatform(p) for p in platforms if hasattr(PublishPlatform, p.upper())]
            results = await self.services["publishing"].publish_job_multi_platform(job_data, publish_platforms)
            return results
        
        # Chatbot endpoints
        @self.app.post("/chatbot/recruitment")
        async def recruitment_chatbot(user_id: str, message: str, platform: str = "whatsapp"):
            response = await self.chatbots["recruitment"].route_conversation(user_id, message, platform)
            if response.get("success"):
                self.system_status["active_conversations"] += 1
            return response
        
        # Business Units endpoints
        @self.app.get("/business-units")
        async def get_business_units():
            return await self.services["business_units"].get_all_business_units()
        
        @self.app.get("/business-units/{unit_id}/metrics")
        async def get_business_unit_metrics(unit_id: str):
            return await self.services["business_units"].get_business_unit_metrics(unit_id)
        
        # Dashboard endpoints
        @self.app.get("/dashboard/main")
        async def get_main_dashboard():
            return await self.services["dashboards"].get_main_dashboard_data()
        
        @self.app.get("/dashboard/analytics")
        async def get_analytics_dashboard():
            return await self.services["dashboards"].get_analytics_dashboard()
        
        # Proposals endpoints
        @self.app.post("/proposals/generate")
        async def generate_proposal(proposal_data: Dict[str, Any]):
            return await self.services["proposals"].generate_comprehensive_proposal(proposal_data)
        
        @self.app.get("/proposals/{proposal_id}/status")
        async def get_proposal_status(proposal_id: str):
            return await self.services["proposals"].get_proposal_status(proposal_id)
        
        # AI endpoints
        @self.app.post("/ai/aura/query")
        async def aura_query(query: str, context: Dict[str, Any] = None):
            return await self.ai_engines["aura"].process_advanced_query(query, context or {})
        
        @self.app.post("/ai/neural/analyze")
        async def neural_analysis(data: Dict[str, Any]):
            return await self.ai_engines["neural"].process_multimodal_input(data)
        
        @self.app.post("/ai/quantum/consciousness")
        async def quantum_consciousness(input_data: Dict[str, Any]):
            return await self.ai_engines["quantum"].process_consciousness_field(input_data)
        
        # Location analytics
        @self.app.post("/location/analyze")
        async def analyze_location(location_data: Dict[str, Any]):
            return await self.services["location"].analyze_comprehensive_location(location_data)
        
        logger.info("✅ Endpoints configurados")
    
    async def _start_virtuous_circle(self):
        """Inicia el círculo virtuoso"""
        
        logger.info("🔄 Iniciando círculo virtuoso...")
        
        # Inicializar Virtuous Circle Orchestrator
        self.services["virtuous_circle"] = VirtuousCircleOrchestrator(
            scrapers=self.scrapers,
            ai_engines=self.ai_engines,
            services=self.services,
            config=self.config
        )
        
        # Programar ciclo automático cada 24 horas
        self.system_status["virtuous_circle_active"] = True
        
        # Ejecutar primer ciclo
        await self._run_virtuous_circle_cycle()
        
        logger.info("✅ Círculo virtuoso activo")
    
    async def _run_virtuous_circle_cycle(self):
        """Ejecuta un ciclo completo del círculo virtuoso"""
        
        try:
            logger.info("🔄 Ejecutando ciclo del círculo virtuoso...")
            
            # Ejecutar ciclo completo
            results = await self.services["virtuous_circle"].execute_complete_cycle()
            
            # Actualizar métricas del sistema
            self.system_status["jobs_scraped_today"] = results.get("jobs_scraped", 0)
            self.system_status["proposals_sent_today"] = results.get("proposals_generated", 0)
            
            logger.info(f"✅ Ciclo completado: {results['jobs_scraped']} jobs, {results['opportunities_detected']} oportunidades, {results['proposals_generated']} propuestas")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo virtuoso: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Ejecuta el servidor principal"""
        
        try:
            # Inicializar sistema completo
            await self.initialize_system()
            
            # Configurar y ejecutar servidor
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
                reload=False
            )
            
            server = uvicorn.Server(config)
            
            logger.info(f"🚀 HuntRED® v2 Complete System running on http://{host}:{port}")
            logger.info("📊 Dashboard disponible en http://localhost:3000")
            logger.info("📝 API docs disponible en http://localhost:8000/docs")
            logger.info("🔄 Círculo virtuoso activo")
            logger.info("🤖 Chatbots de recruitment disponibles")
            logger.info("🕷️ Scrapers enterprise funcionando")
            logger.info("📤 Sistema de publishing multi-plataforma activo")
            
            await server.serve()
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando servidor: {e}")
            raise
    
    async def shutdown(self):
        """Cierra el sistema de forma segura"""
        
        logger.info("🛑 Cerrando HuntRED® v2 System...")
        
        try:
            # Detener orchestrador
            if self.orchestrator:
                await self.orchestrator.stop_monitoring()
            
            # Cerrar servicios
            for service_name, service in self.services.items():
                if hasattr(service, 'shutdown'):
                    await service.shutdown()
                    logger.info(f"✅ {service_name} cerrado")
            
            self.system_status["initialized"] = False
            logger.info("✅ Sistema cerrado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error cerrando sistema: {e}")

# Funciones de utilidad

async def create_sample_data():
    """Crea datos de ejemplo para testing"""
    
    sample_job = {
        "job_id": "test-001",
        "title": "Senior Software Engineer",
        "company": "TechCorp México",
        "location": "Ciudad de México",
        "description": "Desarrollador senior con experiencia en Python y React",
        "salary_min": 800000,
        "salary_max": 1200000,
        "currency": "MXN",
        "remote_work": True,
        "industry": "technology"
    }
    
    sample_candidate = {
        "name": "Juan Pérez",
        "email": "juan@email.com",
        "experience_years": 5,
        "skills": ["python", "react", "sql"],
        "location": "CDMX"
    }
    
    return {
        "sample_job": sample_job,
        "sample_candidate": sample_candidate
    }

async def run_system_demo():
    """Ejecuta demo completo del sistema"""
    
    logger.info("🎬 Iniciando demo completo de HuntRED® v2...")
    
    # Crear sistema
    system = HuntREDv2MainSystem()
    
    try:
        # Inicializar sistema
        await system.initialize_system()
        
        # Crear datos de ejemplo
        sample_data = await create_sample_data()
        
        # Demo de scraping
        logger.info("📡 Demo: Scraping ATS platforms...")
        scraping_results = await system.scrapers["ats"].scrape_all_ats_platforms(
            ["TechCorp", "StartupXYZ"], 
            [ATSPlatform.WORKDAY, ATSPlatform.GREENHOUSE]
        )
        logger.info(f"✅ Scraped {scraping_results['total_jobs']} jobs")
        
        # Demo de chatbot
        logger.info("🤖 Demo: Recruitment chatbot...")
        chat_response = await system.chatbots["recruitment"].route_conversation(
            "demo-user-001",
            "Hola, soy un estudiante de ingeniería buscando mi primer empleo",
            "whatsapp"
        )
        logger.info(f"✅ Chatbot response: {chat_response['message'][:50]}...")
        
        # Demo de publishing
        logger.info("📤 Demo: Multi-platform publishing...")
        publishing_results = await system.services["publishing"].publish_job_multi_platform(
            sample_data["sample_job"],
            [PublishPlatform.INDEED, PublishPlatform.LINKEDIN]
        )
        logger.info(f"✅ Published to {publishing_results['successful_publications']} platforms")
        
        # Demo de AI
        logger.info("🧠 Demo: AURA AI Assistant...")
        ai_response = await system.ai_engines["aura"].process_advanced_query(
            "Analiza el mercado laboral de tecnología en México",
            {"region": "CDMX", "industry": "technology"}
        )
        logger.info(f"✅ AI Analysis complete: {ai_response['summary'][:50]}...")
        
        logger.info("🎉 Demo completo exitoso!")
        
        return {
            "demo_status": "success",
            "scraping_results": scraping_results,
            "chat_response": chat_response,
            "publishing_results": publishing_results,
            "ai_response": ai_response
        }
        
    except Exception as e:
        logger.error(f"❌ Error en demo: {e}")
        return {"demo_status": "error", "error": str(e)}
    
    finally:
        await system.shutdown()

# Main execution
if __name__ == "__main__":
    # Crear y ejecutar sistema
    system = HuntREDv2MainSystem()
    
    try:
        # Ejecutar servidor
        asyncio.run(system.run_server())
    except KeyboardInterrupt:
        logger.info("🛑 Cerrando sistema por interrupción del usuario...")
        asyncio.run(system.shutdown())
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        asyncio.run(system.shutdown())
        raise