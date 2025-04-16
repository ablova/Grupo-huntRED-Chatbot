# /home/pablollh/app/views/main_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from asgiref.sync import sync_to_async
from django.template.response import TemplateResponse
from django.middleware.csrf import get_token
#from ratelimit.decorators import ratelimit

from app.models import (
    BusinessUnit, ChatState, Configuracion, Application, Vacante, Person
)
from app.chatbot.utils import analyze_text
from app.chatbot.gpt import GPTHandler
from app.chatbot.chatbot import ChatBotHandler
from app.chatbot.integrations.services import MessageService, get_business_unit

import json
import logging

logger = logging.getLogger(__name__)



@staff_member_required
def interacciones_por_unidad(request):
    """
    Vista para mostrar estadísticas de interacciones por unidad de negocio.
    """
    data = []
    units = BusinessUnit.objects.prefetch_related('chatstate_set').all()
    for unit in units:
        count = unit.chatstate_set.filter(platform__icontains=unit.name.lower()).count()
        data.append({'unidad': unit.name, 'interacciones': count})
    return render(request, 'admin/estadisticas/interacciones.html', {'data': data})

@login_required
def index(request):
    """
    Vista principal para ai.huntred.com.
    Muestra un formulario de envío de mensajes para administradores autenticados.
    """
    business_units = BusinessUnit.objects.all()
    config = Configuracion.objects.first()
    context = {
        'business_units': business_units,
        'config': config,
        'channels': ['whatsapp', 'telegram', 'messenger', 'instagram', 'slack'],
        'is_admin': request.user.is_staff  # Determina si el usuario es administrador
    }

    if request.method == 'POST' and request.user.is_staff:
        try:
            # Extraer datos del formulario
            recipient_type = request.POST.get('recipient_type')  # 'chatstate', 'person', 'direct'
            recipient_id = request.POST.get('recipient_id')  # ID o número directo
            business_unit_name = request.POST.get('business_unit')
            channel = request.POST.get('channel')
            message = request.POST.get('message')

            # Validaciones iniciales
            if not all([recipient_type, recipient_id, business_unit_name, channel, message]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Todos los campos son requeridos.'
                }, status=400)

            # Obtener BusinessUnit
            business_unit = async_to_sync(get_business_unit)(business_unit_name)
            if not business_unit:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Unidad de negocio "{business_unit_name}" no encontrada.'
                }, status=404)

            # Determinar el user_id según el tipo de destinatario
            user_id = None
            if recipient_type == 'chatstate':
                chat_state = ChatState.objects.filter(
                    id=recipient_id, business_unit=business_unit
                ).first()
                if not chat_state:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'ChatState no encontrado para esta unidad de negocio.'
                    }, status=404)
                user_id = chat_state.user_id
            elif recipient_type == 'person':
                person = Person.objects.filter(id=recipient_id).first()
                if not person or not person.phone:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Persona no encontrada o sin número de teléfono.'
                    }, status=404)
                user_id = person.phone
            elif recipient_type == 'direct':
                # Validar número de teléfono
                try:
                    parsed_number = phonenumbers.parse(recipient_id, None)
                    if not phonenumbers.is_valid_number(parsed_number):
                        raise ValueError('Número inválido')
                    user_id = phonenumbers.format_number(
                        parsed_number, phonenumbers.PhoneNumberFormat.E164
                    )
                except phonenumbers.NumberParseException:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Número de teléfono inválido.'
                    }, status=400)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tipo de destinatario inválido.'
                }, status=400)

            # Crear instancia de MessageService
            message_service = MessageService(business_unit)

            # Verificar si el canal está soportado
            api_instance = async_to_sync(message_service.get_api_instance)(channel)
            if not api_instance:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Canal "{channel}" no configurado para esta unidad de negocio.'
                }, status=400)

            # Enviar el mensaje
            success = async_to_sync(message_service.send_message)(
                platform=channel,
                user_id=user_id,
                message=message.strip()
            )

            if success:
                logger.info(f'[index] Mensaje enviado a {user_id} vía {channel} para {business_unit.name}')
                return JsonResponse({
                    'status': 'success',
                    'message': 'Mensaje enviado correctamente.'
                })
            else:
                logger.error(f'[index] Error enviando mensaje a {user_id} vía {channel}')
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error al enviar el mensaje.'
                }, status=500)

        except Exception as e:
            logger.error(f'[index] Error inesperado: {str(e)}', exc_info=True)
            return JsonResponse({
                'status': 'error',
                'message': f'Error interno: {str(e)}'
            }, status=500)

    return render(request, 'index.html', context)


def finalize_candidates(request, business_unit_id):
    """
    Finaliza el proceso de candidatos seleccionados y envía reportes.
    """
    if request.method == 'POST':
        # Supongamos que recibes una lista de IDs de candidatos a incluir
        candidates_ids = request.POST.getlist('candidates')
        recipient_email = request.POST.get('email')
        
        # Llama a la tarea de Celery
        send_final_candidate_report.delay(business_unit_id, candidates_ids, recipient_email)
        
        return redirect('success_page')
    
    # Renderiza la página de finalización si es GET
    return render(request, 'finalize_candidates.html')

def login_view(request):
    """
    Vista para autenticar a un usuario en WordPress desde la interfaz de Django.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        login_status = login(username, password)  # Asegúrate de que la función login esté importada o definida
        if login_status:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error", "message": "Login failed."})
    else:
        # Retornamos la plantilla de login para métodos GET
        return render(request, "login.html")

def submit_application(request, job_id):
    """
    Vista para manejar la aplicación de un candidato a un trabajo específico.
    """
    if request.method == 'POST':
        # Lógica para procesar la aplicación
        data = request.POST
        person_id = data.get('person_id')
        vacancy = get_object_or_404(Vacante, id=job_id)
        person = get_object_or_404(Person, id=person_id)

        application = Application.objects.create(user=person, vacancy=vacancy)
        return JsonResponse({"status": "success", "application_id": application.id})

    return render(request, 'apply.html', {'job_id': job_id})

def home(request):
    return HttpResponse("Bienvenido al sistema")
    #return render(request, 'home.html')  # Asegúrate de que la plantilla exista