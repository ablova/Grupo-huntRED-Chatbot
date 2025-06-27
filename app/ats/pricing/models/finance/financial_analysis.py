"""
💰 MODELOS DE ANÁLISIS FINANCIERO

Gestión de análisis financiero y ratios.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit, Person

class FinancialAnalysis(models.Model):
    """Análisis financiero."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='financial_analyses'
    )
    
    # Información básica
    analysis_date = models.DateField(help_text="Fecha del análisis")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Ratios de liquidez
    current_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Razón corriente"
    )
    quick_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Razón rápida"
    )
    cash_ratio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Razón de efectivo"
    )
    
    # Ratios de solvencia
    debt_to_equity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Razón deuda-capital"
    )
    debt_to_assets = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Razón deuda-activos"
    )
    interest_coverage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Cobertura de intereses"
    )
    
    # Ratios de rentabilidad
    return_on_assets = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Retorno sobre activos (%)"
    )
    return_on_equity = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Retorno sobre capital (%)"
    )
    return_on_investment = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Retorno sobre inversión (%)"
    )
    
    # Ratios de eficiencia
    asset_turnover = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Rotación de activos"
    )
    inventory_turnover = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Rotación de inventario"
    )
    receivables_turnover = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Rotación de cuentas por cobrar"
    )
    
    # Análisis de tendencias
    trend_analysis = models.JSONField(
        default=dict,
        help_text="Análisis de tendencias"
    )
    
    # Estados
    is_complete = models.BooleanField(default=False, help_text="¿Análisis completo?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_financial_analyses'
    )
    
    class Meta:
        verbose_name = "Análisis Financiero"
        verbose_name_plural = "Análisis Financieros"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"Análisis Financiero - {self.period_start} a {self.period_end}"
    
    def calculate_ratios(self):
        """Calcula todos los ratios financieros."""
        # Obtener datos financieros
        financial_data = self._get_financial_data()
        
        # Ratios de liquidez
        if financial_data['current_liabilities'] > 0:
            self.current_ratio = financial_data['current_assets'] / financial_data['current_liabilities']
            self.quick_ratio = (financial_data['current_assets'] - financial_data['inventory']) / financial_data['current_liabilities']
            self.cash_ratio = financial_data['cash'] / financial_data['current_liabilities']
        
        # Ratios de solvencia
        if financial_data['equity'] > 0:
            self.debt_to_equity = financial_data['total_debt'] / financial_data['equity']
        
        if financial_data['total_assets'] > 0:
            self.debt_to_assets = financial_data['total_debt'] / financial_data['total_assets']
        
        if financial_data['interest_expense'] > 0:
            self.interest_coverage = financial_data['operating_income'] / financial_data['interest_expense']
        
        # Ratios de rentabilidad
        if financial_data['average_assets'] > 0:
            self.return_on_assets = (financial_data['net_income'] / financial_data['average_assets']) * 100
        
        if financial_data['average_equity'] > 0:
            self.return_on_equity = (financial_data['net_income'] / financial_data['average_equity']) * 100
        
        if financial_data['total_investment'] > 0:
            self.return_on_investment = (financial_data['net_income'] / financial_data['total_investment']) * 100
        
        # Ratios de eficiencia
        if financial_data['average_assets'] > 0:
            self.asset_turnover = financial_data['revenue'] / financial_data['average_assets']
        
        if financial_data['average_inventory'] > 0:
            self.inventory_turnover = financial_data['cost_of_goods_sold'] / financial_data['average_inventory']
        
        if financial_data['average_receivables'] > 0:
            self.receivables_turnover = financial_data['revenue'] / financial_data['average_receivables']
        
        self.save()
    
    def _get_financial_data(self):
        """Obtiene los datos financieros del período."""
        # Esta función debería obtener datos reales de la contabilidad
        # Por ahora, retornamos datos de ejemplo
        return {
            'current_assets': Decimal('500000.00'),
            'current_liabilities': Decimal('200000.00'),
            'cash': Decimal('100000.00'),
            'inventory': Decimal('150000.00'),
            'total_assets': Decimal('2000000.00'),
            'total_debt': Decimal('800000.00'),
            'equity': Decimal('1200000.00'),
            'operating_income': Decimal('200000.00'),
            'interest_expense': Decimal('50000.00'),
            'net_income': Decimal('150000.00'),
            'revenue': Decimal('1000000.00'),
            'cost_of_goods_sold': Decimal('600000.00'),
            'average_assets': Decimal('1900000.00'),
            'average_equity': Decimal('1150000.00'),
            'average_inventory': Decimal('140000.00'),
            'average_receivables': Decimal('80000.00'),
            'total_investment': Decimal('1000000.00')
        }
    
    def get_analysis_summary(self):
        """Obtiene el resumen del análisis."""
        return {
            'period': f"{self.period_start} a {self.period_end}",
            'liquidity': {
                'current_ratio': self.current_ratio,
                'quick_ratio': self.quick_ratio,
                'cash_ratio': self.cash_ratio
            },
            'solvency': {
                'debt_to_equity': self.debt_to_equity,
                'debt_to_assets': self.debt_to_assets,
                'interest_coverage': self.interest_coverage
            },
            'profitability': {
                'return_on_assets': self.return_on_assets,
                'return_on_equity': self.return_on_equity,
                'return_on_investment': self.return_on_investment
            },
            'efficiency': {
                'asset_turnover': self.asset_turnover,
                'inventory_turnover': self.inventory_turnover,
                'receivables_turnover': self.receivables_turnover
            }
        }

class RatioAnalysis(models.Model):
    """Análisis de ratios específicos."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='ratio_analyses'
    )
    
    # Información básica
    analysis_date = models.DateField(help_text="Fecha del análisis")
    ratio_name = models.CharField(max_length=100, help_text="Nombre del ratio")
    ratio_category = models.CharField(
        max_length=30,
        choices=[
            ('liquidity', 'Liquidez'),
            ('solvency', 'Solvencia'),
            ('profitability', 'Rentabilidad'),
            ('efficiency', 'Eficiencia'),
            ('market', 'Mercado'),
            ('other', 'Otro')
        ],
        help_text="Categoría del ratio"
    )
    
    # Valores del ratio
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Valor actual del ratio"
    )
    previous_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Valor anterior del ratio"
    )
    industry_average = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Promedio de la industria"
    )
    benchmark_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Valor de referencia"
    )
    
    # Análisis
    trend = models.CharField(
        max_length=20,
        choices=[
            ('improving', 'Mejorando'),
            ('stable', 'Estable'),
            ('declining', 'Deteriorando'),
            ('unknown', 'Desconocido')
        ],
        default='unknown',
        help_text="Tendencia del ratio"
    )
    
    performance = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excelente'),
            ('good', 'Bueno'),
            ('average', 'Promedio'),
            ('poor', 'Pobre'),
            ('critical', 'Crítico')
        ],
        default='average',
        help_text="Rendimiento del ratio"
    )
    
    # Interpretación
    interpretation = models.TextField(
        blank=True,
        help_text="Interpretación del ratio"
    )
    recommendations = models.TextField(
        blank=True,
        help_text="Recomendaciones"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ratio_analyses'
    )
    
    class Meta:
        verbose_name = "Análisis de Ratio"
        verbose_name_plural = "Análisis de Ratios"
        ordering = ['ratio_category', 'ratio_name']
    
    def __str__(self):
        return f"{self.ratio_name} - {self.current_value}"
    
    def calculate_trend(self):
        """Calcula la tendencia del ratio."""
        if self.previous_value:
            if self.current_value > self.previous_value:
                self.trend = 'improving'
            elif self.current_value < self.previous_value:
                self.trend = 'declining'
            else:
                self.trend = 'stable'
        else:
            self.trend = 'unknown'
        
        self.save(update_fields=['trend'])
    
    def assess_performance(self):
        """Evalúa el rendimiento del ratio."""
        # Lógica de evaluación basada en el tipo de ratio
        if self.benchmark_value:
            if self.current_value >= self.benchmark_value:
                self.performance = 'excellent'
            elif self.current_value >= self.benchmark_value * Decimal('0.8'):
                self.performance = 'good'
            elif self.current_value >= self.benchmark_value * Decimal('0.6'):
                self.performance = 'average'
            elif self.current_value >= self.benchmark_value * Decimal('0.4'):
                self.performance = 'poor'
            else:
                self.performance = 'critical'
        
        self.save(update_fields=['performance'])
    
    def get_change_percentage(self):
        """Calcula el porcentaje de cambio."""
        if self.previous_value and self.previous_value > 0:
            return ((self.current_value - self.previous_value) / self.previous_value) * 100
        return Decimal('0.00')
    
    def get_variance_from_industry(self):
        """Calcula la varianza con el promedio de la industria."""
        if self.industry_average:
            return self.current_value - self.industry_average
        return Decimal('0.00')
    
    def get_ratio_summary(self):
        """Obtiene el resumen del ratio."""
        return {
            'name': self.ratio_name,
            'category': self.ratio_category,
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'change_percentage': self.get_change_percentage(),
            'industry_average': self.industry_average,
            'benchmark_value': self.benchmark_value,
            'trend': self.trend,
            'performance': self.performance,
            'interpretation': self.interpretation,
            'recommendations': self.recommendations
        } 