"""
🚀 GhuntRED-v2 Core URLs
API endpoints for authentication and user management
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'system', views.SystemViewSet, basename='system')

urlpatterns = [
    path('auth/login/', views.CustomAuthToken.as_view(), name='auth_login'),
    path('', include(router.urls)),
]