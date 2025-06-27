"""
📊 MODELOS DE LIBROS MAYORES

Gestión de libros mayores y entradas de libro mayor.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit
from .accounts import Account
from .journal_entries import JournalEntry

class GeneralLedger(models.Model):
    """Libro mayor general."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='general_ledgers'
    )
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='general_ledger_entries'
    )
    
    # Información de la entrada
    date = models.DateField(help_text="Fecha de la entrada")
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    
    # Descripción
    description = models.TextField(help_text="Descripción de la entrada")
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia de la entrada"
    )
    
    # Montos
    debit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de débito"
    )
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de crédito"
    )
    
    # Saldos acumulados
    running_debit_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo acumulado de débitos"
    )
    running_credit_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo acumulado de créditos"
    )
    running_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo acumulado neto"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Entrada de Libro Mayor"
        verbose_name_plural = "Entradas de Libro Mayor"
        ordering = ['account', 'date', 'created_at']
        unique_together = ['account', 'journal_entry']
    
    def __str__(self):
        return f"{self.account.account_number} - {self.date} - {self.description[:30]}"
    
    @classmethod
    def create_from_journal_entry(cls, journal_entry):
        """Crea entradas de libro mayor desde un asiento contable."""
        for line in journal_entry.lines.all():
            # Obtener último saldo de la cuenta
            last_entry = cls.objects.filter(
                account=line.account
            ).order_by('-date', '-created_at').first()
            
            if last_entry:
                running_debit = last_entry.running_debit_balance
                running_credit = last_entry.running_credit_balance
                running_balance = last_entry.running_balance
            else:
                running_debit = Decimal('0.00')
                running_credit = Decimal('0.00')
                running_balance = line.account.opening_balance
            
            # Calcular nuevos saldos acumulados
            new_running_debit = running_debit + line.debit_amount
            new_running_credit = running_credit + line.credit_amount
            
            # Calcular saldo neto según tipo de cuenta
            if line.account.account_type in ['asset', 'expense']:
                new_running_balance = running_balance + line.debit_amount - line.credit_amount
            else:
                new_running_balance = running_balance + line.credit_amount - line.debit_amount
            
            # Crear entrada de libro mayor
            cls.objects.create(
                business_unit=journal_entry.business_unit,
                account=line.account,
                date=journal_entry.date,
                journal_entry=journal_entry,
                description=line.description,
                reference=line.reference,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                running_debit_balance=new_running_debit,
                running_credit_balance=new_running_credit,
                running_balance=new_running_balance
            )
    
    def get_balance_as_of_date(self, as_of_date):
        """Obtiene el saldo de la cuenta hasta una fecha específica."""
        last_entry = self.__class__.objects.filter(
            account=self.account,
            date__lte=as_of_date
        ).order_by('-date', '-created_at').first()
        
        if last_entry:
            return last_entry.running_balance
        else:
            return self.account.opening_balance

class SubsidiaryLedger(models.Model):
    """Libro mayor auxiliar."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='subsidiary_ledgers'
    )
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='subsidiary_ledger_entries'
    )
    
    # Entidad relacionada (cliente, proveedor, etc.)
    related_entity_type = models.CharField(
        max_length=50,
        help_text="Tipo de entidad relacionada"
    )
    related_entity_id = models.PositiveIntegerField(
        help_text="ID de la entidad relacionada"
    )
    related_entity_name = models.CharField(
        max_length=200,
        help_text="Nombre de la entidad relacionada"
    )
    
    # Información de la entrada
    date = models.DateField(help_text="Fecha de la entrada")
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='subsidiary_ledger_entries'
    )
    
    # Descripción
    description = models.TextField(help_text="Descripción de la entrada")
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia de la entrada"
    )
    
    # Montos
    debit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de débito"
    )
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de crédito"
    )
    
    # Saldos acumulados
    running_debit_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo acumulado de débitos"
    )
    running_credit_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo acumulado de créditos"
    )
    running_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo acumulado neto"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Entrada de Libro Auxiliar"
        verbose_name_plural = "Entradas de Libro Auxiliar"
        ordering = ['account', 'related_entity_name', 'date', 'created_at']
        unique_together = ['account', 'journal_entry']
    
    def __str__(self):
        return f"{self.account.account_number} - {self.related_entity_name} - {self.date}"
    
    @classmethod
    def create_from_journal_entry(cls, journal_entry, entity_type, entity_id, entity_name):
        """Crea entradas de libro auxiliar desde un asiento contable."""
        for line in journal_entry.lines.all():
            # Solo crear para cuentas que requieren libro auxiliar
            if not line.account.is_detail:
                continue
            
            # Obtener último saldo de la entidad
            last_entry = cls.objects.filter(
                account=line.account,
                related_entity_type=entity_type,
                related_entity_id=entity_id
            ).order_by('-date', '-created_at').first()
            
            if last_entry:
                running_debit = last_entry.running_debit_balance
                running_credit = last_entry.running_credit_balance
                running_balance = last_entry.running_balance
            else:
                running_debit = Decimal('0.00')
                running_credit = Decimal('0.00')
                running_balance = Decimal('0.00')
            
            # Calcular nuevos saldos acumulados
            new_running_debit = running_debit + line.debit_amount
            new_running_credit = running_credit + line.credit_amount
            
            # Calcular saldo neto según tipo de cuenta
            if line.account.account_type in ['asset', 'expense']:
                new_running_balance = running_balance + line.debit_amount - line.credit_amount
            else:
                new_running_balance = running_balance + line.credit_amount - line.debit_amount
            
            # Crear entrada de libro auxiliar
            cls.objects.create(
                business_unit=journal_entry.business_unit,
                account=line.account,
                related_entity_type=entity_type,
                related_entity_id=entity_id,
                related_entity_name=entity_name,
                date=journal_entry.date,
                journal_entry=journal_entry,
                description=line.description,
                reference=line.reference,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                running_debit_balance=new_running_debit,
                running_credit_balance=new_running_credit,
                running_balance=new_running_balance
            )

class LedgerEntry(models.Model):
    """Entrada genérica de libro mayor."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='ledger_entries'
    )
    
    # Información de la entrada
    date = models.DateField(help_text="Fecha de la entrada")
    entry_type = models.CharField(
        max_length=20,
        help_text="Tipo de entrada"
    )
    
    # Descripción
    description = models.TextField(help_text="Descripción de la entrada")
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia de la entrada"
    )
    
    # Montos
    debit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de débito"
    )
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de crédito"
    )
    
    # Saldo
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Saldo después de la entrada"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Entrada de Libro"
        verbose_name_plural = "Entradas de Libro"
        ordering = ['account', 'date', 'created_at']
    
    def __str__(self):
        return f"{self.account.account_number} - {self.date} - {self.description[:30]}" 