"""
💰 MODELOS DE CÁLCULOS FISCALES

Gestión de cálculos de impuestos, retenciones y declaraciones.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit, Person
from .tax_configuration import TaxConfiguration, TaxRate, TaxExemption

class TaxCalculation(models.Model):
    """Cálculo de impuestos."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='tax_calculations'
    )
    
    # Información básica
    calculation_date = models.DateField(help_text="Fecha del cálculo")
    reference = models.CharField(
        max_length=100,
        help_text="Referencia del cálculo"
    )
    
    # Montos base
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Subtotal antes de impuestos"
    )
    
    # Impuestos calculados
    iva_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de IVA"
    )
    isr_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de ISR"
    )
    ieps_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de IEPS"
    )
    other_taxes_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Otros impuestos"
    )
    
    # Total
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total con impuestos"
    )
    
    # Configuración utilizada
    tax_configuration = models.ForeignKey(
        TaxConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calculations'
    )
    
    # Estados
    is_valid = models.BooleanField(default=True, help_text="¿Cálculo válido?")
    is_applied = models.BooleanField(default=False, help_text="¿Cálculo aplicado?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tax_calculations'
    )
    
    class Meta:
        verbose_name = "Cálculo de Impuestos"
        verbose_name_plural = "Cálculos de Impuestos"
        ordering = ['-calculation_date']
    
    def __str__(self):
        return f"{self.reference} - {self.calculation_date}"
    
    def calculate_taxes(self):
        """Calcula todos los impuestos aplicables."""
        if not self.tax_configuration:
            return
        
        # Calcular IVA
        if not self._is_exempt_from_tax('iva'):
            iva_rate = self._get_tax_rate('iva')
            self.iva_amount = (self.subtotal * iva_rate) / Decimal('100.00')
        
        # Calcular ISR
        if not self._is_exempt_from_tax('isr'):
            isr_rate = self._get_tax_rate('isr')
            self.isr_amount = (self.subtotal * isr_rate) / Decimal('100.00')
        
        # Calcular IEPS
        if not self._is_exempt_from_tax('ieps'):
            ieps_rate = self._get_tax_rate('ieps')
            self.ieps_amount = (self.subtotal * ieps_rate) / Decimal('100.00')
        
        # Calcular total
        self.total_amount = (
            self.subtotal + 
            self.iva_amount + 
            self.isr_amount + 
            self.ieps_amount + 
            self.other_taxes_amount
        )
        
        self.save(update_fields=[
            'iva_amount', 'isr_amount', 'ieps_amount', 'total_amount'
        ])
    
    def _get_tax_rate(self, tax_type):
        """Obtiene la tasa de impuesto aplicable."""
        return self.tax_configuration.get_tax_rate(tax_type)
    
    def _is_exempt_from_tax(self, tax_type):
        """Verifica si está exento de un impuesto."""
        # Verificar exenciones aplicables
        exemptions = TaxExemption.objects.filter(
            tax_configuration=self.tax_configuration,
            is_active=True
        )
        
        for exemption in exemptions:
            if exemption.is_exempt_from_tax(tax_type):
                return True
        
        return False
    
    def get_total_taxes(self):
        """Obtiene el total de impuestos."""
        return (
            self.iva_amount + 
            self.isr_amount + 
            self.ieps_amount + 
            self.other_taxes_amount
        )
    
    def get_tax_breakdown(self):
        """Obtiene el desglose de impuestos."""
        return {
            'subtotal': self.subtotal,
            'iva': self.iva_amount,
            'isr': self.isr_amount,
            'ieps': self.ieps_amount,
            'other_taxes': self.other_taxes_amount,
            'total': self.total_amount
        }

class TaxRetention(models.Model):
    """Retención de impuestos."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='tax_retentions'
    )
    
    # Información básica
    retention_date = models.DateField(help_text="Fecha de retención")
    reference = models.CharField(
        max_length=100,
        help_text="Referencia de la retención"
    )
    
    # Monto base
    base_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Monto base para retención"
    )
    
    # Retenciones calculadas
    iva_retention = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Retención de IVA"
    )
    isr_retention = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Retención de ISR"
    )
    
    # Total retenido
    total_retention = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total retenido"
    )
    
    # Monto neto
    net_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Monto neto después de retenciones"
    )
    
    # Configuración utilizada
    tax_configuration = models.ForeignKey(
        TaxConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        related_name='retentions'
    )
    
    # Estados
    is_valid = models.BooleanField(default=True, help_text="¿Retención válida?")
    is_applied = models.BooleanField(default=False, help_text="¿Retención aplicada?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tax_retentions'
    )
    
    class Meta:
        verbose_name = "Retención de Impuestos"
        verbose_name_plural = "Retenciones de Impuestos"
        ordering = ['-retention_date']
    
    def __str__(self):
        return f"{self.reference} - {self.retention_date}"
    
    def calculate_retentions(self):
        """Calcula las retenciones aplicables."""
        if not self.tax_configuration:
            return
        
        # Calcular retención de IVA
        iva_retention_rate = self.tax_configuration.get_retention_rate('iva')
        self.iva_retention = (self.base_amount * iva_retention_rate) / Decimal('100.00')
        
        # Calcular retención de ISR
        isr_retention_rate = self.tax_configuration.get_retention_rate('isr')
        self.isr_retention = (self.base_amount * isr_retention_rate) / Decimal('100.00')
        
        # Calcular totales
        self.total_retention = self.iva_retention + self.isr_retention
        self.net_amount = self.base_amount - self.total_retention
        
        self.save(update_fields=[
            'iva_retention', 'isr_retention', 'total_retention', 'net_amount'
        ])
    
    def get_retention_breakdown(self):
        """Obtiene el desglose de retenciones."""
        return {
            'base_amount': self.base_amount,
            'iva_retention': self.iva_retention,
            'isr_retention': self.isr_retention,
            'total_retention': self.total_retention,
            'net_amount': self.net_amount
        }

class TaxDeclaration(models.Model):
    """Declaración fiscal."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='tax_declarations'
    )
    
    # Información básica
    declaration_type = models.CharField(
        max_length=20,
        choices=[
            ('iva', 'IVA'),
            ('isr', 'ISR'),
            ('ieps', 'IEPS'),
            ('combined', 'Combinada')
        ],
        help_text="Tipo de declaración"
    )
    
    period_start = models.DateField(help_text="Inicio del período")
    period_end = models.DateField(help_text="Fin del período")
    
    # Montos declarados
    gross_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Ingresos brutos"
    )
    gross_expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Gastos brutos"
    )
    
    # Impuestos
    taxes_collected = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Impuestos cobrados"
    )
    taxes_paid = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Impuestos pagados"
    )
    taxes_retained = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Impuestos retenidos"
    )
    
    # Resultado
    tax_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Balance de impuestos"
    )
    
    # Estados
    is_filed = models.BooleanField(default=False, help_text="¿Declaración presentada?")
    filing_date = models.DateField(null=True, blank=True, help_text="Fecha de presentación")
    filing_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia de presentación"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tax_declarations'
    )
    
    class Meta:
        verbose_name = "Declaración Fiscal"
        verbose_name_plural = "Declaraciones Fiscales"
        ordering = ['-period_end']
        unique_together = ['business_unit', 'declaration_type', 'period_start', 'period_end']
    
    def __str__(self):
        return f"{self.declaration_type.upper()} - {self.period_start} a {self.period_end}"
    
    def calculate_balance(self):
        """Calcula el balance de impuestos."""
        self.tax_balance = (
            self.taxes_collected - 
            self.taxes_paid - 
            self.taxes_retained
        )
        self.save(update_fields=['tax_balance'])
    
    def file_declaration(self, filing_reference):
        """Marca la declaración como presentada."""
        self.is_filed = True
        self.filing_date = timezone.now().date()
        self.filing_reference = filing_reference
        self.save(update_fields=['is_filed', 'filing_date', 'filing_reference'])
    
    def get_declaration_summary(self):
        """Obtiene el resumen de la declaración."""
        return {
            'period': f"{self.period_start} a {self.period_end}",
            'gross_income': self.gross_income,
            'gross_expenses': self.gross_expenses,
            'net_income': self.gross_income - self.gross_expenses,
            'taxes_collected': self.taxes_collected,
            'taxes_paid': self.taxes_paid,
            'taxes_retained': self.taxes_retained,
            'tax_balance': self.tax_balance,
            'is_filed': self.is_filed
        } 