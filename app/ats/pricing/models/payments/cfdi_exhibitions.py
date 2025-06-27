"""
Modelos para CFDI en exhibiciones (PUE y PPD).
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

from app.models import BusinessUnit


class CFDIExhibition(models.Model):
    """CFDI en exhibiciones para pagos parciales o diferidos."""
    
    EXHIBITION_TYPES = [
        ('PUE', 'Pago en una sola exhibición'),
        ('PPD', 'Pago en parcialidades o diferido'),
    ]
    
    PAYMENT_STATUSES = [
        ('pending', 'Pendiente'),
        ('partial', 'Parcialmente pagado'),
        ('completed', 'Completamente pagado'),
        ('overdue', 'Vencido'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey('app.Invoice', on_delete=models.CASCADE, related_name='cfdi_exhibitions')
    exhibition_type = models.CharField(max_length=3, choices=EXHIBITION_TYPES, default='PUE')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default='pending')
    
    # Montos
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(help_text="Fecha de vencimiento del pago")
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Cronograma de pagos (para PPD)
    payment_schedule = models.JSONField(default=list, help_text="Cronograma de pagos parciales")
    
    # Pagos parciales
    partial_payments = models.ManyToManyField('PartialPayment', blank=True, related_name='cfdi_exhibitions')
    
    # Notas
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'pricing_cfdi_exhibition'
        verbose_name = 'CFDI en Exhibición'
        verbose_name_plural = 'CFDIs en Exhibición'
    
    def __str__(self):
        return f"CFDI {self.invoice.invoice_number} - {self.exhibition_type} - {self.payment_status}"
    
    def save(self, *args, **kwargs):
        # Calcular monto restante
        self.remaining_amount = self.total_amount - self.paid_amount
        
        # Actualizar estado de pago
        if self.remaining_amount <= 0:
            self.payment_status = 'completed'
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        elif self.due_date and timezone.now() > self.due_date:
            self.payment_status = 'overdue'
        
        super().save(*args, **kwargs)
    
    def add_partial_payment(self, amount, payment_method, reference_number=None, notes=None):
        """Agrega un pago parcial."""
        partial_payment = PartialPayment.objects.create(
            cfdi_exhibition=self,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes
        )
        
        # Actualizar montos
        self.paid_amount += amount
        self.save()
        
        # Agregar a la relación many-to-many
        self.partial_payments.add(partial_payment)
        
        return partial_payment
    
    def get_payment_progress(self):
        """Obtiene el progreso del pago en porcentaje."""
        if self.total_amount > 0:
            return (self.paid_amount / self.total_amount) * 100
        return 0
    
    def is_overdue(self):
        """Verifica si el pago está vencido."""
        return self.due_date and timezone.now() > self.due_date and self.payment_status != 'completed'


class PartialPayment(models.Model):
    """Pago parcial para CFDI en exhibiciones."""
    
    PAYMENT_METHODS = [
        ('credit_card', 'Tarjeta de Crédito'),
        ('debit_card', 'Tarjeta de Débito'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Transferencia Bancaria'),
        ('cash', 'Efectivo'),
        ('check', 'Cheque'),
        ('other', 'Otro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cfdi_exhibition = models.ForeignKey(CFDIExhibition, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    # Información de referencia
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Número de referencia del pago")
    transaction_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID de la transacción")
    
    # Estado
    is_verified = models.BooleanField(default=False, help_text="¿El pago ha sido verificado?")
    
    # Fechas
    payment_date = models.DateTimeField(default=timezone.now, help_text="Fecha del pago")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notas
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'pricing_partial_payment'
        verbose_name = 'Pago Parcial'
        verbose_name_plural = 'Pagos Parciales'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Pago {self.amount} - {self.payment_method} - {self.payment_date.strftime('%Y-%m-%d')}"
    
    def verify_payment(self):
        """Marca el pago como verificado."""
        self.is_verified = True
        self.save()
    
    def get_payment_details(self):
        """Obtiene detalles del pago."""
        return {
            'id': str(self.id),
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'transaction_id': self.transaction_id,
            'is_verified': self.is_verified,
            'payment_date': self.payment_date.isoformat(),
            'notes': self.notes,
        } 