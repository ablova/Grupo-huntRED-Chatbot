from django.db import models
from app.models import BusinessUnit
from app.ats.client_portal.models import PortalAddon

class BusinessUnitAddon(models.Model):
    """
    Relación entre una BusinessUnit y un Addon (PortalAddon por ahora).
    """
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='business_unit_addons')
    addon = models.ForeignKey(PortalAddon, on_delete=models.CASCADE, related_name='business_unit_addons')
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True, default=dict)
    
    class Meta:
        verbose_name = 'Addon de Unidad de Negocio'
        verbose_name_plural = 'Addons de Unidades de Negocio'
        unique_together = ('business_unit', 'addon')
        ordering = ['business_unit', 'addon']

    def __str__(self):
        return f"{self.business_unit} - {self.addon} ({'Activo' if self.is_active else 'Inactivo'})" 