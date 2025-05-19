# /home/pablo/app/com/models.py
#
# Modelos para el módulo de comunicaciones.
#
from django.db import models
from django.contrib.auth.models import User
from app.models import Person
import logging

logger = logging.getLogger('app.com.models')

class Conversation(models.Model):
    """Modelo para conversaciones."""
    recipient = models.ForeignKey(Person, on_delete=models.CASCADE)
    channel = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    last_message = models.TextField()
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['recipient', 'channel']),
            models.Index(fields=['state']),
            models.Index(fields=['timestamp'])
        ]

class Message(models.Model):
    """Modelo para mensajes."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    content = models.TextField()
    direction = models.CharField(max_length=10)  # 'in' o 'out'
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['conversation', 'direction']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp'])
        ]

class Notification(models.Model):
    """Modelo para notificaciones."""
    recipient = models.ForeignKey(Person, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    channel = models.CharField(max_length=50)
    content = models.TextField()
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['recipient', 'type']),
            models.Index(fields=['status']),
            models.Index(fields=['timestamp'])
        ]

class Metric(models.Model):
    """Modelo para métricas del sistema."""
    name = models.CharField(max_length=100)
    value = models.FloatField()
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['timestamp'])
        ]

class WorkflowState(models.Model):
    """Modelo para estados del flujo de trabajo."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    state = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['conversation', 'state']),
            models.Index(fields=['timestamp'])
        ]

class ChannelConfig(models.Model):
    """Modelo para configuración de canales."""
    channel = models.CharField(max_length=50, unique=True)
    config = models.JSONField()
    active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['channel']),
            models.Index(fields=['active'])
        ]
