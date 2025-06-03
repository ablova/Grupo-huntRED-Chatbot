from django.db import models
from django.utils.translation import gettext_lazy as _

class Integration(models.Model):
    """
    Modelo para representar una integración con una plataforma externa
    """
    class IntegrationType(models.TextChoices):
        WHATSAPP = 'whatsapp', _('WhatsApp')
        TELEGRAM = 'telegram', _('Telegram')
        MESSENGER = 'messenger', _('Messenger')
        INSTAGRAM = 'instagram', _('Instagram')
        SLACK = 'slack', _('Slack')
        EMAIL = 'email', _('Email')

    name = models.CharField(_('Nombre'), max_length=100)
    type = models.CharField(
        _('Tipo'),
        max_length=20,
        choices=IntegrationType.choices
    )
    is_active = models.BooleanField(_('Activo'), default=True)
    created_at = models.DateTimeField(_('Creado en'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado en'), auto_now=True)

    class Meta:
        verbose_name = _('Integración')
        verbose_name_plural = _('Integraciones')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class IntegrationConfig(models.Model):
    """
    Modelo para almacenar la configuración de una integración
    """
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='configs',
        verbose_name=_('Integración')
    )
    key = models.CharField(_('Clave'), max_length=100)
    value = models.TextField(_('Valor'))
    is_secret = models.BooleanField(_('Es secreto'), default=False)
    created_at = models.DateTimeField(_('Creado en'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado en'), auto_now=True)

    class Meta:
        verbose_name = _('Configuración de integración')
        verbose_name_plural = _('Configuraciones de integración')
        ordering = ['integration', 'key']
        unique_together = ['integration', 'key']

    def __str__(self):
        return f"{self.integration.name} - {self.key}"

class IntegrationLog(models.Model):
    """
    Modelo para registrar eventos de integración
    """
    class EventType(models.TextChoices):
        MESSAGE_SENT = 'message_sent', _('Mensaje enviado')
        MESSAGE_RECEIVED = 'message_received', _('Mensaje recibido')
        ERROR = 'error', _('Error')
        WEBHOOK = 'webhook', _('Webhook')
        OTHER = 'other', _('Otro')

    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('Integración')
    )
    event_type = models.CharField(
        _('Tipo de evento'),
        max_length=20,
        choices=EventType.choices
    )
    payload = models.JSONField(_('Datos'), null=True, blank=True)
    error = models.TextField(_('Error'), null=True, blank=True)
    created_at = models.DateTimeField(_('Creado en'), auto_now_add=True)

    class Meta:
        verbose_name = _('Log de integración')
        verbose_name_plural = _('Logs de integración')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.integration.name} - {self.get_event_type_display()} - {self.created_at}" 