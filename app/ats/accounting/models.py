"""
Modelos para el módulo de contabilidad.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

from app.models import BusinessUnit, User


class Account(models.Model):
    """Modelo para cuentas contables."""
    
    ACCOUNT_TYPE_CHOICES = [
        ('asset', 'Activo'),
        ('liability', 'Pasivo'),
        ('equity', 'Capital'),
        ('revenue', 'Ingreso'),
        ('expense', 'Gasto'),
    ]
    
    ACCOUNT_CATEGORY_CHOICES = [
        ('cash', 'Efectivo y Equivalentes'),
        ('accounts_receivable', 'Cuentas por Cobrar'),
        ('accounts_payable', 'Cuentas por Pagar'),
        ('sales', 'Ventas'),
        ('cost_of_sales', 'Costo de Ventas'),
        ('operating_expenses', 'Gastos Operativos'),
        ('taxes', 'Impuestos'),
        ('other', 'Otros'),
    ]
    
    # Información básica
    code = models.CharField(max_length=20, unique=True, help_text="Código de cuenta")
    name = models.CharField(max_length=200, help_text="Nombre de la cuenta")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, help_text="Tipo de cuenta")
    category = models.CharField(max_length=30, choices=ACCOUNT_CATEGORY_CHOICES, help_text="Categoría de cuenta")
    
    # Configuración
    is_active = models.BooleanField(default=True, help_text="¿La cuenta está activa?")
    requires_tax = models.BooleanField(default=False, help_text="¿Requiere manejo de impuestos?")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Tasa de impuesto por defecto")
    
    # Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='accounts')
    
    # Metadatos
    description = models.TextField(blank=True, help_text="Descripción de la cuenta")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_accounts')

    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['account_type']),
            models.Index(fields=['category']),
            models.Index(fields=['business_unit']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_balance(self, as_of_date=None):
        """Obtiene el balance de la cuenta hasta una fecha específica."""
        if as_of_date is None:
            as_of_date = timezone.now()
        
        transactions = self.transactions.filter(
            transaction_date__lte=as_of_date
        )
        
        balance = Decimal('0')
        for transaction in transactions:
            if transaction.debit_account == self:
                balance += transaction.amount
            elif transaction.credit_account == self:
                balance -= transaction.amount
        
        return balance
    
    def get_balance_as_of_today(self):
        """Obtiene el balance actual de la cuenta."""
        return self.get_balance()


class Transaction(models.Model):
    """Modelo para transacciones contables."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('sale', 'Venta'),
        ('purchase', 'Compra'),
        ('payment', 'Pago'),
        ('receipt', 'Cobro'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Transferencia'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('posted', 'Registrada'),
        ('cancelled', 'Cancelada'),
    ]
    
    # Información básica
    transaction_number = models.CharField(max_length=50, unique=True, help_text="Número de transacción")
    transaction_date = models.DateTimeField(default=timezone.now, help_text="Fecha de la transacción")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, help_text="Tipo de transacción")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Cuentas involucradas
    debit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='debit_transactions', help_text="Cuenta de débito")
    credit_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='credit_transactions', help_text="Cuenta de crédito")
    
    # Montos
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Monto de la transacción")
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto de impuestos")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Monto total")
    currency = models.CharField(max_length=3, default='MXN')
    
    # Referencias
    reference_number = models.CharField(max_length=100, blank=True, help_text="Número de referencia")
    reference_type = models.CharField(max_length=50, blank=True, help_text="Tipo de referencia")
    reference_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID de la referencia")
    
    # Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='transactions')
    
    # Metadatos
    description = models.TextField(help_text="Descripción de la transacción")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_transactions')
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Transacción Contable"
        verbose_name_plural = "Transacciones Contables"
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_number']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['business_unit']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.transaction_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Generar número de transacción si no existe
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        
        # Calcular total si no está establecido
        if not self.total_amount:
            self.total_amount = self.amount + self.tax_amount
        
        super().save(*args, **kwargs)
    
    def generate_transaction_number(self):
        """Genera un número de transacción único."""
        from datetime import datetime
        year = datetime.now().year
        month = datetime.now().month
        
        # Buscar el último número de transacción del mes
        last_transaction = Transaction.objects.filter(
            transaction_number__startswith=f"T{year}{month:02d}"
        ).order_by('-transaction_number').first()
        
        if last_transaction:
            try:
                last_number = int(last_transaction.transaction_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"T{year}{month:02d}{new_number:04d}"
    
    def post(self, posted_by_user):
        """Registra la transacción en el libro mayor."""
        if self.status != 'draft':
            raise ValueError("Solo se pueden registrar transacciones en borrador")
        
        self.status = 'posted'
        self.posted_by = posted_by_user
        self.posted_at = timezone.now()
        self.save(update_fields=['status', 'posted_by', 'posted_at'])
    
    def cancel(self, reason=""):
        """Cancela la transacción."""
        if self.status == 'posted':
            raise ValueError("No se pueden cancelar transacciones ya registradas")
        
        self.status = 'cancelled'
        self.notes = f"{self.notes}\n\nCancelada: {reason}"
        self.save(update_fields=['status', 'notes'])


class JournalEntry(models.Model):
    """Modelo para asientos contables (múltiples transacciones relacionadas)."""
    
    ENTRY_TYPE_CHOICES = [
        ('sale', 'Venta'),
        ('purchase', 'Compra'),
        ('payment', 'Pago'),
        ('receipt', 'Cobro'),
        ('adjustment', 'Ajuste'),
        ('closing', 'Cierre'),
        ('other', 'Otro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('posted', 'Registrado'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Información básica
    entry_number = models.CharField(max_length=50, unique=True, help_text="Número de asiento")
    entry_date = models.DateTimeField(default=timezone.now, help_text="Fecha del asiento")
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES, help_text="Tipo de asiento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='journal_entries')
    
    # Metadatos
    description = models.TextField(help_text="Descripción del asiento")
    reference = models.CharField(max_length=100, blank=True, help_text="Referencia externa")
    notes = models.TextField(blank=True, help_text="Notas adicionales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_journal_entries')
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_journal_entries')
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-entry_date']
        indexes = [
            models.Index(fields=['entry_number']),
            models.Index(fields=['entry_date']),
            models.Index(fields=['entry_type']),
            models.Index(fields=['status']),
            models.Index(fields=['business_unit']),
        ]

    def __str__(self):
        return f"{self.entry_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        # Generar número de asiento si no existe
        if not self.entry_number:
            self.entry_number = self.generate_entry_number()
        
        super().save(*args, **kwargs)
    
    def generate_entry_number(self):
        """Genera un número de asiento único."""
        from datetime import datetime
        year = datetime.now().year
        month = datetime.now().month
        
        # Buscar el último número de asiento del mes
        last_entry = JournalEntry.objects.filter(
            entry_number__startswith=f"A{year}{month:02d}"
        ).order_by('-entry_number').first()
        
        if last_entry:
            try:
                last_number = int(last_entry.entry_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"A{year}{month:02d}{new_number:04d}"
    
    def get_total_debits(self):
        """Obtiene el total de débitos del asiento."""
        return sum(transaction.amount for transaction in self.transactions.filter(debit_account__isnull=False))
    
    def get_total_credits(self):
        """Obtiene el total de créditos del asiento."""
        return sum(transaction.amount for transaction in self.transactions.filter(credit_account__isnull=False))
    
    def is_balanced(self):
        """Verifica si el asiento está balanceado."""
        return self.get_total_debits() == self.get_total_credits()
    
    def post(self, posted_by_user):
        """Registra el asiento en el libro mayor."""
        if self.status != 'draft':
            raise ValueError("Solo se pueden registrar asientos en borrador")
        
        if not self.is_balanced():
            raise ValueError("El asiento no está balanceado")
        
        # Registrar todas las transacciones del asiento
        for transaction in self.transactions.all():
            transaction.post(posted_by_user)
        
        self.status = 'posted'
        self.posted_by = posted_by_user
        self.posted_at = timezone.now()
        self.save(update_fields=['status', 'posted_by', 'posted_at'])


class FinancialReport(models.Model):
    """Modelo para reportes financieros."""
    
    REPORT_TYPE_CHOICES = [
        ('balance_sheet', 'Balance General'),
        ('income_statement', 'Estado de Resultados'),
        ('cash_flow', 'Estado de Flujo de Efectivo'),
        ('trial_balance', 'Balance de Comprobación'),
        ('general_ledger', 'Libro Mayor'),
        ('custom', 'Reporte Personalizado'),
    ]
    
    PERIOD_TYPE_CHOICES = [
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('yearly', 'Anual'),
        ('custom', 'Personalizado'),
    ]
    
    # Información básica
    name = models.CharField(max_length=200, help_text="Nombre del reporte")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, help_text="Tipo de reporte")
    period_type = models.CharField(max_length=20, choices=PERIOD_TYPE_CHOICES, help_text="Tipo de período")
    
    # Fechas
    start_date = models.DateTimeField(help_text="Fecha de inicio del período")
    end_date = models.DateTimeField(help_text="Fecha de fin del período")
    
    # Business Unit
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='financial_reports')
    
    # Configuración
    include_comparison = models.BooleanField(default=False, help_text="¿Incluir comparación con período anterior?")
    include_budget = models.BooleanField(default=False, help_text="¿Incluir comparación con presupuesto?")
    
    # Resultados
    report_data = models.JSONField(default=dict, help_text="Datos del reporte")
    generated_at = models.DateTimeField(null=True, blank=True, help_text="Fecha de generación")
    
    # Metadatos
    notes = models.TextField(blank=True, help_text="Notas del reporte")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_reports')
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports')

    class Meta:
        verbose_name = "Reporte Financiero"
        verbose_name_plural = "Reportes Financieros"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['business_unit']),
        ]

    def __str__(self):
        return f"{self.name} - {self.start_date.date()} a {self.end_date.date()}"
    
    def generate_report(self, generated_by_user):
        """Genera el reporte financiero."""
        if self.report_type == 'balance_sheet':
            self.generate_balance_sheet()
        elif self.report_type == 'income_statement':
            self.generate_income_statement()
        elif self.report_type == 'cash_flow':
            self.generate_cash_flow()
        elif self.report_type == 'trial_balance':
            self.generate_trial_balance()
        
        self.generated_at = timezone.now()
        self.generated_by = generated_by_user
        self.save(update_fields=['report_data', 'generated_at', 'generated_by'])
    
    def generate_balance_sheet(self):
        """Genera un balance general."""
        # Implementar lógica de balance general
        pass
    
    def generate_income_statement(self):
        """Genera un estado de resultados."""
        # Implementar lógica de estado de resultados
        pass
    
    def generate_cash_flow(self):
        """Genera un estado de flujo de efectivo."""
        # Implementar lógica de flujo de efectivo
        pass
    
    def generate_trial_balance(self):
        """Genera un balance de comprobación."""
        # Implementar lógica de balance de comprobación
        pass 