from django.db import models
from django.utils import timezone
from datetime import timedelta
from .empleador import Person, Vacante

class EstadoPago(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    COMPLETADO = 'completado', 'Completado'
    FALLIDO = 'fallido', 'Fallido'
    RECHAZADO = 'rechazado', 'Rechazado'
    EN_PROCESO = 'en_proceso', 'En Proceso'
    REFUNDADO = 'reembolsado', 'Reembolsado'

class TipoPago(models.TextChoices):
    MONOEDO = 'monoedo', 'Pago Simple'
    MULTIEDO = 'multiedo', 'Pago Múltiple'
    RECURRENTE = 'recurrente', 'Pago Recurrente'
    PRUEBA = 'prueba', 'Pago de Prueba'

class MetodoPago(models.TextChoices):
    PAYPAL = 'paypal', 'PayPal'
    STRIPE = 'stripe', 'Stripe'
    MERCADOPAGO = 'mercadopago', 'MercadoPago'
    TRANSFERENCIA = 'transferencia', 'Transferencia Bancaria'
    CRYPTO = 'crypto', 'Criptomonedas'

class Pago(models.Model):
    empleador = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='pagos_enviados')
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name='pagos')
    business_unit = models.ForeignKey('app.BusinessUnit', on_delete=models.CASCADE, related_name='pagos_recibidos')
    
    # Información de la oportunidad
    oportunidad_id = models.CharField(max_length=100, db_index=True, help_text="ID único de la oportunidad")
    oportunidad_descripcion = models.TextField(help_text="Descripción detallada de la oportunidad")
    numero_plazas = models.IntegerField(default=1, help_text="Número de plazas o contrataciones asociadas")
    plazas_contratadas = models.IntegerField(default=0, help_text="Número de plazas ya contratadas")
    
    # Información de seguimiento
    referencia_cliente = models.CharField(max_length=100, null=True, blank=True, help_text="Referencia interna del cliente")
    numero_contrato = models.CharField(max_length=50, null=True, blank=True, help_text="Número de contrato asociado")
    
    # Información financiera
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    monto_por_plaza = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto base por plaza")
    moneda = models.CharField(max_length=3, default='USD')
    metodo = models.CharField(max_length=20, choices=MetodoPago.choices, default=MetodoPago.PAYPAL)
    tipo = models.CharField(max_length=20, choices=TipoPago.choices, default=TipoPago.MONOEDO)
    
    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE)
    intentos = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    
    # Información del gateway
    id_transaccion = models.CharField(max_length=255, null=True, blank=True)
    url_webhook = models.URLField(null=True, blank=True)
    webhook_payload = models.JSONField(null=True, blank=True)
    
    # Información adicional
    descripcion = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        indexes = [
            models.Index(fields=['oportunidad_id']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_procesamiento'])
        ]
    
    def __str__(self):
        return f'Pago #{self.id} - {self.empleador.nombre} -> {self.business_unit.name} (Oportunidad: {self.oportunidad_id})'
    
    def actualizar_estado(self, nuevo_estado, metadata=None):
        """Actualiza el estado del pago y crea un registro histórico."""
        historico = PagoHistorico.objects.create(
            pago=self,
            estado_anterior=self.estado,
            metadata=metadata or {}
        )
        self.estado = nuevo_estado
        self.fecha_actualizacion = timezone.now()
        self.save()
        return historico
    
    def marcar_como_completado(self, transaccion_id=None):
        self.estado = EstadoPago.COMPLETADO
        self.id_transaccion = transaccion_id
        self.save()
    
    def marcar_como_fallido(self, motivo=None):
        self.estado = EstadoPago.FALLIDO
        self.metadata['motivo_fallo'] = motivo
        self.save()
    
    def plazas_disponibles(self):
        """Devuelve el número de plazas disponibles para contratación."""
        return self.numero_plazas - self.plazas_contratadas
    
    def actualizar_plazas_contratadas(self, cantidad):
        """Actualiza el número de plazas contratadas."""
        if cantidad > self.plazas_disponibles():
            raise ValueError(f"No hay suficientes plazas disponibles. Disponibles: {self.plazas_disponibles()}")
        self.plazas_contratadas += cantidad
        self.save()
    
    def calcular_monto_total(self):
        """Calcula el monto total basado en el número de plazas."""
        return self.monto_por_plaza * self.numero_plazas

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
        return f'Historial #{self.id} - Pago #{self.pago.id}'

class WebhookLog(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='webhook_logs')
    evento = models.CharField(max_length=50)
    payload = models.JSONField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    error = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Log de Webhook'
        verbose_name_plural = 'Logs de Webhooks'

    def __str__(self):
        return f'Webhook Log #{self.id} - {self.evento}'
