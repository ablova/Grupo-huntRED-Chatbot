"""
Modelo para benchmarks de mercado.
"""
from django.db import models
from app.models import BusinessUnit

class MarketBenchmark(models.Model):
    """Modelo para benchmarks de mercado."""
    
    skill = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True, blank=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Rangos salariales
    entry_level = models.JSONField()
    mid_level = models.JSONField()
    senior_level = models.JSONField()
    
    # Estadísticas
    mean_salary = models.DecimalField(max_digits=10, decimal_places=2)
    median_salary = models.DecimalField(max_digits=10, decimal_places=2)
    salary_standard_deviation = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Métricas de mercado
    demand_level = models.FloatField()
    competition_level = models.FloatField()
    market_size = models.CharField(max_length=20)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['skill']),
            models.Index(fields=['location']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['timestamp'])
        ]
    
    def __str__(self):
        return f"{self.skill} - {self.location or 'Global'}" 