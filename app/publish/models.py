from django.db import models
from django.utils import timezone
from app.models import JobOpportunity

class ChannelType(models.Model):
    """
    Tipos de canales disponibles
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Channel(models.Model):
    """
    Representa un canal específico para publicación
    """
    type = models.ForeignKey(ChannelType, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=255)  # ID único del canal
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('type', 'identifier')
    
    def __str__(self):
        return f"{self.type.name} - {self.name}"

class ChannelCredential(models.Model):
    """
    Credenciales específicas por canal
    """
    channel = models.OneToOneField(Channel, on_delete=models.CASCADE)
    api_key = models.CharField(max_length=255, blank=True)
    access_token = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)
    webhook_url = models.URLField(blank=True)
    refresh_token = models.CharField(max_length=255, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def is_expired(self):
        return self.expires_at and self.expires_at < timezone.now()
    
    def update_credentials(self, credentials: dict):
        for key, value in credentials.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()

class ChannelAnalytics(models.Model):
    """
    Métricas por canal
    """
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    date = models.DateField()
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    followers_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('channel', 'date')

class ChannelSubscription(models.Model):
    """
    Suscripciones a canales por usuario
    """
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('channel', 'user')

class Bot(models.Model):
    """
    Bots interactivos
    """
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict)
    
    def __str__(self):
        return self.name

class BotCommand(models.Model):
    """
    Comandos disponibles para el bot
    """
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    command = models.CharField(max_length=50)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('bot', 'command')

class BotResponse(models.Model):
    """
    Respuestas predefinidas para comandos
    """
    command = models.ForeignKey(BotCommand, on_delete=models.CASCADE)
    response_type = models.CharField(max_length=50, choices=[
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('video', 'Video'),
        ('document', 'Documento'),
        ('interactive', 'Interactivo')
    ])
    content = models.TextField()
    media_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class JobChannel(models.Model):
    """
    Canales específicos para oportunidades laborales
    """
    opportunity = models.ForeignKey(JobOpportunity, on_delete=models.CASCADE)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('scheduled', 'Programado'),
        ('published', 'Publicado'),
        ('failed', 'Fallido')
    ])
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    analytics = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
