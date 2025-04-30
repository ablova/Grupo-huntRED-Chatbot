"""ai_huntred URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
"""
# Descripción: Configuración principal de rutas para el proyecto Django

import logging
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

logger = logging.getLogger(__name__)

APPEND_SLASH = False

# ---------------------------------
# 📌 FUNCIONES DE SALUD Y DEBUGGING
# ---------------------------------
def health_check(request):
    """Verifica si el servidor está activo."""
    logger.info("Health check requested")
    return HttpResponse("OK")

def trigger_error(request):
    """Simula un error para pruebas con Sentry u otros sistemas de monitoreo."""
    logger.warning("Triggering error for debugging")
    try:
        division_by_zero = 1 / 0
    except ZeroDivisionError:
        return HttpResponse("Error triggered for debugging", status=500)

urlpatterns = [
    # Redirige /admin a /admin/ para consistencia
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    # Interfaz de administración de Django
    path('admin/', admin.site.urls),
    # Health check del servidor
    path('health/', health_check, name='health_check'),
    # Endpoint para pruebas de errores
    path('sentry-debug/', trigger_error, name='sentry_debug'),
    # Rutas de la aplicación principal
    path('', include('app.urls')),
    path('silk/', include('silk.urls', namespace='silk')),
]

# Soporte condicional para Grappelli
try:
    urlpatterns.append(path('grappelli/', include('grappelli.urls')))
except ImportError:
    pass  # Grappelli no está instalado

# Archivos estáticos solo en modo DEBUG
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)