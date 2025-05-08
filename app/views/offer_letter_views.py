from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

from app.models import CartaOferta, Person, Vacante, Application, BusinessUnit
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def gestion_cartas_oferta(request):
    """
    Vista para gestionar las cartas de oferta desde el admin.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Obtener los datos necesarios
            user_id = data.get('user_id')
            vacancy_id = data.get('vacancy_id')
            salary = data.get('salary')
            benefits = data.get('benefits')
            start_date = data.get('start_date')
            canal_envio = data.get('canal_envio')
            
            # Validar datos
            if not all([user_id, vacancy_id, salary, benefits, start_date]):
                return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
            
            # Obtener objetos
            user = get_object_or_404(Person, id=user_id)
            vacancy = get_object_or_404(Vacante, id=vacancy_id)
            
            # Crear la carta de oferta
            carta = CartaOferta.objects.crear_carta_oferta(
                user=user,
                vacancy=vacancy,
                salary=salary,
                benefits=benefits,
                start_date=start_date
            )
            
            # Enviar la carta por el canal especificado
            success = CartaOferta.objects.enviar_carta_oferta(carta, canal_envio)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Carta de oferta creada y enviada exitosamente',
                    'carta_id': carta.id
                })
            else:
                return JsonResponse({'error': 'Error al enviar la carta de oferta'}, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error en gestión de cartas de oferta: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    # Obtener cartas de oferta pendientes
    cartas_pendientes = CartaOferta.objects.filter(status='pending')
    
    return render(request, 'gestion_cartas_oferta.html', {
        'cartas_pendientes': cartas_pendientes,
        'canal_envio_choices': CartaOferta.CANAL_ENVIO_CHOICES
    })

@login_required
def marcar_como_firmada(request, carta_id):
    """
    Vista para marcar una carta como firmada.
    """
    if request.method == 'POST':
        try:
            carta = get_object_or_404(CartaOferta, id=carta_id)
            carta.marcar_como_firmada()
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Error marcando carta como firmada: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def reenviar_carta(request, carta_id):
    """
    Vista para reenviar una carta de oferta.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            canal_envio = data.get('canal_envio')
            
            if not canal_envio:
                return JsonResponse({'error': 'Canal de envío requerido'}, status=400)
                
            carta = get_object_or_404(CartaOferta, id=carta_id)
            success = CartaOferta.objects.enviar_carta_oferta(carta, canal_envio)
            
            if success:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Error al reenviar la carta'}, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error reenviando carta: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def ver_carta(request, carta_id):
    """
    Vista para ver el PDF de una carta de oferta.
    """
    carta = get_object_or_404(CartaOferta, id=carta_id)
    
    if carta.pdf_file:
        with open(carta.pdf_file.path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="carta_oferta_{carta_id}.pdf"'
            return response
    
    return JsonResponse({'error': 'PDF no encontrado'}, status=404)

@csrf_exempt
@login_required
def generar_preview(request):
    """
    Vista para generar un preview de la carta de oferta.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Obtener los datos necesarios
            user_id = data.get('user_id')
            vacancy_id = data.get('vacancy_id')
            salary = data.get('salary')
            benefits = data.get('benefits')
            start_date = data.get('start_date')
            
            if not all([user_id, vacancy_id, salary, benefits, start_date]):
                return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)
            
            # Obtener objetos
            user = get_object_or_404(Person, id=user_id)
            vacancy = get_object_or_404(Vacante, id=vacancy_id)
            
            # Generar preview
            preview = render_to_string('preview_carta_oferta.html', {
                'user': user,
                'vacancy': vacancy,
                'salary': salary,
                'benefits': benefits,
                'start_date': start_date
            })
            
            return JsonResponse({'preview': preview})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error generando preview: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
