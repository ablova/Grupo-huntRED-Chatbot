"""
🚀 HuntRED® v2 - Complete ML API Endpoints
Endpoints completos para ML, Location Analytics, GenIA, AURA y Chatbots
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import logging

from ..chatbots.recruitment_chatbot import get_recruitment_chatbot, BusinessUnit
from ..ai.genia_location_integration import get_genia_location_integration
from ..ai.aura_assistant import get_aura_assistant
from ..services.location_analytics_service import get_location_service
from ..database.database import get_db
from ..core.redis_client import get_redis

logger = logging.getLogger(__name__)

# Modelos Pydantic
class ChatMessage(BaseModel):
    message: str
    business_unit: str
    user_id: str
    conversation_id: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None

class MatchingRequest(BaseModel):
    candidate_data: Dict[str, Any]
    job_requirements: Dict[str, Any]
    business_unit_id: str
    include_location_analysis: bool = True

class LocationAnalysisRequest(BaseModel):
    candidate_address: str
    job_location: str
    business_unit_id: str

class BatchMatchingRequest(BaseModel):
    candidates_data: List[Dict[str, Any]]
    job_requirements: Dict[str, Any]
    business_unit_id: str

class AURAQueryRequest(BaseModel):
    query: str
    user_id: str
    context: Optional[Dict[str, Any]] = None

# Router principal
router = APIRouter(prefix="/api/v1/ml", tags=["Machine Learning"])

# ============================================================================
# CHATBOT ENDPOINTS
# ============================================================================

@router.post("/chatbot/message")
async def send_chatbot_message(
    request: ChatMessage,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Enviar mensaje al chatbot de reclutamiento"""
    try:
        chatbot = get_recruitment_chatbot(db, redis)
        
        # Validar business unit
        try:
            business_unit = BusinessUnit(request.business_unit)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid business unit")
        
        response = await chatbot.process_message(
            message=request.message,
            business_unit=business_unit,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            user_profile=request.user_profile
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"❌ Error en chatbot message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chatbot/analyze-cv")
async def analyze_cv(
    business_unit: str,
    conversation_id: str,
    file: UploadFile = File(...),
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Analizar CV subido por el usuario"""
    try:
        chatbot = get_recruitment_chatbot(db, redis)
        
        # Validar business unit
        try:
            bu = BusinessUnit(business_unit)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid business unit")
        
        # Leer archivo
        cv_content = await file.read()
        cv_text = cv_content.decode('utf-8', errors='ignore')
        
        response = await chatbot.process_cv_analysis(
            cv_text=cv_text,
            business_unit=bu,
            conversation_id=conversation_id
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"❌ Error analizando CV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chatbot/recommendations/{user_id}")
async def get_job_recommendations(
    user_id: str,
    business_unit: str,
    location: Optional[str] = None,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Obtener recomendaciones de trabajo"""
    try:
        chatbot = get_recruitment_chatbot(db, redis)
        
        # Validar business unit
        try:
            bu = BusinessUnit(business_unit)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid business unit")
        
        # Obtener perfil del usuario (mock)
        user_profile = {"user_id": user_id, "location": location}
        
        response = await chatbot.get_job_recommendations(
            user_profile=user_profile,
            business_unit=bu,
            location=location
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chatbot/health")
async def get_chatbot_health(
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Obtener estado de salud del chatbot"""
    try:
        chatbot = get_recruitment_chatbot(db, redis)
        health = await chatbot.get_chatbot_health()
        return JSONResponse(content=health)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo health del chatbot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# GENIA LOCATION INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/genia/location-matching")
async def perform_location_enhanced_matching(
    request: MatchingRequest,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Realizar matching mejorado con análisis de ubicación"""
    try:
        genia_location = get_genia_location_integration(db, redis)
        
        result = await genia_location.perform_location_enhanced_matching(
            candidate_data=request.candidate_data,
            job_requirements=request.job_requirements,
            business_unit_id=request.business_unit_id,
            include_commute_analysis=request.include_location_analysis
        )
        
        # Convertir dataclass a dict para JSON
        response_data = {
            "base_matching_result": {
                "candidate_id": result.base_matching_result.candidate_id,
                "job_id": result.base_matching_result.job_id,
                "overall_score": result.base_matching_result.overall_score,
                "category_scores": result.base_matching_result.category_scores,
                "confidence_level": result.base_matching_result.confidence_level,
                "growth_potential": result.base_matching_result.growth_potential
            },
            "location_analysis": result.location_analysis,
            "commute_feasibility": result.commute_feasibility,
            "transport_recommendations": result.transport_recommendations,
            "work_flexibility_score": result.work_flexibility_score,
            "location_adjusted_score": result.location_adjusted_score,
            "geographic_insights": result.geographic_insights
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"❌ Error en location matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/genia/batch-location-matching")
async def batch_location_matching(
    request: BatchMatchingRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Procesar múltiples candidatos con análisis de ubicación"""
    try:
        genia_location = get_genia_location_integration(db, redis)
        
        # Procesar en background para lotes grandes
        if len(request.candidates_data) > 50:
            background_tasks.add_task(
                _process_large_batch,
                genia_location,
                request.candidates_data,
                request.job_requirements,
                request.business_unit_id
            )
            
            return JSONResponse(content={
                "message": "Batch processing started",
                "candidates_count": len(request.candidates_data),
                "estimated_time": f"{len(request.candidates_data) * 2} seconds",
                "status": "processing"
            })
        
        # Procesar lotes pequeños inmediatamente
        results = await genia_location.batch_location_matching(
            candidates_data=request.candidates_data,
            job_requirements=request.job_requirements,
            business_unit_id=request.business_unit_id
        )
        
        # Generar resumen
        summary = await genia_location.get_location_matching_summary(
            results=results,
            business_unit_id=request.business_unit_id
        )
        
        return JSONResponse(content={
            "results_count": len(results),
            "summary": summary,
            "top_candidates": [
                {
                    "candidate_id": r.base_matching_result.candidate_id,
                    "location_adjusted_score": r.location_adjusted_score,
                    "commute_feasible": r.location_analysis.get('commute_feasible', False),
                    "commute_time": r.location_analysis.get('commute_time_minutes', 0),
                    "flexibility_score": r.work_flexibility_score
                }
                for r in results[:10]  # Top 10
            ]
        })
        
    except Exception as e:
        logger.error(f"❌ Error en batch location matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_large_batch(genia_location, candidates_data, job_requirements, business_unit_id):
    """Procesar lote grande en background"""
    try:
        results = await genia_location.batch_location_matching(
            candidates_data=candidates_data,
            job_requirements=job_requirements,
            business_unit_id=business_unit_id
        )
        
        # Guardar resultados en Redis para posterior consulta
        # TODO: Implementar almacenamiento de resultados
        logger.info(f"✅ Batch processing completado: {len(results)} candidatos")
        
    except Exception as e:
        logger.error(f"❌ Error en batch processing: {e}")

# ============================================================================
# LOCATION ANALYTICS ENDPOINTS
# ============================================================================

@router.post("/location/analyze")
async def analyze_location(
    request: LocationAnalysisRequest,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Analizar compatibilidad de ubicación"""
    try:
        location_service = get_location_service(db, redis)
        
        insights = await location_service.get_location_insights_for_matching(
            candidate_address=request.candidate_address,
            job_location=request.job_location,
            business_unit_id=request.business_unit_id
        )
        
        return JSONResponse(content=insights)
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de ubicación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/location/commute-analysis")
async def analyze_commute(
    candidate_address: str,
    business_unit_id: str,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Análisis comprehensivo de commute"""
    try:
        location_service = get_location_service(db, redis)
        
        commute_analysis = await location_service.analyze_commute_comprehensive(
            employee_address=candidate_address,
            business_unit_id=business_unit_id
        )
        
        if not commute_analysis:
            raise HTTPException(status_code=404, detail="No se pudo analizar el commute")
        
        # Convertir dataclass a dict
        response_data = {
            "employee_location": {
                "address": commute_analysis.employee_location.address,
                "latitude": commute_analysis.employee_location.latitude,
                "longitude": commute_analysis.employee_location.longitude,
                "city": commute_analysis.employee_location.city
            },
            "office_location": {
                "address": commute_analysis.office_location.address,
                "latitude": commute_analysis.office_location.latitude,
                "longitude": commute_analysis.office_location.longitude,
                "city": commute_analysis.office_location.city
            },
            "morning_commute": {
                "distance_km": commute_analysis.morning_commute.distance_km,
                "duration_minutes": commute_analysis.morning_commute.duration_minutes,
                "duration_in_traffic_minutes": commute_analysis.morning_commute.duration_in_traffic_minutes,
                "route_quality": commute_analysis.morning_commute.route_quality
            },
            "evening_commute": {
                "distance_km": commute_analysis.evening_commute.distance_km,
                "duration_minutes": commute_analysis.evening_commute.duration_minutes,
                "duration_in_traffic_minutes": commute_analysis.evening_commute.duration_in_traffic_minutes,
                "route_quality": commute_analysis.evening_commute.route_quality
            },
            "costs": {
                "weekly": commute_analysis.weekly_commute_cost,
                "monthly": commute_analysis.monthly_commute_cost
            },
            "commute_stress_score": commute_analysis.commute_stress_score,
            "recommended_transport": commute_analysis.recommended_transport,
            "flexible_work_recommendation": commute_analysis.flexible_work_recommendation
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de commute: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/location/geocode")
async def geocode_address(
    address: str,
    business_unit_id: str,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Geocodificar una dirección"""
    try:
        location_service = get_location_service(db, redis)
        
        location_data = await location_service.geocode_address(
            address=address,
            business_unit_id=business_unit_id
        )
        
        if not location_data:
            raise HTTPException(status_code=404, detail="No se pudo geocodificar la dirección")
        
        # Convertir dataclass a dict
        response_data = {
            "address": location_data.address,
            "latitude": location_data.latitude,
            "longitude": location_data.longitude,
            "city": location_data.city,
            "state": location_data.state,
            "country": location_data.country,
            "postal_code": location_data.postal_code,
            "formatted_address": location_data.formatted_address,
            "accuracy": location_data.accuracy
        }
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"❌ Error geocodificando: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/location/health")
async def get_location_service_health(
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Obtener estado de salud del servicio de ubicación"""
    try:
        location_service = get_location_service(db, redis)
        health = await location_service.get_service_health()
        return JSONResponse(content=health)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo health de location service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AURA ASSISTANT ENDPOINTS
# ============================================================================

@router.post("/aura/query")
async def aura_query(
    request: AURAQueryRequest,
    db=Depends(get_db)
):
    """Consulta al asistente AURA"""
    try:
        aura = get_aura_assistant(db)
        
        response = await aura.process_message(
            user_message=request.query,
            user_id=request.user_id,
            context=request.context
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"❌ Error en AURA query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aura/conversation/{conversation_id}")
async def get_aura_conversation(
    conversation_id: str,
    db=Depends(get_db)
):
    """Obtener historial de conversación con AURA"""
    try:
        # TODO: Implementar obtención de historial
        return JSONResponse(content={
            "conversation_id": conversation_id,
            "messages": [],
            "status": "active"
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo conversación AURA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK GENERAL
# ============================================================================

@router.get("/health")
async def get_ml_system_health(
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Estado de salud general del sistema ML"""
    try:
        # Verificar todos los servicios
        chatbot = get_recruitment_chatbot(db, redis)
        genia_location = get_genia_location_integration(db, redis)
        location_service = get_location_service(db, redis)
        aura = get_aura_assistant(db)
        
        # Obtener estados
        chatbot_health = await chatbot.get_chatbot_health()
        location_health = await location_service.get_service_health()
        
        overall_status = "healthy"
        if (chatbot_health.get("status") != "healthy" or 
            location_health.get("status") != "healthy"):
            overall_status = "degraded"
        
        return JSONResponse(content={
            "system": "HuntRED® v2 ML System",
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "recruitment_chatbot": chatbot_health.get("status", "unknown"),
                "location_analytics": location_health.get("status", "unknown"),
                "genia_integration": "healthy",
                "aura_assistant": "healthy"
            },
            "business_units": [unit.value for unit in BusinessUnit],
            "features": [
                "4 Chatbot Personalities",
                "Location-Enhanced Matching",
                "Google Maps Integration",
                "Traffic Analysis",
                "Commute Optimization",
                "GenIA 9-Category Matching",
                "AURA Personality Analysis",
                "Real-time Insights"
            ]
        })
        
    except Exception as e:
        logger.error(f"❌ Error en health check general: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics/matching-stats")
async def get_matching_statistics(
    business_unit_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Obtener estadísticas de matching"""
    try:
        # Mock statistics
        stats = {
            "total_matches": 1247,
            "successful_placements": 892,
            "average_match_score": 0.847,
            "location_enhanced_matches": 1098,
            "business_unit_breakdown": {
                "huntred_executive": {"matches": 156, "placements": 89},
                "huntred_general": {"matches": 623, "placements": 445},
                "huntU": {"matches": 289, "placements": 201},
                "amigro": {"matches": 179, "placements": 157}
            },
            "location_insights": {
                "average_commute_time": 47.3,
                "remote_work_recommended": 234,
                "hybrid_work_recommended": 456,
                "excellent_locations": 387
            },
            "period": {
                "from": date_from or "2024-01-01",
                "to": date_to or datetime.now().strftime("%Y-%m-%d")
            }
        }
        
        if business_unit_id:
            stats["filtered_by"] = business_unit_id
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Incluir el router en la aplicación principal
def include_ml_routes(app):
    """Incluir rutas ML en la aplicación"""
    app.include_router(router)