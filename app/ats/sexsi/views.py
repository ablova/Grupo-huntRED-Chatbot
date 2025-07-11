# app/ats/sexsi/views.py
"""
Vistas del módulo SEXSI (Sistema de Experiencia y Satisfacción del Usuario).
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@login_required
def sexsi_dashboard(request):
    """
    Dashboard principal del sistema SEXSI.
    """
    try:
        context = {
            'title': 'SEXSI Dashboard',
            'module': 'sexsi',
            'page': 'dashboard'
        }
        return render(request, 'ats/sexsi/dashboard.html', context)
    except Exception as e:
        logger.error(f"Error en sexsi_dashboard: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def sexsi_analytics(request):
    """
    Vista de analytics del sistema SEXSI.
    """
    try:
        context = {
            'title': 'SEXSI Analytics',
            'module': 'sexsi',
            'page': 'analytics'
        }
        return render(request, 'ats/sexsi/analytics.html', context)
    except Exception as e:
        logger.error(f"Error en sexsi_analytics: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def sexsi_reports(request):
    """
    Vista de reportes del sistema SEXSI.
    """
    try:
        context = {
            'title': 'SEXSI Reports',
            'module': 'sexsi',
            'page': 'reports'
        }
        return render(request, 'ats/sexsi/reports.html', context)
    except Exception as e:
        logger.error(f"Error en sexsi_reports: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def sexsi_settings(request):
    """
    Vista de configuración del sistema SEXSI.
    """
    try:
        context = {
            'title': 'SEXSI Settings',
            'module': 'sexsi',
            'page': 'settings'
        }
        return render(request, 'ats/sexsi/settings.html', context)
    except Exception as e:
        logger.error(f"Error en sexsi_settings: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def sexsi_api_data(request):
    """
    API para obtener datos del sistema SEXSI.
    """
    try:
        # Simulación de datos SEXSI
        data = {
            'satisfaction_score': 8.5,
            'response_time': 2.3,
            'user_engagement': 0.75,
            'support_tickets': 12,
            'resolution_rate': 0.92,
            'user_feedback': {
                'positive': 85,
                'neutral': 10,
                'negative': 5
            }
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error en sexsi_api_data: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def sexsi_feedback(request):
    """
    API para recibir feedback del usuario.
    """
    try:
        # Procesar feedback del usuario
        feedback_data = request.POST.dict()
        
        # Aquí se procesaría el feedback
        logger.info(f"Feedback recibido: {feedback_data}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Feedback recibido correctamente'
        })
    except Exception as e:
        logger.error(f"Error en sexsi_feedback: {e}")
        return JsonResponse({'error': str(e)}, status=500) 