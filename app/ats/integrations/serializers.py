from rest_framework import serializers
from .models import Integration, IntegrationConfig, IntegrationLog

class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class IntegrationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationConfig
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_secret:
            data['value'] = '********'
        return data

class IntegrationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationLog
        fields = '__all__'
        read_only_fields = ('created_at',) 