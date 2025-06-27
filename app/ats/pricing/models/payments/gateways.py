"""
Modelos para gateways de pago y transacciones.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
import json

from app.models import BusinessUnit, Person


class PaymentGateway(models.Model):
    """Gateway de pago configurado para un business unit."""
    
    GATEWAY_TYPES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('conekta', 'Conekta'),
        ('clip', 'Clip'),
        ('banorte', 'Banorte'),
        ('banamex', 'Banamex'),
        ('bbva', 'BBVA'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('testing', 'Pruebas'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Nombre del gateway")
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Configuración API
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    webhook_url = models.URLField(blank=True, null=True)
    webhook_secret = models.CharField(max_length=255, blank=True, null=True)
    
    # Configuración de pagos
    supported_currencies = models.JSONField(default=list, help_text="Monedas soportadas")
    supported_payment_methods = models.JSONField(default=list, help_text="Métodos de pago soportados")
    processing_fee_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        help_text="Comisión porcentual del gateway"
    )
    processing_fee_fixed = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00'),
        help_text="Comisión fija del gateway"
    )
    
    # Integración PAC
    pac_integration = models.BooleanField(default=False, help_text="¿Integra con PAC?")
    pac_config = models.ForeignKey('PACConfiguration', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Configuración específica
    config = models.JSONField(default=dict, help_text="Configuración específica del gateway")
    
    # Metadatos
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_payment_gateway'
        verbose_name = 'Gateway de Pago'
        verbose_name_plural = 'Gateways de Pago'
        unique_together = ['business_unit', 'gateway_type']
    
    def __str__(self):
        return f"{self.name} ({self.gateway_type}) - {self.business_unit.name}"
    
    def get_processing_fee(self, amount):
        """Calcula la comisión de procesamiento para un monto."""
        percentage_fee = amount * (self.processing_fee_percentage / Decimal('100'))
        return percentage_fee + self.processing_fee_fixed


class BankAccount(models.Model):
    """Cuenta bancaria para pagos."""
    
    ACCOUNT_TYPES = [
        ('checking', 'Cuenta Corriente'),
        ('savings', 'Cuenta de Ahorro'),
        ('business', 'Cuenta Empresarial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_name = models.CharField(max_length=100, help_text="Nombre de la cuenta")
    bank = models.CharField(max_length=100, help_text="Nombre del banco")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    clabe = models.CharField(max_length=18, blank=True, null=True, help_text="CLABE bancaria")
    routing_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Estado
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text="¿Es la cuenta principal?")
    
    # Relaciones
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    owner = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_bank_account'
        verbose_name = 'Cuenta Bancaria'
        verbose_name_plural = 'Cuentas Bancarias'
    
    def __str__(self):
        return f"{self.account_name} - {self.bank}"


class PACConfiguration(models.Model):
    """Configuración de Proveedor Autorizado de Certificación (PAC)."""
    
    PAC_TYPES = [
        ('finkok', 'Finkok'),
        ('edicom', 'EDICOM'),
        ('solucionfactible', 'Solución Factible'),
        ('sw', 'SW'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('testing', 'Pruebas'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Nombre de la configuración PAC")
    pac_type = models.CharField(max_length=20, choices=PAC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Configuración API
    api_url = models.URLField(help_text="URL de la API del PAC")
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    
    # Certificados
    certificate_file = models.FileField(upload_to='pac_certificates/', blank=True, null=True)
    private_key_file = models.FileField(upload_to='pac_private_keys/', blank=True, null=True)
    certificate_password = models.CharField(max_length=255, blank=True, null=True)
    
    # Configuración específica
    config = models.JSONField(default=dict, help_text="Configuración específica del PAC")
    
    # Metadatos
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_pac_configuration'
        verbose_name = 'Configuración PAC'
        verbose_name_plural = 'Configuraciones PAC'
    
    def __str__(self):
        return f"{self.name} ({self.pac_type}) - {self.business_unit.name}" 