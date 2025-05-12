# /home/pablo/app/publish/views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from rest_framework import viewsets, permissions
from .models import Channel, Bot, JobChannel
from .serializers import ChannelSerializer, BotSerializer, JobChannelSerializer

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

class JobChannelViewSet(viewsets.ModelViewSet):
    """
    API endpoint para canales de oportunidades laborales
    """
    queryset = JobChannel.objects.all()
    serializer_class = JobChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra las oportunidades por estado si se especifica
        """
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
