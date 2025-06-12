from django.db import models
from django.utils.translation import gettext_lazy as _
from app.ats.models.business_unit import BusinessUnit

class PremiumAddon(models.Model):
    """Modelo para addons premium"""
    
    class AddonType(models.TextChoices):
        MARKET_REPORT = 'market_report', _('Reporte de Mercado')
        SALARY_BENCHMARK = 'salary_benchmark', _('Benchmark Salarial')
        LEARNING_ANALYTICS = 'learning_analytics', _('Analítica de Aprendizaje')
        ORGANIZATIONAL_ANALYSIS = 'org_analysis', _('Análisis Organizacional')
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, choices=AddonType.choices)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Addon Premium')
        verbose_name_plural = _('Addons Premium')
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class BusinessUnitAddon(models.Model):
    """Modelo para addons activos por unidad de negocio"""
    
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    addon = models.ForeignKey(PremiumAddon, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Addon de Unidad de Negocio')
        verbose_name_plural = _('Addons de Unidades de Negocio')
        unique_together = ('business_unit', 'addon')
    
    def __str__(self):
        return f"{self.business_unit.name} - {self.addon.name}" 