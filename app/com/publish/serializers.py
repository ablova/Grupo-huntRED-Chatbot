from rest_framework import serializers
from .models import Channel, Bot, JobChannel

class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializador para canales de publicación
    """
    type_name = serializers.CharField(source='type.name', read_only=True)
    
    class Meta:
        model = Channel
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class BotSerializer(serializers.ModelSerializer):
    """
    Serializador para bots interactivos
    """
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    
    class Meta:
        model = Bot
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class JobChannelSerializer(serializers.ModelSerializer):
    """
    Serializador para canales de oportunidades laborales
    """
    channel_name = serializers.CharField(source='channel.name', read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    
    class Meta:
        model = JobChannel
        fields = '__all__'
        read_only_fields = ('created_at', 'published_at')
