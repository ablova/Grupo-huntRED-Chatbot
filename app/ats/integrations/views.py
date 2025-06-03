from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Integration, IntegrationConfig, IntegrationLog
from .serializers import (
    IntegrationSerializer,
    IntegrationConfigSerializer,
    IntegrationLogSerializer
)

class IntegrationViewSet(viewsets.ModelViewSet):
    queryset = Integration.objects.all()
    serializer_class = IntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        integration = self.get_object()
        try:
            # Implementar lógica de prueba de conexión según el tipo
            return Response({'status': 'success'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class IntegrationConfigViewSet(viewsets.ModelViewSet):
    queryset = IntegrationConfig.objects.all()
    serializer_class = IntegrationConfigSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        integration_id = self.request.query_params.get('integration_id')
        if integration_id:
            queryset = queryset.filter(integration_id=integration_id)
        return queryset

class IntegrationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IntegrationLog.objects.all()
    serializer_class = IntegrationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        integration_id = self.request.query_params.get('integration_id')
        if integration_id:
            queryset = queryset.filter(integration_id=integration_id)
        return queryset 