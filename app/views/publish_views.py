# /home/pablo/app/views/publish_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
import json
import logging

from app.models import (
    JobOpportunity, BusinessUnit, Channel, WhatsAppAPI, TelegramAPI,
    MessengerAPI, InstagramAPI, SlackAPI
)
from app.ats.publish.tasks import process_new_job_opportunity
from app.ats.publish.utils import get_channel_processor

logger = logging.getLogger(__name__)

@staff_member_required
@login_required
def job_opportunities_list(request):
    """
    Lista de oportunidades laborales
    """
    opportunities = JobOpportunity.objects.all().order_by('-created_at')
    paginator = Paginator(opportunities, 20)
    page = request.GET.get('page', 1)
    
    context = {
        'opportunities': paginator.get_page(page),
        'business_units': BusinessUnit.objects.all(),
        'channels': Channel.objects.filter(is_active=True),
        'status_choices': JobOpportunity.STATUS_CHOICES
    }
    return render(request, 'publish/job_opportunities_list.html', context)

@staff_member_required
@login_required
def create_job_opportunity(request):
    """
    Crear una nueva oportunidad laboral
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar datos
            required_fields = ['title', 'description', 'location', 'business_unit_id']
            if not all(field in data for field in required_fields):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Campos requeridos faltantes'
                }, status=400)
            
            # Crear oportunidad
            opportunity = JobOpportunity.objects.create(
                title=data['title'],
                description=data['description'],
                requirements=data.get('requirements', ''),
                location=data['location'],
                salary=data.get('salary', ''),
                status='DRAFT',
                business_unit_id=data['business_unit_id']
            )
            
            # Procesar oportunidad en segundo plano
            process_new_job_opportunity.delay(opportunity.id)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Oportunidad creada exitosamente',
                'opportunity_id': opportunity.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error creando oportunidad: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    # GET request
    context = {
        'business_units': BusinessUnit.objects.all(),
        'channels': Channel.objects.filter(is_active=True)
    }
    return render(request, 'publish/create_job_opportunity.html', context)

@staff_member_required
@login_required
def publish_job_opportunity(request, opportunity_id):
    """
    Publicar una oportunidad laboral en canales específicos
    """
    opportunity = get_object_or_404(JobOpportunity, id=opportunity_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validar canales
            channels = data.get('channels', [])
            if not channels:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Debe seleccionar al menos un canal'
                }, status=400)
            
            # Publicar en cada canal
            for channel_id in channels:
                channel = get_object_or_404(Channel, id=channel_id)
                processor = get_channel_processor(channel.type)
                if processor:
                    processor.publish(opportunity)
            
            opportunity.status = 'PUBLISHED'
            opportunity.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Oportunidad publicada exitosamente'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error publicando oportunidad: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    # GET request
    context = {
        'opportunity': opportunity,
        'channels': Channel.objects.filter(
            business_unit=opportunity.business_unit,
            is_active=True
        )
    }
    return render(request, 'publish/publish_job_opportunity.html', context)

@staff_member_required
@login_required
def update_job_opportunity_status(request, opportunity_id):
    """
    Actualizar el estado de una oportunidad laboral
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            status = data.get('status')
            
            if status not in [s[0] for s in JobOpportunity.STATUS_CHOICES]:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Estado no válido'
                }, status=400)
            
            opportunity = get_object_or_404(JobOpportunity, id=opportunity_id)
            opportunity.status = status
            opportunity.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Estado actualizado exitosamente'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error actualizando estado: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)

@csrf_exempt
@login_required
def webhook_job_opportunity(request):
    """
    Webhook para recibir interacciones con oportunidades laborales
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Procesar interacción según el canal
            channel_type = data.get('channel_type')
            processor = get_channel_processor(channel_type)
            if processor:
                return processor.handle_webhook(data)
            
            return JsonResponse({
                'status': 'error',
                'message': 'Canal no soportado'
            }, status=400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Error en el formato JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en webhook: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Error interno del servidor'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    }, status=405)
