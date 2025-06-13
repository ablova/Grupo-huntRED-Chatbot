# /home/pablo/app/ats/market/models/analysis.py
from django.db import models
from app.models import BusinessUnit, Skill
from .benchmark import MarketBenchmark

class MarketAnalysis(models.Model):
    """Modelo para análisis detallados de mercado."""
    
    ANALYSIS_TYPES = [
        ('TREND', 'Análisis de Tendencias'),
        ('COMPETITION', 'Análisis de Competencia'),
        ('SALARY', 'Análisis Salarial'),
        ('SKILL', 'Análisis de Habilidades'),
        ('DEMAND', 'Análisis de Demanda'),
        ('SUPPLY', 'Análisis de Oferta'),
        ('GENERAL', 'Análisis General')
    ]
    
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='market_analyses')
    benchmark = models.ForeignKey(
        MarketBenchmark,
        on_delete=models.CASCADE,
        related_name='analyses',
        help_text="Benchmark asociado a este análisis"
    )
    
    analysis_type = models.CharField(
        max_length=20,
        choices=ANALYSIS_TYPES,
        help_text="Tipo de análisis realizado"
    )
    
    # Métricas de calidad
    metrics = models.JSONField(
        default=dict,
        help_text="Métricas de calidad del análisis (confianza, precisión, etc.)"
    )
    
    # Resultados del análisis
    results = models.JSONField(
        default=dict,
        help_text="Resultados del análisis incluyendo hallazgos y recomendaciones"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análisis de Mercado"
        verbose_name_plural = "Análisis de Mercado"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['skill']),
            models.Index(fields=['benchmark']),
            models.Index(fields=['analysis_type']),
            models.Index(fields=['created_at'])
        ]
    
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.skill.name} ({self.created_at.strftime('%Y-%m-%d')})"
    
    @property
    def confidence_score(self):
        return self.metrics.get('confidence_score', 0)
    
    @property
    def accuracy_score(self):
        return self.metrics.get('accuracy_score', 0)
    
    @property
    def findings(self):
        return self.results.get('findings', {})
    
    @property
    def recommendations(self):
        return self.results.get('recommendations', {}) 