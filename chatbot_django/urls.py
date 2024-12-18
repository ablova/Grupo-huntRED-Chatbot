# Ubicación del archivo: /home/pablollh/chatbot_django/urls.py
"""chatbot_django URL Configuration

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

def health_check(request):
    return HttpResponse("OK")

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
]
urlpatterns += staticfiles_urlpatterns()