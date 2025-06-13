from django.db import models
from decimal import Decimal
from typing import Dict, Any

class PricingStrategy(models.Model):
    """Modelo para estrategias de precios"""
    
    STRATEGY_TYPES = [
        ('premium', 'Premium'),
        ('competitive', 'Competitivo'),
        ('value', 'Basado en valor')
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('active', 'Activo'),
        ('inactive', 'Inactivo')
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=STRATEGY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    pricing_model = models.JSONField(default=dict)
    discount_rules = models.ManyToManyField('DiscountRule', blank=True)
    referral_fees = models.ManyToManyField('ReferralFee', blank=True)
    conditions = models.JSONField(default=dict)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    revenue_impact = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Estrategia de Precios'
        verbose_name_plural = 'Estrategias de Precios'
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class PricePoint(models.Model):
    """Modelo para puntos de precio"""
    
    strategy = models.ForeignKey('PricingStrategy', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    conditions = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-valid_from']
    
    def __str__(self):
        return f"{self.amount} {self.currency} ({self.valid_from})"

class DiscountRule(models.Model):
    """Modelo para reglas de descuento"""
    
    DISCOUNT_TYPES = [
        ('percentage', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
        ('volume', 'Por volumen'),
        ('loyalty', 'Por lealtad')
    ]
    
    type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    conditions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-valid_from']
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"

class ReferralFee(models.Model):
    """Modelo para comisiones por referidos"""
    
    FEE_TYPES = [
        ('percentage', 'Porcentaje'),
        ('fixed', 'Monto fijo'),
        ('tiered', 'Por niveles')
    ]
    
    type = models.CharField(max_length=20, choices=FEE_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    conditions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-valid_from']
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.value}" 