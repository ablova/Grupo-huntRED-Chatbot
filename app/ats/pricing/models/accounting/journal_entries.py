"""
📊 MODELOS DE ASIENTOS CONTABLES

Gestión de asientos contables y líneas de asiento.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

from app.models import BusinessUnit, Person
from .accounts import Account

class JournalEntryType(models.TextChoices):
    """Tipos de asiento contable."""
    GENERAL = 'general', 'Asiento General'
    SALES = 'sales', 'Venta'
    PURCHASE = 'purchase', 'Compra'
    PAYMENT = 'payment', 'Pago'
    RECEIPT = 'receipt', 'Cobro'
    ADJUSTMENT = 'adjustment', 'Ajuste'
    CLOSING = 'closing', 'Cierre'
    OPENING = 'opening', 'Apertura'
    TRANSFER = 'transfer', 'Traspaso'

class JournalEntry(models.Model):
    """Asiento contable."""
    
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.CASCADE,
        related_name='journal_entries'
    )
    
    # Información básica
    entry_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Número único del asiento"
    )
    date = models.DateField(help_text="Fecha del asiento")
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia del asiento"
    )
    description = models.TextField(help_text="Descripción del asiento")
    
    # Tipo y estado
    entry_type = models.CharField(
        max_length=20,
        choices=JournalEntryType.choices,
        default=JournalEntryType.GENERAL,
        help_text="Tipo de asiento contable"
    )
    
    # Estados
    is_posted = models.BooleanField(default=False, help_text="¿Asiento publicado?")
    is_reversed = models.BooleanField(default=False, help_text="¿Asiento revertido?")
    is_adjustment = models.BooleanField(default=False, help_text="¿Es un ajuste?")
    
    # Totales
    total_debits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de débitos"
    )
    total_credits = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total de créditos"
    )
    
    # Aprobación
    requires_approval = models.BooleanField(default=False, help_text="¿Requiere aprobación?")
    is_approved = models.BooleanField(default=False, help_text="¿Está aprobado?")
    approved_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_journal_entries'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_journal_entries'
    )
    
    class Meta:
        verbose_name = "Asiento Contable"
        verbose_name_plural = "Asientos Contables"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.entry_number} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        """Genera número de asiento automáticamente."""
        if not self.entry_number:
            self.entry_number = self._generate_entry_number()
        super().save(*args, **kwargs)
    
    def _generate_entry_number(self):
        """Genera número único de asiento."""
        prefix = f"JE{timezone.now().strftime('%Y%m')}"
        last_entry = JournalEntry.objects.filter(
            entry_number__startswith=prefix
        ).order_by('-entry_number').first()
        
        if last_entry:
            last_number = int(last_entry.entry_number[-4:])
            new_number = last_number + 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def calculate_totals(self):
        """Calcula totales de débitos y créditos."""
        totals = self.lines.aggregate(
            total_debits=models.Sum('debit_amount'),
            total_credits=models.Sum('credit_amount')
        )
        
        self.total_debits = totals['total_debits'] or Decimal('0.00')
        self.total_credits = totals['total_credits'] or Decimal('0.00')
        self.save(update_fields=['total_debits', 'total_credits'])
    
    def is_balanced(self):
        """Verifica si el asiento está balanceado."""
        return self.total_debits == self.total_credits
    
    def can_be_posted(self):
        """Verifica si el asiento puede ser publicado."""
        return (
            self.is_balanced() and
            not self.is_posted and
            (not self.requires_approval or self.is_approved)
        )
    
    def post(self, posted_by=None):
        """Publica el asiento contable."""
        if not self.can_be_posted():
            raise ValueError("El asiento no puede ser publicado")
        
        self.is_posted = True
        self.save(update_fields=['is_posted'])
        
        # Actualizar saldos de cuentas
        for line in self.lines.all():
            line.account.update_balance()
        
        # Crear entrada en libro mayor
        from .ledgers import GeneralLedger
        GeneralLedger.create_from_journal_entry(self)
    
    def reverse(self, reversed_by=None, reason=""):
        """Revierte el asiento contable."""
        if not self.is_posted:
            raise ValueError("Solo se pueden revertir asientos publicados")
        
        # Crear asiento de reversión
        reversal = JournalEntry.objects.create(
            business_unit=self.business_unit,
            date=timezone.now().date(),
            reference=f"REV-{self.entry_number}",
            description=f"Reversión: {self.description}",
            entry_type=JournalEntryType.ADJUSTMENT,
            is_reversed=True,
            created_by=reversed_by
        )
        
        # Crear líneas de reversión
        for line in self.lines.all():
            JournalEntryLine.objects.create(
                journal_entry=reversal,
                account=line.account,
                description=f"Reversión: {line.description}",
                debit_amount=line.credit_amount,
                credit_amount=line.debit_amount,
                reference=line.reference
            )
        
        # Marcar asiento original como revertido
        self.is_reversed = True
        self.save(update_fields=['is_reversed'])
        
        # Publicar reversión
        reversal.post(reversed_by)
        
        return reversal
    
    def approve(self, approved_by):
        """Aprueba el asiento contable."""
        if not self.requires_approval:
            raise ValueError("Este asiento no requiere aprobación")
        
        self.is_approved = True
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save(update_fields=['is_approved', 'approved_by', 'approved_at'])

class JournalEntryLine(models.Model):
    """Línea de asiento contable."""
    
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='journal_entry_lines'
    )
    
    # Información básica
    description = models.TextField(help_text="Descripción de la línea")
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Referencia de la línea"
    )
    
    # Montos
    debit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monto de débito"
    )
    credit_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monto de crédito"
    )
    
    # Información adicional
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monto de impuestos"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tasa de impuesto"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Línea de Asiento"
        verbose_name_plural = "Líneas de Asiento"
        ordering = ['id']
    
    def __str__(self):
        return f"{self.journal_entry.entry_number} - {self.account.name}"
    
    def save(self, *args, **kwargs):
        """Valida que solo tenga débito o crédito."""
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValueError("Una línea no puede tener débito y crédito simultáneamente")
        super().save(*args, **kwargs)
    
    def get_net_amount(self):
        """Obtiene el monto neto de la línea."""
        return self.debit_amount - self.credit_amount
    
    def get_total_amount(self):
        """Obtiene el monto total incluyendo impuestos."""
        return abs(self.get_net_amount()) + self.tax_amount 