"""
Vistas para el dashboard de clientes.

Este módulo implementa las vistas interactivas del dashboard para clientes,
permitiéndoles visualizar métricas de satisfacción y onboarding.
"""

import logging
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Avg, Count, Q, F

from app.models import BusinessUnit, Vacante
from app.ats.utilidades.auth_utils import has_bu_permission

logger = logging.getLogger(__name__)

class BaseDashboardView(LoginRequiredMixin, TemplateView):
    """
    Vista base para todas las vistas del dashboard.
    Implementa la verificación de permisos y carga datos comunes.
    """
    
    def get_context_data(self, **kwargs):
        """
        Obtiene datos comunes para todas las vistas del dashboard.
        """
        context = super().get_context_data(**kwargs)
        
        # Obtener unidades de negocio permitidas para el usuario
        available_business_units = []
        all_business_units = BusinessUnit.objects.all()
        
        for bu in all_business_units:
            if has_bu_permission(self.request.user, bu.id):
                available_business_units.append(bu)
        
        # Obtener BU seleccionada (si existe en la URL)
        selected_bu_id = self.kwargs.get('business_unit_id')
        selected_bu = None
        
        if selected_bu_id:
            for bu in available_business_units:
                if bu.id == int(selected_bu_id):
                    selected_bu = bu
                    break
        
        # Si no hay BU seleccionada, usar la primera disponible
        if not selected_bu and available_business_units:
            selected_bu = available_business_units[0]
        
        # Obtener empresas para la BU seleccionada
        available_empresas = []
        if selected_bu:
            # Asumiendo que hay una relación entre vacantes y empresas
            empresas = Vacante.objects.filter(
                business_unit=selected_bu
            ).values('empresa').annotate(
                count=Count('id')
            ).order_by('empresa__name')
            
            for empresa_data in empresas:
                if empresa_data['empresa']:
                    available_empresas.append({
                        'id': empresa_data['empresa'],
                        'name': empresa_data['empresa__name'],
                        'count': empresa_data['count']
                    })
        
        # Añadir datos al contexto
        context.update({
            'available_business_units': available_business_units,
            'selected_business_unit': selected_bu,
            'available_empresas': available_empresas,
            'is_admin': self.request.user.is_staff or self.request.user.is_superuser,
            'dashboard_type': self.dashboard_type
        })
        
        return context

class ClientDashboardView(BaseDashboardView):
    """
    Vista principal del dashboard para clientes.
    Muestra un resumen de las métricas clave.
    """
    template_name = 'dashboard/client/index.html'
    dashboard_type = 'overview'

class ClientSatisfactionDashboardView(BaseDashboardView):
    """
    Vista de satisfacción de clientes.
    Muestra métricas detalladas de satisfacción de clientes y candidatos.
    """
    template_name = 'dashboard/client/satisfaction.html'
    dashboard_type = 'satisfaction'

class OnboardingMetricsDashboardView(BaseDashboardView):
    """
    Vista de métricas de onboarding.
    Muestra estadísticas detalladas del proceso de onboarding.
    """
    template_name = 'dashboard/client/onboarding.html'
    dashboard_type = 'onboarding'

class RecommendationsDashboardView(BaseDashboardView):
    """
    Vista de recomendaciones.
    Muestra recomendaciones personalizadas basadas en análisis de datos.
    """
    template_name = 'dashboard/client/recommendations.html'
    dashboard_type = 'recommendations'
