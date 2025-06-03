"""
Modelos para el sistema Kanban.

Este módulo define los modelos necesarios para la funcionalidad Kanban
del sistema Grupo huntRED®.
"""

from django.db import models
from django.utils import timezone

from app.models import Person, Vacante, BusinessUnit

class KanbanBoard(models.Model):
    """Modelo que representa un tablero Kanban."""
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='kanban_boards')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class KanbanColumn(models.Model):
    """Modelo que representa una columna en un tablero Kanban."""
    board = models.ForeignKey(KanbanBoard, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    position = models.PositiveIntegerField()
    wip_limit = models.PositiveIntegerField(null=True, blank=True)  # Límite de trabajo en progreso
    workflow_stage = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f"{self.board.name} - {self.name}"

class KanbanCard(models.Model):
    """Modelo que representa una tarjeta en una columna Kanban."""
    column = models.ForeignKey(KanbanColumn, on_delete=models.CASCADE, related_name='cards')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='kanban_cards')
    vacancy = models.ForeignKey(Vacante, on_delete=models.SET_NULL, null=True, blank=True, related_name='kanban_cards')
    application_id = models.IntegerField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Baja'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente')
    ], default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class KanbanCardHistory(models.Model):
    """Modelo que registra el historial de movimientos de una tarjeta Kanban."""
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='history')
    from_column = models.ForeignKey(KanbanColumn, on_delete=models.SET_NULL, null=True, related_name='cards_moved_from')
    to_column = models.ForeignKey(KanbanColumn, on_delete=models.SET_NULL, null=True, related_name='cards_moved_to')
    moved_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='card_movements')
    moved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-moved_at']

    def __str__(self):
        return f"{self.card.title} - {self.from_column.name if self.from_column else 'None'} → {self.to_column.name if self.to_column else 'None'}"

class KanbanComment(models.Model):
    """Modelo para comentarios en tarjetas Kanban."""
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='kanban_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comentario en {self.card.title} por {self.author.nombre if self.author else 'Anónimo'}"

class KanbanAttachment(models.Model):
    """Modelo para archivos adjuntos en tarjetas Kanban."""
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='kanban_attachments/')
    uploaded_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, related_name='kanban_attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Tamaño en bytes
    file_type = models.CharField(max_length=100)

    def __str__(self):
        return self.file_name

class KanbanNotification(models.Model):
    """Modelo para notificaciones relacionadas con actividades Kanban."""
    user = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='kanban_notifications')
    card = models.ForeignKey(KanbanCard, on_delete=models.SET_NULL, null=True, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    action_url = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message
