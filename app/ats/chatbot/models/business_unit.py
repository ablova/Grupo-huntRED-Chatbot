from django.db import models
from django.utils.translation import gettext_lazy as _

class BusinessUnit(models.Model):
    """
    Modelo para las unidades de negocio.
    """
    name = models.CharField(_('Nombre'), max_length=100)
    code = models.CharField(_('Código'), max_length=10, unique=True)
    description = models.TextField(_('Descripción'), blank=True)
    is_active = models.BooleanField(_('Activa'), default=True)
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('Unidad de Negocio')
        verbose_name_plural = _('Unidades de Negocio')
        ordering = ['name']
    
    def __str__(self):
        return self.name 