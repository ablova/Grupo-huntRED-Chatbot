"""
📈 MODELOS DE MÉTRICAS DE RENDIMIENTO

Gestión de métricas de rendimiento y KPIs financieros.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from app.models import BusinessUnit, Person

class PerformanceMetrics(models.Model):
    """Métricas de rendimiento financiero."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    
    # Información básica
    metric_date = models.DateField(help_text="Fecha de la métrica")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Métricas de rentabilidad
    gross_profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Margen de utilidad bruta (%)"
    )
    net_profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Margen de utilidad neta (%)"
    )
    operating_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Margen operativo (%)"
    )
    
    # Métricas de eficiencia
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
    
    # Métricas de liquidez
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
    
    # Métricas de solvencia
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
    
    # Métricas de crecimiento
    revenue_growth = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Crecimiento de ingresos (%)"
    )
    profit_growth = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Crecimiento de utilidades (%)"
    )
    asset_growth = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Crecimiento de activos (%)"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_performance_metrics'
    )
    
    class Meta:
        verbose_name = "Métrica de Rendimiento"
        verbose_name_plural = "Métricas de Rendimiento"
        ordering = ['-metric_date']
        unique_together = ['business_unit', 'period_start', 'period_end']
    
    def __str__(self):
        return f"Métricas - {self.period_start} a {self.period_end}"
    
    def calculate_metrics(self):
        """Calcula todas las métricas financieras."""
        # Obtener datos financieros del período
        financial_data = self._get_financial_data()
        
        # Calcular métricas de rentabilidad
        if financial_data['revenue'] > 0:
            self.gross_profit_margin = (financial_data['gross_profit'] / financial_data['revenue']) * 100
            self.net_profit_margin = (financial_data['net_profit'] / financial_data['revenue']) * 100
            self.operating_margin = (financial_data['operating_profit'] / financial_data['revenue']) * 100
        
        # Calcular métricas de eficiencia
        if financial_data['average_assets'] > 0:
            self.asset_turnover = financial_data['revenue'] / financial_data['average_assets']
        
        if financial_data['average_inventory'] > 0:
            self.inventory_turnover = financial_data['cost_of_goods_sold'] / financial_data['average_inventory']
        
        if financial_data['average_receivables'] > 0:
            self.receivables_turnover = financial_data['revenue'] / financial_data['average_receivables']
        
        # Calcular métricas de liquidez
        if financial_data['current_liabilities'] > 0:
            self.current_ratio = financial_data['current_assets'] / financial_data['current_liabilities']
            self.quick_ratio = (financial_data['current_assets'] - financial_data['inventory']) / financial_data['current_liabilities']
            self.cash_ratio = financial_data['cash'] / financial_data['current_liabilities']
        
        # Calcular métricas de solvencia
        if financial_data['equity'] > 0:
            self.debt_to_equity = financial_data['total_debt'] / financial_data['equity']
        
        if financial_data['total_assets'] > 0:
            self.debt_to_assets = financial_data['total_debt'] / financial_data['total_assets']
        
        if financial_data['interest_expense'] > 0:
            self.interest_coverage = financial_data['operating_profit'] / financial_data['interest_expense']
        
        # Calcular métricas de crecimiento
        if financial_data['previous_revenue'] > 0:
            self.revenue_growth = ((financial_data['revenue'] - financial_data['previous_revenue']) / financial_data['previous_revenue']) * 100
        
        if financial_data['previous_profit'] > 0:
            self.profit_growth = ((financial_data['net_profit'] - financial_data['previous_profit']) / financial_data['previous_profit']) * 100
        
        if financial_data['previous_assets'] > 0:
            self.asset_growth = ((financial_data['total_assets'] - financial_data['previous_assets']) / financial_data['previous_assets']) * 100
        
        self.save()
    
    def _get_financial_data(self):
        """Obtiene los datos financieros del período."""
        # Esta función debería obtener datos reales de la contabilidad
        # Por ahora, retornamos datos de ejemplo
        return {
            'revenue': Decimal('1000000.00'),
            'gross_profit': Decimal('400000.00'),
            'operating_profit': Decimal('200000.00'),
            'net_profit': Decimal('150000.00'),
            'cost_of_goods_sold': Decimal('600000.00'),
            'current_assets': Decimal('500000.00'),
            'current_liabilities': Decimal('200000.00'),
            'cash': Decimal('100000.00'),
            'inventory': Decimal('150000.00'),
            'total_assets': Decimal('2000000.00'),
            'total_debt': Decimal('800000.00'),
            'equity': Decimal('1200000.00'),
            'interest_expense': Decimal('50000.00'),
            'average_assets': Decimal('1900000.00'),
            'average_inventory': Decimal('140000.00'),
            'average_receivables': Decimal('80000.00'),
            'previous_revenue': Decimal('900000.00'),
            'previous_profit': Decimal('135000.00'),
            'previous_assets': Decimal('1800000.00')
        }
    
    def get_metrics_summary(self):
        """Obtiene el resumen de métricas."""
        return {
            'profitability': {
                'gross_margin': self.gross_profit_margin,
                'net_margin': self.net_profit_margin,
                'operating_margin': self.operating_margin
            },
            'efficiency': {
                'asset_turnover': self.asset_turnover,
                'inventory_turnover': self.inventory_turnover,
                'receivables_turnover': self.receivables_turnover
            },
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
            'growth': {
                'revenue_growth': self.revenue_growth,
                'profit_growth': self.profit_growth,
                'asset_growth': self.asset_growth
            }
        }

class KPIMetrics(models.Model):
    """Métricas KPI específicas."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='kpi_metrics'
    )
    
    # Información básica
    kpi_name = models.CharField(max_length=100, help_text="Nombre del KPI")
    kpi_category = models.CharField(
        max_length=30,
        choices=[
            ('financial', 'Financiero'),
            ('operational', 'Operacional'),
            ('customer', 'Cliente'),
            ('employee', 'Empleado'),
            ('process', 'Proceso'),
            ('other', 'Otro')
        ],
        help_text="Categoría del KPI"
    )
    
    # Valores
    current_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Valor actual del KPI"
    )
    target_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Valor objetivo del KPI"
    )
    previous_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor anterior del KPI"
    )
    
    # Unidades
    unit = models.CharField(
        max_length=20,
        help_text="Unidad de medida"
    )
    
    # Frecuencia
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Diario'),
            ('weekly', 'Semanal'),
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('annual', 'Anual')
        ],
        help_text="Frecuencia de medición"
    )
    
    # Fechas
    measurement_date = models.DateField(help_text="Fecha de medición")
    next_measurement_date = models.DateField(help_text="Próxima fecha de medición")
    
    # Estados
    is_on_track = models.BooleanField(default=True, help_text="¿KPI en ruta?")
    is_critical = models.BooleanField(default=False, help_text="¿KPI crítico?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_kpi_metrics'
    )
    
    class Meta:
        verbose_name = "Métrica KPI"
        verbose_name_plural = "Métricas KPI"
        ordering = ['kpi_category', 'kpi_name']
    
    def __str__(self):
        return f"{self.kpi_name} - {self.current_value} {self.unit}"
    
    def calculate_performance(self):
        """Calcula el rendimiento del KPI."""
        if self.target_value > 0:
            performance = (self.current_value / self.target_value) * 100
            self.is_on_track = performance >= 100
        else:
            performance = Decimal('0.00')
            self.is_on_track = True
        
        self.save(update_fields=['is_on_track'])
        return performance
    
    def get_growth_rate(self):
        """Calcula la tasa de crecimiento."""
        if self.previous_value and self.previous_value > 0:
            return ((self.current_value - self.previous_value) / self.previous_value) * 100
        return Decimal('0.00')
    
    def get_variance(self):
        """Calcula la varianza con el objetivo."""
        return self.current_value - self.target_value
    
    def get_variance_percentage(self):
        """Calcula el porcentaje de varianza."""
        if self.target_value > 0:
            return (self.get_variance() / self.target_value) * 100
        return Decimal('0.00')
    
    def get_status_color(self):
        """Obtiene el color de estado del KPI."""
        performance = self.calculate_performance()
        
        if performance >= 100:
            return 'success'  # Verde
        elif performance >= 80:
            return 'warning'  # Amarillo
        else:
            return 'danger'   # Rojo
    
    def get_kpi_summary(self):
        """Obtiene el resumen del KPI."""
        return {
            'name': self.kpi_name,
            'category': self.kpi_category,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'unit': self.unit,
            'performance': self.calculate_performance(),
            'growth_rate': self.get_growth_rate(),
            'variance': self.get_variance(),
            'status': self.get_status_color(),
            'is_on_track': self.is_on_track,
            'is_critical': self.is_critical
        } 