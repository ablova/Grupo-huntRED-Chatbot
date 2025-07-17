from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserSession(models.Model):
    """Modelo para rastrear sesiones de usuario"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuario'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Sesión de {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def is_expired(self, max_age_hours=24):
        """Verificar si la sesión ha expirado"""
        return self.last_activity < timezone.now() - timedelta(hours=max_age_hours)


class LoginAttempt(models.Model):
    """Modelo para rastrear intentos de login"""
    SUCCESS = 'success'
    FAILED = 'failed'
    BLOCKED = 'blocked'
    
    STATUS_CHOICES = [
        (SUCCESS, 'Exitoso'),
        (FAILED, 'Fallido'),
        (BLOCKED, 'Bloqueado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='login_attempts')
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = 'Intento de Login'
        verbose_name_plural = 'Intentos de Login'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.username} - {self.status} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class PasswordResetToken(models.Model):
    """Modelo para tokens de reset de contraseña"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_valid = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Token de Reset de Contraseña'
        verbose_name_plural = 'Tokens de Reset de Contraseña'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token para {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def is_expired(self, max_age_hours=24):
        """Verificar si el token ha expirado"""
        return self.created_at < timezone.now() - timedelta(hours=max_age_hours)
    
    def mark_as_used(self):
        """Marcar el token como usado"""
        self.used_at = timezone.now()
        self.is_valid = False
        self.save()
