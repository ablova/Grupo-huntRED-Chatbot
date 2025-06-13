"""
Modelo para benchmarks de mercado.
"""
from django.db import models
from app.models import BusinessUnit, Skill

class MarketBenchmark(models.Model):
    """Modelo para benchmarks de mercado."""
    
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='market_benchmarks')
    location = models.CharField(max_length=100, null=True, blank=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Rangos salariales y estadísticas
    salary_data = models.JSONField(
        default=dict,
        help_text="Datos salariales incluyendo rangos por nivel y estadísticas"
    )
    
    # Métricas de mercado
    market_metrics = models.JSONField(
        default=dict,
        help_text="Métricas de mercado como demanda, competencia y tamaño"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Benchmark de Mercado"
        verbose_name_plural = "Benchmarks de Mercado"
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
    def mean_salary(self):
        return self.salary_data.get('mean_salary', 0)
    
    @property
    def median_salary(self):
        return self.salary_data.get('median_salary', 0)
    
    @property
    def demand_level(self):
        return self.market_metrics.get('demand_level', 0)
    
    @property
    def competition_level(self):
        return self.market_metrics.get('competition_level', 0) 