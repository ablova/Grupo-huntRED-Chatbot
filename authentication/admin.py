from django.contrib import admin
from .models import UserSession, LoginAttempt, PasswordResetToken


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin para sesiones de usuario"""
    list_display = ('user', 'ip_address', 'created_at', 'last_activity', 'is_active')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    ordering = ('-last_activity',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Admin para intentos de login"""
    list_display = ('username', 'ip_address', 'status', 'timestamp', 'failure_reason')
    list_filter = ('status', 'timestamp')
    search_fields = ('username', 'ip_address', 'failure_reason')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin para tokens de reset de contraseña"""
    list_display = ('user', 'created_at', 'used_at', 'is_valid')
    list_filter = ('is_valid', 'created_at', 'used_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
