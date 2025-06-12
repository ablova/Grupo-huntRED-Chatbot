from django.db import models
from django.utils.translation import gettext_lazy as _

class BusinessUnit(models.Model):
    """
    Modelo para las unidades de negocio.
    """
    name = models.CharField(_('Nombre'), max_length=100)
    code = models.CharField(_('Código'), max_length=10, unique=True)
    description = models.TextField(_('Descripción'), blank=True)
    is_active = models.BooleanField(_('Activa'), default=True)
    created_at = models.DateTimeField(_('Fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Fecha de actualización'), auto_now=True)
    
    # Campos para Telegram
    telegram_bot_token = models.CharField(_('Token del Bot de Telegram'), max_length=100, blank=True)
    telegram_channel_id = models.CharField(_('ID del Canal de Telegram'), max_length=100, blank=True)
    telegram_notifications_enabled = models.BooleanField(_('Notificaciones de Telegram habilitadas'), default=True)
    
    class Meta:
        verbose_name = _('Unidad de Negocio')
        verbose_name_plural = _('Unidades de Negocio')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def has_telegram_config(self) -> bool:
        """
        Verifica si la unidad de negocio tiene configurado Telegram.
        """
        return bool(self.telegram_bot_token and self.telegram_channel_id)
    
    def enable_telegram_notifications(self) -> None:
        """
        Habilita las notificaciones de Telegram.
        """
        self.telegram_notifications_enabled = True
        self.save(update_fields=['telegram_notifications_enabled'])
    
    def disable_telegram_notifications(self) -> None:
        """
        Deshabilita las notificaciones de Telegram.
        """
        self.telegram_notifications_enabled = False
        self.save(update_fields=['telegram_notifications_enabled'])
    
    def update_telegram_config(self, bot_token: str, channel_id: str) -> None:
        """
        Actualiza la configuración de Telegram.
        
        Args:
            bot_token: Token del bot de Telegram
            channel_id: ID del canal de Telegram
        """
        self.telegram_bot_token = bot_token
        self.telegram_channel_id = channel_id
        self.save(update_fields=['telegram_bot_token', 'telegram_channel_id']) 