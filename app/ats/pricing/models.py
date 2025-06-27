"""
Modelos unificados para pricing, pagos, facturación, gateways y integraciones.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import json
import uuid
from datetime import timedelta

from app.models import BusinessUnit, User, Person


# ============================================================================
# MODELOS DE PRICING (ya existentes)
# ============================================================================

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


# ============================================================================
# MODELOS DE FACTURACIÓN Y ÓRDENES (ya existentes en app/models.py)
# ============================================================================

class Invoice(models.Model):
    """Modelo para facturas (referencia al modelo principal)"""
    # Este modelo ya existe en app/models.py, aquí solo para referencia
    pass

class Order(models.Model):
    """Modelo para órdenes de servicio (referencia al modelo principal)"""
    # Este modelo ya existe en app/models.py, aquí solo para referencia
    pass

class LineItem(models.Model):
    """Modelo para conceptos de factura (referencia al modelo principal)"""
    # Este modelo ya existe en app/models.py, aquí solo para referencia
    pass


# ============================================================================
# MODELOS DE GATEWAYS Y PAGOS (migrados de payments)
# ============================================================================

class PaymentGateway(models.Model):
    """Modelo para configurar gateways de pago."""
    
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('conekta', 'Conekta'),
        ('mercadopago', 'MercadoPago'),
        ('openpay', 'OpenPay'),
        ('banorte', 'Banorte'),
        ('banamex', 'Banamex'),
        ('bbva', 'BBVA'),
        ('hsbc', 'HSBC'),
        ('santander', 'Santander'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('testing', 'Pruebas'),
        ('maintenance', 'Mantenimiento'),
    ]
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre del gateway")
    gateway_type = models.CharField(max_length=20, choices=GATEWAY_CHOICES, help_text="Tipo de gateway")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    
    # Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='payment_gateways')
    
    # Configuración de API
    api_key = models.CharField(max_length=500, blank=True, help_text="API Key del gateway")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API Secret del gateway")
    webhook_url = models.URLField(blank=True, help_text="URL del webhook")
    webhook_secret = models.CharField(max_length=500, blank=True, help_text="Secret del webhook")
    
    # Configuración específica
    config = models.JSONField(default=dict, help_text="Configuración específica del gateway")
    
    # Configuración de pagos
    supported_currencies = models.JSONField(default=list, help_text="Monedas soportadas")
    supported_payment_methods = models.JSONField(default=list, help_text="Métodos de pago soportados")
    processing_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Comisión por procesamiento (%)")
    processing_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Comisión fija por transacción")
    
    # Configuración de facturación electrónica
    pac_integration = models.BooleanField(default=False, help_text="¿Integrado con PAC para facturación electrónica?")
    pac_config = models.JSONField(default=dict, help_text="Configuración del PAC")
    
    # Metadatos
    description = models.TextField(blank=True, help_text="Descripción del gateway")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_gateways')

    class Meta:
        verbose_name = "Gateway de Pago"
        verbose_name_plural = "Gateways de Pago"
        ordering = ['name']
        indexes = [
            models.Index(fields=['gateway_type']),
            models.Index(fields=['status']),
            models.Index(fields=['business_unit']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_gateway_type_display()}"
    
    def get_config(self, key, default=None):
        """Obtiene un valor de configuración específica."""
        return self.config.get(key, default)
    
    def set_config(self, key, value):
        """Establece un valor de configuración específica."""
        self.config[key] = value
        self.save(update_fields=['config'])
    
    def is_available_for_currency(self, currency):
        """Verifica si el gateway soporta una moneda específica."""
        return currency in self.supported_currencies
    
    def is_available_for_payment_method(self, payment_method):
        """Verifica si el gateway soporta un método de pago específico."""
        return payment_method in self.supported_payment_methods
    
    def calculate_processing_fee(self, amount):
        """Calcula la comisión de procesamiento para un monto."""
        percentage_fee = amount * (self.processing_fee_percentage / 100)
        return percentage_fee + self.processing_fee_fixed


class BankAccount(models.Model):
    """Modelo para cuentas bancarias."""
    
    ACCOUNT_TYPE_CHOICES = [
        ('checking', 'Cuenta Corriente'),
        ('savings', 'Cuenta de Ahorro'),
        ('business', 'Cuenta Empresarial'),
        ('payroll', 'Cuenta de Nómina'),
    ]
    
    BANK_CHOICES = [
        ('banorte', 'Banorte'),
        ('banamex', 'Banamex'),
        ('bbva', 'BBVA'),
        ('hsbc', 'HSBC'),
        ('santander', 'Santander'),
        ('banco_azteca', 'Banco Azteca'),
        ('banregio', 'Banregio'),
        ('inbursa', 'Inbursa'),
        ('scotiabank', 'Scotiabank'),
        ('other', 'Otro'),
    ]
    
    # Información básica
    account_name = models.CharField(max_length=200, help_text="Nombre de la cuenta")
    account_number = models.CharField(max_length=50, help_text="Número de cuenta")
    clabe = models.CharField(max_length=18, blank=True, help_text="CLABE")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, help_text="Tipo de cuenta")
    bank = models.CharField(max_length=20, choices=BANK_CHOICES, help_text="Banco")
    
    # Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='bank_accounts')
    
    # Configuración
    is_active = models.BooleanField(default=True, help_text="¿La cuenta está activa?")
    is_primary = models.BooleanField(default=False, help_text="¿Es la cuenta principal?")
    
    # Metadatos
    description = models.TextField(blank=True, help_text="Descripción de la cuenta")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_bank_accounts')

    class Meta:
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
        ordering = ['-is_primary', 'account_name']
        indexes = [
            models.Index(fields=['bank']),
            models.Index(fields=['is_active']),
            models.Index(fields=['business_unit']),
        ]

    def __str__(self):
        return f"{self.account_name} - {self.get_bank_display()}"


class PaymentTransaction(models.Model):
    """Modelo para transacciones de pago."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Pago'),
        ('refund', 'Reembolso'),
        ('chargeback', 'Contracargo'),
        ('adjustment', 'Ajuste'),
        ('fee', 'Comisión'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('disputed', 'Disputado'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Tarjeta de Crédito'),
        ('debit_card', 'Tarjeta de Débito'),
        ('bank_transfer', 'Transferencia Bancaria'),
        ('cash', 'Efectivo'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('conekta', 'Conekta'),
        ('other', 'Otro'),
    ]
    
    # Información básica
    transaction_id = models.CharField(max_length=100, unique=True, help_text="ID único de la transacción")
    external_id = models.CharField(max_length=100, blank=True, help_text="ID externo del gateway")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, help_text="Tipo de transacción")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Relaciones
    invoice = models.ForeignKey('app.Invoice', on_delete=models.CASCADE, related_name='payment_transactions')
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Montos
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Monto de la transacción")
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Comisión de procesamiento")
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto neto")
    currency = models.CharField(max_length=3, default='MXN')
    
    # Método de pago
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, help_text="Método de pago")
    payment_details = models.JSONField(default=dict, help_text="Detalles del método de pago")
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True, help_text="Fecha de procesamiento")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="Fecha de completado")
    
    # Respuesta del gateway
    gateway_response = models.JSONField(default=dict, help_text="Respuesta del gateway")
    error_message = models.TextField(blank=True, help_text="Mensaje de error si falló")
    
    # Metadatos
    description = models.TextField(help_text="Descripción de la transacción")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')

    class Meta:
        verbose_name = "Transacción de Pago"
        verbose_name_plural = "Transacciones de Pago"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['external_id']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        """Genera ID de transacción si no existe."""
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        """Genera un nuevo ID de transacción."""
        return f"TXN-{uuid.uuid4().hex[:8].upper()}"
    
    def process_payment(self):
        """Procesa el pago."""
        if self.status == 'pending':
            self.status = 'processing'
            self.processed_at = timezone.now()
            self.save()
            return True
        return False
    
    def complete_payment(self):
        """Marca el pago como completado."""
        if self.status in ['pending', 'processing']:
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
    def refund(self, amount=None, reason=""):
        """Procesa un reembolso."""
        if amount is None:
            amount = self.amount
        
        if amount > self.amount:
            raise ValueError("El monto del reembolso no puede ser mayor al monto original")
        
        refund_transaction = PaymentTransaction.objects.create(
            transaction_type='refund',
            status='pending',
            amount=amount,
            currency=self.currency,
            payment_method=self.payment_method,
            description=f"Reembolso de {self.transaction_id}: {reason}",
            created_by=self.created_by
        )
        
        return refund_transaction


class PACConfiguration(models.Model):
    """Modelo para configuración de PAC (Proveedor Autorizado de Certificación)."""
    
    PAC_CHOICES = [
        ('facturama', 'Facturama'),
        ('solucion_factible', 'Solución Factible'),
        ('edicom', 'Edicom'),
        ('sw', 'SW'),
        ('finkok', 'Finkok'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('testing', 'Pruebas'),
    ]
    
    # Información básica
    name = models.CharField(max_length=100, help_text="Nombre del PAC")
    pac_type = models.CharField(max_length=20, choices=PAC_CHOICES, help_text="Tipo de PAC")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')
    
    # Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='pac_configurations')
    
    # Configuración de API
    api_url = models.URLField(help_text="URL de la API del PAC")
    api_key = models.CharField(max_length=500, blank=True, help_text="API Key del PAC")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API Secret del PAC")
    username = models.CharField(max_length=100, blank=True, help_text="Usuario del PAC")
    password = models.CharField(max_length=500, blank=True, help_text="Contraseña del PAC")
    
    # Configuración de certificados
    certificate_file = models.FileField(upload_to='certificates/', blank=True, help_text="Archivo del certificado (.cer)")
    key_file = models.FileField(upload_to='certificates/', blank=True, help_text="Archivo de la llave privada (.key)")
    certificate_password = models.CharField(max_length=500, blank=True, help_text="Contraseña del certificado")
    
    # Configuración específica
    config = models.JSONField(default=dict, help_text="Configuración específica del PAC")
    
    # Metadatos
    description = models.TextField(blank=True, help_text="Descripción del PAC")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_pac_configs')

    class Meta:
        verbose_name = "Configuración de PAC"
        verbose_name_plural = "Configuraciones de PAC"
        ordering = ['name']
        indexes = [
            models.Index(fields=['pac_type']),
            models.Index(fields=['status']),
            models.Index(fields=['business_unit']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_pac_type_display()}"
    
    def get_config(self, key, default=None):
        """Obtiene un valor de configuración específica."""
        return self.config.get(key, default)
    
    def set_config(self, key, value):
        """Establece un valor de configuración específica."""
        self.config[key] = value
        self.save(update_fields=['config'])
    
    def is_ready_for_stamping(self):
        """Verifica si el PAC está listo para timbrar."""
        return (
            self.status == 'active' and
            self.api_url and
            self.certificate_file and
            self.key_file
        )


# ============================================================================
# MODELOS MIGRADOS DEL MÓDULO ANTIGUO (app/ats/pagos)
# ============================================================================

class EstadoPerfil(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    INACTIVO = 'inactivo', 'Inactivo'
    SUSPENDIDO = 'suspendido', 'Suspendido'

class TipoDocumento(models.TextChoices):
    RFC = 'rfc', 'RFC'
    CURP = 'curp', 'CURP'
    DNI = 'dni', 'DNI'
    PASAPORTE = 'pasaporte', 'Pasaporte'

class Empleador(models.Model):
    """Modelo para empleadores (migrado del módulo antiguo)."""
    name = models.CharField(max_length=100, blank=True, null=True)
    persona = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='empleador')
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    
    # Información fiscal
    razon_social = models.CharField(max_length=255)
    rfc = models.CharField(max_length=13, unique=True)
    direccion_fiscal = models.TextField()
    
    # Información bancaria
    clabe = models.CharField(max_length=18, unique=True)
    banco = models.CharField(max_length=100)
    
    # Información de contacto
    img_company = models.CharField(max_length=500, blank=True, null=True)
    sitio_web = models.URLField(null=True, blank=True)
    telefono_oficina = models.CharField(max_length=20)
    address = models.CharField(max_length=200, blank=True, null=True)
    
    # Estado
    estado = models.CharField(max_length=20, choices=EstadoPerfil.choices, default=EstadoPerfil.ACTIVO)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Documentos
    documento_identidad = models.FileField(upload_to='empleadores/documentos/')
    comprobante_domicilio = models.FileField(upload_to='empleadores/documentos/')
    
    # Campos adicionales
    job_id = models.CharField(max_length=100, blank=True, null=True)
    url_name = models.CharField(max_length=100, blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    
    longitude = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    required_skills = models.TextField(blank=True, null=True)
    experience_required = models.IntegerField(blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, help_text="Información adicional del empleador")
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Empleador'
        verbose_name_plural = 'Empleadores'

    def __str__(self):
        return self.razon_social

    def validar_documentos(self):
        """Valida que todos los documentos requeridos estén presentes y sean válidos"""
        return True  # Implementación pendiente

class Empleado(models.Model):
    """Modelo para empleados (migrado del módulo antiguo)."""
    persona = models.OneToOneField(Person, on_delete=models.CASCADE, related_name='empleado')
    
    # Información laboral
    nss = models.CharField(max_length=11, unique=True, null=True, blank=True)
    ocupacion = models.CharField(max_length=100)
    experiencia_anios = models.IntegerField(default=0)
    
    # Información bancaria
    clabe = models.CharField(max_length=18, unique=True)
    banco = models.CharField(max_length=100)
    
    # Estado
    estado = models.CharField(max_length=20, choices=EstadoPerfil.choices, default=EstadoPerfil.ACTIVO)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Documentos
    documento_identidad = models.FileField(upload_to='empleados/documentos/')
    comprobante_domicilio = models.FileField(upload_to='empleados/documentos/')
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido_paterno}"

    def validar_documentos(self):
        """Valida que todos los documentos requeridos estén presentes y sean válidos"""
        return True  # Implementación pendiente

class Oportunidad(models.Model):
    """Modelo para oportunidades (migrado del módulo antiguo)."""
    empleador = models.ForeignKey(Empleador, on_delete=models.CASCADE, related_name='oportunidades')
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    
    # Detalles del trabajo
    tipo_contrato = models.CharField(max_length=50, choices=[
        ('tiempo_completo', 'Tiempo Completo'),
        ('medio_tiempo', 'Medio Tiempo'),
        ('freelance', 'Freelance'),
        ('proyecto', 'Por Proyecto')
    ])
    salario_minimo = models.DecimalField(max_digits=10, decimal_places=2)
    salario_maximo = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Ubicación
    pais = models.CharField(max_length=50)
    ciudad = models.CharField(max_length=100)
    modalidad = models.CharField(max_length=50, choices=[
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido')
    ])
    
    # Estado
    estado = models.CharField(max_length=20, choices=EstadoPerfil.choices, default=EstadoPerfil.ACTIVO)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Oportunidad'
        verbose_name_plural = 'Oportunidades'

    def __str__(self):
        return self.titulo

class PagoRecurrente(models.Model):
    """Modelo para pagos recurrentes (migrado del módulo antiguo)."""
    pago_base = models.OneToOneField('app.Pago', on_delete=models.CASCADE, related_name='recurrente')
    frecuencia = models.CharField(max_length=20, choices=[
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual')
    ])
    fecha_proximo_pago = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_proximo_pago']
        verbose_name = 'Pago Recurrente'
        verbose_name_plural = 'Pagos Recurrentes'

    def __str__(self):
        return f'Pago Recurrente #{self.pago_base.id}'

    def actualizar_proximo_pago(self):
        """Actualiza la fecha del próximo pago según la frecuencia."""
        if not self.activo:
            return
            
        from datetime import timedelta
        
        if self.frecuencia == 'diario':
            self.fecha_proximo_pago += timedelta(days=1)
        elif self.frecuencia == 'semanal':
            self.fecha_proximo_pago += timedelta(days=7)
        elif self.frecuencia == 'quincenal':
            self.fecha_proximo_pago += timedelta(days=15)
        elif self.frecuencia == 'mensual':
            self.fecha_proximo_pago += timedelta(days=30)
        elif self.frecuencia == 'anual':
            self.fecha_proximo_pago += timedelta(days=365)
        self.save()

# Modelos de sincronización con WordPress
class SincronizacionLog(models.Model):
    """Modelo para registrar logs de sincronización con WordPress."""
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En proceso'),
        ('EXITO', 'Éxito'),
        ('ERROR', 'Error')
    ]
    
    oportunidad = models.ForeignKey(
        Oportunidad,
        on_delete=models.CASCADE,
        related_name='sincronizaciones'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    detalle = models.JSONField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Log de Sincronización"
        verbose_name_plural = "Logs de Sincronización"
        
    def __str__(self):
        return f"{self.oportunidad} - {self.estado}"

class SincronizacionError(models.Model):
    """Modelo para registrar errores de sincronización con WordPress."""
    oportunidad = models.ForeignKey(
        Oportunidad,
        on_delete=models.CASCADE,
        related_name='errores_sincronizacion'
    )
    mensaje = models.TextField()
    intento = models.PositiveSmallIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    resuelto = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Error de Sincronización"
        verbose_name_plural = "Errores de Sincronización"
        
    def __str__(self):
        return f"{self.oportunidad} - {self.mensaje[:50]}..."

# ============================================================================
# MODELOS PARA CFDI EN 2 EXHIBICIONES
# ============================================================================

class CFDIExhibition(models.Model):
    """Modelo para manejar CFDI en 2 exhibiciones."""
    
    EXHIBITION_TYPES = [
        ('PUE', 'Pago en una sola exhibición'),
        ('PPD', 'Pago en parcialidades o diferido'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pendiente'),
        ('partial', 'Parcial'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Información básica
    invoice = models.ForeignKey('app.Invoice', on_delete=models.CASCADE, related_name='cfdi_exhibitions')
    exhibition_type = models.CharField(max_length=3, choices=EXHIBITION_TYPES, default='PUE')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Montos
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto total del CFDI")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto pagado hasta el momento")
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto pendiente por pagar")
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(help_text="Fecha límite de pago")
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Información de pagos parciales
    partial_payments = models.JSONField(default=list, help_text="Lista de pagos parciales")
    payment_schedule = models.JSONField(default=list, help_text="Cronograma de pagos")
    
    # Metadatos
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    class Meta:
        verbose_name = "CFDI en Exhibición"
        verbose_name_plural = "CFDIs en Exhibición"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"CFDI {self.invoice.invoice_number} - {self.get_exhibition_type_display()}"
    
    def save(self, *args, **kwargs):
        """Calcula automáticamente el monto restante."""
        if not self.remaining_amount:
            self.remaining_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)
    
    def add_partial_payment(self, amount: Decimal, payment_date=None, payment_method=None):
        """Agrega un pago parcial."""
        if payment_date is None:
            payment_date = timezone.now()
        
        payment_info = {
            'amount': str(amount),
            'date': payment_date.isoformat(),
            'method': payment_method or 'unknown',
            'transaction_id': f"PPD-{uuid.uuid4().hex[:8].upper()}"
        }
        
        self.partial_payments.append(payment_info)
        self.paid_amount += amount
        self.remaining_amount = self.total_amount - self.paid_amount
        
        # Actualizar estado de pago
        if self.remaining_amount <= 0:
            self.payment_status = 'completed'
            self.completed_at = timezone.now()
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        
        self.save()
        
        return payment_info
    
    def get_payment_schedule(self):
        """Obtiene el cronograma de pagos."""
        if not self.payment_schedule:
            # Generar cronograma automático si no existe
            self.generate_payment_schedule()
        return self.payment_schedule
    
    def generate_payment_schedule(self, num_payments=2, start_date=None):
        """Genera un cronograma de pagos automático."""
        if start_date is None:
            start_date = timezone.now()
        
        payment_amount = self.total_amount / num_payments
        schedule = []
        
        for i in range(num_payments):
            payment_date = start_date + timedelta(days=30 * (i + 1))  # Pagos mensuales
            schedule.append({
                'payment_number': i + 1,
                'amount': str(payment_amount),
                'due_date': payment_date.isoformat(),
                'status': 'pending'
            })
        
        self.payment_schedule = schedule
        self.save()
        
        return schedule


class PartialPayment(models.Model):
    """Modelo para pagos parciales de CFDI."""
    
    PAYMENT_METHODS = [
        ('cash', 'Efectivo'),
        ('bank_transfer', 'Transferencia bancaria'),
        ('credit_card', 'Tarjeta de crédito'),
        ('debit_card', 'Tarjeta de débito'),
        ('check', 'Cheque'),
        ('other', 'Otro'),
    ]
    
    # Relaciones
    cfdi_exhibition = models.ForeignKey(CFDIExhibition, on_delete=models.CASCADE, related_name='payments')
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Información del pago
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_date = models.DateTimeField(default=timezone.now)
    
    # Información de referencia
    reference_number = models.CharField(max_length=100, blank=True, help_text="Número de referencia del pago")
    notes = models.TextField(blank=True, help_text="Notas del pago")
    
    # Estado
    is_verified = models.BooleanField(default=False, help_text="¿El pago ha sido verificado?")
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pago Parcial"
        verbose_name_plural = "Pagos Parciales"
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Pago {self.amount} - {self.payment_date.strftime('%Y-%m-%d')}"
    
    def verify_payment(self, verified_by=None):
        """Marca el pago como verificado."""
        self.is_verified = True
        self.verified_at = timezone.now()
        if verified_by:
            self.verified_by = verified_by
        self.save()
        
        # Actualizar el CFDI exhibition
        self.cfdi_exhibition.add_partial_payment(
            self.amount, 
            self.payment_date, 
            self.payment_method
        )


# ============================================================================
# MODELOS PARA PAGOS PROGRAMADOS (SALIENTES)
# ============================================================================

class ScheduledPayment(models.Model):
    """Modelo para pagos programados salientes (renta, PAC, etc.)."""
    
    PAYMENT_TYPES = [
        ('rent', 'Renta'),
        ('utilities', 'Servicios'),
        ('insurance', 'Seguros'),
        ('taxes', 'Impuestos'),
        ('suppliers', 'Proveedores'),
        ('payroll', 'Nómina'),
        ('other', 'Otro'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('paused', 'Pausado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Completado'),
    ]
    
    # Información básica
    name = models.CharField(max_length=200, help_text="Nombre del pago programado")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='scheduled_payments')
    
    # Configuración de pago
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='MXN')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    custom_frequency_days = models.IntegerField(null=True, blank=True, help_text="Días para frecuencia personalizada")
    
    # Fechas
    start_date = models.DateTimeField(help_text="Fecha de inicio de los pagos")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de fin (opcional)")
    next_payment_date = models.DateTimeField(help_text="Próxima fecha de pago")
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    # Información del beneficiario
    beneficiary_name = models.CharField(max_length=200, help_text="Nombre del beneficiario")
    beneficiary_account = models.CharField(max_length=50, help_text="Cuenta del beneficiario")
    beneficiary_bank = models.CharField(max_length=100, help_text="Banco del beneficiario")
    beneficiary_clabe = models.CharField(max_length=18, blank=True, help_text="CLABE del beneficiario")
    
    # Cuenta de origen
    source_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='scheduled_payments_out')
    
    # Metadatos
    description = models.TextField(blank=True, help_text="Descripción del pago")
    reference = models.CharField(max_length=100, blank=True, help_text="Referencia del pago")
    
    # Control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_scheduled_payments')
    
    class Meta:
        verbose_name = "Pago Programado"
        verbose_name_plural = "Pagos Programados"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.amount} {self.currency}"
    
    def calculate_next_payment_date(self):
        """Calcula la próxima fecha de pago."""
        from datetime import timedelta
        
        if self.frequency == 'daily':
            return self.next_payment_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            return self.next_payment_date + timedelta(days=7)
        elif self.frequency == 'biweekly':
            return self.next_payment_date + timedelta(days=15)
        elif self.frequency == 'monthly':
            return self.next_payment_date + timedelta(days=30)
        elif self.frequency == 'quarterly':
            return self.next_payment_date + timedelta(days=90)
        elif self.frequency == 'yearly':
            return self.next_payment_date + timedelta(days=365)
        elif self.frequency == 'custom' and self.custom_frequency_days:
            return self.next_payment_date + timedelta(days=self.custom_frequency_days)
        else:
            return self.next_payment_date + timedelta(days=30)  # Default mensual
    
    def execute_payment(self):
        """Ejecuta el pago programado."""
        try:
            # Crear transacción de pago
            transaction = PaymentTransaction.objects.create(
                transaction_type='payment',
                status='pending',
                amount=self.amount,
                currency=self.currency,
                payment_method='bank_transfer',
                description=f"Pago programado: {self.name}",
                created_by=self.created_by
            )
            
            # Aquí se integraría con el servicio bancario para ejecutar la transferencia
            # Por ahora solo simulamos el éxito
            
            # Actualizar próxima fecha de pago
            self.next_payment_date = self.calculate_next_payment_date()
            
            # Verificar si debe terminar
            if self.end_date and self.next_payment_date > self.end_date:
                self.status = 'completed'
                self.is_active = False
            
            self.save()
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'next_payment_date': self.next_payment_date
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def pause_payment(self):
        """Pausa el pago programado."""
        self.status = 'paused'
        self.is_active = False
        self.save()
    
    def resume_payment(self):
        """Reanuda el pago programado."""
        self.status = 'active'
        self.is_active = True
        self.save()
    
    def cancel_payment(self):
        """Cancela el pago programado."""
        self.status = 'cancelled'
        self.is_active = False
        self.save()


class ScheduledPaymentExecution(models.Model):
    """Modelo para registrar las ejecuciones de pagos programados."""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Relaciones
    scheduled_payment = models.ForeignKey(ScheduledPayment, on_delete=models.CASCADE, related_name='executions')
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Información de la ejecución
    scheduled_date = models.DateTimeField(help_text="Fecha programada para la ejecución")
    executed_date = models.DateTimeField(null=True, blank=True, help_text="Fecha real de ejecución")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Resultado
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, help_text="Mensaje de error si falló")
    
    # Metadatos
    execution_log = models.JSONField(default=dict, help_text="Log de la ejecución")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ejecución de Pago Programado"
        verbose_name_plural = "Ejecuciones de Pagos Programados"
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Ejecución {self.scheduled_payment.name} - {self.scheduled_date.strftime('%Y-%m-%d')}"
    
    def execute(self):
        """Ejecuta el pago programado."""
        try:
            self.status = 'processing'
            self.save()
            
            # Ejecutar el pago
            result = self.scheduled_payment.execute_payment()
            
            if result.get('success'):
                self.status = 'completed'
                self.success = True
                self.executed_date = timezone.now()
                self.execution_log = result
            else:
                self.status = 'failed'
                self.success = False
                self.error_message = result.get('error', 'Error desconocido')
                self.execution_log = result
            
            self.save()
            
            return result
            
        except Exception as e:
            self.status = 'failed'
            self.success = False
            self.error_message = str(e)
            self.save()
            
            return {
                'success': False,
                'error': str(e)
            } 