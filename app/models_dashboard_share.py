"""
Modelos para la gestión de compartición de dashboards.

Define los modelos necesarios para gestionar la compartición de dashboards con clientes
a través de enlaces únicos con caducidad.
"""

import uuid
import secrets
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class ClientDashboardShare(models.Model):
    """
    Modelo para gestionar los enlaces compartidos de dashboards.
    Almacena tokens únicos con fecha de caducidad y registra el uso.
    """
    # Relaciones
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, related_name='dashboard_shares')
    business_unit = models.ForeignKey('BusinessUnit', on_delete=models.CASCADE, related_name='dashboard_shares')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_dashboard_shares')
    
    # Datos del enlace
    token = models.CharField(max_length=64, unique=True, editable=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, help_text="Nombre descriptivo para identificar este enlace")
    
    # Configuración
    expiry_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    require_auth = models.BooleanField(default=False, help_text="Requerir autenticación adicional (código OTP)")
    
    # Permisos y configuración
    allow_satisfaction_view = models.BooleanField(default=True)
    allow_onboarding_view = models.BooleanField(default=True)
    allow_recommendations_view = models.BooleanField(default=True)
    
    # Datos de seguimiento
    created_date = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Enlace de Dashboard Compartido"
        verbose_name_plural = "Enlaces de Dashboard Compartidos"
        ordering = ['-created_date']
    
    def __str__(self):
        return f"Dashboard compartido: {self.empresa.name} ({self.created_date.strftime('%d/%m/%Y')})"
    
    def save(self, *args, **kwargs):
        """Generamos un token único si no existe."""
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Verifica si el enlace ha caducado."""
        return self.expiry_date < timezone.now()
    
    @property
    def days_remaining(self):
        """Calcula los días restantes antes de la caducidad."""
        if self.is_expired:
            return 0
        delta = self.expiry_date - timezone.now()
        return max(0, delta.days)
    
    def register_access(self):
        """Registra un acceso al enlace."""
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])
    
    def extend_expiry(self, days=30):
        """Extiende la caducidad del enlace."""
        self.expiry_date = timezone.now() + timezone.timedelta(days=days)
        self.save(update_fields=['expiry_date'])


class ClientDashboardAccessLog(models.Model):
    """
    Registro detallado de cada acceso a los dashboards compartidos.
    Útil para análisis y auditoría.
    """
    dashboard_share = models.ForeignKey(ClientDashboardShare, on_delete=models.CASCADE, related_name='access_logs')
    access_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Registro de Acceso a Dashboard"
        verbose_name_plural = "Registros de Acceso a Dashboards"
        ordering = ['-access_time']
    
    def __str__(self):
        return f"Acceso: {self.dashboard_share.empresa.name} - {self.access_time.strftime('%d/%m/%Y %H:%M')}"
