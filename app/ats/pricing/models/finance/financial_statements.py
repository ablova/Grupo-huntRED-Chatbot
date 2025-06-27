"""
💰 MODELOS DE ESTADOS FINANCIEROS

Gestión de estados financieros, balance general y estado de resultados.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit, Person

class FinancialStatement(models.Model):
    """Estado financiero base."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='financial_statements'
    )
    
    # Información básica
    statement_date = models.DateField(help_text="Fecha del estado")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Tipo de estado
    statement_type = models.CharField(
        max_length=30,
        choices=[
            ('balance_sheet', 'Balance General'),
            ('income_statement', 'Estado de Resultados'),
            ('cash_flow', 'Estado de Flujo de Efectivo'),
            ('equity', 'Estado de Cambios en el Capital'),
            ('comprehensive', 'Estado de Resultados Integrales')
        ],
        help_text="Tipo de estado financiero"
    )
    
    # Estados
    is_complete = models.BooleanField(default=False, help_text="¿Estado completo?")
    is_audited = models.BooleanField(default=False, help_text="¿Estado auditado?")
    is_approved = models.BooleanField(default=False, help_text="¿Estado aprobado?")
    
    # Aprobación
    approved_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_financial_statements'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_financial_statements'
    )
    
    class Meta:
        verbose_name = "Estado Financiero"
        verbose_name_plural = "Estados Financieros"
        ordering = ['-statement_date']
        unique_together = ['business_unit', 'statement_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.get_statement_type_display()} - {self.period_start} a {self.period_end}"
    
    def approve(self, approved_by):
        """Aprueba el estado financiero."""
        self.is_approved = True
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])

class BalanceSheet(models.Model):
    """Balance general."""
    
    financial_statement = models.OneToOneField(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name='balance_sheet'
    )
    
    # Activos
    current_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Activos corrientes"
    )
    fixed_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Activos fijos"
    )
    intangible_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Activos intangibles"
    )
    other_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Otros activos"
    )
    total_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de activos"
    )
    
    # Pasivos
    current_liabilities = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Pasivos corrientes"
    )
    long_term_liabilities = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Pasivos a largo plazo"
    )
    total_liabilities = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de pasivos"
    )
    
    # Capital
    paid_in_capital = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Capital pagado"
    )
    retained_earnings = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Utilidades retenidas"
    )
    other_equity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Otros componentes del capital"
    )
    total_equity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total del capital"
    )
    
    # Desglose detallado
    assets_breakdown = models.JSONField(
        default=dict,
        help_text="Desglose detallado de activos"
    )
    liabilities_breakdown = models.JSONField(
        default=dict,
        help_text="Desglose detallado de pasivos"
    )
    equity_breakdown = models.JSONField(
        default=dict,
        help_text="Desglose detallado del capital"
    )
    
    class Meta:
        verbose_name = "Balance General"
        verbose_name_plural = "Balances Generales"
    
    def __str__(self):
        return f"Balance General - {self.financial_statement.period_end}"
    
    def calculate_totals(self):
        """Calcula los totales del balance."""
        # Calcular total de activos
        self.total_assets = (
            self.current_assets +
            self.fixed_assets +
            self.intangible_assets +
            self.other_assets
        )
        
        # Calcular total de pasivos
        self.total_liabilities = (
            self.current_liabilities +
            self.long_term_liabilities
        )
        
        # Calcular total del capital
        self.total_equity = (
            self.paid_in_capital +
            self.retained_earnings +
            self.other_equity
        )
        
        self.save(update_fields=[
            'total_assets', 'total_liabilities', 'total_equity'
        ])
    
    def is_balanced(self):
        """Verifica si el balance está balanceado."""
        return self.total_assets == (self.total_liabilities + self.total_equity)
    
    def get_working_capital(self):
        """Calcula el capital de trabajo."""
        return self.current_assets - self.current_liabilities
    
    def get_debt_ratio(self):
        """Calcula la razón de deuda."""
        if self.total_assets > 0:
            return self.total_liabilities / self.total_assets
        return Decimal('0.00')
    
    def get_equity_ratio(self):
        """Calcula la razón de capital."""
        if self.total_assets > 0:
            return self.total_equity / self.total_assets
        return Decimal('0.00')
    
    def get_balance_summary(self):
        """Obtiene el resumen del balance."""
        return {
            'total_assets': self.total_assets,
            'total_liabilities': self.total_liabilities,
            'total_equity': self.total_equity,
            'working_capital': self.get_working_capital(),
            'debt_ratio': self.get_debt_ratio(),
            'equity_ratio': self.get_equity_ratio(),
            'is_balanced': self.is_balanced()
        }

class IncomeStatement(models.Model):
    """Estado de resultados."""
    
    financial_statement = models.OneToOneField(
        FinancialStatement,
        on_delete=models.CASCADE,
        related_name='income_statement'
    )
    
    # Ingresos
    gross_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Ingresos brutos"
    )
    sales_returns = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Devoluciones de ventas"
    )
    net_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Ingresos netos"
    )
    
    # Costos
    cost_of_goods_sold = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Costo de ventas"
    )
    gross_profit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Utilidad bruta"
    )
    
    # Gastos operativos
    operating_expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Gastos operativos"
    )
    operating_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Ingresos operativos"
    )
    
    # Otros ingresos y gastos
    other_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Otros ingresos"
    )
    other_expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Otros gastos"
    )
    
    # Utilidad antes de impuestos
    income_before_taxes = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Utilidad antes de impuestos"
    )
    
    # Impuestos
    income_taxes = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Impuestos sobre la renta"
    )
    
    # Utilidad neta
    net_income = models.DecimalField(
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
    operating_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Margen operativo (%)"
    )
    net_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Margen neto (%)"
    )
    
    # Desglose detallado
    revenue_breakdown = models.JSONField(
        default=dict,
        help_text="Desglose detallado de ingresos"
    )
    expense_breakdown = models.JSONField(
        default=dict,
        help_text="Desglose detallado de gastos"
    )
    
    class Meta:
        verbose_name = "Estado de Resultados"
        verbose_name_plural = "Estados de Resultados"
    
    def __str__(self):
        return f"Estado de Resultados - {self.financial_statement.period_end}"
    
    def calculate_totals(self):
        """Calcula los totales del estado de resultados."""
        # Calcular ingresos netos
        self.net_revenue = self.gross_revenue - self.sales_returns
        
        # Calcular utilidad bruta
        self.gross_profit = self.net_revenue - self.cost_of_goods_sold
        
        # Calcular ingresos operativos
        self.operating_income = self.gross_profit - self.operating_expenses
        
        # Calcular utilidad antes de impuestos
        self.income_before_taxes = (
            self.operating_income +
            self.other_income -
            self.other_expenses
        )
        
        # Calcular utilidad neta
        self.net_income = self.income_before_taxes - self.income_taxes
        
        # Calcular márgenes
        if self.net_revenue > 0:
            self.gross_margin = (self.gross_profit / self.net_revenue) * 100
            self.operating_margin = (self.operating_income / self.net_revenue) * 100
            self.net_margin = (self.net_income / self.net_revenue) * 100
        
        self.save(update_fields=[
            'net_revenue', 'gross_profit', 'operating_income',
            'income_before_taxes', 'net_income', 'gross_margin',
            'operating_margin', 'net_margin'
        ])
    
    def get_ebitda(self):
        """Calcula el EBITDA."""
        # EBITDA = Utilidad operativa + Depreciación + Amortización
        # Esto requeriría datos de depreciación y amortización
        depreciation = Decimal('0.00')  # Ejemplo
        amortization = Decimal('0.00')  # Ejemplo
        
        return self.operating_income + depreciation + amortization
    
    def get_ebitda_margin(self):
        """Calcula el margen EBITDA."""
        ebitda = self.get_ebitda()
        if self.net_revenue > 0:
            return (ebitda / self.net_revenue) * 100
        return Decimal('0.00')
    
    def get_income_summary(self):
        """Obtiene el resumen del estado de resultados."""
        return {
            'net_revenue': self.net_revenue,
            'gross_profit': self.gross_profit,
            'operating_income': self.operating_income,
            'net_income': self.net_income,
            'gross_margin': self.gross_margin,
            'operating_margin': self.operating_margin,
            'net_margin': self.net_margin,
            'ebitda': self.get_ebitda(),
            'ebitda_margin': self.get_ebitda_margin()
        } 