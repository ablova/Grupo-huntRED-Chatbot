"""
Vistas y endpoints para el sistema de onboarding y satisfacción.

Este módulo maneja:
- Visualización y respuesta de encuestas de satisfacción
- Generación de reportes
- Panel de control para procesos de onboarding
"""

import json
import logging
from datetime import datetime

from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.signing import Signer, BadSignature
from django.conf import settings
from asgiref.sync import sync_to_async
from django.utils.decorators import method_decorator
from django.views import View

from app.models import OnboardingProcess, OnboardingTask, Person, Vacante, BusinessUnit
from app.ats.onboarding.onboarding_controller import OnboardingController
from app.ats.onboarding.models import OnboardingProcess
from app.ats.onboarding.managers import OnboardingManager
from app.ats.notifications.notification_manager import NotificationManager

logger = logging.getLogger(__name__)
signer = Signer(salt='onboarding-satisfaction')

@require_http_methods(["GET"])
async def survey_view(request):
    """
    Vista para mostrar una encuesta de satisfacción al candidato.
    Recibe un token firmado y muestra el formulario correspondiente.
    """
    token = request.GET.get('token')
    if not token:
        return HttpResponse("Token no proporcionado", status=400)
    
    try:
        # Validar token
        token_data = json.loads(signer.unsign(token))
        onboarding_id = token_data.get('onboarding_id')
        period = token_data.get('period')
        
        if not onboarding_id or not period:
            return HttpResponse("Token inválido o incompleto", status=400)
        
        # Obtener datos para la encuesta
        @sync_to_async
        def get_survey_data():
            process = get_object_or_404(OnboardingProcess, id=onboarding_id)
            person = process.person
            vacancy = process.vacancy
            
            # Si ya respondió esta encuesta, mostrar mensaje de agradecimiento
            if str(period) in process.survey_responses:
                return {
                    'already_answered': True,
                    'person_name': f"{person.first_name} {person.last_name}"
                }
            
            # Obtener información de la empresa
            company_name = vacancy.empresa.name if hasattr(vacancy, 'empresa') and vacancy.empresa else "la empresa"
            
            # Obtener URL del logo
            logo_url = f"{settings.STATIC_URL}images/logo.png"
            
            return {
                'already_answered': False,
                'token': token,
                'onboarding_id': onboarding_id,
                'period': period,
                'person_name': f"{person.first_name} {person.last_name}",
                'company': company_name,
                'day_count': period,
                'logo_url': logo_url,
                'form_action': '/onboarding/survey/submit/',
                'year': datetime.now().year
            }
        
        context = await get_survey_data()
        
        if context.get('already_answered'):
            return render(request, 'onboarding/satisfaction_already_submitted.html', context)
        
        return render(request, 'onboarding/satisfaction_survey.html', context)
        
    except BadSignature:
        return HttpResponse("Token inválido o expirado", status=400)
    except Exception as e:
        logger.error(f"Error mostrando encuesta: {str(e)}")
        return HttpResponse("Error al procesar la solicitud", status=500)

@csrf_exempt
@require_http_methods(["POST"])
async def survey_submit(request):
    """
    Endpoint para recibir respuestas de la encuesta.
    Procesa los datos y los guarda en el modelo correspondiente.
    """
    token = request.POST.get('token')
    if not token:
        return JsonResponse({"success": False, "error": "Token no proporcionado"}, status=400)
    
    try:
        # Extraer datos del formulario
        form_data = {
            'general_satisfaction': request.POST.get('general_satisfaction'),
            'position_match': request.POST.get('position_match'),
            'team_integration': request.POST.get('team_integration'),
            'resources': request.POST.get('resources'),
            'onboarding_quality': request.POST.get('onboarding_quality'),
            'comments': request.POST.get('comments', ''),
            'submitted_at': timezone.now().isoformat()
        }
        
        # Procesar respuesta
        result = await OnboardingController.process_survey_response(token, form_data)
        
        # Si es una solicitud AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)
        
        # Si no es AJAX, redirigir a página de agradecimiento
        if result.get('success'):
            return HttpResponseRedirect('/onboarding/survey/thanks/')
        else:
            return HttpResponse(f"Error: {result.get('error')}", status=400)
    
    except Exception as e:
        logger.error(f"Error procesando encuesta: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "error": str(e)}, status=500)
        return HttpResponse(f"Error al procesar la solicitud: {str(e)}", status=500)

@require_http_methods(["GET"])
async def survey_thanks(request):
    """Vista de agradecimiento tras enviar una encuesta."""
    context = {
        'year': datetime.now().year,
        'logo_url': f"{settings.STATIC_URL}images/logo.png"
    }
    return render(request, 'onboarding/satisfaction_thanks.html', context)

@login_required
@require_http_methods(["GET"])
async def satisfaction_report(request, onboarding_id):
    """
    Genera y muestra un reporte de satisfacción para un proceso de onboarding.
    Requiere autenticación.
    """
    period = request.GET.get('period')
    period = int(period) if period and period.isdigit() else None
    
    # Generar reporte
    report_response = await OnboardingController.generate_satisfaction_report(onboarding_id, period)
    return report_response

class OnboardingView(View):
    """Vista para gestionar procesos de onboarding."""
    
    @method_decorator(login_required)
    async def get(self, request, onboarding_id=None):
        """Obtiene información de un proceso específico o lista todos."""
        try:
            if onboarding_id:
                # Obtener detalles de un proceso específico
                result = await OnboardingController.get_onboarding_status(onboarding_id)
                return JsonResponse(result)
            else:
                # Listar todos los procesos
                @sync_to_async
                def get_processes():
                    processes = OnboardingProcess.objects.all().order_by('-hire_date')[:50]
                    return [
                        {
                            'id': p.id,
                            'person': str(p.person),
                            'vacancy': p.vacancy.title,
                            'hire_date': p.hire_date.isoformat(),
                            'status': p.status,
                            'satisfaction': p.get_satisfaction_score()
                        }
                        for p in processes
                    ]
                
                processes = await get_processes()
                return JsonResponse({'processes': processes})
        
        except Exception as e:
            logger.error(f"Error en OnboardingView.get: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    @method_decorator(login_required)
    async def post(self, request):
        """Crea un nuevo proceso de onboarding."""
        try:
            data = json.loads(request.body)
            person_id = data.get('person_id')
            vacancy_id = data.get('vacancy_id')
            hire_date_str = data.get('hire_date')
            
            # Validar datos requeridos
            if not person_id or not vacancy_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Se requieren person_id y vacancy_id'
                }, status=400)
            
            # Procesar fecha si se proporciona
            hire_date = None
            if hire_date_str:
                try:
                    hire_date = datetime.fromisoformat(hire_date_str)
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Formato de fecha inválido. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
                    }, status=400)
            
            # Crear proceso
            result = await OnboardingController.start_onboarding_process(
                person_id=person_id,
                vacancy_id=vacancy_id,
                hire_date=hire_date
            )
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido en el cuerpo de la solicitud'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en OnboardingView.post: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    @method_decorator(login_required)
    async def put(self, request, onboarding_id):
        """Actualiza un proceso de onboarding existente."""
        try:
            data = json.loads(request.body)
            
            @sync_to_async
            def update_process():
                process = get_object_or_404(OnboardingProcess, id=onboarding_id)
                
                # Actualizar campos si se proporcionan
                if 'status' in data:
                    process.status = data['status']
                
                if 'consultant_id' in data:
                    process.consultant_id = data['consultant_id']
                
                if 'notes' in data:
                    process.notes = data['notes']
                
                process.save()
                return {
                    'success': True,
                    'id': process.id,
                    'status': process.status
                }
            
            result = await update_process()
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido en el cuerpo de la solicitud'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en OnboardingView.put: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

class OnboardingTaskView(View):
    """Vista para gestionar tareas de onboarding."""
    
    @method_decorator(login_required)
    async def get(self, request, task_id=None):
        """Obtiene información de una tarea específica o lista por proceso."""
        try:
            if task_id:
                # Obtener detalles de una tarea específica
                @sync_to_async
                def get_task():
                    task = get_object_or_404(OnboardingTask, id=task_id)
                    return {
                        'id': task.id,
                        'title': task.title,
                        'description': task.description,
                        'status': task.status,
                        'due_date': task.due_date.isoformat() if task.due_date else None,
                        'priority': task.priority,
                        'onboarding_id': task.onboarding_id,
                        'assigned_to': str(task.assigned_to) if task.assigned_to else None,
                        'is_overdue': task.is_overdue(),
                        'days_remaining': task.get_days_remaining(),
                        'notes': task.notes
                    }
                
                task_data = await get_task()
                return JsonResponse(task_data)
            else:
                # Listar tareas por proceso
                onboarding_id = request.GET.get('onboarding_id')
                if not onboarding_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Se requiere onboarding_id para listar tareas'
                    }, status=400)
                
                @sync_to_async
                def get_tasks():
                    tasks = OnboardingTask.objects.filter(onboarding_id=onboarding_id)
                    return [
                        {
                            'id': t.id,
                            'title': t.title,
                            'status': t.status,
                            'due_date': t.due_date.isoformat() if t.due_date else None,
                            'priority': t.priority,
                            'is_overdue': t.is_overdue()
                        }
                        for t in tasks
                    ]
                
                tasks = await get_tasks()
                return JsonResponse({'tasks': tasks})
        
        except Exception as e:
            logger.error(f"Error en OnboardingTaskView.get: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    @method_decorator(login_required)
    async def post(self, request):
        """Crea una nueva tarea de onboarding."""
        try:
            data = json.loads(request.body)
            
            # Validar datos requeridos
            required_fields = ['onboarding_id', 'title']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Campo requerido: {field}'
                    }, status=400)
            
            @sync_to_async
            def create_task():
                # Crear tarea
                task = OnboardingTask.objects.create(
                    onboarding_id=data['onboarding_id'],
                    title=data['title'],
                    description=data.get('description', ''),
                    assigned_to_id=data.get('assigned_to_id'),
                    due_date=datetime.fromisoformat(data['due_date']) if 'due_date' in data else None,
                    status=data.get('status', 'PENDING'),
                    priority=data.get('priority', 5),
                    notes=data.get('notes', '')
                )
                
                return {
                    'success': True,
                    'id': task.id,
                    'title': task.title,
                    'status': task.status
                }
            
            result = await create_task()
            return JsonResponse(result)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Error de formato: {str(e)}'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en OnboardingTaskView.post: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    @method_decorator(login_required)
    async def put(self, request, task_id):
        """Actualiza una tarea existente."""
        try:
            data = json.loads(request.body)
            
            @sync_to_async
            def update_task():
                task = get_object_or_404(OnboardingTask, id=task_id)
                
                # Actualizar campos si se proporcionan
                for field in ['title', 'description', 'assigned_to_id', 'status', 'priority', 'notes']:
                    if field in data:
                        setattr(task, field, data[field])
                
                # Manejo especial para due_date
                if 'due_date' in data:
                    task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
                
                # Si se marca como completada
                if data.get('status') == 'COMPLETED' and task.status != 'COMPLETED':
                    task.completion_date = timezone.now()
                    
                task.save()
                
                return {
                    'success': True,
                    'id': task.id,
                    'status': task.status
                }
            
            result = await update_task()
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'JSON inválido en el cuerpo de la solicitud'
            }, status=400)
        except Exception as e:
            logger.error(f"Error en OnboardingTaskView.put: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    @method_decorator(login_required)
    async def delete(self, request, task_id):
        """Elimina una tarea."""
        try:
            @sync_to_async
            def delete_task():
                task = get_object_or_404(OnboardingTask, id=task_id)
                task_id = task.id
                task.delete()
                return {'success': True, 'id': task_id}
            
            result = await delete_task()
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error en OnboardingTaskView.delete: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
async def onboarding_dashboard(request):
    """
    Vista para el dashboard de onboarding.
    """
    try:
        business_unit = request.user.business_unit
        onboarding_manager = OnboardingManager(business_unit)
        
        # Obtener procesos de onboarding activos
        active_onboarding = await sync_to_async(OnboardingProcess.objects.filter)(
            business_unit=business_unit,
            status__in=['in_progress', 'pending']
        ).select_related('person')
        
        # Obtener procesos de onboarding completados
        completed_onboarding = await sync_to_async(OnboardingProcess.objects.filter)(
            business_unit=business_unit,
            status='completed'
        ).select_related('person')
        
        context = {
            'active_onboarding': active_onboarding,
            'completed_onboarding': completed_onboarding,
        }
        
        return render(request, 'onboarding/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en onboarding_dashboard: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
async def onboarding_detail(request, onboarding_id):
    """
    Vista para ver los detalles de un proceso de onboarding.
    """
    try:
        business_unit = request.user.business_unit
        onboarding = await sync_to_async(OnboardingProcess.objects.get)(
            id=onboarding_id,
            business_unit=business_unit
        )
        
        context = {
            'onboarding': onboarding,
            'person': onboarding.person,
            'check_ins': onboarding.check_ins,
            'completed_steps': onboarding.completed_steps,
            'feedback_data': onboarding.feedback_data
        }
        
        return render(request, 'onboarding/detail.html', context)
        
    except OnboardingProcess.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Proceso de onboarding no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en onboarding_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
async def complete_onboarding_step(request, onboarding_id):
    """
    Vista para marcar un paso de onboarding como completado.
    """
    try:
        business_unit = request.user.business_unit
        onboarding_manager = OnboardingManager(business_unit)
        
        step = request.POST.get('step')
        if not step:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere el paso a completar'
            }, status=400)
        
        result = await onboarding_manager.complete_step(
            person=request.user,
            step=step
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en complete_onboarding_step: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
async def perform_check_in(request, onboarding_id):
    """
    Vista para realizar un check-in de onboarding.
    """
    try:
        business_unit = request.user.business_unit
        onboarding_manager = OnboardingManager(business_unit)
        
        onboarding = await sync_to_async(OnboardingProcess.objects.get)(
            id=onboarding_id,
            business_unit=business_unit
        )
        
        result = await onboarding_manager.perform_check_in(
            person=request.user,
            onboarding=onboarding
        )
        
        return JsonResponse(result)
        
    except OnboardingProcess.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Proceso de onboarding no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en perform_check_in: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET", "POST"])
async def candidato_feedback(request, onboarding_id):
    """
    Vista para manejar el feedback del candidato.
    """
    try:
        onboarding = await sync_to_async(OnboardingProcess.objects.get)(id=onboarding_id)
        
        if request.method == "POST":
            feedback_data = {
                'general_rating': request.POST.get('general_rating'),
                'induction_rating': request.POST.get('induction_rating'),
                'check_in_rating': request.POST.get('check_in_rating'),
                'improvements': request.POST.get('improvements'),
                'useful_aspects': request.POST.get('useful_aspects'),
                'recommendation_rating': request.POST.get('recommendation_rating')
            }
            
            await onboarding.add_feedback('candidato', feedback_data)
            
            return JsonResponse({
                'success': True,
                'message': 'Feedback enviado exitosamente'
            })
        
        return render(request, 'notifications/candidato_feedback_survey.html', {
            'onboarding': onboarding,
            'recipient': onboarding.person
        })
        
    except OnboardingProcess.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Proceso de onboarding no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en candidato_feedback: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET", "POST"])
async def cliente_feedback(request, empresa_id):
    """
    Vista para manejar el feedback del cliente.
    """
    try:
        empresa = await sync_to_async(BusinessUnit.objects.get)(id=empresa_id)
        
        if request.method == "POST":
            feedback_data = {
                'candidate_quality': request.POST.get('candidate_quality'),
                'process_satisfaction': request.POST.get('process_satisfaction'),
                'communication_rating': request.POST.get('communication_rating'),
                'improvements': request.POST.get('improvements'),
                'useful_aspects': request.POST.get('useful_aspects'),
                'recommendation_rating': request.POST.get('recommendation_rating'),
                'suggestions': request.POST.get('suggestions')
            }
            
            # Guardar feedback del cliente
            notification_manager = NotificationManager(empresa)
            await notification_manager.send_notification(
                notification_type='CLIENTE_FEEDBACK_RECIBIDO',
                recipient=empresa.contact_person,
                context={
                    'feedback_data': feedback_data,
                    'empresa_id': empresa.id
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Feedback enviado exitosamente'
            })
        
        return render(request, 'notifications/cliente_feedback_survey.html', {
            'empresa': empresa,
            'recipient': empresa.contact_person
        })
        
    except BusinessUnit.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Empresa no encontrada'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en cliente_feedback: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
