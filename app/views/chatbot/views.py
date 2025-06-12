"""
Vistas para el sistema de chatbot.

Responsabilidades:
- Gestión de conversaciones
- Perfilamiento de candidatos
- Integración con ATS
- Manejo de estados de conversación
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.core.cache import caches
from django_ratelimit.decorators import ratelimit
from django_prometheus import exports

from app.ats.decorators import (
    bu_complete_required, bu_division_required,
    permission_required, verified_user_required
)
from app.models import (
    ChatState, Person, BusinessUnit,
    Application, Interview
)
from app.ats.chatbot.conversational_flow import ConversationalFlowManager
from app.ats.integrations.services import MessageService
from app.ats.chatbot.utils import analyze_text

import logging
import json
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class ChatbotViews(View):
    """
    Vistas principales del sistema de chatbot.
    """
    
    def __init__(self):
        super().__init__()
        self.message_service = MessageService()
        self.flow_manager = ConversationalFlowManager()
        
    @method_decorator(csrf_exempt)
    @method_decorator(ratelimit(key='ip', rate='5/m'))
    async def process_message(self, request, platform):
        """
        Procesa mensajes del chatbot.
        
        Args:
            request: HttpRequest
            platform: str - Plataforma de mensajería
            
        Returns:
            JsonResponse: Respuesta con el estado de la operación
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            user_id = data.get('user_id')
            text = data.get('text')
            bu_name = data.get('business_unit')
            
            if not all([user_id, text, bu_name]):
                return JsonResponse({'error': 'Parámetros requeridos faltantes'}, status=400)
            
            # Obtener o crear persona
            person = await sync_to_async(Person.objects.get_or_create)(
                external_id=user_id,
                defaults={'name': 'Desconocido'}
            )
            
            # Obtener business unit
            bu = await sync_to_async(BusinessUnit.objects.get)(name=bu_name)
            
            # Procesar mensaje
            result = await self.flow_manager.process_message(person, text)
            
            if result['success']:
                # Enviar respuesta
                await self.message_service.send_message(
                    platform,
                    user_id,
                    result['response']['text']
                )
                
                # Actualizar estado de chat
                chat_state = await sync_to_async(ChatState.objects.get_or_create)(
                    person=person,
                    platform=platform,
                    business_unit=bu
                )
                
                # Si es una aplicación, crear registro
                if result['response'].get('application_created'):
                    await sync_to_async(Application.objects.create)(
                        person=person,
                        vacante=result['response']['vacante'],
                        status=ApplicationStatus.PENDING
                    )
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except BusinessUnit.DoesNotExist:
            return JsonResponse({'error': 'Unidad de negocio no encontrada'}, status=404)
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return JsonResponse({'error': 'Error interno del servidor'}, status=500)
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    def chat_history(self, request, person_id):
        """
        Muestra el historial de chat de un candidato.
        """
        person = get_object_or_404(Person, id=person_id)
        chat_states = ChatState.objects.filter(
            person=person
        ).select_related('business_unit')
        
        applications = Application.objects.filter(
            person=person
        ).select_related('vacante')
        
        interviews = Interview.objects.filter(
            application__person=person
        ).select_related('application')
        
        context = {
            'person': person,
            'chat_states': chat_states,
            'applications': applications,
            'interviews': interviews
        }
        return render(request, 'chatbot/chat_history.html', context)
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    def analytics(self, request):
        """
        Muestra métricas y análisis del chatbot.
        """
        cache = caches['default']
        cached_data = cache.get('chatbot_analytics')
        
        if cached_data is None:
            data = {
                'total_conversations': ChatState.objects.count(),
                'active_conversations': ChatState.objects.filter(
                    last_message__gte=timezone.now() - timezone.timedelta(hours=24)
                ).count(),
                'applications_created': Application.objects.filter(
                    created_at__gte=timezone.now() - timezone.timedelta(days=7)
                ).count(),
                'interviews_scheduled': Interview.objects.filter(
                    created_at__gte=timezone.now() - timezone.timedelta(days=7)
                ).count()
            }
            cache.set('chatbot_analytics', data, timeout=300)
        else:
            data = cached_data
        
        return render(request, 'chatbot/analytics.html', {'data': data})
