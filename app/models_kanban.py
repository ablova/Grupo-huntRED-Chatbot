# app/models_kanban.pykanban:index
kanban:board_view
kanban:card_detail
kanban:move_card
kanban:update_card
kanban:add_comment
kanban:upload_attachment
kanban:archive_card
kanban:mark_notification_read
kanban:create_board
kanban:create_cardALg
"""
Modelos para el sistema Kanban de gestión de candidatos.
Este módulo define las estructuras de datos necesarias para implementar una 
interfaz tipo Kanban para el seguimiento del estado de los candidatos.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from typing import List, Dict, Any, Optional
import json
import logging

from app.models import Person, Vacante, Application, BusinessUnit, WorkflowStage
from app.com.utils.logger_utils import get_module_logger

logger = get_module_logger('kanban')

class KanbanBoard(models.Model):
    """Representa un tablero Kanban para una unidad de negocio específica."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE, related_name='kanban_boards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Tablero Kanban')
        verbose_name_plural = _('Tableros Kanban')
        ordering = ['business_unit', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.business_unit.name})"
    
    @property
    def columns(self):
        """Devuelve las columnas del tablero ordenadas por posición."""
        return self.kanban_columns.all()
    
    def get_active_cards(self):
        """Obtiene las tarjetas activas organizadas por columnas."""
        result = {}
        for column in self.columns:
            result[column.id] = column.cards.filter(is_archived=False).order_by('position')
        return result

class KanbanColumn(models.Model):
    """Representa una columna en el tablero Kanban."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    board = models.ForeignKey(KanbanBoard, on_delete=models.CASCADE, related_name='kanban_columns')
    workflow_stage = models.ForeignKey(WorkflowStage, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='kanban_columns')
    position = models.PositiveIntegerField(default=0)
    wip_limit = models.PositiveIntegerField(default=0, help_text=_("Límite de trabajo en progreso (0 = sin límite)"))
    color = models.CharField(max_length=20, default="#f5f5f5", help_text=_("Color de la columna en formato hexadecimal"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Columna Kanban')
        verbose_name_plural = _('Columnas Kanban')
        ordering = ['board', 'position']
    
    def __str__(self):
        return f"{self.name} ({self.board.name})"
    
    def is_at_wip_limit(self):
        """Comprueba si la columna ha alcanzado su límite de trabajo en progreso."""
        if self.wip_limit == 0:
            return False
        return self.cards.filter(is_archived=False).count() >= self.wip_limit
    
    @property
    def cards(self):
        """Devuelve las tarjetas de la columna ordenadas por posición."""
        return self.kanban_cards.all()

class KanbanCard(models.Model):
    """Representa una tarjeta en el tablero Kanban."""
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='kanban_card')
    column = models.ForeignKey(KanbanColumn, on_delete=models.CASCADE, related_name='kanban_cards')
    position = models.PositiveIntegerField(default=0)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='assigned_cards')
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(
        choices=[
            (1, _('Baja')),
            (2, _('Normal')),
            (3, _('Alta')),
            (4, _('Urgente'))
        ],
        default=2
    )
    labels = models.JSONField(default=list, blank=True, help_text=_("Etiquetas asociadas a la tarjeta"))
    is_archived = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Tarjeta Kanban')
        verbose_name_plural = _('Tarjetas Kanban')
        ordering = ['column', 'position']
    
    def __str__(self):
        return f"{self.application.user.nombre} - {self.application.vacancy.titulo}"
    
    def save(self, *args, **kwargs):
        """Guarda la tarjeta y actualiza el estado de la aplicación."""
        if self.column.workflow_stage and self.application.status != self.column.workflow_stage.name:
            old_status = self.application.status
            self.application.status = self.column.workflow_stage.name
            self.application.save()
            
            # Registrar el cambio de estado
            KanbanCardHistory.objects.create(
                card=self,
                change_type='status',
                old_value=old_status,
                new_value=self.column.workflow_stage.name,
                user=kwargs.pop('user', None)
            )
        
        # Si es una tarjeta nueva, posicionarla al final de la columna
        if not self.pk:
            max_position = KanbanCard.objects.filter(
                column=self.column, is_archived=False
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1
        
        super().save(*args, **kwargs)
    
    def move_to_column(self, target_column, user=None, position=None):
        """Mueve la tarjeta a otra columna."""
        if self.column.id == target_column.id:
            return False
        
        old_column = self.column
        self.column = target_column
        
        # Si no se especifica posición, colocar al final
        if position is None:
            max_position = KanbanCard.objects.filter(
                column=target_column, is_archived=False
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1
        else:
            self.position = position
            
            # Reordenar las tarjetas en la columna de destino
            cards_to_update = KanbanCard.objects.filter(
                column=target_column,
                position__gte=position,
                is_archived=False
            ).exclude(pk=self.pk)
            
            for card in cards_to_update:
                card.position += 1
                card.save()
        
        # Actualizar el estado de la aplicación si la columna está asociada a una etapa
        if target_column.workflow_stage:
            old_status = self.application.status
            self.application.status = target_column.workflow_stage.name
            self.application.save()
            
            # Registrar el cambio de estado
            KanbanCardHistory.objects.create(
                card=self,
                change_type='status',
                old_value=old_status,
                new_value=target_column.workflow_stage.name,
                user=user
            )
        
        # Registrar el movimiento de columna
        KanbanCardHistory.objects.create(
            card=self,
            change_type='column',
            old_value=old_column.name,
            new_value=target_column.name,
            user=user
        )
        
        self.save()
        return True
    
    def archive(self, user=None):
        """Archiva la tarjeta."""
        if not self.is_archived:
            self.is_archived = True
            
            # Registrar la acción
            KanbanCardHistory.objects.create(
                card=self,
                change_type='archive',
                old_value='active',
                new_value='archived',
                user=user
            )
            
            self.save()
            return True
        return False
    
    def unarchive(self, user=None):
        """Restaura la tarjeta archivada."""
        if self.is_archived:
            self.is_archived = False
            
            # Registrar la acción
            KanbanCardHistory.objects.create(
                card=self,
                change_type='archive',
                old_value='archived',
                new_value='active',
                user=user
            )
            
            self.save()
            return True
        return False

class KanbanCardHistory(models.Model):
    """Registra el historial de cambios en las tarjetas Kanban."""
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='history')
    timestamp = models.DateTimeField(auto_now_add=True)
    change_type = models.CharField(max_length=50, choices=[
        ('status', _('Cambio de estado')),
        ('column', _('Cambio de columna')),
        ('assignee', _('Cambio de asignado')),
        ('priority', _('Cambio de prioridad')),
        ('due_date', _('Cambio de fecha límite')),
        ('archive', _('Archivado/Desarchivado')),
        ('comment', _('Comentario')),
        ('attachment', _('Archivo adjunto'))
    ])
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Historial de Tarjeta')
        verbose_name_plural = _('Historial de Tarjetas')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.card} - {self.change_type} - {self.timestamp}"

class KanbanComment(models.Model):
    """Comentarios en las tarjetas Kanban."""
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Comentario')
        verbose_name_plural = _('Comentarios')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"
    
    def save(self, *args, **kwargs):
        """Guarda el comentario y registra la acción en el historial."""
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            # Registrar el nuevo comentario en el historial
            KanbanCardHistory.objects.create(
                card=self.card,
                change_type='comment',
                new_value=self.id,
                comment=self.text,
                user=self.user
            )

class KanbanAttachment(models.Model):
    """Archivos adjuntos a las tarjetas Kanban."""
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='kanban_attachments/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()  # Tamaño en bytes
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Archivo Adjunto')
        verbose_name_plural = _('Archivos Adjuntos')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        """Guarda el archivo adjunto y registra la acción en el historial."""
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            # Registrar el nuevo archivo en el historial
            KanbanCardHistory.objects.create(
                card=self.card,
                change_type='attachment',
                new_value=self.id,
                comment=f"Archivo adjunto: {self.filename}",
                user=self.uploaded_by
            )

class KanbanNotification(models.Model):
    """Notificaciones sobre actividad en el tablero Kanban."""
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kanban_notifications')
    card = models.ForeignKey(KanbanCard, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    history_entry = models.ForeignKey(KanbanCardHistory, on_delete=models.CASCADE, related_name='notifications', 
                                     null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Notificación')
        verbose_name_plural = _('Notificaciones')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    @staticmethod
    def create_from_history(history_entry, recipients=None):
        """Crea notificaciones a partir de un evento en el historial de una tarjeta."""
        if not history_entry:
            return []
        
        # Determinar los destinatarios si no se especifican
        if recipients is None:
            recipients = []
            # Incluir al asignado a la tarjeta
            if history_entry.card.assignee:
                recipients.append(history_entry.card.assignee)
                
            # Incluir usuarios que han comentado en la tarjeta
            commented_users = KanbanComment.objects.filter(
                card=history_entry.card
            ).values_list('user', flat=True).distinct()
            
            for user_id in commented_users:
                user = User.objects.get(id=user_id)
                if user not in recipients:
                    recipients.append(user)
        
        # Generar título y mensaje según el tipo de cambio
        title = f"Actividad en tarjeta: {history_entry.card}"
        message = "Se ha producido un cambio en una tarjeta que estás siguiendo."
        
        if history_entry.change_type == 'status':
            title = f"Cambio de estado en: {history_entry.card}"
            message = f"El estado ha cambiado de '{history_entry.old_value}' a '{history_entry.new_value}'."
        elif history_entry.change_type == 'column':
            title = f"Movimiento de tarjeta: {history_entry.card}"
            message = f"La tarjeta se ha movido de '{history_entry.old_value}' a '{history_entry.new_value}'."
        elif history_entry.change_type == 'assignee':
            title = f"Asignación actualizada: {history_entry.card}"
            message = f"La tarjeta ha sido reasignada de '{history_entry.old_value}' a '{history_entry.new_value}'."
        elif history_entry.change_type == 'comment':
            title = f"Nuevo comentario en: {history_entry.card}"
            message = f"{history_entry.user.get_full_name() or history_entry.user.username} ha comentado: {history_entry.comment[:100]}"
        
        # Crear notificaciones para cada destinatario
        notifications = []
        for recipient in recipients:
            # No notificar al usuario que realizó la acción
            if recipient == history_entry.user:
                continue
                
            notification = KanbanNotification.objects.create(
                recipient=recipient,
                card=history_entry.card,
                history_entry=history_entry,
                title=title,
                message=message
            )
            notifications.append(notification)
            
        return notifications
