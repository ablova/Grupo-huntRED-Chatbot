from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),
    path('payments/', include('app.payments.urls')),
    path('analytics/', include('app.analytics.urls')),
    path('social/', include('app.social.urls')),
    path('proposals/', include('app.proposals.urls')),
    path('communications/', include('app.communications.urls')),
    path('simulator/', include('app.simulator.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('app.urls')),
    path('payments/', include('app.payments.urls')),
    path('analytics/', include('app.analytics.urls')),
    path('social/', include('app.social.urls')),
    path('proposals/', include('app.proposals.urls')),
    path('communications/', include('app.communications.urls')),
    path('simulator/', include('app.simulator.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
