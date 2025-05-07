from django.db import models
from django.utils import timezone
from app.models import Person, Vacante

class EstadoPago(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    COMPLETADO = 'completado', 'Completado'
    FALLIDO = 'fallido', 'Fallido'
    RECHAZADO = 'rechazado', 'Rechazado'
    EN_PROCESO = 'en_proceso', 'En Proceso'

class TipoPago(models.TextChoices):
    MONOEDO = 'monoedo', 'Pago Simple'
    MULTIEDO = 'multiedo', 'Pago Múltiple'
    RECURRENTE = 'recurrente', 'Pago Recurrente'

class MetodoPago(models.TextChoices):
    PAYPAL = 'paypal', 'PayPal'
    STRIPE = 'stripe', 'Stripe'
    MERCADOPAGO = 'mercadopago', 'MercadoPago'
    TRANSFERENCIA = 'transferencia', 'Transferencia Bancaria'

class Pago(models.Model):
    empleado = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='pagos_recibidos')
    empleador = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='pagos_enviados')
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='pagos')
    
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default='USD')
    metodo = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.PAYPAL)
    tipo = models.CharField(max_length=20, choices=TipoPago.choices, default=TipoPago.MONOEDO)
    
    estado = models.CharField(max_length=20, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)
    intentos = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Información del gateway
    id_transaccion = models.CharField(max_length=255, null=True, blank=True)
    url_webhook = models.URLField(null=True, blank=True)
    
    # Información adicional
    descripcion = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago #{self.id} - {self.empleado} ({self.monto} {self.moneda})"

    def marcar_como_completado(self, transaccion_id=None):
        self.estado = EstadoPago.COMPLETADO
        self.id_transaccion = transaccion_id
        self.save()

    def marcar_como_fallido(self, motivo=None):
        self.estado = EstadoPago.FALLIDO
        self.metadata['motivo_fallo'] = motivo
        self.save()

class PagoRecurrente(models.Model):
    pago_base = models.OneToOneField(Pago, on_delete=models.CASCADE, related_name='recurrente')
    frecuencia = models.CharField(max_length=20, choices=[
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('anual', 'Anual')
    ])
    fecha_proximo_pago = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Pago Recurrente'
        verbose_name_plural = 'Pagos Recurrentes'

    def __str__(self):
        return f"{self.pago_base} - {self.frecuencia}"

    def actualizar_proximo_pago(self):
        # Lógica para calcular la próxima fecha de pago
        pass

class PagoHistorico(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='historico')
    estado_anterior = models.CharField(max_length=20, choices=EstadoPago.choices)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-fecha_cambio']
        verbose_name = 'Historial de Pago'
        verbose_name_plural = 'Historial de Pagos'

    def __str__(self):
        return f"{self.pago} - {self.estado_anterior} -> {self.pago.estado}"
