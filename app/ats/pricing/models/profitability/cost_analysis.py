"""
📈 MODELOS DE ANÁLISIS DE COSTOS

Gestión de centros de costo, asignaciones y análisis de costos.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from app.models import BusinessUnit, Person

class CostCenter(models.Model):
    """Centro de costo."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='cost_centers'
    )
    
    # Información básica
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código del centro de costo"
    )
    name = models.CharField(max_length=100, help_text="Nombre del centro de costo")
    description = models.TextField(blank=True, help_text="Descripción del centro de costo")
    
    # Clasificación
    cost_center_type = models.CharField(
        max_length=30,
        choices=[
            ('production', 'Producción'),
            ('service', 'Servicio'),
            ('administration', 'Administración'),
            ('sales', 'Ventas'),
            ('marketing', 'Mercadotecnia'),
            ('research', 'Investigación'),
            ('support', 'Soporte'),
            ('other', 'Otro')
        ],
        help_text="Tipo de centro de costo"
    )
    
    # Responsable
    manager = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_cost_centers'
    )
    
    # Presupuesto
    budget_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto presupuestado"
    )
    budget_period = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('annual', 'Anual')
        ],
        default='monthly',
        help_text="Período del presupuesto"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Centro de costo activo?")
    is_profit_center = models.BooleanField(
        default=False,
        help_text="¿Es un centro de utilidades?"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cost_centers'
    )
    
    class Meta:
        verbose_name = "Centro de Costo"
        verbose_name_plural = "Centros de Costo"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_total_costs(self, start_date=None, end_date=None):
        """Obtiene el total de costos del centro."""
        from app.ats.pricing.models.accounting.journal_entries import JournalEntryLine
        
        query = JournalEntryLine.objects.filter(
            account__chart_of_accounts__business_unit=self.business_unit,
            account__account_type='expense',
            journal_entry__is_posted=True
        )
        
        if start_date:
            query = query.filter(journal_entry__date__gte=start_date)
        if end_date:
            query = query.filter(journal_entry__date__lte=end_date)
        
        # Filtrar por centro de costo (esto requeriría un campo adicional en JournalEntryLine)
        # Por ahora, asumimos que todos los gastos se asignan al centro de costo
        
        return query.aggregate(
            total=models.Sum('debit_amount')
        )['total'] or Decimal('0.00')
    
    def get_budget_variance(self, start_date=None, end_date=None):
        """Obtiene la variación del presupuesto."""
        actual_costs = self.get_total_costs(start_date, end_date)
        return actual_costs - self.budget_amount
    
    def get_budget_variance_percentage(self, start_date=None, end_date=None):
        """Obtiene el porcentaje de variación del presupuesto."""
        variance = self.get_budget_variance(start_date, end_date)
        if self.budget_amount > 0:
            return (variance / self.budget_amount) * 100
        return Decimal('0.00')

class CostAllocation(models.Model):
    """Asignación de costos."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='cost_allocations'
    )
    
    # Centros de costo
    from_cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.CASCADE,
        related_name='allocations_from',
        help_text="Centro de costo origen"
    )
    to_cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.CASCADE,
        related_name='allocations_to',
        help_text="Centro de costo destino"
    )
    
    # Información básica
    allocation_date = models.DateField(help_text="Fecha de asignación")
    description = models.TextField(help_text="Descripción de la asignación")
    
    # Montos
    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Monto asignado"
    )
    
    # Método de asignación
    allocation_method = models.CharField(
        max_length=30,
        choices=[
            ('percentage', 'Porcentaje'),
            ('fixed_amount', 'Monto Fijo'),
            ('proportional', 'Proporcional'),
            ('activity_based', 'Basado en Actividad'),
            ('other', 'Otro')
        ],
        help_text="Método de asignación"
    )
    
    # Factor de asignación
    allocation_factor = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('1.0000'),
        help_text="Factor de asignación"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Asignación activa?")
    is_automatic = models.BooleanField(
        default=False,
        help_text="¿Asignación automática?"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cost_allocations'
    )
    
    class Meta:
        verbose_name = "Asignación de Costos"
        verbose_name_plural = "Asignaciones de Costos"
        ordering = ['-allocation_date']
    
    def __str__(self):
        return f"{self.from_cost_center.code} → {self.to_cost_center.code} - {self.allocated_amount}"
    
    def calculate_allocation(self):
        """Calcula la asignación basada en el método."""
        if self.allocation_method == 'percentage':
            # Asignación por porcentaje del total
            total_costs = self.from_cost_center.get_total_costs()
            self.allocated_amount = (total_costs * self.allocation_factor) / 100
        elif self.allocation_method == 'fixed_amount':
            # Monto fijo (ya establecido)
            pass
        elif self.allocation_method == 'proportional':
            # Proporcional a algún criterio
            # Esto requeriría lógica adicional específica
            pass
        
        self.save(update_fields=['allocated_amount'])

class CostAnalysis(models.Model):
    """Análisis de costos."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='cost_analyses'
    )
    
    # Información básica
    analysis_date = models.DateField(help_text="Fecha del análisis")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Costos totales
    total_direct_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costos directos totales"
    )
    total_indirect_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costos indirectos totales"
    )
    total_fixed_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costos fijos totales"
    )
    total_variable_costs = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costos variables totales"
    )
    
    # Análisis por centro de costo
    cost_center_breakdown = models.JSONField(
        default=dict,
        help_text="Desglose por centro de costo"
    )
    
    # Análisis de tendencias
    cost_trends = models.JSONField(
        default=dict,
        help_text="Tendencias de costos"
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
        related_name='created_cost_analyses'
    )
    
    class Meta:
        verbose_name = "Análisis de Costos"
        verbose_name_plural = "Análisis de Costos"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"Análisis de Costos - {self.period_start} a {self.period_end}"
    
    def calculate_costs(self):
        """Calcula todos los costos del período."""
        # Obtener todos los centros de costo
        cost_centers = CostCenter.objects.filter(
            business_unit=self.business_unit,
            is_active=True
        )
        
        breakdown = {}
        total_direct = Decimal('0.00')
        total_indirect = Decimal('0.00')
        total_fixed = Decimal('0.00')
        total_variable = Decimal('0.00')
        
        for center in cost_centers:
            # Obtener costos del centro
            center_costs = center.get_total_costs(self.period_start, self.period_end)
            
            # Clasificar costos (esto requeriría lógica adicional)
            direct_costs = center_costs * Decimal('0.7')  # Ejemplo
            indirect_costs = center_costs * Decimal('0.3')  # Ejemplo
            fixed_costs = center_costs * Decimal('0.6')  # Ejemplo
            variable_costs = center_costs * Decimal('0.4')  # Ejemplo
            
            breakdown[center.code] = {
                'name': center.name,
                'total_costs': center_costs,
                'direct_costs': direct_costs,
                'indirect_costs': indirect_costs,
                'fixed_costs': fixed_costs,
                'variable_costs': variable_costs,
                'budget_variance': center.get_budget_variance(self.period_start, self.period_end)
            }
            
            total_direct += direct_costs
            total_indirect += indirect_costs
            total_fixed += fixed_costs
            total_variable += variable_costs
        
        # Actualizar campos
        self.total_direct_costs = total_direct
        self.total_indirect_costs = total_indirect
        self.total_fixed_costs = total_fixed
        self.total_variable_costs = total_variable
        self.cost_center_breakdown = breakdown
        
        self.save(update_fields=[
            'total_direct_costs', 'total_indirect_costs',
            'total_fixed_costs', 'total_variable_costs',
            'cost_center_breakdown'
        ])
    
    def get_total_costs(self):
        """Obtiene el total de costos."""
        return (
            self.total_direct_costs + 
            self.total_indirect_costs
        )
    
    def get_cost_structure(self):
        """Obtiene la estructura de costos."""
        total = self.get_total_costs()
        if total > 0:
            return {
                'direct_percentage': (self.total_direct_costs / total) * 100,
                'indirect_percentage': (self.total_indirect_costs / total) * 100,
                'fixed_percentage': (self.total_fixed_costs / total) * 100,
                'variable_percentage': (self.total_variable_costs / total) * 100
            }
        return {
            'direct_percentage': Decimal('0.00'),
            'indirect_percentage': Decimal('0.00'),
            'fixed_percentage': Decimal('0.00'),
            'variable_percentage': Decimal('0.00')
        } 