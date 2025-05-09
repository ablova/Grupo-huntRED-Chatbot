from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
import json
import logging
from asgiref.sync import sync_to_async
from app.chatbot.conversational_flow import ConversationalFlowManager
from app.chatbot.integrations.services import MessageService
from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

class ChatbotView(View):
    """
    Vista principal del chatbot que maneja las interacciones con diferentes plataformas.
    
    Características:
    - Manejo de mensajes de diferentes plataformas
    - Procesamiento de intents
    - Gestión de estados
    - Manejo de errores
    """

    def __init__(self):
        super().__init__()
        self.message_service = MessageService()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    async def post(self, request, platform):
        """
        Maneja las peticiones POST del chatbot.
        
        Args:
            request: HttpRequest
            platform (str): Plataforma de mensajería (whatsapp, telegram, etc.)
            
        Returns:
            JsonResponse: Respuesta con el estado de la operación
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            user_id = data.get('user_id')
            text = data.get('text')
            bu_name = data.get('business_unit')

            if not all([user_id, text, bu_name]):
                return JsonResponse({'error': 'Missing required parameters'}, status=400)

            # Obtener o crear el usuario
            person = await sync_to_async(Person.objects.get_or_create)(
                external_id=user_id,
                defaults={'name': 'Unknown User'}
            )

            # Obtener el business unit
            bu = await sync_to_async(BusinessUnit.objects.get)(name=bu_name)

            # Inicializar gestor de flujo conversacional
            flow_manager = ConversationalFlowManager(bu)
            
            # Procesar el mensaje
            result = await flow_manager.process_message(person, text)
            
            if result['success']:
                # Enviar respuesta usando el servicio de mensajes
                await self.message_service.send_message(
                    platform,
                    user_id,
                    result['response']['text']
                )
                
                # Si hay opciones, enviarlas
                if result['response'].get('options'):
                    await self.message_service.send_options(
                        platform,
                        user_id,
                        result['response']['text'],
                        result['response']['options']
                    )
            
            return JsonResponse({'status': 'success'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except BusinessUnit.DoesNotExist:
            return JsonResponse({'error': 'Business unit not found'}, status=404)
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return JsonResponse({'error': 'Internal server error'}, status=500)

    async def _show_job_options(self, platform: str, user_id: str, bu_name: str, person: Person) -> None:
        """Muestra las opciones de vacantes disponibles."""
        try:
            # Obtener vacantes recomendadas
            recommended_jobs = await sync_to_async(vacante_service.get_recommended_jobs)(person)
            
            if not recommended_jobs:
                await send_message(platform, user_id, "No hay vacantes recomendadas actualmente.", bu_name)
                return
                
            # Crear mensaje con opciones
            message = "Vacantes recomendadas:\n\n"
            for i, job in enumerate(recommended_jobs, 1):
                score = await sync_to_async(matching_service.calculate_match_score)(person, job)
                message += f"{i}. {job['title']} (Puntaje: {score:.2f})\n"
                
            message += "\nIngresa el número de la vacante que te interesa."
            await send_message(platform, user_id, message, bu_name)
            
        except Exception as e:
            logger.error(f"Error showing job options: {e}")
            await send_message(platform, user_id, "Lo siento, ha ocurrido un error al mostrar las vacantes.", bu_name)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except BusinessUnit.DoesNotExist:
            return JsonResponse({'error': 'Business unit not found'}, status=404)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    def get(self, request, platform):
        """Maneja las peticiones GET para verificación inicial."""
        return JsonResponse({'status': 'ok'})

@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    async def post(self, request):
        """Maneja los webhooks de los gateways de pago y otros servicios."""
        try:
            data = json.loads(request.body.decode('utf-8'))
            event_type = data.get('event_type')
            
            if event_type == 'payment_status_changed':
                await self._handle_payment_status_changed(data)
            elif event_type == 'job_application':
                await self._handle_job_application(data)
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

    async def _handle_payment_status_changed(self, data):
        """Maneja cambios en el estado de un pago."""
        payment_id = data.get('payment_id')
        new_status = data.get('status')
        
        # Actualizar el estado del pago
        await sync_to_async(Pago.objects.filter(id=payment_id).update)(
            estado=new_status,
            fecha_actualizacion=timezone.now()
        )

    async def _handle_job_application(self, data):
        """Maneja nuevas aplicaciones a vacantes."""
        job_id = data.get('job_id')
        candidate_id = data.get('candidate_id')
        
        # Crear evento de aplicación
        event = await sync_to_async(Event.objects.create)(
            event_type=EventType.CHECKIN,
            title=f"Nueva aplicación a vacante",
            description=f"Candidato {candidate_id} aplicó a la vacante {job_id}",
            start_time=timezone.now(),
            status=EventStatus.COMPLETADO
        )
        
        await sync_to_async(EventParticipant.objects.create)(
            event=event,
            person_id=candidate_id,
            status=EventStatus.COMPLETADO
        )
