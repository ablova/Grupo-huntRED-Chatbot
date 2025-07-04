"""
🚀 GhuntRED-v2 Main URLs Configuration
Complete API routing for all business units
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 Endpoints
    path('api/v1/auth/', include('apps.core.urls')),
    path('api/v1/candidates/', include('apps.candidates.urls')),
    path('api/v1/companies/', include('apps.companies.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/integrations/', include('apps.integrations.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    
    # ML API Endpoints
    path('api/v1/ml/', include('ml.core.urls')),
    path('api/v1/genia/', include('ml.genia.urls')),
    path('api/v1/aura/', include('ml.aura.urls')),
    
    # Frontend Routes (catch-all for React Router)
    path('', include('apps.core.frontend_urls')),
]

# Static and Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin customization
admin.site.site_header = "GhuntRED v2 Administration"
admin.site.site_title = "GhuntRED v2 Admin Portal"
admin.site.index_title = "Welcome to GhuntRED v2 Administration"