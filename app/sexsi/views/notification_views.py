# Ubicacion SEXSI -- /home/pablo/app/sexsi/views/notification_views.py
"""
Vistas para manejo de notificaciones en SEXSI.
"""
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from app.sexsi.models import Notification

@method_decorator(login_required, name='dispatch')
class NotificationMarkAsReadView(View):
    """
    Vista para marcar una notificación como leída.
    """
    def post(self, request, pk):
        """
        Marca una notificación como leída.
        """
        try:
            notification = get_object_or_404(Notification, id=pk, recipient=request.user)
            notification.is_read = True
            notification.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Notificación marcada como leída'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

@method_decorator(login_required, name='dispatch')
class NotificationDeleteView(View):
    """
    Vista para eliminar una notificación.
    """
    def post(self, request, pk):
        """
        Elimina una notificación.
        """
        try:
            notification = get_object_or_404(Notification, id=pk, recipient=request.user)
            notification.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Notificación eliminada exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
