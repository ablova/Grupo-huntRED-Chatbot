"""Modelo de Unidad de Negocio."""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class BusinessUnit(models.Model):
    """Unidad de Negocio en el sistema."""
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuración
    settings = models.JSONField(default=dict)
    
    # Relaciones
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_business_units'
    )
    members = models.ManyToManyField(
        User,
        through='BusinessUnitMember',
        related_name='business_units'
    )
    
    class Meta:
        verbose_name = 'Unidad de Negocio'
        verbose_name_plural = 'Unidades de Negocio'
        ordering = ['name']
        
    def __str__(self):
        return self.name
        
    def get_settings(self, key=None, default=None):
        """Obtiene configuración específica."""
        if key is None:
            return self.settings
        return self.settings.get(key, default)
        
    def set_settings(self, key, value):
        """Actualiza configuración específica."""
        self.settings[key] = value
        self.save(update_fields=['settings'])
        
    @property
    def is_active(self):
        """Verifica si la unidad está activa."""
        return self.active
        
    def deactivate(self):
        """Desactiva la unidad de negocio."""
        self.active = False
        self.save(update_fields=['active', 'updated_at'])
        
    def activate(self):
        """Activa la unidad de negocio."""
        self.active = True
        self.save(update_fields=['active', 'updated_at'])


class BusinessUnitMember(models.Model):
    """Miembros de una Unidad de Negocio."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('member', 'Miembro'),
    ]
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='business_unit_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['business_unit', 'user']
        verbose_name = 'Miembro de Unidad de Negocio'
        verbose_name_plural = 'Miembros de Unidades de Negocio'
        
    def __str__(self):
        return f"{self.user.username} - {self.business_unit.name}" 