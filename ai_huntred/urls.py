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
from django.urls import path, include, re_path
from django.http import HttpResponse, JsonResponse
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from ai_huntred.config.development import METRICS_ENDPOINT, ENABLE_METRICS
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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
        'environment': settings.ENVIRONMENT,
        'services': {
            'database': check_database(),
            'redis': check_redis(),
            'celery': check_celery()
        }
    })

def check_database():
    """Verifica la conexión a la base de datos."""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False

def check_redis():
    """Verifica la conexión a Redis."""
    try:
        import redis
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        return r.ping()
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        return False

def check_celery():
    """Verifica el estado de Celery."""
    try:
        from ai_huntred.celery_app import app
        return app.control.inspect().active() is not None
    except Exception as e:
        logger.error(f"Celery check failed: {e}")
        return False

@csrf_exempt
def metrics(request):
    """Endpoint para métricas de Prometheus."""
    if not ENABLE_METRICS:
        return HttpResponse("Metrics disabled", status=403)
    
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return HttpResponse("Error generating metrics", status=500)

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

# Configuración de Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="AI HuntRED API",
        default_version='v1',
        description="API documentation for AI HuntRED",
        terms_of_service="https://www.huntred.com/terms/",
        contact=openapi.Contact(email="hola@huntred.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Interfaz de administración de Django
    path('admin/', admin.site.urls),
    # Redirección de raíz al admin
    path('', RedirectView.as_view(url='/admin/', permanent=True)),
    # Salud
    path('health/', health_check),
    # Métricas
    path('metrics/', metrics),
    # Debug
    path('debug/error/', trigger_error),
    # Documentación API
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # Rutas de autenticación
    path('api/auth/', include('authentication.urls')),
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
