"""
Modelo para tendencias de mercado.
"""
from django.db import models
from app.models import BusinessUnit

class MarketTrend(models.Model):
    """Modelo para tendencias de mercado."""
    
    skill = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True, blank=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Métricas
    demand_level = models.FloatField()
    salary_range = models.JSONField()
    competition_level = models.FloatField()
    
    # Tendencias
    demand_trend = models.CharField(max_length=20)
    salary_trend = models.CharField(max_length=20)
    competition_trend = models.CharField(max_length=20)
    
    # Predicciones
    predictions = models.JSONField()
    
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