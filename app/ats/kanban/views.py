"""
Vistas para el sistema Kanban de gestión de candidatos.
Proporciona las interfaces y APIs necesarias para la manipulación 
del tablero y las tarjetas Kanban.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, F, Count, Prefetch
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.models import User
from asgiref.sync import sync_to_async, async_to_sync
from typing import Dict, List, Any, Optional
import logging
import asyncio
import json

# Importaciones directas siguiendo reglas de Grupo huntRED®
from app.models import (
    KanbanBoard, KanbanColumn, KanbanCard, KanbanCardHistory,
    KanbanComment, KanbanAttachment, KanbanNotification,
    Person, Vacante, Application, BusinessUnit, WorkflowStage
)
from app.ats.kanban.ml_integration import KanbanMLIntegration, get_ml_recommendations
from app.ats.utils.rbac import check_permission, has_organization_access
from app.ats.utils.cache import cache_result
from app.ats.utils.logger_utils import get_module_logger
from app.ats.chatbot.integrations.services import send_message

# Configura el logger
logger = get_module_logger('kanban_views')

# Constantes
ITEMS_PER_PAGE = 20  # Elementos por página para paginación

@login_required
def index(request):
    """Vista principal que muestra los tableros Kanban disponibles para el usuario."""
    # Obtener las unidades de negocio a las que tiene acceso el usuario
    business_units = BusinessUnit.objects.filter(
        Q(user_permissions__user=request.user) | 
        Q(user_permissions__group__user=request.user)
    ).distinct()
    
    boards = KanbanBoard.objects.filter(business_unit__in=business_units)
    
    # Obtener estadísticas por tablero
    board_stats = {}
    for board in boards:
        stats = {
            'total_cards': KanbanCard.objects.filter(column__board=board, is_archived=False).count(),
            'total_columns': board.kanban_columns.count(),
            'recent_activity': KanbanCardHistory.objects.filter(
                card__column__board=board
            ).order_by('-timestamp')[:5]
        }
        board_stats[board.id] = stats
    
    context = {
        'boards': boards,
        'board_stats': board_stats,
        'business_units': business_units,
        'page_title': 'Tableros Kanban'
    }
    
    return render(request, 'kanban/index.html', context)

@login_required
def board_view(request, board_id):
    """Vista detallada de un tablero Kanban específico."""
    board = get_object_or_404(KanbanBoard, id=board_id)
    
    # Verificar permisos del usuario para acceder al tablero
    if not user_can_access_board(request.user, board):
        raise PermissionDenied("No tienes permisos para acceder a este tablero.")
    
    # Obtener columnas con sus tarjetas
    columns = board.kanban_columns.prefetch_related(
        Prefetch(
            'kanban_cards',
            queryset=KanbanCard.objects.filter(
                is_archived=False
            ).select_related(
                'application__user', 
                'application__vacancy',
                'assignee'
            ).prefetch_related(
                'comments', 
                'attachments'
            ).order_by('position'),
            to_attr='active_cards'
        )
    ).order_by('position')
    
    # Obtener usuarios para el selector de asignación
    assignable_users = get_assignable_users(board.business_unit)
    
    # Obtener notificaciones no leídas para el usuario actual
    notifications = KanbanNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).select_related('card', 'history_entry').order_by('-created_at')[:10]
    
    # Obtener recomendaciones ML solo si está habilitado en settings
    ml_enabled = getattr(settings, 'ENABLE_ML_FEATURES', True)
    ml_recommendations = {}
    
    if ml_enabled:
        # Determinar si mostrar recomendaciones basado en el rol
        show_ml = True
        if hasattr(request.user, 'role'):
            show_ml = request.user.role in ['super_admin', 'consultant_complete']
        
        if show_ml:
            # Obtener recomendaciones ML para el tablero
            ml_recommendations = get_ml_recommendations(request, board_id=board_id)
    
    context = {
        'board': board,
        'columns': columns,
        'assignable_users': assignable_users,
        'notifications': notifications,
        'page_title': f'Tablero: {board.name}',
        'ml_recommendations': ml_recommendations,
        'show_ml_features': ml_enabled
    }
    
    return render(request, 'kanban/board.html', context)

@login_required
def card_detail_view(request, card_id):
    """Vista detallada de una tarjeta Kanban."""
    card = get_object_or_404(KanbanCard, id=card_id)
    
    # Verificar permisos del usuario para ver la tarjeta
    if not user_can_access_board(request.user, card.column.board):
        raise PermissionDenied("No tienes permisos para acceder a esta tarjeta.")
    
    # Obtener historial, comentarios y archivos adjuntos
    history = card.history.select_related('user').order_by('-timestamp')
    comments = card.comments.select_related('user').order_by('-created_at')
    attachments = card.attachments.select_related('uploaded_by').order_by('-created_at')
    
    # Obtener columnas disponibles para mover la tarjeta
    available_columns = card.column.board.kanban_columns.all()
    
    # Obtener usuarios para el selector de asignación
    assignable_users = get_assignable_users(card.column.board.business_unit)
    
    # Obtener recomendaciones ML solo si está habilitado en settings
    ml_enabled = getattr(settings, 'ENABLE_ML_FEATURES', True)
    ml_recommendations = {}
    
    if ml_enabled:
        # Determinar si mostrar recomendaciones basado en el rol
        show_ml = True
        if hasattr(request.user, 'role'):
            show_ml = request.user.role in ['super_admin', 'consultant_complete']
        
        if show_ml:
            try:
                # Obtener recomendaciones ML para la tarjeta
                ml_recommendations = get_ml_recommendations(request, card_id=card_id)
                
                # Cache para evitar cálculos repetidos
                cache_key = f"card_ml_score_{card_id}"
                ml_score = cache.get(cache_key)
                
                if ml_score is None:
                    # Calcular score de ML para este candidato/vacante
                    business_unit = None
                    if hasattr(request.user, 'business_unit'):
                        business_unit = request.user.business_unit
                    
                    # Usar async para optimizar rendimiento
                    ml_integration = KanbanMLIntegration(business_unit=business_unit)
                    ml_score = ml_integration.ml_system.predict_candidate_success(
                        card.application.user, 
                        card.application.vacancy
                    )
                    # Guardar en caché para evitar recálculos frecuentes (1 hora)
                    cache.set(cache_key, ml_score, 3600)
                    
                    # Registrar para monitoreo
                    logger.info(f"ML score calculado para tarjeta {card_id}: {ml_score:.2f}")
                
                ml_recommendations['candidate_score'] = ml_score
            except Exception as e:
                logger.error(f"Error calculando recomendaciones ML: {e}")
    
    context = {
        'card': card,
        'history': history,
        'comments': comments,
        'attachments': attachments,
        'available_columns': available_columns,
        'assignable_users': assignable_users,
        'ml_recommendations': ml_recommendations,
        'show_ml_features': ml_enabled and ml_recommendations,
        'now': timezone.now(),  # Para comparaciones de fecha en plantilla
        'page_title': f'Tarjeta: {card.application.user.nombre} - {card.application.vacancy.titulo}'
    }
    
    return render(request, 'kanban/card_detail.html', context)

# APIs JSON para manipulación de tarjetas

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def move_card(request):
    """API para mover una tarjeta a otra columna."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        target_column_id = data.get('target_column_id')
        position = data.get('position')
        
        if not card_id or not target_column_id:
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)
        
        card = get_object_or_404(KanbanCard, id=card_id)
        target_column = get_object_or_404(KanbanColumn, id=target_column_id)
        
        # Verificar permisos
        if not user_can_access_board(request.user, card.column.board):
            return JsonResponse({'error': 'No tienes permisos para esta acción'}, status=403)
        
        # Verificar que la columna pertenece al mismo tablero
        if card.column.board.id != target_column.board.id:
            return JsonResponse({'error': 'Columna de destino no pertenece al mismo tablero'}, status=400)
        
        # Verificar límite WIP si existe
        if target_column.is_at_wip_limit():
            return JsonResponse({
                'error': f'La columna {target_column.name} ha alcanzado su límite de trabajo en progreso'
            }, status=400)
        
        with transaction.atomic():
            # Mover la tarjeta
            success = card.move_to_column(target_column, user=request.user, position=position)
            
            if success:
                # Notificar al candidato si el estado cambió
                notify_candidate_of_status_change(card)
                
                # Crear notificaciones para otros usuarios
                latest_history = card.history.latest('timestamp')
                KanbanNotification.create_from_history(latest_history)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Tarjeta movida a {target_column.name}',
                    'card': {
                        'id': card.id,
                        'column_id': card.column.id,
                        'position': card.position,
                        'status': card.application.status
                    }
                })
            else:
                return JsonResponse({'error': 'No se pudo mover la tarjeta'}, status=400)
                
    except Exception as e:
        logger.error(f"Error al mover tarjeta: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def update_card(request):
    """API para actualizar los detalles de una tarjeta."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        
        if not card_id:
            return JsonResponse({'error': 'Falta el ID de la tarjeta'}, status=400)
        
        card = get_object_or_404(KanbanCard, id=card_id)
        
        # Verificar permisos
        if not user_can_access_board(request.user, card.column.board):
            return JsonResponse({'error': 'No tienes permisos para esta acción'}, status=403)
        
        # Campos que se pueden actualizar
        fields_to_update = {
            'assignee_id': ('assignee', User, 'assignee'),
            'priority': ('priority', int, 'priority'),
            'due_date': ('due_date', parse_date, 'due_date'),
            'labels': ('labels', json.loads, 'labels')
        }
        
        with transaction.atomic():
            changes_made = False
            
            for field, (attr_name, converter, history_type) in fields_to_update.items():
                if field in data:
                    old_value = getattr(card, attr_name)
                    new_value = data.get(field)
                    
                    if new_value is not None:
                        # Convertir el valor si es necesario
                        new_value = converter(new_value)
                        
                        # Solo actualizar si el valor cambió
                        if new_value != old_value:
                            # Registrar el cambio en el historial
                            KanbanCardHistory.objects.create(
                                card=card,
                                change_type=history_type,
                                old_value=str(old_value) if old_value else '',
                                new_value=str(new_value) if new_value else '',
                                user=request.user
                            )
                            
                            # Actualizar el atributo
                            setattr(card, attr_name, new_value)
                            changes_made = True
            
            if changes_made:
                card.save()
                
                # Crear notificaciones
                latest_history = card.history.latest('timestamp')
                KanbanNotification.create_from_history(latest_history)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Tarjeta actualizada correctamente',
                    'card': {
                        'id': card.id,
                        'assignee': card.assignee.username if card.assignee else None,
                        'priority': card.priority,
                        'due_date': card.due_date.isoformat() if card.due_date else None,
                        'labels': card.labels
                    }
                })
            else:
                return JsonResponse({'success': True, 'message': 'No se realizaron cambios'})
                
    except Exception as e:
        logger.error(f"Error al actualizar tarjeta: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_comment(request):
    """API para añadir un comentario a una tarjeta."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        comment_text = data.get('comment')
        
        if not card_id or not comment_text:
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)
        
        card = get_object_or_404(KanbanCard, id=card_id)
        
        # Verificar permisos
        if not user_can_access_board(request.user, card.column.board):
            return JsonResponse({'error': 'No tienes permisos para esta acción'}, status=403)
        
        # Crear el comentario
        comment = KanbanComment.objects.create(
            card=card,
            user=request.user,
            text=comment_text
        )
        
        # Crear notificaciones (se hace automáticamente en el save() del comentario)
        
        return JsonResponse({
            'success': True,
            'message': 'Comentario añadido correctamente',
            'comment': {
                'id': comment.id,
                'text': comment.text,
                'user': comment.user.get_full_name() or comment.user.username,
                'created_at': comment.created_at.isoformat()
            }
        })
                
    except Exception as e:
        logger.error(f"Error al añadir comentario: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def archive_card(request):
    """API para archivar o desarchivar una tarjeta."""
    try:
        data = json.loads(request.body)
        card_id = data.get('card_id')
        action = data.get('action', 'archive')  # 'archive' o 'unarchive'
        
        if not card_id:
            return JsonResponse({'error': 'Falta el ID de la tarjeta'}, status=400)
        
        card = get_object_or_404(KanbanCard, id=card_id)
        
        # Verificar permisos
        if not user_can_access_board(request.user, card.column.board):
            return JsonResponse({'error': 'No tienes permisos para esta acción'}, status=403)
        
        # Archivar o desarchivar
        if action == 'archive':
            success = card.archive(user=request.user)
            message = 'Tarjeta archivada correctamente'
        else:
            success = card.unarchive(user=request.user)
            message = 'Tarjeta desarchivada correctamente'
        
        if success:
            return JsonResponse({
                'success': True,
                'message': message,
                'card': {
                    'id': card.id,
                    'is_archived': card.is_archived
                }
            })
        else:
            return JsonResponse({'error': 'No se pudo realizar la acción'}, status=400)
                
    except Exception as e:
        logger.error(f"Error al archivar/desarchivar tarjeta: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def upload_attachment(request):
    """API para subir un archivo adjunto a una tarjeta."""
    try:
        card_id = request.POST.get('card_id')
        file = request.FILES.get('file')
        
        if not card_id or not file:
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)
        
        card = get_object_or_404(KanbanCard, id=card_id)
        
        # Verificar permisos
        if not user_can_access_board(request.user, card.column.board):
            return JsonResponse({'error': 'No tienes permisos para esta acción'}, status=403)
        
        # Crear el archivo adjunto
        attachment = KanbanAttachment.objects.create(
            card=card,
            file=file,
            filename=file.name,
            content_type=file.content_type,
            size=file.size,
            uploaded_by=request.user
        )
        
        # Crear notificaciones (se hace automáticamente en el save() del attachment)
        
        return JsonResponse({
            'success': True,
            'message': 'Archivo subido correctamente',
            'attachment': {
                'id': attachment.id,
                'filename': attachment.filename,
                'url': attachment.file.url,
                'content_type': attachment.content_type,
                'size': attachment.size,
                'uploaded_by': attachment.uploaded_by.get_full_name() or attachment.uploaded_by.username,
                'created_at': attachment.created_at.isoformat()
            }
        })
                
    except Exception as e:
        logger.error(f"Error al subir archivo: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def mark_notification_read(request):
    """API para marcar notificaciones como leídas."""
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        mark_all = data.get('mark_all', False)
        
        if mark_all:
            # Marcar todas las notificaciones como leídas
            count = KanbanNotification.objects.filter(
                recipient=request.user,
                is_read=False
            ).update(is_read=True)
            
            return JsonResponse({
                'success': True,
                'message': f'{count} notificaciones marcadas como leídas',
                'count': count
            })
        elif notification_id:
            # Marcar una notificación específica como leída
            notification = get_object_or_404(
                KanbanNotification, 
                id=notification_id,
                recipient=request.user
            )
            
            notification.is_read = True
            notification.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Notificación marcada como leída',
                'notification_id': notification.id
            })
        else:
            return JsonResponse({'error': 'Faltan parámetros requeridos'}, status=400)
                
    except Exception as e:
        logger.error(f"Error al marcar notificación: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

# Funciones auxiliares

def user_can_access_board(user, board):
    """Verifica si un usuario tiene permisos para acceder a un tablero."""
    # Superadmin tiene acceso a todo
    if user.is_superuser:
        return True
    
    # Verificar permisos específicos
    business_unit = board.business_unit
    
    # Verificar si el usuario tiene permiso "super_admin" o "consultant_bu_complete" para esta BU
    has_permission = business_unit.user_permissions.filter(
        Q(user=user) & 
        (Q(role='super_admin') | Q(role='consultant_bu_complete'))
    ).exists()
    
    # Verificar también grupos
    has_group_permission = business_unit.user_permissions.filter(
        Q(group__user=user) & 
        (Q(role='super_admin') | Q(role='consultant_bu_complete'))
    ).exists()
    
    return has_permission or has_group_permission

def get_assignable_users(business_unit):
    """Obtiene la lista de usuarios que pueden ser asignados a tarjetas en esta BU."""
    # Usuarios con permisos directos
    direct_users = User.objects.filter(
        business_unit_permissions__business_unit=business_unit
    )
    
    # Usuarios con permisos a través de grupos
    group_users = User.objects.filter(
        groups__business_unit_permissions__business_unit=business_unit
    )
    
    # Combinar y eliminar duplicados
    return (direct_users | group_users).distinct()

def parse_date(date_str):
    """Convierte una cadena en formato ISO a un objeto datetime."""
    if not date_str:
        return None
    return timezone.datetime.fromisoformat(date_str)

@sync_to_async
def notify_candidate_of_status_change(card):
    """Notifica al candidato sobre un cambio de estado en su aplicación."""
    try:
        person = card.application.user
        vacancy = card.application.vacancy
        status = card.application.status
        column_name = card.column.name
        
        # Solo enviar notificación si la persona tiene un ID externo (WhatsApp, Telegram, etc.)
        if not person.external_id or not person.platform:
            logger.warning(f"No se puede notificar a persona {person.id}: Sin ID externo o plataforma")
            return False
        
        # Mensaje personalizado según el estado
        message = f"¡Hola {person.nombre}! El estado de tu aplicación para '{vacancy.titulo}' ha cambiado a '{column_name}'."
        
        if status == "interview":
            message += " ¡Felicidades! Has sido seleccionado para una entrevista. Pronto nos pondremos en contacto contigo para agendar una fecha."
        elif status == "hired":
            message += " ¡Enhorabuena! Has sido seleccionado para el puesto. Nos pondremos en contacto contigo para los siguientes pasos."
        elif status == "rejected":
            message += " Lamentablemente, tu perfil no ha sido seleccionado para continuar en el proceso. Te animamos a seguir aplicando a otras posiciones."
        
        # Enviar el mensaje
        asyncio.create_task(
            send_message(person.platform, person.external_id, message, vacancy.business_unit.key)
        )
        
        logger.info(f"Notificación enviada a {person.nombre} ({person.external_id}) sobre cambio de estado a {status}")
        return True
        
    except Exception as e:
        logger.error(f"Error al notificar al candidato: {str(e)}", exc_info=True)
        return False
