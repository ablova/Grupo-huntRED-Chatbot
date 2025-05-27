# /home/pablo/ai_huntred/urls.py
"""ai_huntred URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""
# Descripción: Configuración principal de rutas para el proyecto Django

import logging
from datetime import datetime
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from ai_huntred.settings import METRICS_ENDPOINT, ENABLE_METRICS

logger = logging.getLogger(__name__)

APPEND_SLASH = False

# ---------------------------------
# 📌 FUNCIONES DE SALUD Y DEBUGGING
# ---------------------------------
def health_check(request):
    """Verifica si el servidor está activo."""
    logger.info("Health check requested")
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': 'development'
    })

@csrf_exempt
def metrics(request):
    """Endpoint para métricas de Prometheus."""
    if not ENABLE_METRICS:
        return HttpResponse("Metrics disabled", status=403)
    
    # Aquí iría la lógica para recopilar métricas
    metrics_data = ""  # Se reemplazaría con las métricas reales
    return HttpResponse(metrics_data, content_type='text/plain')

@csrf_exempt
def trigger_error(request):
    """Simula un error para pruebas con Sentry u otros sistemas de monitoreo."""
    logger.warning("Triggering error for debugging")
    try:
        division_by_zero = 1 / 0
    except ZeroDivisionError:
        return JsonResponse({
            'error': 'Division by zero',
            'timestamp': datetime.now().isoformat()
        }, status=500)

#schema_view = get_swagger_view(title='ai_huntred API')

urlpatterns = [
    # Interfaz de administración de Django
    path('admin/', admin.site.urls),
    # Redirección de raíz al admin
    path('', RedirectView.as_view(url='/admin/', permanent=True)),
    # Salud
    path('health/', health_check),
    # Rutas de la aplicación principal
    path('', include('app.urls')),
]

# Soporte condicional para Grappelli
try:
    urlpatterns.append(path('grappelli/', include('grappelli.urls')))
except ImportError:
    pass  # Grappelli no está instalado

# Archivos estáticos en modo DEBUG
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
