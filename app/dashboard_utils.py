"""
Utilidades y configuraciones para el dashboard de Grupo huntRED®.

Este módulo proporciona funciones y configuraciones para la generación
de tableros de control (dashboards) optimizados para bajo uso de CPU.
Sigue la estructura modular y las reglas globales del sistema.
"""

from typing import Dict, Any, Optional, List, Union
import logging
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from functools import wraps
from datetime import timedelta
from app.models import (
    Person, Application, Vacante, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState, WorkflowStage,
    GamificationAchievement, GamificationBadge, GamificationEvent
)
from app.utils.cache import cache_result, invalidate_cache

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
        },
        'applications_timeline': {
            'title': 'Tendencia de Aplicaciones',
            'type': 'line',
            'fields': ['created_at', 'count']
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
        },
        'business_unit_performance': {
            'title': 'Rendimiento por Unidad de Negocio',
            'columns': ['name', 'total_vacancies', 'total_applications', 'active']
        }
    }
}


# Funciones para generar datos para dashboards
@cache_result(prefix="dashboard", timeout=900)  # Cache por 15 minutos
def get_applications_by_status(business_unit_id=None, date_range=None):
    """
    Obtiene el número de aplicaciones por estado, con filtros opcionales.
    Optimizado con caché para reducir uso de CPU siguiendo reglas globales.
    
    Args:
        business_unit_id (int, optional): ID de la unidad de negocio para filtrar
        date_range (tuple, optional): Rango de fechas (fecha_inicio, fecha_fin)
        
    Returns:
        list: Lista de diccionarios con estado y conteo
    """
    query = Application.objects.all()
    
    # Filtrar por unidad de negocio si se especifica
    if business_unit_id:
        query = query.filter(vacancy__business_unit_id=business_unit_id)
    
    # Filtrar por rango de fechas si se especifica
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        query = query.filter(created_at__range=(start_date, end_date))
    
    # Uso optimizado de valores y anotaciones para reducir consultas
    result = list(query.values('status').annotate(count=Count('id')))
    
    logger.debug(f"Consulta de aplicaciones por estado completada. Registros: {len(result)}")
    return result


@cache_result(prefix="dashboard", timeout=1800)  # Cache por 30 minutos
def get_vacancies_by_business_unit(active_only=True, with_applications=False):
    """
    Obtiene el número de vacantes por unidad de negocio con filtros opcionales.
    Optimizado con caché para reducir uso de CPU siguiendo reglas globales.
    
    Args:
        active_only (bool): Si solo se deben incluir vacantes activas
        with_applications (bool): Si se debe incluir el conteo de aplicaciones
        
    Returns:
        list: Lista de diccionarios con unidad de negocio y conteos
    """
    query = Vacante.objects.all()
    
    # Filtrar solo vacantes activas si se solicita
    if active_only:
        query = query.filter(active=True)
    
    # Optimizar consulta según si se necesita información de aplicaciones
    if with_applications:
        result = list(query.values(
            'business_unit__name', 'business_unit_id'
        ).annotate(
            count=Count('id'),
            applications=Count('application')
        ))
    else:
        result = list(query.values('business_unit__name', 'business_unit_id').annotate(count=Count('id')))
    
    logger.debug(f"Consulta de vacantes por BU completada. Registros: {len(result)}")
    return result

class DashboardUtils:
    """
    Clase utilitaria para el dashboard que proporciona métodos para generar
    estadísticas y visualizaciones.
    """
    
    @staticmethod
    @cache_result(prefix="dashboard_stats", timeout=1200)  # Cache por 20 minutos
    def get_dashboard_stats(business_unit_id=None):
        """
        Obtiene estadísticas generales para el dashboard con optimizaciones de
        rendimiento siguiendo las reglas globales de bajo uso de CPU.
        Implementa caché con Redis para reducir la carga en consultas frecuentes.
        
        Args:
            business_unit_id: ID opcional de BU para filtrar resultados
            
        Returns:
            dict: Estadísticas del dashboard
        """
        # Optimizando consultas para reducir carga de CPU
        applications_query = Application.objects.all()
        vacancies_query = Vacante.objects.all()
        persons_query = Person.objects.all()
        
        # Aplicar filtro de BU si se proporciona
        if business_unit_id:
            vacancies_query = vacancies_query.filter(business_unit_id=business_unit_id)
            applications_query = applications_query.filter(vacancy__business_unit_id=business_unit_id)
            persons_query = persons_query.filter(applications__vacancy__business_unit_id=business_unit_id).distinct()
        
        # Usar select_related para optimizar consultas de aplicaciones recientes
        recent_applications = list(
            applications_query
            .select_related('person', 'vacancy')
            .only(
                'id', 'status', 'created_at', 'updated_at',
                'person__id', 'person__first_name', 'person__last_name', 'person__email',
                'vacancy__id', 'vacancy__title', 'vacancy__business_unit__name'
            )
            .order_by('-created_at')[:5]
            .values(
                'id', 'status', 'created_at',
                'person__first_name', 'person__last_name', 'person__email',
                'vacancy__title', 'vacancy__business_unit__name'
            )
        )
        
        # Usar solo los campos necesarios para candidatos top
        top_candidates = list(
            persons_query
            .only('id', 'first_name', 'last_name', 'email', 'gamification_score', 'last_updated')
            .order_by('-gamification_score')[:5]
            .values('id', 'first_name', 'last_name', 'email', 'gamification_score', 'last_updated')
        )
        
        # Construir estadísticas con consultas optimizadas
        stats = {
            'total_applications': applications_query.count(),
            'active_vacancies': vacancies_query.filter(status='active').count(),
            'total_candidates': persons_query.count(),
            'recent_applications': recent_applications,
            'top_candidates': top_candidates,
            # Estadísticas adicionales
            'last_updated': timezone.now().isoformat(),
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"Estadísticas de dashboard generadas {' para BU: ' + str(business_unit_id) if business_unit_id else ''}")
        return stats
        
    # Método para invalidar estadísticas de caché tras cambios importantes
    @staticmethod
    def invalidate_stats_cache(business_unit_id=None):
        """
        Invalida el caché de estadísticas del dashboard.
        Debe llamarse cuando ocurren cambios significativos en los datos.
        
        Args:
            business_unit_id: ID opcional de BU cuyo caché debe invalidarse
        """
        if business_unit_id:
            # Invalidar cache para una BU específica
            key = f"dashboard_stats:get_dashboard_stats:{business_unit_id}"
            invalidate_cache(keys=[key])
            logger.info(f"Caché de estadísticas invalidado para BU: {business_unit_id}")
        else:
            # Invalidar todo el caché de estadísticas
            invalidate_cache(prefix="dashboard_stats")
            logger.info("Caché de estadísticas invalidado completamente")
    
    @staticmethod
    def get_chart_data(chart_type: str, business_unit_id=None, date_range=None) -> Dict[str, Any]:
        """
        Obtiene datos para un gráfico específico del dashboard con optimizaciones
        de rendimiento siguiendo las reglas globales de bajo uso de CPU.
        
        Args:
            chart_type: Tipo de gráfico (ej: 'applications_by_status')
            business_unit_id: ID opcional de BU para filtrar resultados
            date_range: Rango de fechas opcional (fecha_inicio, fecha_fin)
            
        Returns:
            dict: Datos para el gráfico con estructura normalizada
        """
        # Inicializar estructura de respuesta
        result = {
            'type': chart_type,
            'data': [],
            'labels': [],
            'title': DASHBOARD_CONFIG['charts'].get(chart_type, {}).get('title', 'Gráfico'),
            'last_updated': timezone.now().isoformat()
        }
        
        # Applications by Status - Con filtros opcionales
        if chart_type == 'applications_by_status':
            # Obtener datos utilizando la función optimizada
            data = get_applications_by_status(business_unit_id, date_range)
            
            # Normalizar formato para consumo en frontend
            for item in data:
                result['labels'].append(item['status'] or 'Sin estado')
                result['data'].append(item['count'])
            
            # Metadatos adicionales
            result['chart_type'] = 'pie'
            logger.debug(f"Datos de gráfico 'applications_by_status' generados. Registros: {len(data)}")
            
        # Vacancies by Business Unit - Con filtros opcionales
        elif chart_type == 'vacancies_by_business_unit':
            # Obtener datos utilizando la función optimizada con aplicaciones
            data = get_vacancies_by_business_unit(True, True)
            
            # Filtrar por BU si se especifica
            if business_unit_id:
                data = [item for item in data if item.get('business_unit_id') == business_unit_id]
            
            # Normalizar formato para consumo en frontend
            for item in data:
                result['labels'].append(item['business_unit__name'] or 'Sin BU')
                result['data'].append(item['count'])
                
            # Metadatos adicionales
            result['chart_type'] = 'bar'
            result['applications'] = [item.get('applications', 0) for item in data]
            logger.debug(f"Datos de gráfico 'vacancies_by_business_unit' generados. Registros: {len(data)}")
            
        # Applications Timeline - Gráfico adicional
        elif chart_type == 'applications_timeline':
            # Calcular rango de fechas por defecto (30 días)
            if not date_range:
                end_date = timezone.now()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)
            else:
                start_date, end_date = date_range
            
            # Preparar consulta optimizada con filtros por fecha
            query = Application.objects.filter(
                created_at__range=(start_date, end_date)
            )
            
            # Filtrar por BU si se especifica
            if business_unit_id:
                query = query.filter(vacancy__business_unit_id=business_unit_id)
            
            # Agrupar por día usando annotate para procesar en la base de datos
            from django.db.models.functions import TruncDay
            timeline_data = (
                query
                .annotate(day=TruncDay('created_at'))
                .values('day')
                .annotate(count=Count('id'))
                .order_by('day')
            )
            
            # Normalizar formato para consumo en frontend
            for item in timeline_data:
                result['labels'].append(item['day'].strftime('%Y-%m-%d'))
                result['data'].append(item['count'])
            
            # Metadatos adicionales
            result['chart_type'] = 'line'
            result['date_range'] = {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
            logger.debug(f"Datos de gráfico 'applications_timeline' generados. Registros: {len(timeline_data)}")
            
        return result
    
    @staticmethod
    def get_table_data(table_type: str, business_unit_id=None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene datos para una tabla específica del dashboard con optimizaciones
        de rendimiento siguiendo las reglas globales de bajo uso de CPU.
        
        Args:
            table_type: Tipo de tabla (ej: 'recent_applications')
            business_unit_id: ID opcional de BU para filtrar resultados
            limit: Número máximo de registros
            
        Returns:
            list: Datos para la tabla
        """
        # Inicializar resultado vacío
        result = []
        
        # Recent Applications - Optimizado con select_related
        if table_type == 'recent_applications':
            query = Application.objects.all()
            
            # Filtrar por BU si se especifica
            if business_unit_id:
                query = query.filter(vacancy__business_unit_id=business_unit_id)
            
            # Optimizar carga con select_related para evitar múltiples consultas
            result = (
                query
                .select_related('person', 'vacancy', 'vacancy__business_unit')
                .only(
                    'id', 'status', 'created_at', 'updated_at',
                    'person__first_name', 'person__last_name', 'person__email',
                    'vacancy__title', 'vacancy__business_unit__name'
                )
                .order_by('-created_at')[:limit]
            )
            
            logger.debug(f"Datos de tabla 'recent_applications' generados. Registros: {len(result)}")
        
        # Top Candidates - Optimizado con prefetch_related
        elif table_type == 'top_candidates':
            query = Person.objects.all()
            
            # Filtrar por BU si se especifica
            if business_unit_id:
                query = query.filter(applications__vacancy__business_unit_id=business_unit_id).distinct()
            
            # Optimizar carga usando only() para reducir datos transferidos
            result = (
                query
                .prefetch_related('applications')
                .only(
                    'id', 'first_name', 'last_name', 'email', 
                    'gamification_score', 'last_updated'
                )
                .order_by('-gamification_score')[:limit]
            )
            
            logger.debug(f"Datos de tabla 'top_candidates' generados. Registros: {len(result)}")
        
        # Business Unit Performance - Tabla adicional
        elif table_type == 'business_unit_performance':
            query = BusinessUnit.objects.all()
            
            # Filtrar por BU si se especifica
            if business_unit_id:
                query = query.filter(id=business_unit_id)
            
            # Optimizar carga con annotate para calcular métricas en la base de datos
            result = (
                query
                .annotate(
                    total_vacancies=Count('vacantes', distinct=True),
                    total_applications=Count('vacantes__application', distinct=True)
                )
                .only('id', 'name', 'description', 'active')
                .order_by('name')[:limit]
            )
            
            logger.debug(f"Datos de tabla 'business_unit_performance' generados. Registros: {len(result)}")
        
        return result
