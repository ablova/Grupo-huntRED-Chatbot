# /home/pablo/app/notifications/views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from app.ats.notifications.notifications_manager import NotificationsManager
from app.ats.notifications.config import NotificationsConfig
import logging

logger = logging.getLogger('app.ats.notifications.views')

@api_view(['POST'])
@csrf_exempt
def send_notification(request):
    """Endpoint para enviar una notificación."""
    try:
        data = request.data
        
        # Validar datos
        required_fields = ['recipient_type', 'recipient_id', 'notification_type', 'context']
        if not all(field in data for field in required_fields):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Inicializar gestor de notificaciones
        manager = NotificationsManager()
        
        # Enviar notificación
        success = manager.send_notification(
            data['recipient_type'],
            data['recipient_id'],
            data['notification_type'],
            data['context']
        )
        
        return Response(
            {'success': success},
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    except Exception as e:
        logger.error(f"Error in send_notification: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@csrf_exempt
def send_bulk_notifications(request):
    """Endpoint para enviar notificaciones en masa."""
    try:
        data = request.data
        
        # Validar datos
        required_fields = ['recipient_type', 'recipient_ids', 'notification_type', 'context']
        if not all(field in data for field in required_fields):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Inicializar gestor de notificaciones
        manager = NotificationsManager()
        
        # Enviar notificaciones
        results = manager.send_bulk_notifications(
            data['recipient_type'],
            data['recipient_ids'],
            data['notification_type'],
            data['context']
        )
        
        return Response(
            {'results': results},
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in send_bulk_notifications: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_notification_status(request, notification_id):
    """Endpoint para obtener el estado de una notificación."""
    try:
        # Aquí iría la lógica para obtener el estado de la notificación
        # Por ahora solo simulamos
        return Response(
            {
                'status': 'delivered',
                'timestamp': None,
                'channel': None
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in get_notification_status: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def list_templates(request):
    """Endpoint para listar todos los templates disponibles."""
    try:
        templates = NotificationsConfig.get_template_config()
        return Response(
            {'templates': templates},
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in list_templates: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def list_channels(request):
    """Endpoint para listar todos los canales disponibles."""
    try:
        channels = NotificationsConfig.get_channel_config()
        return Response(
            {'channels': channels},
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in list_channels: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def list_recipients(request):
    """Endpoint para listar todos los tipos de destinatarios."""
    try:
        recipients = NotificationsConfig.get_recipient_config()
        return Response(
            {'recipients': recipients},
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error in list_recipients: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
