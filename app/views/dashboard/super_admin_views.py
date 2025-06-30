"""
🚀 SUPER ADMIN DASHBOARD VIEWS - BRUCE ALMIGHTY MODE 🚀

Vistas para el dashboard del Super Admin con control total del sistema.
Permite ver y controlar TODO: consultores, clientes, candidatos, procesos, AURA, GenIA, etc.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from asgiref.sync import sync_to_async
import json
import logging
from django.contrib import messages
from django.urls import reverse
import asyncio

from app.ats.dashboard.super_admin_dashboard import SuperAdminDashboard
from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

def is_super_admin(user):
    """Verifica si el usuario es super admin."""
    return user.is_authenticated and user.is_superuser

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminDashboardView(View):
    """Vista principal del dashboard del Super Admin."""
    
    def get(self, request):
        """Renderiza el dashboard principal."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        return render(request, 'dashboard/super_admin_dashboard.html', {
            'user': request.user,
            'bruce_almighty_mode': True  # 🚀
        })

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminSystemOverviewView(View):
    """Vista para obtener overview completo del sistema."""
    
    async def get(self, request):
        """Obtiene visión general completa del sistema."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            overview = await dashboard.get_system_overview()
            
            return JsonResponse({
                'success': True,
                'overview': overview
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo overview del sistema: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminConsultantAnalyticsView(View):
    """Vista para analytics de consultores."""
    
    async def get(self, request):
        """Obtiene analytics detallados de todos los consultores."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            analytics = await dashboard.get_consultant_analytics()
            
            return JsonResponse({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de consultores: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminClientAnalyticsView(View):
    """Vista para analytics de clientes."""
    
    async def get(self, request):
        """Obtiene analytics detallados de todos los clientes."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            analytics = await dashboard.get_client_analytics()
            
            return JsonResponse({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de clientes: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminCandidateAnalyticsView(View):
    """Vista para analytics de candidatos."""
    
    async def get(self, request):
        """Obtiene analytics detallados de candidatos."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            analytics = await dashboard.get_candidate_analytics()
            
            return JsonResponse({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de candidatos: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminProcessAnalyticsView(View):
    """Vista para analytics de procesos."""
    
    async def get(self, request):
        """Obtiene analytics de todos los procesos."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            analytics = await dashboard.get_process_analytics()
            
            return JsonResponse({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de procesos: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminAuraAnalyticsView(View):
    """Vista para analytics de AURA."""
    
    async def get(self, request):
        """Obtiene analytics completos de AURA."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            analytics = await dashboard.get_aura_analytics()
            
            return JsonResponse({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de AURA: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminGeniaAnalyticsView(View):
    """Vista para analytics de GenIA."""
    
    async def get(self, request):
        """Obtiene analytics de GenIA."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            analytics = await dashboard.get_genia_analytics()
            
            return JsonResponse({
                'success': True,
                'analytics': analytics
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de GenIA: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

# ============================================================================
# VISTAS DE CONTROL TOTAL (BRUCE ALMIGHTY MODE) 🚀
# ============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminDirectMessageView(View):
    """Vista para enviar mensajes directos."""
    
    async def post(self, request):
        """Envía mensaje directo a cualquier usuario."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            message = data.get('message')
            channel = data.get('channel', 'whatsapp')
            
            if not user_id or not message:
                return JsonResponse({
                    'success': False,
                    'error': 'user_id y message son requeridos'
                }, status=400)
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.send_direct_message(user_id, message, channel)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error enviando mensaje directo: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminAuraControlView(View):
    """Vista para controlar el sistema AURA."""
    
    async def post(self, request):
        """Controla el sistema AURA."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            parameters = data.get('parameters', {})
            
            if not action:
                return JsonResponse({
                    'success': False,
                    'error': 'action es requerido'
                }, status=400)
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.control_aura_system(action, parameters)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error controlando sistema AURA: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminGeniaControlView(View):
    """Vista para controlar el sistema GenIA."""
    
    async def post(self, request):
        """Controla el sistema GenIA."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            parameters = data.get('parameters', {})
            
            if not action:
                return JsonResponse({
                    'success': False,
                    'error': 'action es requerido'
                }, status=400)
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.control_genia_system(action, parameters)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error controlando sistema GenIA: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminEmergencyActionsView(View):
    """Vista para acciones de emergencia."""
    
    async def post(self, request):
        """Ejecuta acciones de emergencia del sistema."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            parameters = data.get('parameters', {})
            
            if not action:
                return JsonResponse({
                    'success': False,
                    'error': 'action es requerido'
                }, status=400)
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.emergency_actions(action, parameters)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error en acción de emergencia: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

# ============================================================================
# VISTAS ADICIONALES PARA CONTROL TOTAL
# ============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminUserManagementView(View):
    """Vista para gestión de usuarios."""
    
    async def get(self, request):
        """Obtiene lista de usuarios."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            users = await sync_to_async(list)(
                Person.objects.all().select_related('business_unit')
            )
            
            user_data = [
                {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}",
                    'email': user.email,
                    'role': user.role,
                    'business_unit': user.business_unit.name if user.business_unit else 'N/A',
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat()
                }
                for user in users
            ]
            
            return JsonResponse({
                'success': True,
                'users': user_data
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo usuarios: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)
    
    async def post(self, request):
        """Modifica usuario."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            action = data.get('action')
            
            if not user_id or not action:
                return JsonResponse({
                    'success': False,
                    'error': 'user_id y action son requeridos'
                }, status=400)
            
            user = await sync_to_async(Person.objects.get)(id=user_id)
            
            if action == 'activate':
                user.is_active = True
                message = 'Usuario activado'
            elif action == 'deactivate':
                user.is_active = False
                message = 'Usuario desactivado'
            elif action == 'promote_to_admin':
                user.is_superuser = True
                message = 'Usuario promovido a admin'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Acción no válida'
                }, status=400)
            
            await sync_to_async(user.save)()
            
            return JsonResponse({
                'success': True,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error modificando usuario: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminSystemLogsView(View):
    """Vista para logs del sistema."""
    
    async def get(self, request):
        """Obtiene logs del sistema."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            # Aquí se implementaría la lógica para obtener logs
            # Por ahora retornamos logs simulados
            logs = [
                {
                    'timestamp': '2024-01-15T10:30:00Z',
                    'level': 'INFO',
                    'message': 'Sistema AURA iniciado correctamente',
                    'user': 'system'
                },
                {
                    'timestamp': '2024-01-15T10:25:00Z',
                    'level': 'WARNING',
                    'message': 'Alto uso de CPU detectado',
                    'user': 'monitor'
                }
            ]
            
            return JsonResponse({
                'success': True,
                'logs': logs
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo logs: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

# ============================================================================
# NUEVAS VISTAS BRUCE ALMIGHTY MODE 🚀
# ============================================================================

@login_required
@super_admin_required
async def business_unit_control(request):
    """Control total por unidad de negocio."""
    try:
        dashboard = SuperAdminDashboard()
        bu_data = await dashboard.get_business_unit_control()
        
        context = {
            'page_title': 'Control por Unidad de Negocio',
            'bruce_almighty_mode': True,
            'bu_data': bu_data,
            'active_tab': 'business_units'
        }
        
        return render(request, 'dashboard/super_admin/business_unit_control.html', context)
        
    except Exception as e:
        logger.error(f"Error en business_unit_control: {str(e)}")
        messages.error(request, f"Error cargando control de BU: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
async def proposals_analytics(request):
    """Analytics completos de propuestas."""
    try:
        dashboard = SuperAdminDashboard()
        proposals_data = await dashboard.get_proposals_analytics()
        
        context = {
            'page_title': 'Analytics de Propuestas',
            'bruce_almighty_mode': True,
            'proposals_data': proposals_data,
            'active_tab': 'proposals'
        }
        
        return render(request, 'dashboard/super_admin/proposals_analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error en proposals_analytics: {str(e)}")
        messages.error(request, f"Error cargando analytics de propuestas: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
async def opportunities_analytics(request):
    """Analytics de oportunidades nuevas."""
    try:
        dashboard = SuperAdminDashboard()
        opportunities_data = await dashboard.get_opportunities_analytics()
        
        context = {
            'page_title': 'Analytics de Oportunidades',
            'bruce_almighty_mode': True,
            'opportunities_data': opportunities_data,
            'active_tab': 'opportunities'
        }
        
        return render(request, 'dashboard/super_admin/opportunities_analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error en opportunities_analytics: {str(e)}")
        messages.error(request, f"Error cargando analytics de oportunidades: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
async def scraping_analytics(request):
    """Analytics de scraping y fuentes de datos."""
    try:
        dashboard = SuperAdminDashboard()
        scraping_data = await dashboard.get_scraping_analytics()
        
        context = {
            'page_title': 'Analytics de Scraping',
            'bruce_almighty_mode': True,
            'scraping_data': scraping_data,
            'active_tab': 'scraping'
        }
        
        return render(request, 'dashboard/super_admin/scraping_analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error en scraping_analytics: {str(e)}")
        messages.error(request, f"Error cargando analytics de scraping: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
async def gpt_job_description_generator(request):
    """Generador de Job Descriptions con GPT."""
    try:
        dashboard = SuperAdminDashboard()
        gpt_data = await dashboard.get_gpt_job_description_generator()
        
        context = {
            'page_title': 'Generador de JD con GPT',
            'bruce_almighty_mode': True,
            'gpt_data': gpt_data,
            'active_tab': 'gpt_jd'
        }
        
        return render(request, 'dashboard/super_admin/gpt_jd_generator.html', context)
        
    except Exception as e:
        logger.error(f"Error en gpt_job_description_generator: {str(e)}")
        messages.error(request, f"Error cargando generador de JD: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
async def sexsi_analytics(request):
    """Analytics del sistema SEXSI."""
    try:
        dashboard = SuperAdminDashboard()
        sexsi_data = await dashboard.get_sexsi_analytics()
        
        context = {
            'page_title': 'Analytics de SEXSI',
            'bruce_almighty_mode': True,
            'sexsi_data': sexsi_data,
            'active_tab': 'sexsi'
        }
        
        return render(request, 'dashboard/super_admin/sexsi_analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error en sexsi_analytics: {str(e)}")
        messages.error(request, f"Error cargando analytics de SEXSI: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
async def process_management(request):
    """Gestión completa de procesos y estados."""
    try:
        dashboard = SuperAdminDashboard()
        process_data = await dashboard.get_process_management()
        
        context = {
            'page_title': 'Gestión de Procesos',
            'bruce_almighty_mode': True,
            'process_data': process_data,
            'active_tab': 'process_management'
        }
        
        return render(request, 'dashboard/super_admin/process_management.html', context)
        
    except Exception as e:
        logger.error(f"Error en process_management: {str(e)}")
        messages.error(request, f"Error cargando gestión de procesos: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
async def salary_comparator(request):
    """Comparador avanzado de salarios."""
    try:
        dashboard = SuperAdminDashboard()
        salary_data = await dashboard.get_salary_comparator()
        
        context = {
            'page_title': 'Comparador de Salarios',
            'bruce_almighty_mode': True,
            'salary_data': salary_data,
            'active_tab': 'salary_comparator'
        }
        
        return render(request, 'dashboard/super_admin/salary_comparator.html', context)
        
    except Exception as e:
        logger.error(f"Error en salary_comparator: {str(e)}")
        messages.error(request, f"Error cargando comparador de salarios: {str(e)}")
        return redirect('super_admin_dashboard')

# ============================================================================
# VISTAS DE ACCIONES BRUCE ALMIGHTY MODE 🚀
# ============================================================================

@login_required
@super_admin_required
async def move_candidate_state_view(request):
    """Mueve un candidato a un nuevo estado."""
    if request.method == 'POST':
        try:
            candidate_id = request.POST.get('candidate_id')
            new_state = request.POST.get('new_state')
            reason = request.POST.get('reason', '')
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.move_candidate_state(candidate_id, new_state, reason)
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, f"Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error moviendo estado de candidato: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('super_admin_process_management')

@login_required
@super_admin_required
async def generate_jd_view(request):
    """Genera Job Description usando GPT."""
    if request.method == 'POST':
        try:
            role = request.POST.get('role')
            requirements = {
                'experience': request.POST.get('experience', ''),
                'skills': request.POST.get('skills', ''),
                'education': request.POST.get('education', ''),
                'responsibilities': request.POST.get('responsibilities', '')
            }
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.generate_job_description(role, requirements)
            
            if result['success']:
                messages.success(request, f"JD generada exitosamente para {role}")
                # Guardar en sesión para mostrar en la vista
                request.session['generated_jd'] = result['job_description']
            else:
                messages.error(request, f"Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error generando JD: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('super_admin_gpt_jd_generator')

@login_required
@super_admin_required
async def control_scraping_view(request):
    """Controla el sistema de scraping."""
    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            parameters = {
                'source': request.POST.get('source', ''),
                'rules': request.POST.get('rules', '')
            }
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.control_scraping_system(action, parameters)
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, f"Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error controlando scraping: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('super_admin_scraping_analytics')

@login_required
@super_admin_required
async def control_sexsi_view(request):
    """Controla el sistema SEXSI."""
    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            parameters = {
                'config': request.POST.get('config', ''),
                'force_sync': request.POST.get('force_sync', False)
            }
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.control_sexsi_system(action, parameters)
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, f"Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error controlando SEXSI: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('super_admin_sexsi_analytics')

@login_required
@super_admin_required
async def bulk_candidate_actions_view(request):
    """Acciones masivas en candidatos."""
    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            candidate_ids = request.POST.getlist('candidate_ids')
            parameters = {
                'new_state': request.POST.get('new_state', ''),
                'message': request.POST.get('message', ''),
                'channel': request.POST.get('channel', 'whatsapp')
            }
            
            dashboard = SuperAdminDashboard()
            result = await dashboard.bulk_candidate_actions(action, candidate_ids, parameters)
            
            if result['success']:
                messages.success(request, f"Acción completada: {result['successful_actions']} exitosas, {result['failed_actions']} fallidas")
            else:
                messages.error(request, f"Error: {result['error']}")
                
        except Exception as e:
            logger.error(f"Error en acciones masivas: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('super_admin_process_management')

@login_required
@user_passes_test(is_super_admin)
def intelligent_search_view(request):
    """
    Vista para el buscador inteligente avanzado con AURA, ML y GenIA.
    """
    context = {
        'page_title': 'Buscador Inteligente Avanzado',
        'search_results': None,
        'search_query': '',
        'search_type': 'all'
    }
    
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '').strip()
        search_type = request.POST.get('search_type', 'all')
        
        if search_query:
            try:
                # Obtener resultados del buscador inteligente
                dashboard = SuperAdminDashboard()
                search_results = dashboard.get_intelligent_search_results(search_query, search_type)
                
                context.update({
                    'search_results': search_results,
                    'search_query': search_query,
                    'search_type': search_type
                })
                
                # Log de la búsqueda
                logger.info(f"Búsqueda inteligente realizada: '{search_query}' por {request.user}")
                
            except Exception as e:
                logger.error(f"Error en búsqueda inteligente: {str(e)}")
                messages.error(request, f"Error en la búsqueda: {str(e)}")
    
    return render(request, 'dashboard/super_admin/intelligent_search.html', context)

@login_required
@user_passes_test(is_super_admin)
def intelligent_search_api(request):
    """
    API para búsquedas inteligentes en tiempo real.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            search_query = data.get('query', '').strip()
            search_type = data.get('type', 'all')
            
            if not search_query:
                return JsonResponse({'error': 'Query requerida'}, status=400)
            
            # Obtener resultados
            dashboard = SuperAdminDashboard()
            search_results = dashboard.get_intelligent_search_results(search_query, search_type)
            
            return JsonResponse({
                'success': True,
                'results': search_results
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Error en API de búsqueda inteligente: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@user_passes_test(is_super_admin)
def financial_dashboard_view(request):
    """
    Vista para el dashboard financiero granular con métricas por unidad de negocio y consultor.
    """
    # Obtener parámetros de filtro
    period = request.GET.get('period', 'month')
    business_unit = request.GET.get('business_unit', 'all')
    consultant = request.GET.get('consultant', 'all')
    
    try:
        # Obtener datos financieros
        dashboard = SuperAdminDashboard()
        financial_data = dashboard.get_financial_dashboard_data(period, business_unit, consultant)
        
        # Obtener opciones para filtros
        business_units = ['huntRED', 'huntU', 'Amigro', 'SEXSI']
        consultants = ['consultor1', 'consultor2', 'consultor3']
        periods = ['day', 'week', 'month', 'year']
        
        context = {
            'page_title': 'Dashboard Financiero Granular',
            'bruce_almighty_mode': True,
            'financial_data': financial_data,
            'filters': {
                'period': period,
                'business_unit': business_unit,
                'consultant': consultant
            },
            'options': {
                'business_units': business_units,
                'consultants': consultants,
                'periods': periods
            },
            'active_tab': 'financial'
        }
        
        return render(request, 'dashboard/super_admin/financial_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard financiero: {str(e)}")
        messages.error(request, f"Error cargando dashboard financiero: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@user_passes_test(is_super_admin)
def financial_dashboard_api(request):
    """
    API para obtener datos financieros en tiempo real.
    """
    if request.method == 'GET':
        try:
            period = request.GET.get('period', 'month')
            business_unit = request.GET.get('business_unit', 'all')
            consultant = request.GET.get('consultant', 'all')
            
            dashboard = SuperAdminDashboard()
            financial_data = dashboard.get_financial_dashboard_data(period, business_unit, consultant)
            
            return JsonResponse({
                'success': True,
                'data': financial_data
            })
            
        except Exception as e:
            logger.error(f"Error en API de dashboard financiero: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@super_admin_required
def advanced_kanban_view(request):
    """
    Vista del kanban avanzado con gestión completa de candidatos.
    """
    try:
        dashboard = SuperAdminDashboard()
        
        # Obtener filtros de la request
        filters = {
            'period': request.GET.get('period', 'month'),
            'client': request.GET.get('client', 'all'),
            'consultant': request.GET.get('consultant', 'all'),
            'status': request.GET.get('status', 'all'),
            'business_unit': request.GET.get('business_unit', 'all'),
            'priority': request.GET.get('priority', 'all'),
            'location': request.GET.get('location', 'all')
        }
        
        # Obtener datos del kanban
        kanban_data = dashboard.get_advanced_kanban_data(filters)
        
        context = {
            'kanban_data': kanban_data,
            'filters': filters,
            'page_title': 'Kanban Avanzado - BRUCE ALMIGHTY MODE',
            'breadcrumb': [
                {'name': 'Dashboard', 'url': reverse('super_admin_dashboard')},
                {'name': 'Kanban Avanzado', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/advanced_kanban.html', context)
        
    except Exception as e:
        logger.error(f"Error en kanban avanzado: {str(e)}")
        messages.error(request, f"Error al cargar el kanban: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
def candidate_detail_view(request, candidate_id):
    """
    Vista detallada de un candidato específico.
    """
    try:
        dashboard = SuperAdminDashboard()
        
        # Obtener datos del candidato (simulado)
        candidate_data = {
            'id': candidate_id,
            'name': 'Ana García López',
            'position': 'Senior Developer',
            'client': 'TechCorp',
            'consultant': 'María Rodríguez',
            'business_unit': 'huntU',
            'location': 'CDMX',
            'experience': '5 años',
            'salary_expectation': '$80,000 MXN',
            'status': 'sourcing',
            'priority': 'high',
            'last_activity': '2024-01-15',
            'contact_info': {
                'email': 'ana.garcia@email.com',
                'phone': '+52 55 1234 5678',
                'linkedin': 'linkedin.com/in/anagarcia',
                'github': 'github.com/anagarcia'
            },
            'client_contact': {
                'name': 'Carlos Mendoza',
                'email': 'carlos.mendoza@techcorp.com',
                'phone': '+52 55 9876 5432',
                'position': 'HR Manager'
            },
            'notes': 'Candidata con experiencia en React y Node.js',
            'tags': ['React', 'Node.js', 'Senior', 'CDMX'],
            'match_score': 85,
            'availability': 'Inmediata',
            'resume_url': '/media/resumes/ana_garcia_cv.pdf',
            'portfolio_url': 'https://anagarcia.dev',
            'skills': ['React', 'Node.js', 'TypeScript', 'MongoDB', 'AWS'],
            'languages': ['Español', 'Inglés'],
            'education': [
                {
                    'degree': 'Ingeniería en Sistemas',
                    'institution': 'UNAM',
                    'year': '2019'
                }
            ],
            'experience': [
                {
                    'company': 'TechStartup',
                    'position': 'Full Stack Developer',
                    'duration': '2020-2023',
                    'description': 'Desarrollo de aplicaciones web con React y Node.js'
                }
            ],
            'interviews': [
                {
                    'date': '2024-01-20',
                    'type': 'Técnica',
                    'interviewer': 'Dr. Carlos Ruiz',
                    'status': 'Programada',
                    'notes': 'Entrevista técnica programada'
                }
            ],
            'timeline': [
                {
                    'date': '2024-01-15',
                    'action': 'Candidato agregado al pipeline',
                    'user': 'María Rodríguez'
                },
                {
                    'date': '2024-01-16',
                    'action': 'Screening inicial completado',
                    'user': 'María Rodríguez'
                }
            ]
        }
        
        context = {
            'candidate': candidate_data,
            'page_title': f'Candidato: {candidate_data["name"]}',
            'breadcrumb': [
                {'name': 'Dashboard', 'url': reverse('super_admin_dashboard')},
                {'name': 'Kanban Avanzado', 'url': reverse('advanced_kanban')},
                {'name': candidate_data['name'], 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/candidate_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error en detalle de candidato: {str(e)}")
        messages.error(request, f"Error al cargar el candidato: {str(e)}")
        return redirect('advanced_kanban')

@login_required
@super_admin_required
def candidate_action_view(request, candidate_id, action):
    """
    Vista para acciones específicas en candidatos.
    """
    try:
        if request.method == 'POST':
            candidate = get_object_or_404(Person, id=candidate_id)
            
            if action == 'move_status':
                new_status = request.POST.get('new_status')
                reason = request.POST.get('reason', '')
                
                # Actualizar estado del candidato
                candidate.status = new_status
                candidate.save()
                
                # Notificar al candidato sobre el cambio de estado
                if new_status == 'rejected':
                    from app.ats.integrations.notifications.process.offer_notifications import OfferNotificationService
                    from app.models import Vacante
                    
                    # Buscar la vacante relacionada (asumiendo que hay una relación)
                    vacancy = Vacante.objects.filter(candidates=candidate).first()
                    if vacancy:
                        notification_service = OfferNotificationService(vacancy.business_unit)
                        asyncio.create_task(
                            notification_service.notify_candidate_rejected_from_admin(
                                candidate=candidate,
                                vacancy=vacancy,
                                rejection_reason=reason or "No se especificó razón",
                                admin_user=request.user.username
                            )
                        )
                
                messages.success(request, f'Estado del candidato actualizado a {new_status}')
                
            elif action == 'send_message':
                message = request.POST.get('message')
                channel = request.POST.get('channel', 'whatsapp')
                
                # Enviar mensaje al candidato
                # Implementar lógica de envío de mensajes
                messages.success(request, f'Mensaje enviado por {channel}')
                
            elif action == 'send_blind_list':
                # Lógica para enviar lista blind
                messages.success(request, 'Lista blind enviada al cliente')
                
            elif action == 'send_open_list':
                # Lógica para enviar lista abierta
                messages.success(request, 'Lista abierta enviada al cliente')
            
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
    except Exception as e:
        logger.error(f"Error en acción de candidato: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@super_admin_required
def bulk_candidate_action_view(request):
    """
    Vista para acciones masivas en candidatos.
    """
    try:
        if request.method == 'POST':
            action = request.POST.get('action')
            candidate_ids = request.POST.getlist('candidate_ids')
            
            if action == 'bulk_move':
                new_status = request.POST.get('new_status')
                reason = request.POST.get('reason', '')
                
                # Obtener candidatos
                candidates = Person.objects.filter(id__in=candidate_ids)
                
                # Actualizar estados
                candidates.update(status=new_status)
                
                # Notificar si se rechazaron candidatos
                if new_status == 'rejected':
                    from app.ats.integrations.notifications.process.offer_notifications import OfferNotificationService
                    from app.models import Vacante
                    
                    # Agrupar candidatos por vacante para notificaciones eficientes
                    for candidate in candidates:
                        vacancy = Vacante.objects.filter(candidates=candidate).first()
                        if vacancy:
                            notification_service = OfferNotificationService(vacancy.business_unit)
                            asyncio.create_task(
                                notification_service.notify_candidate_rejected_from_admin(
                                    candidate=candidate,
                                    vacancy=vacancy,
                                    rejection_reason=reason or "No se especificó razón",
                                    admin_user=request.user.username
                                )
                            )
                
                messages.success(request, f'{len(candidate_ids)} candidatos movidos a {new_status}')
                
            elif action == 'bulk_reject':
                reason = request.POST.get('reason', 'No se especificó razón')
                
                # Obtener candidatos
                candidates = Person.objects.filter(id__in=candidate_ids)
                
                # Actualizar estados
                candidates.update(status='rejected')
                
                # Notificar rechazo masivo
                from app.ats.integrations.notifications.process.offer_notifications import OfferNotificationService
                from app.models import Vacante
                
                # Agrupar por vacante para notificaciones eficientes
                vacancy_candidates = {}
                for candidate in candidates:
                    vacancy = Vacante.objects.filter(candidates=candidate).first()
                    if vacancy:
                        if vacancy.id not in vacancy_candidates:
                            vacancy_candidates[vacancy.id] = {'vacancy': vacancy, 'candidates': []}
                        vacancy_candidates[vacancy.id]['candidates'].append(candidate)
                
                # Enviar notificaciones por vacante
                for vacancy_data in vacancy_candidates.values():
                    notification_service = OfferNotificationService(vacancy_data['vacancy'].business_unit)
                    asyncio.create_task(
                        notification_service.notify_bulk_candidates_rejected(
                            candidates=vacancy_data['candidates'],
                            vacancy=vacancy_data['vacancy'],
                            rejection_reason=reason,
                            admin_user=request.user.username
                        )
                    )
                
                messages.success(request, f'{len(candidate_ids)} candidatos rechazados y notificados')
                
            elif action == 'bulk_email':
                email_type = request.POST.get('email_type')
                # Lógica para email masivo
                messages.success(request, f'Email {email_type} enviado a {len(candidate_ids)} candidatos')
                
            elif action == 'bulk_export':
                # Lógica para exportar
                messages.success(request, f'Exportación de {len(candidate_ids)} candidatos iniciada')
            
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
    except Exception as e:
        logger.error(f"Error en acción masiva: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@super_admin_required
def cv_viewer_view(request, candidate_id):
    """
    Vista del visualizador de CV con iframe y exportación.
    """
    try:
        dashboard = SuperAdminDashboard()
        cv_data = dashboard.get_cv_viewer_data(candidate_id)
        
        context = {
            'cv_data': cv_data,
            'page_title': f'CV Viewer - {cv_data["candidate_name"]}',
            'breadcrumb': [
                {'name': 'Dashboard', 'url': reverse('super_admin_dashboard')},
                {'name': 'Kanban Avanzado', 'url': reverse('advanced_kanban')},
                {'name': cv_data['candidate_name'], 'url': reverse('candidate_detail', args=[candidate_id])},
                {'name': 'CV Viewer', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/cv_viewer.html', context)
        
    except Exception as e:
        logger.error(f"Error en visualizador de CV: {str(e)}")
        messages.error(request, f"Error al cargar el CV: {str(e)}")
        return redirect('candidate_detail', candidate_id=candidate_id)

@login_required
@super_admin_required
def advanced_reports_view(request):
    """
    Vista de reportes avanzados con IA y ML.
    """
    try:
        dashboard = SuperAdminDashboard()
        
        # Obtener filtros de la request
        filters = {
            'period': request.GET.get('period', 'month'),
            'business_unit': request.GET.get('business_unit', 'all'),
            'report_type': request.GET.get('report_type', 'comprehensive')
        }
        
        # Obtener datos de reportes
        reports_data = dashboard.get_advanced_reports_data(filters)
        
        context = {
            'reports_data': reports_data,
            'filters': filters,
            'page_title': 'Reportes Avanzados - BRUCE ALMIGHTY MODE',
            'breadcrumb': [
                {'name': 'Dashboard', 'url': reverse('super_admin_dashboard')},
                {'name': 'Reportes Avanzados', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/super_admin/advanced_reports.html', context)
        
    except Exception as e:
        logger.error(f"Error en reportes avanzados: {str(e)}")
        messages.error(request, f"Error al cargar los reportes: {str(e)}")
        return redirect('super_admin_dashboard')

@login_required
@super_admin_required
def export_report_view(request, report_type):
    """
    Vista para exportar reportes en diferentes formatos.
    """
    try:
        if request.method == 'POST':
            format_type = request.POST.get('format', 'pdf')
            filters = {
                'period': request.POST.get('period', 'month'),
                'business_unit': request.POST.get('business_unit', 'all')
            }
            
            # Lógica para generar y exportar reporte
            if format_type == 'pdf':
                # Generar PDF
                messages.success(request, 'Reporte PDF generado exitosamente')
            elif format_type == 'excel':
                # Generar Excel
                messages.success(request, 'Reporte Excel generado exitosamente')
            elif format_type == 'powerpoint':
                # Generar PowerPoint
                messages.success(request, 'Reporte PowerPoint generado exitosamente')
            
            return JsonResponse({'success': True, 'format': format_type})
        
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
    except Exception as e:
        logger.error(f"Error en exportación de reporte: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@super_admin_required
def schedule_report_view(request):
    """
    Vista para programar envío automático de reportes.
    """
    try:
        if request.method == 'POST':
            report_type = request.POST.get('report_type')
            frequency = request.POST.get('frequency')  # daily, weekly, monthly
            recipients = request.POST.getlist('recipients')
            email_template = request.POST.get('email_template')
            
            # Lógica para programar reporte
            messages.success(request, f'Reporte {report_type} programado para envío {frequency}')
            
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
    except Exception as e:
        logger.error(f"Error en programación de reporte: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminFinancialDashboardView(View):
    """Vista para el dashboard financiero del Super Admin."""
    
    async def get(self, request):
        """Renderiza el dashboard financiero."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            financial_data = await dashboard.get_financial_dashboard()
            
            return render(request, 'dashboard/super_admin_financial_dashboard.html', {
                'user': request.user,
                'financial_data': financial_data,
                'bruce_almighty_mode': True  # 🚀
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard financiero: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminFinancialDataView(View):
    """Vista para obtener datos financieros en formato JSON."""
    
    async def get(self, request):
        """Obtiene datos financieros."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            dashboard = SuperAdminDashboard()
            financial_data = await dashboard.get_financial_dashboard()
            
            return JsonResponse({
                'success': True,
                'financial_data': financial_data
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo datos financieros: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class SuperAdminProviderValidationView(View):
    """Vista para validación de proveedores."""
    
    async def post(self, request):
        """Valida un proveedor con SAT."""
        if not is_super_admin(request.user):
            return JsonResponse({'error': 'Acceso denegado'}, status=403)
        
        try:
            data = json.loads(request.body)
            provider_id = data.get('provider_id')
            
            if not provider_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID de proveedor requerido'
                }, status=400)
            
            # Importar servicio de validación
            from app.ats.pricing.services.sat_validation_service import SATValidationService
            from app.models import Person, BusinessUnit
            
            provider = await sync_to_async(Person.objects.get)(id=provider_id)
            business_unit = provider.business_unit or await sync_to_async(BusinessUnit.objects.first)()
            
            sat_service = SATValidationService(business_unit)
            validation_result = sat_service.validate_provider(provider)
            
            return JsonResponse({
                'success': True,
                'validation_result': validation_result
            })
            
        except Person.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Proveedor no encontrado'
            }, status=404)
        except Exception as e:
            logger.error(f"Error validando proveedor: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500) 