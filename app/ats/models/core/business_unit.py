"""Modelo de Unidad de Negocio."""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache

class BusinessUnit(models.Model):
    """Unidad de Negocio en el sistema."""
    
    name = models.CharField(max_length=100, db_index=True)
    code = models.CharField(max_length=10, unique=True, db_index=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuración estructurada en un solo JSONField
    settings = models.JSONField(
        default=dict,
        help_text="Configuración de la unidad de negocio. Estructura: {notifications: {}, integrations: {}, pricing: {}}"
    )
    
    # Relaciones
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_business_units',
        db_index=True
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
        indexes = [
            models.Index(fields=['name', 'code']),
            models.Index(fields=['active', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_settings(self, section=None, key=None, default=None):
        """Obtiene configuración específica con caché."""
        cache_key = f'business_unit_settings_{self.id}'
        settings = cache.get(cache_key)
        
        if settings is None:
            settings = self.settings
            cache.set(cache_key, settings, 3600)  # Cache por 1 hora
            
        if section is None:
            return settings
            
        section_data = settings.get(section, {})
        if key is None:
            return section_data
            
        return section_data.get(key, default)
    
    def set_settings(self, section, key, value):
        """Actualiza configuración específica y limpia caché."""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
        self.save(update_fields=['settings', 'updated_at'])
        cache.delete(f'business_unit_settings_{self.id}')
    
    @property
    def is_active(self):
        """Verifica si la unidad está activa."""
        return self.active
    
    def deactivate(self):
        """Desactiva la unidad de negocio."""
        self.active = False
        self.save(update_fields=['active', 'updated_at'])
        self._clear_caches()
    
    def activate(self):
        """Activa la unidad de negocio."""
        self.active = True
        self.save(update_fields=['active', 'updated_at'])
        self._clear_caches()
    
    def _clear_caches(self):
        """Limpia todas las cachés relacionadas con esta unidad."""
        cache.delete(f'business_unit_settings_{self.id}')
        cache.delete(f'business_unit_members_{self.id}')
    
    def get_members(self, role=None):
        """Obtiene miembros con caché."""
        cache_key = f'business_unit_members_{self.id}_{role or "all"}'
        members = cache.get(cache_key)
        
        if members is None:
            query = self.memberships.all()
            if role:
                query = query.filter(role=role)
            members = list(query)
            cache.set(cache_key, members, 3600)  # Cache por 1 hora
            
        return members


class BusinessUnitMember(models.Model):
    """Miembros de una Unidad de Negocio."""
    
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('manager', 'Gerente'),
        ('member', 'Miembro'),
        ('viewer', 'Solo Lectura'),
    ]
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='memberships',
        db_index=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='business_unit_memberships',
        db_index=True
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        db_index=True
    )
    joined_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Permisos específicos en settings
    settings = models.JSONField(
        default=dict,
        help_text="Configuración específica del miembro. Estructura: {permissions: {}, preferences: {}}"
    )
    
    class Meta:
        unique_together = ['business_unit', 'user']
        verbose_name = 'Miembro de Unidad de Negocio'
        verbose_name_plural = 'Miembros de Unidades de Negocio'
        indexes = [
            models.Index(fields=['business_unit', 'role']),
            models.Index(fields=['user', 'role']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.business_unit.name} ({self.get_role_display()})"
    
    def has_permission(self, permission_key):
        """Verifica si el miembro tiene un permiso específico."""
        return self.settings.get('permissions', {}).get(permission_key, False)
    
    def grant_permission(self, permission_key):
        """Otorga un permiso específico."""
        if 'permissions' not in self.settings:
            self.settings['permissions'] = {}
        self.settings['permissions'][permission_key] = True
        self.save(update_fields=['settings', 'updated_at'])
        self.business_unit._clear_caches()
    
    def revoke_permission(self, permission_key):
        """Revoca un permiso específico."""
        if 'permissions' in self.settings:
            self.settings['permissions'][permission_key] = False
            self.save(update_fields=['settings', 'updated_at'])
            self.business_unit._clear_caches() 