from django.shortcuts import render
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    LoginAttemptSerializer
)
from .models import LoginAttempt, PasswordResetToken

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener tokens JWT"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """Manejar intento de login"""
        try:
            response = super().post(request, *args, **kwargs)
            
            # Si el login es exitoso, ya se registra en el serializer
            return response
            
        except Exception as e:
            # Registrar intento fallido
            LoginAttempt.objects.create(
                username=request.data.get('username', ''),
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status=LoginAttempt.FAILED,
                failure_reason=str(e)
            )
            raise


class UserRegistrationView(generics.CreateAPIView):
    """Vista para registro de usuarios"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Crear usuario y generar tokens"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Usuario registrado exitosamente',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vista para perfil de usuario"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """Vista para cambiar contraseña"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Cambiar contraseña del usuario"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Contraseña cambiada exitosamente'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Vista para solicitar reset de contraseña"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Solicitar reset de contraseña"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generar token único
        token = get_random_string(64)
        
        # Crear token de reset
        PasswordResetToken.objects.create(
            user=user,
            token=token
        )
        
        # Enviar email (en desarrollo se imprime en consola)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        if settings.DEBUG:
            print(f"Reset URL: {reset_url}")
        else:
            # En producción, enviar email real
            send_mail(
                subject='Reset de Contraseña - huntRED®',
                message=f'Para resetear tu contraseña, visita: {reset_url}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        
        return Response({
            'message': 'Se ha enviado un email con instrucciones para resetear tu contraseña'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Vista para confirmar reset de contraseña"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Confirmar reset de contraseña"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_obj = serializer.validated_data['token_obj']
        new_password = serializer.validated_data['new_password']
        
        # Cambiar contraseña
        user = token_obj.user
        user.set_password(new_password)
        user.save()
        
        # Marcar token como usado
        token_obj.mark_as_used()
        
        return Response({
            'message': 'Contraseña cambiada exitosamente'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Vista para logout"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Logout del usuario"""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout exitoso'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message': 'Error en logout',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginAttemptsView(generics.ListAPIView):
    """Vista para listar intentos de login"""
    serializer_class = LoginAttemptSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filtrar intentos de login"""
        queryset = LoginAttempt.objects.all()
        
        # Filtros opcionales
        username = self.request.query_params.get('username', None)
        status_filter = self.request.query_params.get('status', None)
        days = self.request.query_params.get('days', None)
        
        if username:
            queryset = queryset.filter(username__icontains=username)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if days:
            try:
                days = int(days)
                cutoff_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(timestamp__gte=cutoff_date)
            except ValueError:
                pass
        
        return queryset


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_info(request):
    """Obtener información del usuario actual"""
    user = request.user
    return Response({
        'user': UserProfileSerializer(user).data,
        'permissions': list(user.get_all_permissions()),
        'groups': list(user.groups.values_list('name', flat=True))
    })
