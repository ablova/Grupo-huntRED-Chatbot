"""
🚀 GhuntRED-v2 Core API Views
Authentication, user management, and system APIs
"""

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from django.utils import timezone

from .serializers import UserSerializer, UserRegistrationSerializer
from ml import ml_factory

User = get_user_model()

class CustomAuthToken(ObtainAuthToken):
    """Custom authentication with user details"""
    
    @extend_schema(
        summary="User Login",
        description="Authenticate user and return token with user details"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'created': created
        })

class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        summary="Get current user profile",
        description="Retrieve the current authenticated user's profile"
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Update current user profile",
        description="Update the current authenticated user's profile"
    )
    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class SystemViewSet(viewsets.ViewSet):
    """System status and health check endpoints"""
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="System Health Check",
        description="Get comprehensive system health status"
    )
    @action(detail=False, methods=['get'])
    def health(self, request):
        """System health check"""
        try:
            # ML system health
            ml_health = ml_factory.health_check()
            
            # Database health (simple check)
            db_health = self._check_database()
            
            # Cache health
            cache_health = self._check_cache()
            
            overall_status = "healthy"
            if (ml_health.get('status') != 'healthy' or 
                not db_health or not cache_health):
                overall_status = "degraded"
            
            return Response({
                'status': overall_status,
                'components': {
                    'ml_system': ml_health,
                    'database': {'status': 'healthy' if db_health else 'unhealthy'},
                    'cache': {'status': 'healthy' if cache_health else 'unhealthy'},
                },
                'timestamp': timezone.now()
            })
            
        except Exception as e:
            return Response({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': timezone.now()
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @extend_schema(
        summary="ML System Status",
        description="Get ML system status and available analyzers"
    )
    @action(detail=False, methods=['get'])
    def ml_status(self, request):
        """ML system status"""
        try:
            available_analyzers = ml_factory.get_available_analyzers()
            ml_health = ml_factory.health_check()
            
            return Response({
                'status': ml_health.get('status', 'unknown'),
                'available_analyzers': available_analyzers,
                'health_details': ml_health,
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _check_database(self):
        """Simple database health check"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except:
            return False
    
    def _check_cache(self):
        """Simple cache health check"""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 30)
            return cache.get('health_check') == 'ok'
        except:
            return False