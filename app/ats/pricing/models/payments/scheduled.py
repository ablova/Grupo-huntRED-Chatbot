"""
Modelos para pagos programados.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from datetime import datetime, timedelta

from app.models import BusinessUnit, Person, PaymentTransaction


class ScheduledPayment(models.Model):
    """Pago programado para ejecutarse automáticamente."""
    
    PAYMENT_TYPES = [
        ('rent', 'Renta'),
        ('utilities', 'Servicios'),
        ('insurance', 'Seguros'),
        ('taxes', 'Impuestos'),
        ('salary', 'Nómina'),
        ('supplier', 'Proveedores'),
        ('loan', 'Préstamo'),
        ('subscription', 'Suscripción'),
        ('other', 'Otro'),
    ]
    
    FREQUENCIES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('biweekly', 'Quincenal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('semiannual', 'Semestral'),
        ('annual', 'Anual'),
        ('custom', 'Personalizado'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('paused', 'Pausado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Nombre del pago programado")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Configuración de pago
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='MXN')
    frequency = models.CharField(max_length=20, choices=FREQUENCIES)
    custom_frequency_days = models.IntegerField(null=True, blank=True, help_text="Días para frecuencia personalizada")
    
    # Fechas
    start_date = models.DateTimeField(help_text="Fecha de inicio del pago programado")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Fecha de fin (opcional)")
    next_payment_date = models.DateTimeField(help_text="Próxima fecha de pago")
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_active = models.BooleanField(default=True)
    
    # Beneficiario
    beneficiary_name = models.CharField(max_length=200, help_text="Nombre del beneficiario")
    beneficiary_account = models.CharField(max_length=50, blank=True, null=True, help_text="Número de cuenta del beneficiario")
    beneficiary_bank = models.CharField(max_length=100, blank=True, null=True, help_text="Banco del beneficiario")
    beneficiary_clabe = models.CharField(max_length=18, blank=True, null=True, help_text="CLABE del beneficiario")
    
    # Cuenta de origen
    source_account = models.ForeignKey('BankAccount', on_delete=models.CASCADE, null=True, blank=True)
    
    # Metadatos
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True, help_text="Referencia del pago")
    
    # Control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'pricing_scheduled_payment'
        verbose_name = 'Pago Programado'
        verbose_name_plural = 'Pagos Programados'
        ordering = ['next_payment_date']
    
    def __str__(self):
        return f"{self.name} - {self.amount} {self.currency} - {self.frequency}"
    
    def calculate_next_payment_date(self):
        """Calcula la próxima fecha de pago basada en la frecuencia."""
        if not self.next_payment_date:
            base_date = self.start_date
        else:
            base_date = self.next_payment_date
        
        if self.frequency == 'daily':
            return base_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            return base_date + timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            return base_date + timedelta(weeks=2)
        elif self.frequency == 'monthly':
            # Aproximación simple para meses
            return base_date + timedelta(days=30)
        elif self.frequency == 'quarterly':
            return base_date + timedelta(days=90)
        elif self.frequency == 'semiannual':
            return base_date + timedelta(days=180)
        elif self.frequency == 'annual':
            return base_date + timedelta(days=365)
        elif self.frequency == 'custom' and self.custom_frequency_days:
            return base_date + timedelta(days=self.custom_frequency_days)
        else:
            return base_date + timedelta(days=30)  # Default mensual
    
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
    
    def complete_payment(self):
        """Marca el pago programado como completado."""
        self.status = 'completed'
        self.is_active = False
        self.save()
    
    def is_due(self):
        """Verifica si el pago está vencido."""
        return self.next_payment_date and timezone.now() >= self.next_payment_date
    
    def get_execution_history(self):
        """Obtiene el historial de ejecuciones."""
        return self.executions.all().order_by('-scheduled_date')
    
    def get_total_executed_amount(self):
        """Obtiene el monto total ejecutado."""
        return self.executions.filter(success=True).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
    
    def get_success_rate(self):
        """Obtiene la tasa de éxito de las ejecuciones."""
        total_executions = self.executions.count()
        if total_executions == 0:
            return 0
        
        successful_executions = self.executions.filter(success=True).count()
        return (successful_executions / total_executions) * 100


class ScheduledPaymentExecution(models.Model):
    """Ejecución de un pago programado."""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scheduled_payment = models.ForeignKey(ScheduledPayment, on_delete=models.CASCADE, related_name='executions')
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    success = models.BooleanField(default=False)
    
    # Monto
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Fechas
    scheduled_date = models.DateTimeField(help_text="Fecha programada para la ejecución")
    executed_date = models.DateTimeField(null=True, blank=True, help_text="Fecha real de ejecución")
    
    # Resultado
    error_message = models.TextField(blank=True, help_text="Mensaje de error si falló")
    execution_log = models.JSONField(default=dict, help_text="Log completo de la ejecución")
    
    # Control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pricing_scheduled_payment_execution'
        verbose_name = 'Ejecución de Pago Programado'
        verbose_name_plural = 'Ejecuciones de Pagos Programados'
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['scheduled_payment', 'status'], name='pricing_sched_pay_stat_idx'),
            models.Index(fields=['scheduled_date'], name='pricing_sched_pay_date_idx'),
            models.Index(fields=['success'], name='pricing_sched_pay_succ_idx'),
        ]
    
    def __str__(self):
        return f"Ejecución {self.scheduled_payment.name} - {self.scheduled_date.strftime('%Y-%m-%d')}"
    
    def mark_as_processing(self):
        """Marca la ejecución como procesando."""
        self.status = 'processing'
        self.save()
    
    def mark_as_completed(self, transaction=None):
        """Marca la ejecución como completada."""
        self.status = 'completed'
        self.success = True
        self.executed_date = timezone.now()
        if transaction:
            self.transaction = transaction
        self.save()
    
    def mark_as_failed(self, error_message):
        """Marca la ejecución como fallida."""
        self.status = 'failed'
        self.success = False
        self.executed_date = timezone.now()
        self.error_message = error_message
        self.save()
    
    def cancel_execution(self):
        """Cancela la ejecución."""
        self.status = 'cancelled'
        self.save()
    
    def get_execution_details(self):
        """Obtiene detalles de la ejecución."""
        return {
            'id': str(self.id),
            'scheduled_payment': self.scheduled_payment.name,
            'amount': float(self.amount),
            'status': self.status,
            'success': self.success,
            'scheduled_date': self.scheduled_date.isoformat(),
            'executed_date': self.executed_date.isoformat() if self.executed_date else None,
            'error_message': self.error_message,
            'execution_log': self.execution_log,
        } 