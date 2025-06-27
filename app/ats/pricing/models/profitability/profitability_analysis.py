"""
📈 MODELOS DE ANÁLISIS DE RENTABILIDAD

Gestión de análisis de rentabilidad, márgenes y punto de equilibrio.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from app.models import BusinessUnit, Person
from .cost_analysis import CostCenter

class ProfitabilityAnalysis(models.Model):
    """Análisis de rentabilidad."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='profitability_analyses'
    )
    
    # Información básica
    analysis_date = models.DateField(help_text="Fecha del análisis")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Ingresos
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Ingresos totales"
    )
    
    # Costos
    total_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costos totales"
    )
    direct_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costos directos"
    )
    indirect_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costos indirectos"
    )
    
    # Utilidades
    gross_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Utilidad bruta"
    )
    net_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Utilidad neta"
    )
    
    # Márgenes
    gross_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Margen bruto (%)"
    )
    net_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Margen neto (%)"
    )
    
    # Análisis por segmento
    segment_analysis = models.JSONField(
        default=dict,
        help_text="Análisis por segmento"
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
        related_name='created_profitability_analyses'
    )
    
    class Meta:
        verbose_name = "Análisis de Rentabilidad"
        verbose_name_plural = "Análisis de Rentabilidad"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"Análisis de Rentabilidad - {self.period_start} a {self.period_end}"
    
    def calculate_profitability(self):
        """Calcula la rentabilidad del período."""
        # Calcular utilidad bruta
        self.gross_profit = self.total_revenue - self.direct_costs
        
        # Calcular utilidad neta
        self.net_profit = self.gross_profit - self.indirect_costs
        
        # Calcular márgenes
        if self.total_revenue > 0:
            self.gross_margin = (self.gross_profit / self.total_revenue) * 100
            self.net_margin = (self.net_profit / self.total_revenue) * 100
        
        self.save(update_fields=[
            'gross_profit', 'net_profit', 'gross_margin', 'net_margin'
        ])
    
    def get_roi(self):
        """Calcula el retorno sobre inversión."""
        # Esto requeriría información de activos/inversiones
        # Por ahora, usamos una aproximación simple
        if self.total_costs > 0:
            return (self.net_profit / self.total_costs) * 100
        return Decimal('0.00')
    
    def get_profitability_summary(self):
        """Obtiene el resumen de rentabilidad."""
        return {
            'period': f"{self.period_start} a {self.period_end}",
            'total_revenue': self.total_revenue,
            'total_costs': self.total_costs,
            'gross_profit': self.gross_profit,
            'net_profit': self.net_profit,
            'gross_margin': self.gross_margin,
            'net_margin': self.net_margin,
            'roi': self.get_roi()
        }

class MarginAnalysis(models.Model):
    """Análisis de márgenes."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='margin_analyses'
    )
    
    # Información básica
    analysis_date = models.DateField(help_text="Fecha del análisis")
    product_service_id = models.PositiveIntegerField(
        help_text="ID del producto o servicio"
    )
    product_service_type = models.CharField(
        max_length=20,
        choices=[
            ('product', 'Producto'),
            ('service', 'Servicio')
        ],
        help_text="Tipo de producto o servicio"
    )
    
    # Volúmenes
    units_sold = models.PositiveIntegerField(
        default=0,
        help_text="Unidades vendidas"
    )
    total_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Cantidad total"
    )
    
    # Precios
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio unitario"
    )
    total_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Ingresos totales"
    )
    
    # Costos
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo unitario"
    )
    total_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Costos totales"
    )
    
    # Márgenes
    unit_margin = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Margen unitario"
    )
    total_margin = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Margen total"
    )
    margin_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje de margen"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Análisis de Margen"
        verbose_name_plural = "Análisis de Márgenes"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"Margen - {self.product_service_type} #{self.product_service_id}"
    
    def calculate_margins(self):
        """Calcula los márgenes."""
        # Calcular ingresos totales
        self.total_revenue = self.unit_price * self.total_quantity
        
        # Calcular costos totales
        self.total_cost = self.unit_cost * self.total_quantity
        
        # Calcular márgenes
        self.unit_margin = self.unit_price - self.unit_cost
        self.total_margin = self.total_revenue - self.total_cost
        
        # Calcular porcentaje de margen
        if self.total_revenue > 0:
            self.margin_percentage = (self.total_margin / self.total_revenue) * 100
        
        self.save(update_fields=[
            'total_revenue', 'total_cost', 'unit_margin',
            'total_margin', 'margin_percentage'
        ])
    
    def get_margin_contribution(self):
        """Obtiene la contribución al margen total."""
        return {
            'unit_contribution': self.unit_margin,
            'total_contribution': self.total_margin,
            'percentage_contribution': self.margin_percentage
        }

class BreakEvenAnalysis(models.Model):
    """Análisis de punto de equilibrio."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='break_even_analyses'
    )
    
    # Información básica
    analysis_date = models.DateField(help_text="Fecha del análisis")
    product_service_id = models.PositiveIntegerField(
        help_text="ID del producto o servicio"
    )
    product_service_type = models.CharField(
        max_length=20,
        choices=[
            ('product', 'Producto'),
            ('service', 'Servicio')
        ],
        help_text="Tipo de producto o servicio"
    )
    
    # Costos
    fixed_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Costos fijos"
    )
    variable_cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo variable por unidad"
    )
    
    # Precios
    selling_price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio de venta por unidad"
    )
    
    # Punto de equilibrio
    break_even_units = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Unidades de punto de equilibrio"
    )
    break_even_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Ingresos de punto de equilibrio"
    )
    
    # Análisis de sensibilidad
    sensitivity_analysis = models.JSONField(
        default=dict,
        help_text="Análisis de sensibilidad"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_break_even_analyses'
    )
    
    class Meta:
        verbose_name = "Análisis de Punto de Equilibrio"
        verbose_name_plural = "Análisis de Punto de Equilibrio"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"Punto de Equilibrio - {self.product_service_type} #{self.product_service_id}"
    
    def calculate_break_even(self):
        """Calcula el punto de equilibrio."""
        # Contribución marginal por unidad
        contribution_margin = self.selling_price_per_unit - self.variable_cost_per_unit
        
        if contribution_margin > 0:
            # Punto de equilibrio en unidades
            self.break_even_units = self.fixed_costs / contribution_margin
            
            # Punto de equilibrio en ingresos
            self.break_even_revenue = self.break_even_units * self.selling_price_per_unit
        else:
            self.break_even_units = Decimal('0.00')
            self.break_even_revenue = Decimal('0.00')
        
        self.save(update_fields=['break_even_units', 'break_even_revenue'])
    
    def calculate_sensitivity(self):
        """Calcula el análisis de sensibilidad."""
        sensitivity = {}
        
        # Variaciones en precio de venta
        price_variations = [-10, -5, 0, 5, 10]  # Porcentajes
        for variation in price_variations:
            new_price = self.selling_price_per_unit * (1 + variation / 100)
            contribution_margin = new_price - self.variable_cost_per_unit
            
            if contribution_margin > 0:
                break_even_units = self.fixed_costs / contribution_margin
                break_even_revenue = break_even_units * new_price
            else:
                break_even_units = Decimal('0.00')
                break_even_revenue = Decimal('0.00')
            
            sensitivity[f'price_{variation}%'] = {
                'price': new_price,
                'break_even_units': break_even_units,
                'break_even_revenue': break_even_revenue
            }
        
        # Variaciones en costos variables
        cost_variations = [-10, -5, 0, 5, 10]  # Porcentajes
        for variation in cost_variations:
            new_cost = self.variable_cost_per_unit * (1 + variation / 100)
            contribution_margin = self.selling_price_per_unit - new_cost
            
            if contribution_margin > 0:
                break_even_units = self.fixed_costs / contribution_margin
                break_even_revenue = break_even_units * self.selling_price_per_unit
            else:
                break_even_units = Decimal('0.00')
                break_even_revenue = Decimal('0.00')
            
            sensitivity[f'cost_{variation}%'] = {
                'cost': new_cost,
                'break_even_units': break_even_units,
                'break_even_revenue': break_even_revenue
            }
        
        self.sensitivity_analysis = sensitivity
        self.save(update_fields=['sensitivity_analysis'])
    
    def get_margin_of_safety(self, current_sales):
        """Calcula el margen de seguridad."""
        if self.break_even_revenue > 0:
            return ((current_sales - self.break_even_revenue) / current_sales) * 100
        return Decimal('0.00')
    
    def get_break_even_summary(self):
        """Obtiene el resumen del punto de equilibrio."""
        return {
            'fixed_costs': self.fixed_costs,
            'variable_cost_per_unit': self.variable_cost_per_unit,
            'selling_price_per_unit': self.selling_price_per_unit,
            'contribution_margin': self.selling_price_per_unit - self.variable_cost_per_unit,
            'break_even_units': self.break_even_units,
            'break_even_revenue': self.break_even_revenue
        } 