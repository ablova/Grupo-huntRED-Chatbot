from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from asgiref.sync import sync_to_async
import json
import logging

from app.ats.dashboard.consultant_dashboard import ConsultantDashboard
from app.models import Person, BusinessUnit

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class ConsultantAuraInsightsView(View):
    """Vista para obtener insights de AURA para consultores."""
    
    async def get(self, request, consultant_id):
        """Obtiene insights de AURA para un consultor."""
        try:
            # Verificar que el consultor existe
            consultant = await sync_to_async(Person.objects.get)(id=consultant_id)
            
            # Obtener business unit si se especifica
            business_unit_id = request.GET.get('business_unit_id')
            business_unit = None
            if business_unit_id:
                business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
            
            # Crear dashboard
            dashboard = ConsultantDashboard(consultant_id, business_unit)
            
            # Obtener insights de AURA
            aura_insights = await dashboard.get_aura_insights()
            predictive_analytics = await dashboard.get_predictive_analytics()
            
            return JsonResponse({
                'success': True,
                'aura_insights': aura_insights,
                'predictive_analytics': predictive_analytics
            })
            
        except Person.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Consultor no encontrado'
            }, status=404)
        except Exception as e:
            logger.error(f"Error obteniendo insights de AURA: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ConsultantAuraCandidateAnalysisView(View):
    """Vista para análisis de candidatos con AURA."""
    
    async def get(self, request, consultant_id, candidate_id):
        """Obtiene análisis de un candidato usando AURA."""
        try:
            # Verificar que el consultor existe
            consultant = await sync_to_async(Person.objects.get)(id=consultant_id)
            
            # Obtener business unit si se especifica
            business_unit_id = request.GET.get('business_unit_id')
            business_unit = None
            if business_unit_id:
                business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
            
            # Crear dashboard
            dashboard = ConsultantDashboard(consultant_id, business_unit)
            
            # Obtener análisis del candidato
            candidate_analysis = await dashboard.get_aura_candidate_analysis(candidate_id)
            
            return JsonResponse({
                'success': True,
                'candidate_analysis': candidate_analysis
            })
            
        except Person.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Consultor o candidato no encontrado'
            }, status=404)
        except Exception as e:
            logger.error(f"Error analizando candidato con AURA: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ConsultantAuraVacancyAnalysisView(View):
    """Vista para análisis de vacantes con AURA."""
    
    async def get(self, request, consultant_id, vacancy_id):
        """Obtiene análisis de una vacante usando AURA."""
        try:
            # Verificar que el consultor existe
            consultant = await sync_to_async(Person.objects.get)(id=consultant_id)
            
            # Obtener business unit si se especifica
            business_unit_id = request.GET.get('business_unit_id')
            business_unit = None
            if business_unit_id:
                business_unit = await sync_to_async(BusinessUnit.objects.get)(id=business_unit_id)
            
            # Crear dashboard
            dashboard = ConsultantDashboard(consultant_id, business_unit)
            
            # Obtener análisis de la vacante
            vacancy_analysis = await dashboard.get_aura_vacancy_analysis(vacancy_id)
            
            return JsonResponse({
                'success': True,
                'vacancy_analysis': vacancy_analysis
            })
            
        except Person.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Consultor o vacante no encontrado'
            }, status=404)
        except Exception as e:
            logger.error(f"Error analizando vacante con AURA: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            }, status=500) 