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

# Archivo simplificado para modularidad de rutas en el proyecto Django

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from app.views.dashboard_views import dashboard_view
from app.views.candidatos_views import (
    list_candidatos,
    candidato_dashboard,
    evaluate_candidate,
    send_notification,
)

def health_check(request):
    return HttpResponse("OK")

def trigger_error(request):
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

    # APIs principales
    #path('api/chatbot/', include('chatbot.urls')),  # API del chatbot
    #path('api/users/', include('users.urls')),      # API de usuarios
    #path('api/tasks/', include('tasks.urls')),      # API de tareas

    # Health Check
    path('health/', health_check, name='health_check'),
    path('sentry-debug/', trigger_error),

    # Rutas para el flujo de trabajo
    path('business-unit/', include('app.urls.workflow_urls')),

    # Nuevas rutas
    path('dashboard/', dashboard_view, name='dashboard'),
    path('candidatos/', list_candidatos, name='list_candidatos'),
    path('candidatos/dashboard/', candidato_dashboard, name='candidate_dashboard'),
    path('candidatos/<int:candidate_id>/evaluate/', evaluate_candidate, name='evaluate_candidate'),
    path('send-notification/', send_notification, name='send_notification'),

    # Incluir las rutas de 'app.urls.py' bajo el prefijo 'webhook/'
    path('webhook/', include('app.urls.webhook_urls')),  # Incluye solo las rutas de 'webhook_urls.py'
]

urlpatterns += staticfiles_urlpatterns()