"""
Vistas para el dashboard global del sistema huntRED®
"""
import logging
from typing import Dict, Any
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from app.ats.core.global_orchestrator import global_orchestrator
from app.ats.core.demand_driven_updater import demand_driven_updater

logger = logging.getLogger(__name__)

@login_required
def global_system_dashboard(request):
    """
    Vista del dashboard global del sistema
    """
    return render(request, 'admin/global_system_dashboard.html')

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_global_system_status(request):
    """
    Obtiene el estado completo del sistema global
    """
    try:
        # Obtener estado del orquestador global
        system_status = await global_orchestrator.get_global_system_status()
        
        # Obtener estado del sistema de actualizaciones
        update_status = await demand_driven_updater.get_update_status()
        
        # Combinar estados
        combined_status = {
            **system_status,
            'update_system': update_status
        }
        
        return JsonResponse({
            'success': True,
            'data': combined_status,
            'message': 'Estado del sistema obtenido exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error obteniendo estado del sistema'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def request_system_update(request):
    """
    Solicita una actualización del sistema bajo demanda
    """
    try:
        data = json.loads(request.body)
        
        module_type = data.get('module_type')
        update_type = data.get('update_type')
        trigger = data.get('trigger', 'user_request')
        priority = data.get('priority', 'normal')
        update_data = data.get('data', {})
        
        # Validar datos requeridos
        if not module_type or not update_type:
            return JsonResponse({
                'success': False,
                'error': 'module_type y update_type son requeridos',
                'message': 'Datos incompletos'
            }, status=400)
        
        # Solicitar actualización
        success = await demand_driven_updater.request_update(
            module_type=module_type,
            update_type=update_type,
            trigger=trigger,
            data=update_data,
            priority=priority
        )
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Actualización solicitada exitosamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo programar la actualización',
                'message': 'Actualización no programada'
            }, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido',
            'message': 'Formato de datos incorrecto'
        }, status=400)
    except Exception as e:
        logger.error(f"Error solicitando actualización: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error interno del servidor'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def optimize_system_performance(request):
    """
    Ejecuta optimización manual del rendimiento del sistema
    """
    try:
        await global_orchestrator.optimize_global_performance()
        
        return JsonResponse({
            'success': True,
            'message': 'Optimización del sistema ejecutada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error optimizando sistema: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error optimizando sistema'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_module_details(request, module_type: str):
    """
    Obtiene detalles específicos de un módulo
    """
    try:
        # Obtener detalles del módulo desde el orquestador
        module_status = global_orchestrator.modules.get(module_type)
        
        if not module_status:
            return JsonResponse({
                'success': False,
                'error': f'Módulo {module_type} no encontrado',
                'message': 'Módulo no existe'
            }, status=404)
        
        # Obtener métricas específicas del módulo
        module_metrics = {
            'module_type': module_status.module_type.value,
            'enabled': module_status.enabled,
            'active_operations': module_status.active_operations,
            'error_count': module_status.error_count,
            'success_rate': module_status.success_rate,
            'avg_response_time': module_status.avg_response_time,
            'last_activity': module_status.last_activity.isoformat() if module_status.last_activity else None,
            'resource_usage': module_status.resource_usage
        }
        
        return JsonResponse({
            'success': True,
            'data': module_metrics,
            'message': f'Detalles del módulo {module_type} obtenidos'
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo detalles del módulo {module_type}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error obteniendo detalles del módulo'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_rate_limit_status(request):
    """
    Obtiene el estado detallado de los límites de tasa
    """
    try:
        rate_limits = global_orchestrator.global_rate_limits
        
        # Calcular porcentajes de uso
        rate_limit_status = {}
        for limit_type, limit_info in rate_limits.items():
            percentage = (limit_info['current'] / limit_info['limit']) * 100
            status = 'safe' if percentage < 70 else 'warning' if percentage < 90 else 'danger'
            
            rate_limit_status[limit_type] = {
                'current': limit_info['current'],
                'limit': limit_info['limit'],
                'window': limit_info['window'],
                'percentage': percentage,
                'status': status,
                'reset_time': limit_info['reset_time']
            }
        
        return JsonResponse({
            'success': True,
            'data': rate_limit_status,
            'message': 'Estado de límites de tasa obtenido'
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de rate limits: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error obteniendo estado de rate limits'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_update_history(request):
    """
    Obtiene el historial de actualizaciones
    """
    try:
        update_status = await demand_driven_updater.get_update_status()
        
        return JsonResponse({
            'success': True,
            'data': update_status,
            'message': 'Historial de actualizaciones obtenido'
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo historial de actualizaciones: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error obteniendo historial de actualizaciones'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def execute_ml_operation(request):
    """
    Ejecuta una operación ML coordinada
    """
    try:
        data = json.loads(request.body)
        
        operation_type = data.get('operation_type')
        operation_data = data.get('data', {})
        
        if not operation_type:
            return JsonResponse({
                'success': False,
                'error': 'operation_type es requerido',
                'message': 'Tipo de operación no especificado'
            }, status=400)
        
        # Ejecutar operación ML
        result = await global_orchestrator.coordinate_ml_operation(
            operation_type=operation_type,
            data=operation_data
        )
        
        return JsonResponse({
            'success': True,
            'data': result,
            'message': 'Operación ML ejecutada'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido',
            'message': 'Formato de datos incorrecto'
        }, status=400)
    except Exception as e:
        logger.error(f"Error ejecutando operación ML: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error ejecutando operación ML'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_system_health(request):
    """
    Obtiene el estado de salud del sistema
    """
    try:
        # Obtener carga del sistema
        system_load = await global_orchestrator.get_system_load()
        
        # Obtener métricas del sistema
        system_metrics = global_orchestrator.system_metrics
        
        # Calcular salud general
        health_score = 100
        health_status = 'healthy'
        
        if system_load.value == 'critical':
            health_score = 25
            health_status = 'critical'
        elif system_load.value == 'high':
            health_score = 50
            health_status = 'warning'
        elif system_load.value == 'medium':
            health_score = 75
            health_status = 'stable'
        
        health_data = {
            'health_score': health_score,
            'health_status': health_status,
            'system_load': system_load.value,
            'metrics': system_metrics,
            'active_operations': len(global_orchestrator.active_operations),
            'queue_length': len(global_orchestrator.operation_queue),
            'ml_available': global_orchestrator.AURA_AVAILABLE
        }
        
        return JsonResponse({
            'success': True,
            'data': health_data,
            'message': 'Estado de salud del sistema obtenido'
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo salud del sistema: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Error obteniendo salud del sistema'
        }, status=500) 