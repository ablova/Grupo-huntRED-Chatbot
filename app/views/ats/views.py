"""
Vistas para el sistema ATS (Application Tracking System).

Responsabilidades:
- Gestión de candidatos
- Seguimiento de aplicaciones
- Manejo de entrevistas
- Generación de reportes
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from django.db import transaction
from django.utils import timezone
from django.core.cache import caches
from django_ratelimit.decorators import ratelimit

from app.ats.decorators import (
    bu_complete_required, bu_division_required,
    permission_required, verified_user_required
)
from app.models import (
    Application, Interview, Person, Vacante,
    ApplicationStatus, InterviewStatus
)
from app.ats.utils import get_business_unit, get_user_permissions

import logging
logger = logging.getLogger(__name__)

class ATSViews(View):
    """
    Vistas principales del ATS.
    """
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    def applications_list(self, request):
        """
        Lista de todas las aplicaciones con filtros y búsqueda.
        """
        business_unit = get_business_unit(request.user)
        applications = Application.objects.filter(
            vacante__business_unit=business_unit
        ).select_related('person', 'vacante')
        
        # Filtros
        status = request.GET.get('status')
        if status:
            applications = applications.filter(status=status)
            
        # Ordenamiento
        order_by = request.GET.get('order_by', '-created_at')
        applications = applications.order_by(order_by)
        
        context = {
            'applications': applications,
            'business_unit': business_unit,
            'status_choices': ApplicationStatus.choices
        }
        return render(request, 'ats/applications_list.html', context)
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    @method_decorator(ratelimit(key='user', rate='100/m'))
    def update_application_status(self, request, application_id):
        """
        Actualiza el estado de una aplicación.
        """
        if request.method == 'POST':
            application = get_object_or_404(Application, id=application_id)
            
            # Verificar permisos
            if not request.user.has_perm('can_update_application_status'):
                return JsonResponse({'error': 'No tienes permisos para actualizar el estado'}, status=403)
            
            new_status = request.POST.get('status')
            if new_status not in dict(ApplicationStatus.choices):
                return JsonResponse({'error': 'Estado inválido'}, status=400)
            
            with transaction.atomic():
                application.status = new_status
                application.updated_at = timezone.now()
                application.save()
                
                # Actualizar estado de entrevista si existe
                interview = Interview.objects.filter(
                    application=application
                ).first()
                if interview and new_status == ApplicationStatus.REJECTED:
                    interview.status = InterviewStatus.REJECTED
                    interview.save()
            
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    def interviews_list(self, request):
        """
        Lista de entrevistas con estadísticas.
        """
        business_unit = get_business_unit(request.user)
        interviews = Interview.objects.filter(
            application__vacante__business_unit=business_unit
        ).select_related('application', 'application__person')
        
        # Estadísticas
        stats = Interview.objects.filter(
            application__vacante__business_unit=business_unit
        ).values('status').annotate(count=Count('id'))
        
        context = {
            'interviews': interviews,
            'stats': stats,
            'status_choices': InterviewStatus.choices
        }
        return render(request, 'ats/interviews_list.html', context)
    
    @method_decorator(login_required)
    @method_decorator(bu_complete_required)
    def generate_report(self, request):
        """
        Genera reportes de ATS con métricas.
        """
        business_unit = get_business_unit(request.user)
        
        # Métricas
        metrics = {
            'total_applications': Application.objects.filter(
                vacante__business_unit=business_unit
            ).count(),
            'applications_by_status': Application.objects.filter(
                vacante__business_unit=business_unit
            ).values('status').annotate(count=Count('id')),
            'interviews_by_status': Interview.objects.filter(
                application__vacante__business_unit=business_unit
            ).values('status').annotate(count=Count('id'))
        }
        
        return render(request, 'ats/report.html', {'metrics': metrics})
