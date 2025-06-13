# /home/pablo/app/ats/market/models/analysis.py
from django.db import models
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
    
    confidence_score = models.FloatField(
        default=0.0,
        help_text="Nivel de confianza del análisis (0-1)"
    )
    
    findings = models.JSONField(
        default=dict,
        help_text="Hallazgos principales del análisis"
    )
    
    recommendations = models.JSONField(
        default=dict,
        help_text="Recomendaciones basadas en el análisis"
    )
    
    data_points = models.JSONField(
        default=dict,
        help_text="Puntos de datos utilizados en el análisis"
    )
    
    accuracy_score = models.FloatField(
        default=0.0,
        help_text="Puntuación de precisión del análisis (0-1)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análisis de Mercado"
        verbose_name_plural = "Análisis de Mercado"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_analysis_type_display()} - {self.benchmark.skill} ({self.created_at.strftime('%Y-%m-%d')})" 