from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

class EventType(models.TextChoices):
    ENTREVISTA = 'entrevista', 'Entrevista'
    CHECKIN = 'checkin', 'Check-in'
    CHECKOUT = 'checkout', 'Check-out'
    WEBINAR = 'webinar', 'Webinar'
    WORKSHOP = 'workshop', 'Workshop'

class EventStatus(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    CONFIRMADO = 'confirmado', 'Confirmado'
    CANCELADO = 'cancelado', 'Cancelado'
    COMPLETADO = 'completado', 'Completado'

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.PENDIENTE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, null=True, blank=True)
    virtual_link = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f'{self.event_type}: {self.title}'

    def is_upcoming(self) -> bool:
        """Verifica si el evento está por venir."""
        return self.start_time > timezone.now()

    def is_overdue(self) -> bool:
        """Verifica si el evento ya pasó."""
        return self.end_time < timezone.now()

class EventParticipant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participants')
    person = models.ForeignKey('app.Person', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.PENDIENTE)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('event', 'person')
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'

    def __str__(self):
        return f'{self.person} - {self.event}'

class EventBooking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    participant = models.ForeignKey(EventParticipant, on_delete=models.CASCADE, related_name='bookings')
    booking_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('event', 'participant')
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f'Reserva #{self.id} - {self.participant}'

class EventReminder(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reminders')
    participant = models.ForeignKey(EventParticipant, on_delete=models.CASCADE, related_name='reminders')
    reminder_time = models.DateTimeField()
    sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Recordatorio'
        verbose_name_plural = 'Recordatorios'

    def __str__(self):
        return f'Recordatorio #{self.id} - {self.participant}'

class EventFeedback(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedback')
    participant = models.ForeignKey(EventParticipant, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField()
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'participant')
        verbose_name = 'Retroalimentación'
        verbose_name_plural = 'Retroalimentaciones'

    def __str__(self):
        return f'Retroalimentación #{self.id} - {self.participant}'
