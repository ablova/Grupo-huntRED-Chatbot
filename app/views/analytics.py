"""
Vistas para Analytics Avanzados y Matching Automático.
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def advanced_analytics_dashboard(request):
    """Dashboard principal de analytics avanzados."""
    return render(request, 'analytics/advanced_dashboard.html', {
        'title': 'Analytics Avanzados'
    })


@login_required
def matching_analytics(request):
    """Analytics de matching de candidatos."""
    return render(request, 'analytics/matching_analytics.html', {
        'title': 'Matching Analytics'
    })


@login_required
def performance_metrics(request):
    """Métricas de rendimiento del sistema."""
    return render(request, 'analytics/performance_metrics.html', {
        'title': 'Métricas de Rendimiento'
    })


@login_required
def predictive_insights(request):
    """Insights predictivos."""
    return render(request, 'analytics/predictive_insights.html', {
        'title': 'Insights Predictivos'
    })


@login_required
def automated_matching(request):
    """Sistema de matching automático."""
    return render(request, 'analytics/automated_matching.html', {
        'title': 'Matching Automático'
    })


@login_required
def analytics_api(request):
    """API para analytics."""
    return JsonResponse({
        'status': 'success',
        'message': 'Analytics API funcionando'
    }) 