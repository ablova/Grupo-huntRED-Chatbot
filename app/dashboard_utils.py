"""
Utilidades y configuraciones para el dashboard del sistema.
"""

from typing import Dict, Any, Optional, List, Union
import logging
from django.utils import timezone
from django.db.models import Q, Count, Avg
from app.models import (
    Person, Application, Vacante, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState, WorkflowStage,
    GamificationAchievement, GamificationBadge, GamificationEvent
)

logger = logging.getLogger(__name__)

# Configuraciones del dashboard
DASHBOARD_CONFIG = {
    'charts': {
        'applications_by_status': {
            'title': 'Aplicaciones por Estado',
            'type': 'pie',
            'fields': ['status']
        },
        'vacancies_by_business_unit': {
            'title': 'Vacantes por Unidad de Negocio',
            'type': 'bar',
            'fields': ['business_unit']
        }
    },
    'tables': {
        'recent_applications': {
            'title': 'Aplicaciones Recientes',
            'columns': ['candidate', 'vacancy', 'status', 'created_at']
        },
        'top_candidates': {
            'title': 'Candidatos Top',
            'columns': ['candidate', 'score', 'gamification_score', 'last_updated']
        }
    }
}

class DashboardUtils:
    """
    Clase utilitaria para el dashboard que proporciona métodos para generar
    estadísticas y visualizaciones.
    """
    
    @staticmethod
    def get_dashboard_stats():
        """
        Obtiene estadísticas generales para el dashboard.
        
        Returns:
            dict: Estadísticas del dashboard
        """
        stats = {
            'total_applications': Application.objects.count(),
            'active_vacancies': Vacante.objects.filter(status='active').count(),
            'total_candidates': Person.objects.count(),
            'recent_applications': Application.objects.order_by('-created_at')[:5],
            'top_candidates': Person.objects.order_by('-gamification_score')[:5]
        }
        return stats
    
    @staticmethod
    def get_chart_data(chart_type: str) -> Dict[str, Any]:
        """
        Obtiene datos para un gráfico específico del dashboard.
        
        Args:
            chart_type: Tipo de gráfico (ej: 'applications_by_status')
            
        Returns:
            dict: Datos para el gráfico
        """
        if chart_type == 'applications_by_status':
            return Application.objects.values('status').annotate(count=Count('id'))
        elif chart_type == 'vacancies_by_business_unit':
            return Vacante.objects.values('business_unit__name').annotate(count=Count('id'))
        return {}
    
    @staticmethod
    def get_table_data(table_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene datos para una tabla específica del dashboard.
        
        Args:
            table_type: Tipo de tabla (ej: 'recent_applications')
            limit: Número máximo de registros
            
        Returns:
            list: Datos para la tabla
        """
        if table_type == 'recent_applications':
            return Application.objects.order_by('-created_at')[:limit]
        elif table_type == 'top_candidates':
            return Person.objects.order_by('-gamification_score')[:limit]
        return []
