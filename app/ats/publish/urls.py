# app/ats/publish/urls.py
#
# Configuración de URLs para el módulo. Define endpoints, vistas y patrones de URL.

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.ats.publish.views import ChannelViewSet, BotViewSet

router = DefaultRouter()
router.register(r'channels', ChannelViewSet)
router.register(r'bots', BotViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
