"""
AURA API Views
Vistas API para el sistema AURA.
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from app.ml.aura.orchestrator import aura_orchestrator
from app.ml.aura.orchestrator import AnalysisType

logger = logging.getLogger(__name__)

@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
async def aura_analyze_comprehensive(request):
    """
    API para análisis comprehensivo de AURA.
    """
    try:
        data = json.loads(request.body)
        person_data = data.get('person_data', {})
        business_context = data.get('business_context')
        analysis_depth = data.get('analysis_depth', 'standard')
        priority = data.get('priority', 5)
        
        # Validar datos de entrada
        if not person_data:
            return JsonResponse({
                'success': False,
                'error': 'Datos de persona requeridos'
            }, status=400)
        
        # Ejecutar análisis comprehensivo
        result = await aura_orchestrator.analyze_comprehensive(
            person_data=person_data,
            business_context=business_context,
            analysis_depth=analysis_depth,
            priority=priority
        )
        
        # Preparar respuesta
        response_data = {
            'analysis_id': result.analysis_id,
            'timestamp': result.timestamp.isoformat(),
            'analysis_type': result.analysis_type.value,
            'overall_score': result.results.get('overall_score', 0.0),
            'confidence': result.confidence,
            'execution_time': result.execution_time,
            'modules_used': result.modules_used,
            'recommendations': result.recommendations,
            'resource_usage': result.resource_usage
        }
        
        logger.info(f"Análisis comprehensivo completado: {result.analysis_id}")
        
        return JsonResponse({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error en análisis comprehensivo: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
async def aura_analyze_specific(request):
    """
    API para análisis específico de AURA.
    """
    try:
        data = json.loads(request.body)
        analysis_type = data.get('analysis_type')
        person_data = data.get('person_data', {})
        business_context = data.get('business_context')
        priority = data.get('priority', 5)
        
        # Validar tipo de análisis
        valid_types = [t.value for t in AnalysisType]
        if analysis_type not in valid_types:
            return JsonResponse({
                'success': False,
                'error': f'Tipo de análisis no válido. Tipos válidos: {valid_types}'
            }, status=400)
        
        # Convertir a enum
        analysis_type_enum = AnalysisType(analysis_type)
        
        # Ejecutar análisis específico
        result = await aura_orchestrator.analyze_specific(
            analysis_type=analysis_type_enum,
            person_data=person_data,
            business_context=business_context,
            priority=priority
        )
        
        # Preparar respuesta
        response_data = {
            'analysis_id': result.analysis_id,
            'timestamp': result.timestamp.isoformat(),
            'analysis_type': result.analysis_type.value,
            'overall_score': result.results.get('overall_score', 0.0),
            'confidence': result.confidence,
            'execution_time': result.execution_time,
            'modules_used': result.modules_used,
            'recommendations': result.recommendations,
            'resource_usage': result.resource_usage
        }
        
        logger.info(f"Análisis específico completado: {result.analysis_id}")
        
        return JsonResponse({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error en análisis específico: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["GET"])
def aura_system_status(request):
    """
    API para obtener estado del sistema AURA.
    """
    try:
        status = aura_orchestrator.get_system_status()
        
        return JsonResponse({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["GET"])
def aura_performance_metrics(request):
    """
    API para obtener métricas de rendimiento de AURA.
    """
    try:
        metrics = aura_orchestrator.performance_metrics
        
        # Calcular métricas agregadas
        total_analyses = len(metrics)
        avg_execution_time = sum(m['execution_time'] for m in metrics.values()) / total_analyses if total_analyses > 0 else 0
        avg_confidence = sum(m['confidence'] for m in metrics.values()) / total_analyses if total_analyses > 0 else 0
        
        response_data = {
            'total_analyses': total_analyses,
            'avg_execution_time': avg_execution_time,
            'avg_confidence': avg_confidence,
            'recent_analyses': list(metrics.values())[-10:]  # Últimos 10 análisis
        }
        
        return JsonResponse({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["GET"])
def aura_audit_trail(request):
    """
    API para obtener auditoría de AURA.
    """
    try:
        audit_trail = aura_orchestrator.audit_trail
        
        # Filtrar por fecha si se especifica
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            audit_trail = [entry for entry in audit_trail if entry['timestamp'] >= start_date]
        
        if end_date:
            audit_trail = [entry for entry in audit_trail if entry['timestamp'] <= end_date]
        
        # Limitar resultados
        limit = int(request.GET.get('limit', 100))
        audit_trail = audit_trail[-limit:]
        
        return JsonResponse({
            'success': True,
            'data': {
                'audit_trail': audit_trail,
                'total_entries': len(audit_trail)
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo auditoría: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
async def aura_test_analysis(request):
    """
    API para probar análisis con datos de ejemplo.
    """
    try:
        # Datos de ejemplo para prueba
        test_person_data = {
            'id': 'test_001',
            'name': 'Juan Pérez',
            'email': 'juan.perez@example.com',
            'experience': [
                {
                    'title': 'Senior Software Engineer',
                    'company': 'Tech Corp',
                    'start_date': '2020-01-01',
                    'end_date': '2023-12-31',
                    'description': 'Desarrollo de aplicaciones web y móviles'
                }
            ],
            'education': [
                {
                    'degree': 'Ingeniero en Sistemas',
                    'institution': 'Universidad Nacional',
                    'field': 'Computer Science',
                    'graduation_date': '2019-06-01'
                }
            ],
            'certifications': [
                {
                    'name': 'AWS Certified Developer',
                    'issuer': 'Amazon Web Services',
                    'date': '2022-03-15'
                }
            ],
            'linkedin': {
                'username': 'juanperez',
                'name': 'Juan Pérez',
                'experience': [
                    {
                        'title': 'Senior Software Engineer',
                        'company': 'Tech Corp'
                    }
                ]
            }
        }
        
        # Ejecutar análisis de prueba
        result = await aura_orchestrator.analyze_comprehensive(
            person_data=test_person_data,
            analysis_depth='standard',
            priority=5
        )
        
        response_data = {
            'analysis_id': result.analysis_id,
            'timestamp': result.timestamp.isoformat(),
            'analysis_type': result.analysis_type.value,
            'overall_score': result.results.get('overall_score', 0.0),
            'confidence': result.confidence,
            'execution_time': result.execution_time,
            'modules_used': result.modules_used,
            'recommendations': result.recommendations
        }
        
        logger.info(f"Análisis de prueba completado: {result.analysis_id}")
        
        return JsonResponse({
            'success': True,
            'data': response_data,
            'message': 'Análisis de prueba ejecutado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error en análisis de prueba: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
