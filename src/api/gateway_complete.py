"""
🚀 HUNTRED® V2 - API GATEWAY COMPLETO
====================================

Gateway unificado que centraliza todos los endpoints del sistema.
Maneja autenticación, rate limiting, logging y orquestación de servicios.

Autor: GHUNTRED V2 Team
Fecha: Diciembre 2024
Versión: 1.0.0
"""

from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import redis
import logging

# Core imports
from ..core.system_orchestrator import get_system_orchestrator, SystemOrchestrator
from ..database.connection import get_db_session
from ..auth.auth_service import AuthService
from ..config.settings import get_settings

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize components
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer()
redis_client = redis.Redis.from_url(settings.REDIS_URL)

app = FastAPI(
    title="HuntRED® v2 Complete API",
    description="Sistema completo de reclutamiento con IA avanzada",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# =============================================================================
# MIDDLEWARE PERSONALIZADO
# =============================================================================

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Middleware para logging y métricas"""
    start_time = time.time()
    
    # Log request
    logger.info(f"📨 {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Timestamp"] = datetime.utcnow().isoformat()
        
        # Log response
        logger.info(f"✅ {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        # Store metrics in Redis
        await _store_request_metrics(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time=process_time
        )
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - Error: {e} ({process_time:.3f}s)")
        
        await _store_request_metrics(
            method=request.method,
            path=request.url.path,
            status_code=500,
            response_time=process_time,
            error=str(e)
        )
        
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "detail": str(e)}
        )

async def _store_request_metrics(method: str, path: str, status_code: int, 
                               response_time: float, error: str = None):
    """Almacena métricas de requests en Redis"""
    try:
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "error": error
        }
        
        # Store individual metric
        redis_client.lpush("huntred:api:metrics", json.dumps(metrics))
        redis_client.ltrim("huntred:api:metrics", 0, 1000)  # Keep last 1000
        
        # Update counters
        redis_client.incr("huntred:api:total_requests")
        if status_code < 400:
            redis_client.incr("huntred:api:successful_requests")
        else:
            redis_client.incr("huntred:api:failed_requests")
            
    except Exception as e:
        logger.error(f"Error storing metrics: {e}")

# =============================================================================
# AUTHENTICATION
# =============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el usuario actual desde el token JWT"""
    try:
        auth_service = AuthService()
        token = credentials.credentials
        user_data = auth_service.verify_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        return user_data
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error de autenticación: {e}")

async def get_orchestrator() -> SystemOrchestrator:
    """Obtiene la instancia del orchestrator"""
    db = next(get_db_session())
    return await get_system_orchestrator(db)

# =============================================================================
# MODELOS PYDANTIC
# =============================================================================

class SystemStatusResponse(BaseModel):
    status: str
    uptime: float
    modules: Dict[str, Any]
    metrics: Dict[str, Any]

class JobCreateRequest(BaseModel):
    title: str
    description: str
    requirements: List[str]
    location: str
    salary_range: Optional[Dict[str, float]] = None
    client_id: str

class CandidateSearchRequest(BaseModel):
    job_id: str
    max_candidates: int = 50
    filters: Optional[Dict[str, Any]] = None

class NotificationRequest(BaseModel):
    recipient_id: str
    channel: str
    template: str
    data: Dict[str, Any]

# =============================================================================
# ENDPOINTS PRINCIPALES
# =============================================================================

@app.get("/")
async def root():
    """Endpoint raíz con información del API"""
    return {
        "service": "HuntRED® v2 Complete API",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "documentation": "/docs"
    }

@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check del API Gateway"""
    try:
        orchestrator = await get_orchestrator()
        system_status = orchestrator.get_system_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_status,
            "api_gateway": {
                "status": "operational",
                "response_time": "< 50ms"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/system/status", response_model=SystemStatusResponse)
@limiter.limit("30/minute")
async def get_system_status(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene el estado completo del sistema"""
    try:
        orchestrator = await get_orchestrator()
        return orchestrator.get_system_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE AUTENTICACIÓN
# =============================================================================

@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, credentials: dict):
    """Login de usuario"""
    try:
        orchestrator = await get_orchestrator()
        auth_service = orchestrator.get_service("auth")
        
        token_data = auth_service.authenticate(
            username=credentials.get("username"),
            password=credentials.get("password")
        )
        
        if not token_data:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        return {
            "access_token": token_data["access_token"],
            "token_type": "bearer",
            "user": token_data["user"],
            "expires_in": token_data["expires_in"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Obtiene información del usuario actual"""
    return current_user

# =============================================================================
# ENDPOINTS DE RECLUTAMIENTO
# =============================================================================

@app.post("/recruitment/jobs")
@limiter.limit("20/minute")
async def create_job(
    request: Request,
    job_data: JobCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Crea una nueva posición de trabajo"""
    try:
        orchestrator = await get_orchestrator()
        
        # Ejecutar workflow completo de reclutamiento
        workflow_result = await orchestrator.execute_recruitment_workflow(
            job_id=f"job_{int(time.time())}",
            client_id=job_data.client_id
        )
        
        return {
            "job_created": True,
            "workflow": workflow_result,
            "message": "Trabajo creado y workflow iniciado"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recruitment/search")
@limiter.limit("30/minute")
async def search_candidates(
    request: Request,
    search_data: CandidateSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Busca candidatos usando GenIA"""
    try:
        orchestrator = await get_orchestrator()
        genia_service = orchestrator.get_service("genia")
        
        candidates = await genia_service.find_candidates(
            job_id=search_data.job_id,
            max_candidates=search_data.max_candidates,
            filters=search_data.filters
        )
        
        return {
            "candidates": candidates,
            "total_found": len(candidates),
            "search_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE NOTIFICACIONES
# =============================================================================

@app.post("/notifications/send")
@limiter.limit("100/minute")
async def send_notification(
    request: Request,
    notification_data: NotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Envía una notificación"""
    try:
        orchestrator = await get_orchestrator()
        notifications_service = orchestrator.get_service("notifications")
        
        result = await notifications_service.send_notification(
            recipient_id=notification_data.recipient_id,
            channel=notification_data.channel,
            template=notification_data.template,
            data=notification_data.data
        )
        
        return {
            "notification_sent": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications/channels")
async def get_notification_channels(current_user: dict = Depends(get_current_user)):
    """Obtiene los canales de notificación disponibles"""
    try:
        orchestrator = await get_orchestrator()
        notifications_service = orchestrator.get_service("notifications")
        
        channels = await notifications_service.get_available_channels()
        
        return {
            "channels": channels,
            "total": len(channels)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE AURA AI
# =============================================================================

@app.post("/ai/aura/chat")
@limiter.limit("60/minute")
async def aura_chat(
    request: Request,
    chat_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Chat con AURA AI Assistant"""
    try:
        orchestrator = await get_orchestrator()
        aura_service = orchestrator.get_service("aura")
        
        response = await aura_service.process_query(
            query=chat_data.get("message"),
            user_id=current_user.get("id"),
            context=chat_data.get("context", {})
        )
        
        return {
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user.get("id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE NÓMINA
# =============================================================================

@app.get("/payroll/employee/{employee_id}/latest")
async def get_latest_payslip(
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene la última nómina de un empleado"""
    try:
        orchestrator = await get_orchestrator()
        payroll_service = orchestrator.get_service("payroll")
        
        payslip = await payroll_service.get_latest_payslip(employee_id)
        
        return {
            "payslip": payslip,
            "employee_id": employee_id,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/payroll/calculate")
@limiter.limit("20/minute")
async def calculate_payroll(
    request: Request,
    payroll_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Calcula la nómina para un empleado"""
    try:
        orchestrator = await get_orchestrator()
        payroll_service = orchestrator.get_service("payroll")
        
        calculation = await payroll_service.calculate_payroll(
            employee_id=payroll_data.get("employee_id"),
            period=payroll_data.get("period"),
            additional_data=payroll_data.get("additional_data", {})
        )
        
        return {
            "calculation": calculation,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE ASISTENCIA
# =============================================================================

@app.post("/attendance/checkin")
@limiter.limit("10/minute")
async def checkin(
    request: Request,
    checkin_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Registra entrada de empleado"""
    try:
        orchestrator = await get_orchestrator()
        attendance_service = orchestrator.get_service("attendance")
        
        result = await attendance_service.check_in(
            employee_id=current_user.get("id"),
            location=checkin_data.get("location"),
            timestamp=datetime.utcnow()
        )
        
        return {
            "checkin_successful": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/attendance/checkout")
@limiter.limit("10/minute")
async def checkout(
    request: Request,
    checkout_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Registra salida de empleado"""
    try:
        orchestrator = await get_orchestrator()
        attendance_service = orchestrator.get_service("attendance")
        
        result = await attendance_service.check_out(
            employee_id=current_user.get("id"),
            location=checkout_data.get("location"),
            timestamp=datetime.utcnow()
        )
        
        return {
            "checkout_successful": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE REPORTES
# =============================================================================

@app.get("/reports/dashboard/{dashboard_type}")
async def get_dashboard_data(
    dashboard_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtiene datos para dashboards"""
    try:
        orchestrator = await get_orchestrator()
        dashboards_service = orchestrator.get_service("dashboards")
        
        data = await dashboards_service.get_dashboard_data(
            dashboard_type=dashboard_type,
            user_id=current_user.get("id")
        )
        
        return {
            "dashboard_data": data,
            "dashboard_type": dashboard_type,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# ENDPOINTS DE MÉTRICAS
# =============================================================================

@app.get("/metrics/api")
async def get_api_metrics(current_user: dict = Depends(get_current_user)):
    """Obtiene métricas del API"""
    try:
        total_requests = int(redis_client.get("huntred:api:total_requests") or 0)
        successful_requests = int(redis_client.get("huntred:api:successful_requests") or 0)
        failed_requests = int(redis_client.get("huntred:api:failed_requests") or 0)
        
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 100
        
        # Get recent metrics
        recent_metrics = redis_client.lrange("huntred:api:metrics", 0, 100)
        recent_metrics = [json.loads(m) for m in recent_metrics]
        
        avg_response_time = sum(m.get("response_time", 0) for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(avg_response_time, 3),
            "recent_activity": recent_metrics[:10]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# STARTUP Y SHUTDOWN
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio del API"""
    logger.info("🚀 Iniciando HuntRED® v2 Complete API...")
    
    try:
        # Initialize system
        db = next(get_db_session())
        orchestrator = await get_system_orchestrator(db)
        
        logger.info("✅ API Gateway inicializado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando API Gateway: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre del API"""
    logger.info("🛑 Cerrando HuntRED® v2 Complete API...")
    
    try:
        # Shutdown system
        db = next(get_db_session())
        orchestrator = await get_system_orchestrator(db)
        await orchestrator.shutdown()
        
        logger.info("✅ API Gateway cerrado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error cerrando API Gateway: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "gateway_complete:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )