"""
📊 MODELOS DE CUENTAS CONTABLES

Gestión completa del plan de cuentas y estructura contable.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit, Person

class AccountType(models.TextChoices):
    """Tipos de cuenta contable."""
    ASSET = 'asset', 'Activo'
    LIABILITY = 'liability', 'Pasivo'
    EQUITY = 'equity', 'Capital'
    REVENUE = 'revenue', 'Ingreso'
    EXPENSE = 'expense', 'Gasto'

class AccountCategory(models.TextChoices):
    """Categorías de cuenta contable."""
    # Activos
    CURRENT_ASSETS = 'current_assets', 'Activos Corrientes'
    FIXED_ASSETS = 'fixed_assets', 'Activos Fijos'
    INTANGIBLE_ASSETS = 'intangible_assets', 'Activos Intangibles'
    
    # Pasivos
    CURRENT_LIABILITIES = 'current_liabilities', 'Pasivos Corrientes'
    LONG_TERM_LIABILITIES = 'long_term_liabilities', 'Pasivos a Largo Plazo'
    
    # Capital
    PAID_IN_CAPITAL = 'paid_in_capital', 'Capital Pagado'
    RETAINED_EARNINGS = 'retained_earnings', 'Utilidades Retenidas'
    
    # Ingresos
    OPERATING_REVENUE = 'operating_revenue', 'Ingresos Operativos'
    NON_OPERATING_REVENUE = 'non_operating_revenue', 'Ingresos No Operativos'
    
    # Gastos
    OPERATING_EXPENSES = 'operating_expenses', 'Gastos Operativos'
    NON_OPERATING_EXPENSES = 'non_operating_expenses', 'Gastos No Operativos'

class ChartOfAccounts(models.Model):
    """Plan de cuentas contables."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='chart_of_accounts'
    )
    
    name = models.CharField(max_length=100, help_text="Nombre del plan de cuentas")
    description = models.TextField(blank=True, help_text="Descripción del plan de cuentas")
    
    # Configuración
    account_number_length = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(4), MaxValueValidator(10)],
        help_text="Longitud del número de cuenta"
    )
    
    # Estados
    is_active = models.BooleanField(default=True, help_text="¿Plan de cuentas activo?")
    is_default = models.BooleanField(default=False, help_text="¿Plan de cuentas por defecto?")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_charts_of_accounts'
    )
    
    class Meta:
        verbose_name = "Plan de Cuentas"
        verbose_name_plural = "Planes de Cuentas"
        unique_together = ['business_unit', 'name']
    
    def __str__(self):
        return f"{self.business_unit.name} - {self.name}"
    
    def get_root_accounts(self):
        """Obtiene las cuentas raíz (sin padre)."""
        return self.accounts.filter(parent__isnull=True).order_by('account_number')
    
    def get_account_tree(self):
        """Obtiene el árbol completo de cuentas."""
        return self.accounts.filter(parent__isnull=True).prefetch_related('children')

class Account(models.Model):
    """Cuenta contable individual."""
    
    chart_of_accounts = models.ForeignKey(
        ChartOfAccounts,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    
    # Información básica
    account_number = models.CharField(
        max_length=20,
        help_text="Número de cuenta contable"
    )
    name = models.CharField(max_length=200, help_text="Nombre de la cuenta")
    description = models.TextField(blank=True, help_text="Descripción de la cuenta")
    
    # Clasificación
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        help_text="Tipo de cuenta contable"
    )
    category = models.CharField(
        max_length=30,
        choices=AccountCategory.choices,
        help_text="Categoría de la cuenta"
    )
    
    # Jerarquía
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Cuenta padre"
    )
    level = models.PositiveIntegerField(default=0, help_text="Nivel en la jerarquía")
    
    # Configuración
    is_active = models.BooleanField(default=True, help_text="¿Cuenta activa?")
    is_detail = models.BooleanField(default=False, help_text="¿Cuenta de detalle?")
    requires_approval = models.BooleanField(default=False, help_text="¿Requiere aprobación?")
    
    # Saldos
    opening_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo de apertura"
    )
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo actual"
    )
    
    # Configuración fiscal
    tax_code = models.CharField(
        max_length=10,
        blank=True,
        help_text="Código fiscal para reportes"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tasa de impuesto aplicable"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_accounts'
    )
    
    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"
        unique_together = ['chart_of_accounts', 'account_number']
        ordering = ['account_number']
    
    def __str__(self):
        return f"{self.account_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        """Calcula el nivel automáticamente."""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        """Obtiene la ruta completa de la cuenta."""
        path = [self.account_number]
        current = self.parent
        while current:
            path.insert(0, current.account_number)
            current = current.parent
        return ' > '.join(path)
    
    def get_balance(self, as_of_date=None):
        """Obtiene el saldo de la cuenta hasta una fecha específica."""
        if not as_of_date:
            as_of_date = timezone.now().date()
        
        # Calcular saldo desde asientos contables
        from .journal_entries import JournalEntryLine
        
        debits = JournalEntryLine.objects.filter(
            account=self,
            journal_entry__date__lte=as_of_date,
            journal_entry__is_posted=True
        ).aggregate(total=models.Sum('debit_amount'))['total'] or Decimal('0.00')
        
        credits = JournalEntryLine.objects.filter(
            account=self,
            journal_entry__date__lte=as_of_date,
            journal_entry__is_posted=True
        ).aggregate(total=models.Sum('credit_amount'))['total'] or Decimal('0.00')
        
        # Calcular saldo según tipo de cuenta
        if self.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            return self.opening_balance + debits - credits
        else:
            return self.opening_balance + credits - debits
    
    def update_balance(self):
        """Actualiza el saldo actual de la cuenta."""
        self.current_balance = self.get_balance()
        self.save(update_fields=['current_balance'])
    
    def get_children_balances(self):
        """Obtiene saldos de cuentas hijas."""
        if not self.children.exists():
            return Decimal('0.00')
        
        total = Decimal('0.00')
        for child in self.children.all():
            total += child.get_balance()
        return total
    
    def is_balanced(self):
        """Verifica si la cuenta está balanceada."""
        if self.children.exists():
            return self.get_balance() == self.get_children_balances()
        return True
    
    def can_be_deleted(self):
        """Verifica si la cuenta puede ser eliminada."""
        # No puede tener asientos contables
        from .journal_entries import JournalEntryLine
        has_entries = JournalEntryLine.objects.filter(account=self).exists()
        
        # No puede tener cuentas hijas
        has_children = self.children.exists()
        
        return not (has_entries or has_children) 