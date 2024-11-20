# /home/amigro/chatbot_django/urls.py
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
#from app.admin import admin_site
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import HttpResponse
#from app.urls import admin_patterns

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('', include('app.urls')),
    path('admin/', admin.site.urls),
   # path('admin/', admin_site.urls, name='grupo_huntred_admin'),
    path('grappelli/', include('grappelli.urls')),  # Si utilizas Grappelli
    # Asegúrate de que esta sea la única inclusión de admin_patterns
    #path('admin/app/', include(admin_patterns)),
    # Incluye las URLs regulares de la app, pero no las admin_patterns
    path('health/', health_check, name='health_check'),
]
urlpatterns += staticfiles_urlpatterns()