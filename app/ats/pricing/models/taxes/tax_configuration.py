"""
💰 MODELOS DE CONFIGURACIÓN DE IMPUESTOS

Gestión de configuración fiscal y tasas de impuestos.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from app.models import BusinessUnit

class TaxConfiguration(models.Model):
    """Configuración general de impuestos."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='tax_configurations'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre de la configuración")
    description = models.TextField(blank=True, help_text="Descripción de la configuración")
    
    # Configuración fiscal
    fiscal_year = models.PositiveIntegerField(help_text="Año fiscal")
    tax_regime = models.CharField(
        max_length=50,
        help_text="Régimen fiscal aplicable"
    )
    
    # Configuración de impuestos
    default_iva_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('16.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Tasa de IVA por defecto (%)"
    )
    default_isr_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('30.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Tasa de ISR por defecto (%)"
    )
    
    # Configuración de retenciones
    iva_retention_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.67'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Tasa de retención de IVA (%)"
    )
    isr_retention_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Tasa de retención de ISR (%)"
    )
    
    # Configuración de declaraciones
    iva_declaration_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('annual', 'Anual')
        ],
        default='monthly',
        help_text="Frecuencia de declaración de IVA"
    )
    isr_declaration_frequency = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Mensual'),
            ('quarterly', 'Trimestral'),
            ('annual', 'Anual')
        ],
        default='monthly',
        help_text="Frecuencia de declaración de ISR"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Configuración activa?")
    is_default = models.BooleanField(default=False, help_text="¿Configuración por defecto?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Impuestos"
        verbose_name_plural = "Configuraciones de Impuestos"
        unique_together = ['business_unit', 'fiscal_year']
    
    def __str__(self):
        return f"{self.business_unit.name} - {self.name} ({self.fiscal_year})"
    
    def get_tax_rate(self, tax_type):
        """Obtiene la tasa de impuesto por tipo."""
        if tax_type == 'iva':
            return self.default_iva_rate
        elif tax_type == 'isr':
            return self.default_isr_rate
        return Decimal('0.00')
    
    def get_retention_rate(self, tax_type):
        """Obtiene la tasa de retención por tipo."""
        if tax_type == 'iva':
            return self.iva_retention_rate
        elif tax_type == 'isr':
            return self.isr_retention_rate
        return Decimal('0.00')

class TaxRate(models.Model):
    """Tasa de impuesto específica."""
    
    tax_configuration = models.ForeignKey(
        TaxConfiguration,
        on_delete=models.CASCADE,
        related_name='tax_rates'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre de la tasa")
    tax_type = models.CharField(
        max_length=20,
        choices=[
            ('iva', 'IVA'),
            ('isr', 'ISR'),
            ('ieps', 'IEPS'),
            ('ish', 'ISH'),
            ('other', 'Otro')
        ],
        help_text="Tipo de impuesto"
    )
    
    # Configuración de la tasa
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Tasa de impuesto (%)"
    )
    
    # Aplicación
    applies_to_products = models.BooleanField(default=True, help_text="¿Aplica a productos?")
    applies_to_services = models.BooleanField(default=True, help_text="¿Aplica a servicios?")
    
    # Categorías específicas
    product_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Categorías de productos específicas"
    )
    service_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Categorías de servicios específicas"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Tasa activa?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tasa de Impuesto"
        verbose_name_plural = "Tasas de Impuesto"
        unique_together = ['tax_configuration', 'tax_type', 'rate']
    
    def __str__(self):
        return f"{self.tax_type.upper()} - {self.rate}%"
    
    def applies_to_item(self, item_type, category=None):
        """Verifica si la tasa aplica a un item específico."""
        if item_type == 'product':
            if not self.applies_to_products:
                return False
            if self.product_categories and category not in self.product_categories:
                return False
        elif item_type == 'service':
            if not self.applies_to_services:
                return False
            if self.service_categories and category not in self.service_categories:
                return False
        
        return True
    
    def calculate_tax(self, base_amount):
        """Calcula el impuesto sobre un monto base."""
        return (base_amount * self.rate) / Decimal('100.00')

class TaxExemption(models.Model):
    """Exención de impuestos."""
    
    tax_configuration = models.ForeignKey(
        TaxConfiguration,
        on_delete=models.CASCADE,
        related_name='tax_exemptions'
    )
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre de la exención")
    description = models.TextField(help_text="Descripción de la exención")
    
    # Tipo de exención
    exemption_type = models.CharField(
        max_length=20,
        choices=[
            ('zero_rate', 'Tasa Cero'),
            ('exempt', 'Exento'),
            ('not_subject', 'No Sujeto'),
            ('other', 'Otro')
        ],
        help_text="Tipo de exención"
    )
    
    # Impuestos exentos
    exempt_iva = models.BooleanField(default=False, help_text="¿Exento de IVA?")
    exempt_isr = models.BooleanField(default=False, help_text="¿Exento de ISR?")
    exempt_ieps = models.BooleanField(default=False, help_text="¿Exento de IEPS?")
    
    # Aplicación
    applies_to_products = models.BooleanField(default=True, help_text="¿Aplica a productos?")
    applies_to_services = models.BooleanField(default=True, help_text="¿Aplica a servicios?")
    
    # Categorías específicas
    product_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Categorías de productos específicas"
    )
    service_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Categorías de servicios específicas"
    )
    
    # Documentación requerida
    required_documents = models.JSONField(
        default=list,
        blank=True,
        help_text="Documentos requeridos para la exención"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Exención activa?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Exención de Impuestos"
        verbose_name_plural = "Exenciones de Impuestos"
    
    def __str__(self):
        return f"{self.name} - {self.exemption_type}"
    
    def applies_to_item(self, item_type, category=None):
        """Verifica si la exención aplica a un item específico."""
        if item_type == 'product':
            if not self.applies_to_products:
                return False
            if self.product_categories and category not in self.product_categories:
                return False
        elif item_type == 'service':
            if not self.applies_to_services:
                return False
            if self.service_categories and category not in self.service_categories:
                return False
        
        return True
    
    def is_exempt_from_tax(self, tax_type):
        """Verifica si está exento de un impuesto específico."""
        if tax_type == 'iva':
            return self.exempt_iva
        elif tax_type == 'isr':
            return self.exempt_isr
        elif tax_type == 'ieps':
            return self.exempt_ieps
        return False 