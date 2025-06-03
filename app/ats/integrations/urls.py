from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'integrations', views.IntegrationViewSet)
router.register(r'configs', views.IntegrationConfigViewSet)
router.register(r'logs', views.IntegrationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/', include('app.ats.integrations.webhooks.urls')),
] 