"""
💰 MODELOS DE FLUJO DE EFECTIVO

Gestión de flujo de efectivo y categorías de flujo.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit, Person

class CashFlowCategory(models.Model):
    """Categoría de flujo de efectivo."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='cash_flow_categories'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre de la categoría")
    description = models.TextField(blank=True, help_text="Descripción de la categoría")
    
    # Clasificación
    category_type = models.CharField(
        max_length=20,
        choices=[
            ('operating', 'Operativo'),
            ('investing', 'Inversión'),
            ('financing', 'Financiamiento')
        ],
        help_text="Tipo de categoría"
    )
    
    # Flujo
    flow_direction = models.CharField(
        max_length=10,
        choices=[
            ('inflow', 'Entrada'),
            ('outflow', 'Salida'),
            ('both', 'Ambos')
        ],
        help_text="Dirección del flujo"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Categoría activa?")
    is_default = models.BooleanField(default=False, help_text="¿Categoría por defecto?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Categoría de Flujo de Efectivo"
        verbose_name_plural = "Categorías de Flujo de Efectivo"
        unique_together = ['business_unit', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category_type})"

class CashFlow(models.Model):
    """Movimiento de flujo de efectivo."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='cash_flows'
    )
    
    # Información básica
    transaction_date = models.DateField(help_text="Fecha de la transacción")
    description = models.TextField(help_text="Descripción del movimiento")
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia del movimiento"
    )
    
    # Categorización
    category = models.ForeignKey(
        CashFlowCategory,
        on_delete=models.CASCADE,
        related_name='cash_flows'
    )
    
    # Montos
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Monto del movimiento"
    )
    is_inflow = models.BooleanField(default=True, help_text="¿Es entrada de efectivo?")
    
    # Información adicional
    payment_method = models.CharField(
        max_length=30,
        choices=[
            ('cash', 'Efectivo'),
            ('bank_transfer', 'Transferencia Bancaria'),
            ('check', 'Cheque'),
            ('credit_card', 'Tarjeta de Crédito'),
            ('debit_card', 'Tarjeta de Débito'),
            ('digital_payment', 'Pago Digital'),
            ('other', 'Otro')
        ],
        help_text="Método de pago"
    )
    
    # Estados
    is_confirmed = models.BooleanField(default=False, help_text="¿Movimiento confirmado?")
    is_reconciled = models.BooleanField(default=False, help_text="¿Movimiento conciliado?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cash_flows'
    )
    
    class Meta:
        verbose_name = "Flujo de Efectivo"
        verbose_name_plural = "Flujos de Efectivo"
        ordering = ['-transaction_date', '-created_at']
    
    def __str__(self):
        direction = "Entrada" if self.is_inflow else "Salida"
        return f"{self.transaction_date} - {direction} - {self.amount}"
    
    def get_net_amount(self):
        """Obtiene el monto neto (positivo para entradas, negativo para salidas)."""
        if self.is_inflow:
            return self.amount
        else:
            return -self.amount
    
    def confirm(self, confirmed_by=None):
        """Confirma el movimiento de efectivo."""
        self.is_confirmed = True
        self.save(update_fields=['is_confirmed'])
    
    def reconcile(self, reconciled_by=None):
        """Marca el movimiento como conciliado."""
        self.is_reconciled = True
        self.save(update_fields=['is_reconciled'])

class CashFlowStatement(models.Model):
    """Estado de flujo de efectivo."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='cash_flow_statements'
    )
    
    # Información básica
    statement_date = models.DateField(help_text="Fecha del estado")
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Saldos
    opening_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Saldo de apertura"
    )
    closing_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Saldo de cierre"
    )
    
    # Flujos operativos
    operating_inflows = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Entradas operativas"
    )
    operating_outflows = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Salidas operativas"
    )
    net_operating_cash_flow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Flujo operativo neto"
    )
    
    # Flujos de inversión
    investing_inflows = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Entradas de inversión"
    )
    investing_outflows = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Salidas de inversión"
    )
    net_investing_cash_flow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Flujo de inversión neto"
    )
    
    # Flujos de financiamiento
    financing_inflows = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Entradas de financiamiento"
    )
    financing_outflows = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Salidas de financiamiento"
    )
    net_financing_cash_flow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Flujo de financiamiento neto"
    )
    
    # Flujo neto total
    net_cash_flow = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Flujo de efectivo neto"
    )
    
    # Estados
    is_complete = models.BooleanField(default=False, help_text="¿Estado completo?")
    is_audited = models.BooleanField(default=False, help_text="¿Estado auditado?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cash_flow_statements'
    )
    
    class Meta:
        verbose_name = "Estado de Flujo de Efectivo"
        verbose_name_plural = "Estados de Flujo de Efectivo"
        ordering = ['-statement_date']
        unique_together = ['business_unit', 'period_start', 'period_end']
    
    def __str__(self):
        return f"Estado de Flujo - {self.period_start} a {self.period_end}"
    
    def calculate_cash_flows(self):
        """Calcula todos los flujos de efectivo del período."""
        # Obtener movimientos del período
        cash_flows = CashFlow.objects.filter(
            business_unit=self.business_unit,
            transaction_date__gte=self.period_start,
            transaction_date__lte=self.period_end,
            is_confirmed=True
        )
        
        # Inicializar totales
        operating_inflows = Decimal('0.00')
        operating_outflows = Decimal('0.00')
        investing_inflows = Decimal('0.00')
        investing_outflows = Decimal('0.00')
        financing_inflows = Decimal('0.00')
        financing_outflows = Decimal('0.00')
        
        # Clasificar movimientos
        for flow in cash_flows:
            amount = flow.amount
            
            if flow.category.category_type == 'operating':
                if flow.is_inflow:
                    operating_inflows += amount
                else:
                    operating_outflows += amount
            elif flow.category.category_type == 'investing':
                if flow.is_inflow:
                    investing_inflows += amount
                else:
                    investing_outflows += amount
            elif flow.category.category_type == 'financing':
                if flow.is_inflow:
                    financing_inflows += amount
                else:
                    financing_outflows += amount
        
        # Calcular flujos netos
        self.operating_inflows = operating_inflows
        self.operating_outflows = operating_outflows
        self.net_operating_cash_flow = operating_inflows - operating_outflows
        
        self.investing_inflows = investing_inflows
        self.investing_outflows = investing_outflows
        self.net_investing_cash_flow = investing_inflows - investing_outflows
        
        self.financing_inflows = financing_inflows
        self.financing_outflows = financing_outflows
        self.net_financing_cash_flow = financing_inflows - financing_outflows
        
        # Calcular flujo neto total
        self.net_cash_flow = (
            self.net_operating_cash_flow +
            self.net_investing_cash_flow +
            self.net_financing_cash_flow
        )
        
        # Calcular saldo de cierre
        self.closing_balance = self.opening_balance + self.net_cash_flow
        
        self.save(update_fields=[
            'operating_inflows', 'operating_outflows', 'net_operating_cash_flow',
            'investing_inflows', 'investing_outflows', 'net_investing_cash_flow',
            'financing_inflows', 'financing_outflows', 'net_financing_cash_flow',
            'net_cash_flow', 'closing_balance'
        ])
    
    def get_cash_flow_summary(self):
        """Obtiene el resumen del flujo de efectivo."""
        return {
            'period': f"{self.period_start} a {self.period_end}",
            'opening_balance': self.opening_balance,
            'closing_balance': self.closing_balance,
            'net_cash_flow': self.net_cash_flow,
            'operating': {
                'inflows': self.operating_inflows,
                'outflows': self.operating_outflows,
                'net': self.net_operating_cash_flow
            },
            'investing': {
                'inflows': self.investing_inflows,
                'outflows': self.investing_outflows,
                'net': self.net_investing_cash_flow
            },
            'financing': {
                'inflows': self.financing_inflows,
                'outflows': self.financing_outflows,
                'net': self.net_financing_cash_flow
            }
        }
    
    def get_cash_flow_ratios(self):
        """Calcula ratios de flujo de efectivo."""
        # Obtener ingresos operativos (esto requeriría datos de contabilidad)
        operating_revenue = Decimal('1000000.00')  # Ejemplo
        
        ratios = {}
        
        if operating_revenue > 0:
            ratios['operating_cash_flow_ratio'] = self.net_operating_cash_flow / operating_revenue
        
        if self.operating_outflows > 0:
            ratios['cash_coverage_ratio'] = self.net_operating_cash_flow / self.operating_outflows
        
        return ratios 