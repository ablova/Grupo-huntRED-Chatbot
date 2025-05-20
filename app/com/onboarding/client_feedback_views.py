"""
Vistas y endpoints para el sistema de feedback de clientes.

Este módulo maneja:
- Visualización y respuesta de encuestas de satisfacción para clientes
- Generación de reportes por Business Unit
- Dashboard de satisfacción de clientes
"""

import json
import logging
from datetime import datetime

from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.signing import Signer, BadSignature
from django.conf import settings
from asgiref.sync import sync_to_async
from django.utils.decorators import method_decorator
from django.views import View

from app.models import BusinessUnit, Empresa, Person, ClientFeedback, ClientFeedbackSchedule, CLIENT_FEEDBACK_PERIODS
from app.com.onboarding.client_feedback_controller import ClientFeedbackController

logger = logging.getLogger(__name__)
signer = Signer(salt='client-satisfaction')

@require_http_methods(["GET"])
async def client_survey_view(request):
    """
    Vista para mostrar una encuesta de satisfacción al cliente.
    Recibe un token firmado y muestra el formulario correspondiente.
    """
    token = request.GET.get('token')
    if not token:
        return HttpResponse("Token no proporcionado", status=400)
    
    try:
        # Validar token
        token_data = json.loads(signer.unsign(token))
        feedback_id = token_data.get('feedback_id')
        
        if not feedback_id:
            return HttpResponse("Token inválido o incompleto", status=400)
        
        # Obtener datos para la encuesta
        @sync_to_async
        def get_survey_data():
            feedback = get_object_or_404(ClientFeedback, id=feedback_id)
            empresa = feedback.empresa
            business_unit = feedback.business_unit
            respondent = feedback.respondent
            
            # Si ya respondió esta encuesta, mostrar mensaje de agradecimiento
            if feedback.status == 'COMPLETED':
                return {
                    'already_answered': True,
                    'client_name': respondent.first_name if respondent else empresa.name
                }
            
            # Obtener URL del logo
            logo_url = f"{settings.STATIC_URL}images/logo.png"
            
            return {
                'already_answered': False,
                'token': token,
                'business_unit': business_unit,
                'client_name': respondent.first_name if respondent else empresa.name,
                'client_id': respondent.id if respondent else None,
                'logo_url': logo_url,
                'form_action': '/onboarding/client-survey/submit/',
                'year': datetime.now().year
            }
        
        context = await get_survey_data()
        
        if context.get('already_answered'):
            return render(request, 'onboarding/satisfaction_already_submitted.html', context)
        
        return render(request, 'onboarding/client_satisfaction_survey.html', context)
        
    except BadSignature:
        return HttpResponse("Token inválido o expirado", status=400)
    except Exception as e:
        logger.error(f"Error mostrando encuesta de cliente: {str(e)}")
        return HttpResponse("Error al procesar la solicitud", status=500)

@csrf_exempt
@require_http_methods(["POST"])
async def client_survey_submit(request):
    """
    Endpoint para recibir respuestas de la encuesta de clientes.
    Procesa los datos y los guarda en el modelo correspondiente.
    """
    token = request.POST.get('token')
    if not token:
        return JsonResponse({"success": False, "error": "Token no proporcionado"}, status=400)
    
    try:
        # Extraer datos del formulario
        form_data = {
            'general_satisfaction': request.POST.get('general_satisfaction'),
            'candidate_quality': request.POST.get('candidate_quality'),
            'recruitment_speed': request.POST.get('recruitment_speed'),
            'clear_communication': request.POST.get('clear_communication'),
            'candidate_adaptation': request.POST.get('candidate_adaptation'),
            'would_recommend': request.POST.get('would_recommend'),
            'improvement_suggestions': request.POST.get('improvement_suggestions', ''),
            'submitted_at': timezone.now().isoformat()
        }
        
        # Procesar respuesta
        result = await ClientFeedbackController.process_feedback_response(token, form_data)
        
        # Si es una solicitud AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)
        
        # Si no es AJAX, redirigir a página de agradecimiento
        if result.get('success'):
            return HttpResponseRedirect('/onboarding/client-survey/thanks/')
        else:
            return HttpResponse(f"Error: {result.get('error')}", status=400)
    
    except Exception as e:
        logger.error(f"Error procesando encuesta de cliente: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "error": str(e)}, status=500)
        return HttpResponse(f"Error al procesar la solicitud: {str(e)}", status=500)

@require_http_methods(["GET"])
async def client_survey_thanks(request):
    """Vista de agradecimiento tras enviar una encuesta de cliente."""
    context = {
        'year': datetime.now().year,
        'logo_url': f"{settings.STATIC_URL}images/logo.png"
    }
    return render(request, 'onboarding/satisfaction_thanks.html', context)

@method_decorator(login_required, name='dispatch')
class ClientFeedbackView(View):
    """Vista para gestionar el feedback de clientes."""
    
    async def get(self, request, feedback_id=None):
        """Obtiene información de un feedback específico o lista todos."""
        try:
            if feedback_id:
                # Obtener detalles de un feedback específico
                @sync_to_async
                def get_feedback():
                    feedback = get_object_or_404(ClientFeedback, id=feedback_id)
                    return {
                        'id': feedback.id,
                        'empresa': {
                            'id': feedback.empresa.id,
                            'name': feedback.empresa.name
                        },
                        'business_unit': {
                            'id': feedback.business_unit.id,
                            'name': feedback.business_unit.name
                        },
                        'respondent': str(feedback.respondent) if feedback.respondent else None,
                        'period_days': feedback.period_days,
                        'status': feedback.status,
                        'satisfaction_score': feedback.satisfaction_score,
                        'sent_date': feedback.sent_date.isoformat() if feedback.sent_date else None,
                        'completed_date': feedback.completed_date.isoformat() if feedback.completed_date else None,
                        'responses': feedback.responses,
                        'improvement_areas': feedback.get_improvement_areas()
                    }
                
                result = await get_feedback()
                return JsonResponse(result)
            else:
                # Filtrar por Business Unit si se proporciona
                business_unit_id = request.GET.get('business_unit_id')
                empresa_id = request.GET.get('empresa_id')
                
                filters = {}
                if business_unit_id:
                    filters['business_unit_id'] = business_unit_id
                if empresa_id:
                    filters['empresa_id'] = empresa_id
                
                @sync_to_async
                def get_feedback_list():
                    feedback_list = ClientFeedback.objects.filter(
                        **filters
                    ).select_related('empresa', 'business_unit', 'respondent')[:100]
                    
                    return [
                        {
                            'id': fb.id,
                            'empresa': fb.empresa.name,
                            'business_unit': fb.business_unit.name,
                            'period_days': fb.period_days,
                            'status': fb.status,
                            'satisfaction_score': fb.satisfaction_score,
                            'sent_date': fb.sent_date.isoformat() if fb.sent_date else None,
                            'completed_date': fb.completed_date.isoformat() if fb.completed_date else None
                        }
                        for fb in feedback_list
                    ]
                
                result = await get_feedback_list()
                return JsonResponse({'feedback_list': result})
                
        except Exception as e:
            logger.error(f"Error en ClientFeedbackView.get: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    async def post(self, request):
        """Crea una nueva programación de feedback para un cliente."""
        try:
            data = json.loads(request.body)
            empresa_id = data.get('empresa_id')
            business_unit_id = data.get('business_unit_id')
            respondent_id = data.get('respondent_id')
            start_date_str = data.get('start_date')
            
            # Validar datos requeridos
            if not empresa_id or not business_unit_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Se requieren empresa_id y business_unit_id'
                }, status=400)
            
            # Procesar fecha si se proporciona
            start_date = None
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Formato de fecha inválido. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            # Crear programación
            result = await ClientFeedbackController.schedule_client_feedback(
                empresa_id=empresa_id,
                business_unit_id=business_unit_id,
                start_date=start_date,
                respondent_id=respondent_id
            )
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido en el cuerpo de la solicitud'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en ClientFeedbackView.post: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class ClientFeedbackReportView(View):
    """Vista para generar reportes de satisfacción por Business Unit."""
    
    async def get(self, request, business_unit_id):
        """Genera un reporte de satisfacción para una Business Unit específica."""
        try:
            # Obtener fechas del período
            start_date_str = request.GET.get('start_date')
            end_date_str = request.GET.get('end_date')
            
            start_date = None
            end_date = None
            
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Formato de fecha de inicio inválido'
                    }, status=400)
            
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Formato de fecha de fin inválido'
                    }, status=400)
            
            # Generar reporte
            report_data = await ClientFeedbackController.generate_bu_satisfaction_report(
                business_unit_id=business_unit_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Determinar formato de salida
            output_format = request.GET.get('format', 'json')
            
            if output_format == 'html':
                # Renderizar como HTML
                context = {
                    'report': report_data,
                    'year': datetime.now().year,
                    'logo_url': f"{settings.STATIC_URL}images/logo.png"
                }
                return render(request, 'onboarding/client_satisfaction_report.html', context)
            else:
                # Devolver como JSON
                return JsonResponse(report_data)
                
        except Exception as e:
            logger.error(f"Error en ClientFeedbackReportView.get: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class SendClientFeedbackView(View):
    """Vista para enviar encuestas de satisfacción a clientes."""
    
    async def post(self, request, feedback_id):
        """Envía una encuesta de satisfacción específica."""
        try:
            result = await ClientFeedbackController.send_feedback_survey(feedback_id)
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error enviando encuesta de cliente: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    async def get(self, request):
        """Verifica encuestas pendientes de envío."""
        try:
            result = await ClientFeedbackController.check_pending_feedback()
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error verificando encuestas pendientes: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
