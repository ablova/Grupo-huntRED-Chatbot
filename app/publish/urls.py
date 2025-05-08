from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChannelViewSet, BotViewSet, JobChannelViewSet

router = DefaultRouter()
router.register(r'channels', ChannelViewSet)
router.register(r'bots', BotViewSet)
router.register(r'job-channels', JobChannelViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
