# app/ats/publish/views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from rest_framework import viewsets, permissions
from app.ats.publish.models import Channel, Bot
from app.ats.publish.serializers import ChannelSerializer, BotSerializer

class ChannelViewSet(viewsets.ModelViewSet):
    """
    API endpoint para canales de publicación
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

class BotViewSet(viewsets.ModelViewSet):
    """
    API endpoint para bots interactivos
    """
    queryset = Bot.objects.all()
    serializer_class = BotSerializer
    permission_classes = [permissions.IsAuthenticated]


