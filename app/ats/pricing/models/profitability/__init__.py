"""
📈 MÓDULO DE RENTABILIDAD - huntRED

Modelos para análisis de rentabilidad:
- Análisis de costos
- Margen de contribución
- Punto de equilibrio
- Rentabilidad por servicio/cliente
"""

from .cost_analysis import CostCenter, CostAllocation, CostAnalysis
from .profitability_analysis import ProfitabilityAnalysis, MarginAnalysis, BreakEvenAnalysis
from .performance_metrics import PerformanceMetrics, KPIMetrics

__all__ = [
    # Análisis de costos
    'CostCenter', 'CostAllocation', 'CostAnalysis',
    
    # Análisis de rentabilidad
    'ProfitabilityAnalysis', 'MarginAnalysis', 'BreakEvenAnalysis',
    
    # Métricas de rendimiento
    'PerformanceMetrics', 'KPIMetrics',
] 