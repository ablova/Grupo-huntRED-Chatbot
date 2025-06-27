"""
💰 MODELOS DE PRESUPUESTOS

Gestión de presupuestos, líneas presupuestarias y variaciones.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from app.models import BusinessUnit, Person

class Budget(models.Model):
    """Presupuesto."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre del presupuesto")
    description = models.TextField(blank=True, help_text="Descripción del presupuesto")
    
    # Período
    fiscal_year = models.PositiveIntegerField(help_text="Año fiscal")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Tipo de presupuesto
    budget_type = models.CharField(
        max_length=30,
        choices=[
            ('operating', 'Operativo'),
            ('capital', 'Capital'),
            ('cash_flow', 'Flujo de Efectivo'),
            ('project', 'Proyecto'),
            ('department', 'Departamento'),
            ('other', 'Otro')
        ],
        help_text="Tipo de presupuesto"
    )
    
    # Montos
    total_budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Presupuesto total"
    )
    total_actual = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Gasto real total"
    )
    total_variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Variación total"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Presupuesto activo?")
    is_approved = models.BooleanField(default=False, help_text="¿Presupuesto aprobado?")
    is_final = models.BooleanField(default=False, help_text="¿Presupuesto final?")
    
    # Aprobación
    approved_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budgets'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_budgets'
    )
    
    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        ordering = ['-fiscal_year', '-created_at']
        unique_together = ['business_unit', 'name', 'fiscal_year']
    
    def __str__(self):
        return f"{self.name} - {self.fiscal_year}"
    
    def calculate_totals(self):
        """Calcula los totales del presupuesto."""
        lines = self.budget_lines.all()
        
        total_budget = sum(line.budget_amount for line in lines)
        total_actual = sum(line.actual_amount for line in lines)
        total_variance = total_actual - total_budget
        
        self.total_budget = total_budget
        self.total_actual = total_actual
        self.total_variance = total_variance
        
        self.save(update_fields=['total_budget', 'total_actual', 'total_variance'])
    
    def approve(self, approved_by):
        """Aprueba el presupuesto."""
        self.is_approved = True
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])
    
    def get_variance_percentage(self):
        """Obtiene el porcentaje de variación."""
        if self.total_budget > 0:
            return (self.total_variance / self.total_budget) * 100
        return Decimal('0.00')
    
    def get_budget_summary(self):
        """Obtiene el resumen del presupuesto."""
        return {
            'name': self.name,
            'fiscal_year': self.fiscal_year,
            'period': f"{self.period_start} a {self.period_end}",
            'total_budget': self.total_budget,
            'total_actual': self.total_actual,
            'total_variance': self.total_variance,
            'variance_percentage': self.get_variance_percentage(),
            'is_approved': self.is_approved,
            'is_final': self.is_final
        }

class BudgetLine(models.Model):
    """Línea presupuestaria."""
    
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='budget_lines'
    )
    
    # Información básica
    line_number = models.PositiveIntegerField(help_text="Número de línea")
    description = models.TextField(help_text="Descripción de la línea")
    
    # Categorización
    category = models.CharField(
        max_length=50,
        help_text="Categoría de la línea"
    )
    subcategory = models.CharField(
        max_length=50,
        blank=True,
        help_text="Subcategoría de la línea"
    )
    
    # Montos presupuestados
    budget_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Monto presupuestado"
    )
    
    # Montos reales
    actual_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto real gastado"
    )
    
    # Variaciones
    variance_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Variación en monto"
    )
    variance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Variación en porcentaje"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Línea activa?")
    is_approved = models.BooleanField(default=False, help_text="¿Línea aprobada?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Línea Presupuestaria"
        verbose_name_plural = "Líneas Presupuestarias"
        ordering = ['line_number']
        unique_together = ['budget', 'line_number']
    
    def __str__(self):
        return f"{self.budget.name} - Línea {self.line_number}: {self.description}"
    
    def calculate_variance(self):
        """Calcula la variación de la línea."""
        self.variance_amount = self.actual_amount - self.budget_amount
        
        if self.budget_amount > 0:
            self.variance_percentage = (self.variance_amount / self.budget_amount) * 100
        else:
            self.variance_percentage = Decimal('0.00')
        
        self.save(update_fields=['variance_amount', 'variance_percentage'])
    
    def get_status_color(self):
        """Obtiene el color de estado de la línea."""
        if self.variance_percentage <= 5:
            return 'success'  # Verde - dentro del presupuesto
        elif self.variance_percentage <= 15:
            return 'warning'  # Amarillo - atención
        else:
            return 'danger'   # Rojo - sobre presupuesto
    
    def get_line_summary(self):
        """Obtiene el resumen de la línea."""
        return {
            'line_number': self.line_number,
            'description': self.description,
            'category': self.category,
            'budget_amount': self.budget_amount,
            'actual_amount': self.actual_amount,
            'variance_amount': self.variance_amount,
            'variance_percentage': self.variance_percentage,
            'status': self.get_status_color()
        }

class BudgetVariance(models.Model):
    """Análisis de variaciones presupuestarias."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='budget_variances'
    )
    
    # Información básica
    analysis_date = models.DateField(help_text="Fecha del análisis")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Presupuesto relacionado
    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='variances'
    )
    
    # Variaciones totales
    total_budget_variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Variación total del presupuesto"
    )
    total_budget_variance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Porcentaje de variación total"
    )
    
    # Análisis por categoría
    category_variances = models.JSONField(
        default=dict,
        help_text="Variaciones por categoría"
    )
    
    # Análisis de tendencias
    variance_trends = models.JSONField(
        default=dict,
        help_text="Tendencias de variaciones"
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
        related_name='created_budget_variances'
    )
    
    class Meta:
        verbose_name = "Análisis de Variación Presupuestaria"
        verbose_name_plural = "Análisis de Variaciones Presupuestarias"
        ordering = ['-analysis_date']
    
    def __str__(self):
        return f"Análisis de Variación - {self.period_start} a {self.period_end}"
    
    def calculate_variances(self):
        """Calcula todas las variaciones presupuestarias."""
        # Obtener líneas del presupuesto
        budget_lines = self.budget.budget_lines.filter(is_active=True)
        
        # Calcular variaciones totales
        total_budget = sum(line.budget_amount for line in budget_lines)
        total_actual = sum(line.actual_amount for line in budget_lines)
        
        self.total_budget_variance = total_actual - total_budget
        
        if total_budget > 0:
            self.total_budget_variance_percentage = (self.total_budget_variance / total_budget) * 100
        
        # Calcular variaciones por categoría
        category_variances = {}
        for line in budget_lines:
            category = line.category
            if category not in category_variances:
                category_variances[category] = {
                    'budget_amount': Decimal('0.00'),
                    'actual_amount': Decimal('0.00'),
                    'variance_amount': Decimal('0.00'),
                    'variance_percentage': Decimal('0.00')
                }
            
            category_variances[category]['budget_amount'] += line.budget_amount
            category_variances[category]['actual_amount'] += line.actual_amount
            category_variances[category]['variance_amount'] += line.variance_amount
        
        # Calcular porcentajes por categoría
        for category, data in category_variances.items():
            if data['budget_amount'] > 0:
                data['variance_percentage'] = (data['variance_amount'] / data['budget_amount']) * 100
        
        self.category_variances = category_variances
        
        self.save(update_fields=[
            'total_budget_variance', 'total_budget_variance_percentage',
            'category_variances'
        ])
    
    def get_variance_summary(self):
        """Obtiene el resumen de variaciones."""
        return {
            'period': f"{self.period_start} a {self.period_end}",
            'budget_name': self.budget.name,
            'total_variance': self.total_budget_variance,
            'total_variance_percentage': self.total_budget_variance_percentage,
            'category_breakdown': self.category_variances,
            'is_complete': self.is_complete
        }
    
    def get_critical_variances(self, threshold=15):
        """Obtiene variaciones críticas (sobre el umbral)."""
        critical = []
        
        for category, data in self.category_variances.items():
            if abs(data['variance_percentage']) > threshold:
                critical.append({
                    'category': category,
                    'variance_percentage': data['variance_percentage'],
                    'variance_amount': data['variance_amount']
                })
        
        return sorted(critical, key=lambda x: abs(x['variance_percentage']), reverse=True) 