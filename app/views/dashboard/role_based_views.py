"""
Vistas específicas por rol con control de acceso y funcionalidades limitadas.
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
import json

from app.ats.dashboard.consultant_dashboard import ConsultantSeniorDashboard
from app.ats.dashboard.client_dashboard import ClientDashboard
from app.ats.dashboard.super_admin_dashboard import SuperAdminDashboard

logger = logging.getLogger(__name__)

def is_consultant_senior(user):
    """Verifica si el usuario es consultor senior."""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'consultant_senior'

def is_client(user):
    """Verifica si el usuario es cliente."""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'client'

def is_super_admin(user):
    """Verifica si el usuario es super administrador."""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'super_admin'

# ============================================================================
# VISTAS PARA CONSULTORES SENIOR
# ============================================================================

@login_required
@user_passes_test(is_consultant_senior)
def consultant_dashboard(request):
    """
    Dashboard principal para consultores senior.
    """
    try:
        consultant_id = request.user.id
        dashboard = ConsultantSeniorDashboard(consultant_id)
        
        # Obtener datos del dashboard
        summary_data = dashboard.get_consultant_dashboard_summary()
        
        context = {
            'dashboard_data': summary_data,
            'user_role': 'consultant_senior',
            'page_title': 'Dashboard Consultor Senior',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/consultant_senior/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de consultor: {str(e)}")
        messages.error(request, 'Error al cargar el dashboard')
        return redirect('home')

@login_required
@user_passes_test(is_consultant_senior)
def consultant_kanban(request):
    """
    Kanban avanzado para consultores senior.
    """
    try:
        consultant_id = request.user.id
        dashboard = ConsultantSeniorDashboard(consultant_id)
        
        # Obtener filtros
        filters = {
            'period': request.GET.get('period', 'month'),
            'status': request.GET.get('status', 'all'),
            'priority': request.GET.get('priority', 'all'),
            'client': request.GET.get('client', 'all')
        }
        
        # Obtener datos del kanban
        kanban_data = dashboard.get_consultant_kanban_data(filters)
        
        context = {
            'kanban_data': kanban_data,
            'user_role': 'consultant_senior',
            'page_title': 'Kanban Avanzado',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'consultant_dashboard'},
                {'name': 'Kanban', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/consultant_senior/kanban.html', context)
        
    except Exception as e:
        logger.error(f"Error en kanban de consultor: {str(e)}")
        messages.error(request, 'Error al cargar el kanban')
        return redirect('consultant_dashboard')

@login_required
@user_passes_test(is_consultant_senior)
def consultant_cv_viewer(request, candidate_id):
    """
    Visualizador de CV para consultores senior.
    """
    try:
        consultant_id = request.user.id
        dashboard = ConsultantSeniorDashboard(consultant_id)
        
        # Obtener datos del CV
        cv_data = dashboard.get_consultant_cv_data(candidate_id)
        
        if 'error' in cv_data:
            messages.error(request, cv_data['error'])
            return redirect('consultant_kanban')
        
        context = {
            'cv_data': cv_data,
            'user_role': 'consultant_senior',
            'page_title': f'CV - {cv_data["candidate_name"]}',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'consultant_dashboard'},
                {'name': 'Kanban', 'url': 'consultant_kanban'},
                {'name': 'CV Viewer', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/consultant_senior/cv_viewer.html', context)
        
    except Exception as e:
        logger.error(f"Error en CV viewer de consultor: {str(e)}")
        messages.error(request, 'Error al cargar el CV')
        return redirect('consultant_kanban')

@login_required
@user_passes_test(is_consultant_senior)
def consultant_reports(request):
    """
    Reportes para consultores senior.
    """
    try:
        consultant_id = request.user.id
        dashboard = ConsultantSeniorDashboard(consultant_id)
        
        # Obtener filtros
        filters = {
            'period': request.GET.get('period', 'month'),
            'report_type': request.GET.get('report_type', 'performance')
        }
        
        # Obtener datos de reportes
        reports_data = dashboard.get_consultant_reports_data(filters)
        
        context = {
            'reports_data': reports_data,
            'user_role': 'consultant_senior',
            'page_title': 'Mis Reportes',
            'breadcrumbs': [
                {'name': 'Dashboard', 'url': 'consultant_dashboard'},
                {'name': 'Reportes', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/consultant_senior/reports.html', context)
        
    except Exception as e:
        logger.error(f"Error en reportes de consultor: {str(e)}")
        messages.error(request, 'Error al cargar los reportes')
        return redirect('consultant_dashboard')

# ============================================================================
# VISTAS PARA CLIENTES
# ============================================================================

@login_required
@user_passes_test(is_client)
def client_dashboard(request):
    """
    Dashboard principal para clientes.
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        # Obtener datos del dashboard
        summary_data = dashboard.get_client_dashboard_summary()
        
        context = {
            'dashboard_data': summary_data,
            'user_role': 'client',
            'page_title': 'Portal Cliente',
            'breadcrumbs': [
                {'name': 'Portal Cliente', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/client/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard de cliente: {str(e)}")
        messages.error(request, 'Error al cargar el portal')
        return redirect('home')

@login_required
@user_passes_test(is_client)
def client_kanban(request):
    """
    Kanban simplificado para clientes.
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        # Obtener filtros
        filters = {
            'period': request.GET.get('period', 'month'),
            'status': request.GET.get('status', 'all'),
            'position': request.GET.get('position', 'all')
        }
        
        # Obtener datos del kanban
        kanban_data = dashboard.get_client_kanban_data(filters)
        
        context = {
            'kanban_data': kanban_data,
            'user_role': 'client',
            'page_title': 'Mis Candidatos',
            'breadcrumbs': [
                {'name': 'Portal Cliente', 'url': 'client_dashboard'},
                {'name': 'Candidatos', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/client/kanban.html', context)
        
    except Exception as e:
        logger.error(f"Error en kanban de cliente: {str(e)}")
        messages.error(request, 'Error al cargar los candidatos')
        return redirect('client_dashboard')

@login_required
@user_passes_test(is_client)
def client_cv_viewer(request, candidate_id):
    """
    Visualizador de CV para clientes (limitado).
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        # Obtener datos del CV
        cv_data = dashboard.get_client_cv_data(candidate_id)
        
        if 'error' in cv_data:
            messages.error(request, cv_data['error'])
            return redirect('client_kanban')
        
        context = {
            'cv_data': cv_data,
            'user_role': 'client',
            'page_title': f'CV - {cv_data["candidate_name"]}',
            'breadcrumbs': [
                {'name': 'Portal Cliente', 'url': 'client_dashboard'},
                {'name': 'Candidatos', 'url': 'client_kanban'},
                {'name': 'CV', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/client/cv_viewer.html', context)
        
    except Exception as e:
        logger.error(f"Error en CV viewer de cliente: {str(e)}")
        messages.error(request, 'Error al cargar el CV')
        return redirect('client_kanban')

@login_required
@user_passes_test(is_client)
def client_reports(request):
    """
    Reportes para clientes (limitados).
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        # Obtener filtros
        filters = {
            'period': request.GET.get('period', 'month'),
            'report_type': request.GET.get('report_type', 'process')
        }
        
        # Obtener datos de reportes
        reports_data = dashboard.get_client_reports_data(filters)
        
        context = {
            'reports_data': reports_data,
            'user_role': 'client',
            'page_title': 'Mis Reportes',
            'breadcrumbs': [
                {'name': 'Portal Cliente', 'url': 'client_dashboard'},
                {'name': 'Reportes', 'url': '#'}
            ]
        }
        
        return render(request, 'dashboard/client/reports.html', context)
        
    except Exception as e:
        logger.error(f"Error en reportes de cliente: {str(e)}")
        messages.error(request, 'Error al cargar los reportes')
        return redirect('client_dashboard')

# ============================================================================
# VISTAS PARA SUPER ADMIN (REDIRECCIÓN)
# ============================================================================

@login_required
@user_passes_test(is_super_admin)
def super_admin_redirect(request):
    """
    Redirección al dashboard de super admin.
    """
    return redirect('super_admin_dashboard')

# ============================================================================
# API ENDPOINTS PARA CONSULTORES SENIOR
# ============================================================================

@login_required
@user_passes_test(is_consultant_senior)
@csrf_exempt
def consultant_api_kanban_data(request):
    """
    API para obtener datos del kanban del consultor.
    """
    try:
        consultant_id = request.user.id
        dashboard = ConsultantSeniorDashboard(consultant_id)
        
        if request.method == 'POST':
            filters = json.loads(request.body)
        else:
            filters = {
                'period': request.GET.get('period', 'month'),
                'status': request.GET.get('status', 'all'),
                'priority': request.GET.get('priority', 'all')
            }
        
        kanban_data = dashboard.get_consultant_kanban_data(filters)
        
        return JsonResponse(kanban_data)
        
    except Exception as e:
        logger.error(f"Error en API kanban de consultor: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_consultant_senior)
@csrf_exempt
def consultant_api_cv_data(request, candidate_id):
    """
    API para obtener datos de CV del consultor.
    """
    try:
        consultant_id = request.user.id
        dashboard = ConsultantSeniorDashboard(consultant_id)
        
        cv_data = dashboard.get_consultant_cv_data(candidate_id)
        
        return JsonResponse(cv_data)
        
    except Exception as e:
        logger.error(f"Error en API CV de consultor: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_consultant_senior)
@csrf_exempt
def consultant_api_reports_data(request):
    """
    API para obtener datos de reportes del consultor.
    """
    try:
        consultant_id = request.user.id
        dashboard = ConsultantSeniorDashboard(consultant_id)
        
        if request.method == 'POST':
            filters = json.loads(request.body)
        else:
            filters = {
                'period': request.GET.get('period', 'month'),
                'report_type': request.GET.get('report_type', 'performance')
            }
        
        reports_data = dashboard.get_consultant_reports_data(filters)
        
        return JsonResponse(reports_data)
        
    except Exception as e:
        logger.error(f"Error en API reportes de consultor: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ============================================================================
# API ENDPOINTS PARA CLIENTES
# ============================================================================

@login_required
@user_passes_test(is_client)
@csrf_exempt
def client_api_kanban_data(request):
    """
    API para obtener datos del kanban del cliente.
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        if request.method == 'POST':
            filters = json.loads(request.body)
        else:
            filters = {
                'period': request.GET.get('period', 'month'),
                'status': request.GET.get('status', 'all'),
                'position': request.GET.get('position', 'all')
            }
        
        kanban_data = dashboard.get_client_kanban_data(filters)
        
        return JsonResponse(kanban_data)
        
    except Exception as e:
        logger.error(f"Error en API kanban de cliente: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_client)
@csrf_exempt
def client_api_cv_data(request, candidate_id):
    """
    API para obtener datos de CV del cliente.
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        cv_data = dashboard.get_client_cv_data(candidate_id)
        
        return JsonResponse(cv_data)
        
    except Exception as e:
        logger.error(f"Error en API CV de cliente: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_client)
@csrf_exempt
def client_api_add_note(request, candidate_id):
    """
    API para que el cliente agregue notas.
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        if request.method == 'POST':
            data = json.loads(request.body)
            note = data.get('note', '')
            
            result = dashboard.add_client_note(candidate_id, note)
            
            return JsonResponse(result)
        
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    except Exception as e:
        logger.error(f"Error en API nota de cliente: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_client)
@csrf_exempt
def client_api_cv_download(request, candidate_id):
    """
    API para descarga de CV del cliente.
    """
    try:
        client_id = request.user.id
        dashboard = ClientDashboard(client_id)
        
        result = dashboard.request_cv_download(candidate_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en API descarga CV de cliente: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ============================================================================
# VISTAS DE REDIRECCIÓN INTELIGENTE
# ============================================================================

@login_required
def role_based_dashboard_redirect(request):
    """
    Redirección inteligente basada en el rol del usuario.
    """
    try:
        if hasattr(request.user, 'role'):
            if request.user.role == 'super_admin':
                return redirect('super_admin_dashboard')
            elif request.user.role == 'consultant_senior':
                return redirect('consultant_dashboard')
            elif request.user.role == 'client':
                return redirect('client_dashboard')
            else:
                # Rol no reconocido, redirigir al dashboard por defecto
                return redirect('home')
        else:
            # Usuario sin rol definido
            return redirect('home')
            
    except Exception as e:
        logger.error(f"Error en redirección por rol: {str(e)}")
        return redirect('home')

@login_required
def role_based_kanban_redirect(request):
    """
    Redirección inteligente al kanban según el rol.
    """
    try:
        if hasattr(request.user, 'role'):
            if request.user.role == 'super_admin':
                return redirect('super_admin_kanban')
            elif request.user.role == 'consultant_senior':
                return redirect('consultant_kanban')
            elif request.user.role == 'client':
                return redirect('client_kanban')
            else:
                return redirect('home')
        else:
            return redirect('home')
            
    except Exception as e:
        logger.error(f"Error en redirección kanban por rol: {str(e)}")
        return redirect('home')

@login_required
def role_based_reports_redirect(request):
    """
    Redirección inteligente a reportes según el rol.
    """
    try:
        if hasattr(request.user, 'role'):
            if request.user.role == 'super_admin':
                return redirect('super_admin_reports')
            elif request.user.role == 'consultant_senior':
                return redirect('consultant_reports')
            elif request.user.role == 'client':
                return redirect('client_reports')
            else:
                return redirect('home')
        else:
            return redirect('home')
            
    except Exception as e:
        logger.error(f"Error en redirección reportes por rol: {str(e)}")
        return redirect('home') 