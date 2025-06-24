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
    SESSION_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("grupal", "Grupal"),
    ]
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        default="individual",
        help_text="Define si el evento es individual o grupal."
    )
    cupo_maximo = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Máximo de participantes para slots grupales. Solo aplica si session_type es grupal."
    )
    EVENT_MODE_CHOICES = [
        ("presencial", "Presencial"),
        ("virtual", "Virtual"),
        ("hibrido", "Híbrido"),
    ]
    event_mode = models.CharField(
        max_length=20,
        choices=EVENT_MODE_CHOICES,
        default="virtual",
        help_text="Modalidad del evento: presencial, virtual o híbrido."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f'{self.event_type}: {self.title} [{self.get_event_mode_display()}]'

    def is_upcoming(self) -> bool:
        """Verifica si el evento está por venir."""
        return self.start_time > timezone.now()

    def is_overdue(self) -> bool:
        """Verifica si el evento ya pasó."""
        return self.end_time < timezone.now()

    def lugares_disponibles(self) -> int:
        """Devuelve el número de lugares disponibles para slots grupales."""
        if self.session_type == "grupal" and self.cupo_maximo:
            return max(0, self.cupo_maximo - self.participants.count())
        return 1  # Para individuales, solo 1 lugar

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
