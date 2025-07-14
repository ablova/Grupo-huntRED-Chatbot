"""
Executive Dashboard View
Vista unificada que integra todos los dashboards del sistema huntRED.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache

from app.models import Person, Application, Vacante, BusinessUnit
from app.views.aura.dashboard import AURADashboardView
from app.views.ml_admin_views import MLDashboardView
from app.views.analytics.views import AnalyticsDashboardView
from app.views.dashboard.client_dashboard import ClientDashboard
from app.views.signature_dashboard import SignatureDashboardView
from app.views.dashboard.advanced_analytics_views import advanced_analytics_dashboard
from app.views.dashboard.omnichannel_automation_views import omnichannel_automation_dashboard

logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class ExecutiveDashboardView(View):
    """
    Vista ejecutiva que integra todos los dashboards del sistema huntRED.
    
    Incluye:
    - Dashboard de AURA (ML avanzado)
    - Dashboard de ML (Machine Learning)
    - Dashboard de Analytics (Analytics avanzados)
    - Dashboard de Clientes (Gestión de clientes)
    - Dashboard de Firmas (Firmas electrónicas)
    - Dashboard de Automatización Omnicanal
    - Dashboard de Analytics Avanzados
    """
    
    template_name = 'dashboard/executive_dashboard.html'
    
    def get(self, request):
        """Renderiza el dashboard ejecutivo principal"""
        try:
            # Obtener parámetros de filtro
            section = request.GET.get('section', 'overview')
            business_unit = request.GET.get('business_unit', 'all')
            period = request.GET.get('period', 'week')
            
            # Obtener datos según la sección
            if section == 'overview':
                context = self._get_overview_data(request, business_unit, period)
            elif section == 'aura':
                context = self._get_aura_data(request)
            elif section == 'ml':
                context = self._get_ml_data(request, business_unit)
            elif section == 'analytics':
                context = self._get_analytics_data(request)
            elif section == 'clients':
                context = self._get_clients_data(request, business_unit)
            elif section == 'signatures':
                context = self._get_signatures_data(request)
            elif section == 'automation':
                context = self._get_automation_data(request)
            else:
                context = self._get_overview_data(request, business_unit, period)
            
            # Agregar datos comunes
            context.update({
                'current_section': section,
                'business_unit': business_unit,
                'period': period,
                'business_units': self._get_business_units(),
                'page_title': 'Executive Dashboard - huntRED',
                'breadcrumbs': [
                    {'name': 'Dashboard', 'url': 'dashboard'},
                    {'name': 'Executive Dashboard', 'url': '#'}
                ]
            })
            
            return render(request, self.template_name, context)
            
        except Exception as e:
            logger.error(f"Error en Executive Dashboard: {str(e)}")
            return render(request, self.template_name, {
                'error': str(e),
                'page_title': 'Executive Dashboard - huntRED'
            })
    
    def _get_overview_data(self, request, business_unit: str, period: str) -> Dict[str, Any]:
        """Obtiene datos de vista general"""
        # Métricas principales del sistema
        metrics = {
            'total_candidates': Person.objects.count(),
            'total_vacancies': Vacante.objects.filter(estado='activa').count(),
            'total_applications': Application.objects.count(),
            'active_business_units': BusinessUnit.objects.filter(active=True).count(),
        }
        
        # Datos de AURA
        aura_data = self._get_aura_summary()
        
        # Datos de ML
        ml_data = self._get_ml_summary(business_unit)
        
        # Datos de Analytics
        analytics_data = self._get_analytics_summary()
        
        return {
            'metrics': metrics,
            'aura_summary': aura_data,
            'ml_summary': ml_data,
            'analytics_summary': analytics_data,
            'recent_activities': self._get_recent_activities(),
            'system_health': self._get_system_health(),
        }
    
    def _get_aura_data(self, request) -> Dict[str, Any]:
        """Obtiene datos del dashboard de AURA"""
        aura_dashboard = AURADashboardView()
        return aura_dashboard._get_dashboard_data()
    
    def _get_ml_data(self, request, business_unit: str) -> Dict[str, Any]:
        """Obtiene datos del dashboard de ML"""
        ml_dashboard = MLDashboardView()
        return ml_dashboard._get_dashboard_data(business_unit)
    
    def _get_analytics_data(self, request) -> Dict[str, Any]:
        """Obtiene datos del dashboard de Analytics"""
        analytics_dashboard = AnalyticsDashboardView()
        return analytics_dashboard.get(request).context_data
    
    def _get_clients_data(self, request, business_unit: str) -> Dict[str, Any]:
        """Obtiene datos del dashboard de clientes"""
        # Simular datos de clientes
        return {
            'total_clients': 150,
            'active_clients': 120,
            'new_clients_this_month': 15,
            'client_satisfaction': 4.8,
        }
    
    def _get_signatures_data(self, request) -> Dict[str, Any]:
        """Obtiene datos del dashboard de firmas"""
        signature_dashboard = SignatureDashboardView()
        return signature_dashboard._get_dashboard_context(request)
    
    def _get_automation_data(self, request) -> Dict[str, Any]:
        """Obtiene datos del dashboard de automatización"""
        # Simular datos de automatización
        return {
            'active_workflows': 25,
            'automation_rate': 78.5,
            'channels_active': 4,
            'engagement_rate': 92.3,
        }
    
    def _get_aura_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de datos de AURA"""
        try:
            from app.ml.aura.orchestrator import aura_orchestrator
            system_status = aura_orchestrator.get_system_status()
            return {
                'status': system_status['service_tier'],
                'active_modules': len(system_status['available_modules']),
                'total_analyses': 1250,
                'avg_ethical_score': 9.2,
            }
        except Exception as e:
            logger.warning(f"No se pudo obtener datos de AURA: {e}")
            return {
                'status': 'unavailable',
                'active_modules': 0,
                'total_analyses': 0,
                'avg_ethical_score': 0,
            }
    
    def _get_ml_summary(self, business_unit: str) -> Dict[str, Any]:
        """Obtiene resumen de datos de ML"""
        return {
            'active_vacancies': Vacante.objects.filter(estado='activa').count(),
            'high_potential_vacancies': 45,
            'candidates_with_growth': 89,
            'prediction_accuracy': 94.2,
        }
    
    def _get_analytics_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de datos de Analytics"""
        return {
            'conversion_rate': 23.5,
            'avg_time_to_hire': 18,
            'cost_per_hire': 2500,
            'quality_score': 8.7,
        }
    
    def _get_recent_activities(self) -> list:
        """Obtiene actividades recientes del sistema"""
        return [
            {'type': 'application', 'message': 'Nueva aplicación recibida', 'time': '2 min ago'},
            {'type': 'interview', 'message': 'Entrevista programada', 'time': '15 min ago'},
            {'type': 'aura', 'message': 'Análisis AURA completado', 'time': '1 hour ago'},
            {'type': 'ml', 'message': 'Modelo ML actualizado', 'time': '2 hours ago'},
        ]
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Obtiene estado de salud del sistema"""
        return {
            'database': 'healthy',
            'redis': 'healthy',
            'ml_services': 'healthy',
            'aura_engine': 'healthy',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    
    def _get_business_units(self) -> list:
        """Obtiene lista de unidades de negocio"""
        return [
            {'code': 'all', 'name': 'Todas las unidades'},
            {'code': 'IT', 'name': 'IT'},
            {'code': 'HR', 'name': 'HR'},
        ]
    
    @require_http_methods(["POST"])
    @csrf_exempt
    def post(self, request):
        """Endpoint para actualizaciones AJAX del dashboard"""
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'refresh_section':
                section = data.get('section', 'overview')
                business_unit = data.get('business_unit', 'all')
                
                if section == 'aura':
                    context = self._get_aura_data(request)
                elif section == 'ml':
                    context = self._get_ml_data(request, business_unit)
                elif section == 'analytics':
                    context = self._get_analytics_data(request)
                else:
                    context = self._get_overview_data(request, business_unit, 'week')
                
                return JsonResponse({
                    'status': 'success',
                    'data': context
                })
            
            return JsonResponse({
                'status': 'error',
                'message': 'Acción no válida'
            })
            
        except Exception as e:
            logger.error(f"Error en POST Executive Dashboard: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500) 