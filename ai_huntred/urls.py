# Ubicación del archivo: /home/pablollh/ai_huntred/urls.py
"""ai_huntred URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# Descripción: Configuración principal de rutas para el proyecto Django

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# ---------------------------------
# 📌 FUNCIONES DE SALUD Y DEBUGGING
# ---------------------------------
def health_check(request):
    """Verifica si el servidor está activo."""
    return HttpResponse("OK")

def trigger_error(request):
    """Simula un error para pruebas con Sentry u otros sistemas de monitoreo."""
    division_by_zero = 1 / 0

class WorkflowStageListView(ListView):
    pass

class WorkflowStageCreateView(CreateView):
    pass

class WorkflowStageUpdateView(UpdateView):
    pass

class WorkflowStageDeleteView(DeleteView):
    pass

urlpatterns = [
    # Administración
    path('admin/', admin.site.urls),

    # Grappelli (si está habilitado)
    path('grappelli/', include('grappelli.urls')),

    # Health Check y Debugging
    path('health/', health_check, name='health_check'),
    path('sentry-debug/', trigger_error),

    # Rutas de la aplicación principal (contiene chatbot, candidatos, workflows, sexsi, webhooks, etc.)
    path('', include('app.urls')),  
]

urlpatterns += staticfiles_urlpatterns()