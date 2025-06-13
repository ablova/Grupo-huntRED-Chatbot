"""
Modelo para tendencias de mercado.
"""
from django.db import models
from app.models import BusinessUnit, Skill

class MarketTrend(models.Model):
    """Modelo para tendencias de mercado."""
    
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='market_trends')
    location = models.CharField(max_length=100, null=True, blank=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Métricas y tendencias
    trend_data = models.JSONField(
        default=dict,
        help_text="Datos de tendencias incluyendo demanda, salarios y competencia"
    )
    
    # Predicciones
    predictions = models.JSONField(
        default=dict,
        help_text="Predicciones futuras del mercado"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tendencia de Mercado"
        verbose_name_plural = "Tendencias de Mercado"
        indexes = [
            models.Index(fields=['skill']),
            models.Index(fields=['location']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['updated_at'])
        ]
        unique_together = ['skill', 'location', 'business_unit']
    
    def __str__(self):
        return f"{self.skill.name} - {self.location or 'Global'}"
    
    @property
    def demand_level(self):
        return self.trend_data.get('demand_level', 0)
    
    @property
    def demand_trend(self):
        return self.trend_data.get('demand_trend', 'stable')
    
    @property
    def salary_trend(self):
        return self.trend_data.get('salary_trend', 'stable')
    
    @property
    def competition_trend(self):
        return self.trend_data.get('competition_trend', 'stable') 