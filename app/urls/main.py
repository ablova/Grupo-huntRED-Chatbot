"""
URLs principales del sistema.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django
    path('admin/', admin.site.urls),
    
    # URLs de la aplicación principal
    path('', include('app.urls.main')),
    
    # URLs de ATS
    path('ats/', include('app.ats.urls')),
    
    # URLs de dashboards
    path('dashboard/', include('app.urls.dashboards')),
    
    # URLs de analytics avanzados
    path('analytics/', include('app.urls.advanced_analytics')),
    
    # URLs de automatización omnicanal
    path('automation/', include('app.urls.omnichannel_automation')),
    
    # URLs de API
    path('api/', include('app.urls.api')),
    
    # URLs de autenticación
    path('auth/', include('app.urls.auth')),
    
    # URLs de notificaciones
    path('notifications/', include('app.urls.notifications')),
    
    # URLs de chatbot
    path('chatbot/', include('app.urls.chatbot')),
    
    # URLs de integraciones
    path('integrations/', include('app.urls.integrations')),
    
    # URLs de reportes
    path('reports/', include('app.urls.reports')),
    
    # URLs de configuración
    path('config/', include('app.urls.config')),
    
    # URLs de utilidades
    path('utils/', include('app.urls.utils')),
]

# URLs para archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 