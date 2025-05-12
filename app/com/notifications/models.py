"""
Modelos para el sistema de notificaciones.

Implementa un sistema completo de notificaciones con seguimiento
de estado, preferencias por usuario y soporte multicanal.
"""

from django.db import models
from django.conf import settings
from app.models import BusinessUnit, Person, Vacante, User

class NotificationStatus(models.TextChoices):
    """Estados posibles para una notificación."""
    PENDING = 'pending', 'Pendiente'
    SENT = 'sent', 'Enviada'
    DELIVERED = 'delivered', 'Entregada'
    READ = 'read', 'Leída'
    FAILED = 'failed', 'Fallida'
    CANCELLED = 'cancelled', 'Cancelada'

class NotificationType(models.TextChoices):
    """Tipos de notificaciones disponibles en el sistema."""
    # Notificaciones para responsable del proceso
    PROCESO_CREADO = 'proceso_creado', 'Creación de Proceso'
    FEEDBACK_REQUERIDO = 'feedback_requerido', 'Feedback Requerido'
    CONFIRMACION_ENTREVISTA = 'confirmacion_entrevista', 'Confirmación de Entrevista'
    FELICITACION_CONTRATACION = 'felicitacion_contratacion', 'Felicitaciones por Contratación'
    ACTUALIZACION_CANDIDATO = 'actualizacion_candidato', 'Actualización de Candidato'
    
    # Notificaciones para contacto en cliente
    FIRMA_CONTRATO = 'firma_contrato', 'Firma de Contrato'
    EMISION_PROPUESTA = 'emision_propuesta', 'Emisión de Propuesta'
    CANDIDATOS_DISPONIBLES = 'candidatos_disponibles', 'Candidatos Disponibles'
    CANDIDATOS_BLIND = 'candidatos_blind', 'Candidatos con CV Blind'
    
    # Notificaciones para consultor asignado
    ESTATUS_DIARIO = 'estatus_diario', 'Estatus Diario del Proceso'
    DASHBOARD_ACTUALIZADO = 'dashboard_actualizado', 'Dashboard Actualizado'
    
    # Notificaciones para pagos y facturación
    RECORDATORIO_PAGO = 'recordatorio_pago', 'Recordatorio de Pago'
    CONFIRMACION_PAGO = 'confirmacion_pago', 'Confirmación de Pago'
    FACTURA_EMITIDA = 'factura_emitida', 'Factura Emitida'
    
    # Notificaciones para candidatos
    INVITACION_ENTREVISTA = 'invitacion_entrevista', 'Invitación a Entrevista'
    PROGRESO_PROCESO = 'progreso_proceso', 'Progreso en el Proceso'
    OFERTA_EMITIDA = 'oferta_emitida', 'Oferta Emitida'
    
    # Notificaciones para todos los usuarios
    SISTEMA_ACTUALIZADO = 'sistema_actualizado', 'Sistema Actualizado'
    EVENTO_PROGRAMADO = 'evento_programado', 'Evento Programado'

class NotificationChannel(models.TextChoices):
    """Canales disponibles para enviar notificaciones."""
    EMAIL = 'email', 'Correo Electrónico'
    WHATSAPP = 'whatsapp', 'WhatsApp'
    SMS = 'sms', 'SMS'
    TELEGRAM = 'telegram', 'Telegram'
    APP = 'app', 'Aplicación Web'
    SLACK = 'slack', 'Slack'

class NotificationPreference(models.Model):
    """Preferencias de notificación por usuario y tipo."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, null=True, blank=True)
    
    # Canales habilitados
    email_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    telegram_enabled = models.BooleanField(default=False)
    app_enabled = models.BooleanField(default=True)
    slack_enabled = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'notification_type', 'business_unit')
        indexes = [
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['business_unit']),
        ]

class Notification(models.Model):
    """Modelo central para todas las notificaciones del sistema."""
    # Información básica
    title = models.CharField(max_length=255)
    content = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    
    # Estado y seguimiento
    status = models.CharField(max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING)
    error_message = models.TextField(blank=True, null=True)
    
    # Relaciones con otros modelos
    recipient = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Datos específicos para cada canal
    email_data = models.JSONField(null=True, blank=True)
    whatsapp_data = models.JSONField(null=True, blank=True)
    sms_data = models.JSONField(null=True, blank=True)
    telegram_data = models.JSONField(null=True, blank=True)
    app_data = models.JSONField(null=True, blank=True)
    slack_data = models.JSONField(null=True, blank=True)
    
    # Seguimiento
    delivery_attempts = models.IntegerField(default=0)
    last_delivery_attempt = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Verificación y seguridad
    verification_code = models.CharField(max_length=64, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['business_unit', 'created_at']),
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['vacante', 'notification_type']),
            models.Index(fields=['verification_code']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} para {self.recipient} ({self.status})"
    
    def mark_as_sent(self):
        """Marca la notificación como enviada."""
        self.status = NotificationStatus.SENT
        self.save(update_fields=['status'])
    
    def mark_as_delivered(self):
        """Marca la notificación como entregada."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = models.functions.Now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_read(self):
        """Marca la notificación como leída."""
        self.status = NotificationStatus.READ
        self.read_at = models.functions.Now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_as_failed(self, error_message=None):
        """Marca la notificación como fallida."""
        self.status = NotificationStatus.FAILED
        if error_message:
            self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])
    
    def verify(self, code):
        """Verifica el código de la notificación."""
        if self.verification_code == code:
            self.is_verified = True
            self.save(update_fields=['is_verified'])
            return True
        return False
