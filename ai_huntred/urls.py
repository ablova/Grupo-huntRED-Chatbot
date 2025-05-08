"""ai_huntred URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""
# Descripción: Configuración principal de rutas para el proyecto Django

import logging
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
        'environment': settings.ENVIRONMENT
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

schema_view = get_swagger_view(title='ai_huntred API')

urlpatterns = [
    # Redirige /admin a /admin/ para consistencia
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    # Interfaz de administración de Django
    path('admin/', admin.site.urls),
    # API REST
    path('api/', include('app.api.urls')),
    # API de publicación
    path('api/publish/', include('app.publish.urls')),
    # Swagger UI
    path('swagger/', schema_view, name='schema-swagger-ui'),
    # Redirección de raíz a Swagger
    path('', RedirectView.as_view(url='/swagger/', permanent=True)),
    # Páginas de error
    path('500/', trigger_error),
    # Métricas
    path(METRICS_ENDPOINT, metrics),
    # Salud
    path('health/', health_check),
    # Rutas de la aplicación principal
    path('', include('app.urls')),
    path('silk/', include('silk.urls', namespace='silk')),
    # Rutas de publicación
    path('publicacion/', include('app.publicacion.urls')),
    # Rutas de pagos
    path('pagos/', include('app.pagos.urls', namespace='pagos')),
]

# Soporte condicional para Grappelli
try:
    urlpatterns.append(path('grappelli/', include('grappelli.urls')))
except ImportError:
    pass  # Grappelli no está instalado

# Archivos estáticos solo en modo DEBUG
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
