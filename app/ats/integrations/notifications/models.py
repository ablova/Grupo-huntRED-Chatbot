from django.db import models
from django.utils import timezone

class Notification(models.Model):
    """Modelo para notificaciones del sistema."""
    
    NOTIFICATION_TYPES = [
        ('SYSTEM', 'Sistema'),
        ('USER', 'Usuario'),
        ('SECURITY', 'Seguridad'),
        ('MAINTENANCE', 'Mantenimiento'),
        ('EVENT', 'Evento'),
        ('METRICS', 'Métricas'),
        ('PERFORMANCE', 'Rendimiento'),
        ('PROCESS', 'Proceso'),
        ('PAYMENT', 'Pago'),
        ('PLACEMENT', 'Colocación')
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('FAILED', 'Fallido'),
        ('DELIVERED', 'Entregado'),
        ('READ', 'Leído')
    ]
    
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    recipient = models.ForeignKey('app.Person', on_delete=models.CASCADE)
    content = models.TextField()
    template = models.ForeignKey('NotificationTemplate', on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.ForeignKey('NotificationChannel', on_delete=models.SET_NULL, null=True)
    channel_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.type} - {self.recipient} ({self.status})"
        
    def mark_as_sent(self):
        self.status = 'SENT'
        self.sent_at = timezone.now()
        self.save()
        
    def mark_as_failed(self, error_message):
        self.status = 'FAILED'
        self.error_message = error_message
        self.save()
        
    def increment_retry(self):
        self.retry_count += 1
        self.save()

class NotificationTemplate(models.Model):
    """Modelo para plantillas de notificación."""
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=Notification.NOTIFICATION_TYPES)
    channel = models.ForeignKey('NotificationChannel', on_delete=models.CASCADE)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    variables = models.JSONField(default=list, help_text="Lista de variables disponibles en la plantilla")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla de Notificación"
        verbose_name_plural = "Plantillas de Notificación"
        ordering = ['name']
        
    def __str__(self):
        return self.name

class NotificationChannel(models.Model):
    """Modelo para canales de notificación."""
    
    CHANNEL_TYPES = [
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('TELEGRAM', 'Telegram'),
        ('SLACK', 'Slack'),
        ('DISCORD', 'Discord'),
        ('TEAMS', 'Microsoft Teams'),
        ('WEB', 'Web'),
        ('API', 'API'),
        ('DATABASE', 'Base de Datos'),
        ('QUEUE', 'Cola'),
        ('CACHE', 'Caché')
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    config = models.JSONField(default=dict, help_text="Configuración específica del canal")
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    rate_limit = models.IntegerField(default=100, help_text="Límite de mensajes por minuto")
    retry_policy = models.JSONField(default=dict, help_text="Política de reintentos")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Canal de Notificación"
        verbose_name_plural = "Canales de Notificación"
        ordering = ['priority', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.type})" 