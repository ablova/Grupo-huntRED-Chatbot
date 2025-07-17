from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import LoginAttempt, PasswordResetToken

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para obtener tokens JWT"""
    
    def validate(self, attrs):
        """Validar credenciales y crear tokens"""
        data = super().validate(attrs)
        
        # Agregar información adicional al token
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        # Información del usuario
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_active': self.user.is_active,
            'is_staff': self.user.is_staff,
            'is_superuser': self.user.is_superuser,
        }
        
        # Registrar intento de login exitoso
        LoginAttempt.objects.create(
            user=self.user,
            username=self.user.username,
            ip_address=self.context.get('request').META.get('REMOTE_ADDR', ''),
            user_agent=self.context.get('request').META.get('HTTP_USER_AGENT', ''),
            status=LoginAttempt.SUCCESS
        )
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuarios"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        return attrs
    
    def create(self, validated_data):
        """Crear nuevo usuario"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para perfil de usuario"""
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')
        read_only_fields = ('id', 'username', 'date_joined')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validar contraseñas"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Las nuevas contraseñas no coinciden.")
        return attrs
    
    def validate_old_password(self, value):
        """Validar contraseña actual"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer para solicitar reset de contraseña"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validar que el email existe"""
        if not User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("No existe una cuenta activa con este email.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar reset de contraseña"""
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        """Validar token y contraseñas"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden.")
        
        try:
            token_obj = PasswordResetToken.objects.get(
                token=attrs['token'],
                is_valid=True
            )
            if token_obj.is_expired():
                raise serializers.ValidationError("El token ha expirado.")
            attrs['token_obj'] = token_obj
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Token inválido.")
        
        return attrs


class LoginAttemptSerializer(serializers.ModelSerializer):
    """Serializer para intentos de login"""
    
    class Meta:
        model = LoginAttempt
        fields = '__all__'
        read_only_fields = ('user', 'username', 'ip_address', 'user_agent', 'status', 'timestamp', 'failure_reason') 