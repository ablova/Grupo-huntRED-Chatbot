"""
AURA Dashboard Views
Vistas para el dashboard de AURA.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from app.ml.aura.orchestrator import aura_orchestrator
from app.ml.aura.core.ethics_engine import ServiceTier

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class AURADashboardView(View):
    """
    Vista principal del dashboard de AURA.
    """
    
    def get(self, request):
        """Renderiza el dashboard principal de AURA"""
        try:
            # Obtener estado del sistema
            system_status = aura_orchestrator.get_system_status()
            
            # Simular datos para el dashboard
            dashboard_data = self._get_dashboard_data()
            
            context = {
                'service_tier': system_status['service_tier'],
                'total_analyses': dashboard_data['total_analyses'],
                'avg_ethical_score': dashboard_data['avg_ethical_score'],
                'active_modules': len(system_status['available_modules']),
                'avg_execution_time': dashboard_data['avg_execution_time'],
                
                # Scores de módulos
                'ethics_engine_score': dashboard_data['module_scores']['ethics_engine'],
                'ethics_engine_analyses': dashboard_data['module_analyses']['ethics_engine'],
                'truth_sense_score': dashboard_data['module_scores']['truth_sense'],
                'truth_sense_analyses': dashboard_data['module_analyses']['truth_sense'],
                'social_verify_score': dashboard_data['module_scores']['social_verify'],
                'social_verify_analyses': dashboard_data['module_analyses']['social_verify'],
                'bias_detection_score': dashboard_data['module_scores']['bias_detection'],
                'bias_detection_analyses': dashboard_data['module_analyses']['bias_detection'],
                'fairness_optimizer_score': dashboard_data['module_scores']['fairness_optimizer'],
                'fairness_optimizer_analyses': dashboard_data['module_analyses']['fairness_optimizer'],
                'impact_analyzer_score': dashboard_data['module_scores']['impact_analyzer'],
                'impact_analyzer_analyses': dashboard_data['module_analyses']['impact_analyzer'],
                
                # Análisis recientes
                'recent_analyses': dashboard_data['recent_analyses'],
                
                # Configuración
                'max_concurrent_analyses': system_status.get('max_concurrent_analyses', 10),
                'cache_ttl': 3600,
                'enable_monitoring': True,
            }
            
            return render(request, 'aura/ethical_dashboard.html', context)
            
        except Exception as e:
            logger.error(f"Error en dashboard de AURA: {str(e)}")
            return render(request, 'aura/error.html', {
                'error_message': 'Error cargando el dashboard de AURA'
            })
    
    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Obtiene datos simulados para el dashboard"""
        import random
        
        return {
            'total_analyses': random.randint(150, 500),
            'avg_ethical_score': random.uniform(75, 92),
            'avg_execution_time': random.uniform(2.5, 8.0),
            
            'module_scores': {
                'ethics_engine': random.uniform(80, 95),
                'truth_sense': random.uniform(75, 90),
                'social_verify': random.uniform(70, 85),
                'bias_detection': random.uniform(85, 98),
                'fairness_optimizer': random.uniform(80, 92),
                'impact_analyzer': random.uniform(75, 88)
            },
            
            'module_analyses': {
                'ethics_engine': random.randint(50, 150),
                'truth_sense': random.randint(80, 200),
                'social_verify': random.randint(60, 120),
                'bias_detection': random.randint(40, 100),
                'fairness_optimizer': random.randint(30, 80),
                'impact_analyzer': random.randint(45, 90)
            },
            
            'recent_analyses': [
                {
                    'analysis_id': f'aura_{random.randint(1000, 9999)}',
                    'analysis_type': 'Comprehensive',
                    'overall_score': random.uniform(70, 95),
                    'confidence': random.uniform(75, 90),
                    'modules_used': ['ethics_engine', 'truth_sense', 'social_verify'],
                    'execution_time': random.uniform(3.0, 12.0),
                    'timestamp': datetime.now() - timedelta(hours=random.randint(1, 24))
                }
                for _ in range(10)
            ]
        }

@login_required
@staff_member_required
@require_http_methods(["GET"])
def aura_dashboard_data(request):
    """API para obtener datos del dashboard"""
    try:
        # Obtener estado del sistema
        system_status = aura_orchestrator.get_system_status()
        
        # Simular datos actualizados
        dashboard_data = AURADashboardView()._get_dashboard_data()
        
        return JsonResponse({
            'success': True,
            'data': {
                'system_status': system_status,
                'dashboard_data': dashboard_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo datos del dashboard: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def aura_update_tier(request):
    """API para actualizar tier de servicio"""
    try:
        data = json.loads(request.body)
        new_tier = data.get('tier', 'basic')
        
        # Validar tier
        valid_tiers = ['basic', 'pro', 'enterprise']
        if new_tier not in valid_tiers:
            return JsonResponse({
                'success': False,
                'error': 'Tier no válido'
            }, status=400)
        
        # Actualizar tier
        service_tier = ServiceTier(new_tier)
        aura_orchestrator.upgrade_service_tier(service_tier)
        
        logger.info(f"Tier de AURA actualizado a: {new_tier}")
        
        return JsonResponse({
            'success': True,
            'message': f'Tier actualizado a {new_tier}'
        })
        
    except Exception as e:
        logger.error(f"Error actualizando tier: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def aura_save_config(request):
    """API para guardar configuración"""
    try:
        data = json.loads(request.body)
        
        # Validar datos
        max_concurrent = int(data.get('max_concurrent_analyses', 10))
        cache_ttl = int(data.get('cache_ttl', 3600))
        enable_monitoring = bool(data.get('enable_monitoring', True))
        
        # Aquí se guardaría la configuración en la base de datos
        # Por ahora solo simulamos el guardado
        
        logger.info(f"Configuración de AURA guardada: {data}")
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración guardada exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error guardando configuración: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def aura_reset_config(request):
    """API para restablecer configuración"""
    try:
        # Restablecer configuración por defecto
        aura_orchestrator.config = aura_orchestrator.config.__class__()
        
        logger.info("Configuración de AURA restablecida")
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración restablecida exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error restableciendo configuración: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@staff_member_required
@require_http_methods(["GET"])
def aura_analysis_details(request, analysis_id):
    """API para obtener detalles de un análisis"""
    try:
        # Simular datos de análisis
        analysis_data = {
            'analysis_id': analysis_id,
            'analysis_type': 'Comprehensive',
            'timestamp': datetime.now().isoformat(),
            'overall_score': 85.5,
            'confidence': 87.2,
            'modules_used': ['ethics_engine', 'truth_sense', 'social_verify'],
            'execution_time': 6.8,
            'recommendations': [
                'Verificar experiencia laboral',
                'Validar credenciales educativas',
                'Analizar presencia social'
            ],
            'results': {
                'ethics_engine': {
                    'overall_ethical_score': 87.3,
                    'confidence_level': 0.89
                },
                'truth_sense': {
                    'overall_veracity_score': 82.1,
                    'veracity_level': 'high'
                },
                'social_verify': {
                    'overall_authenticity_score': 78.9,
                    'authenticity_level': 'likely_authentic'
                }
            }
        }
        
        return JsonResponse({
            'success': True,
            'data': analysis_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo detalles de análisis: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
