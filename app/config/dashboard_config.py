from django.db.models import Count, Q, Avg, F, ExtractDay
from django.utils import timezone
from datetime import timedelta
from app.models import (
    Person, Application, Vacante, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState
)
from app.config.dashboard_utils import DashboardUtils
import logging
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class DashboardConfig:
    """
    Clase que maneja la configuración y estadísticas del dashboard.
    
    Métodos:
        get_stats(): Obtiene estadísticas generales del sistema
        get_kpis(): Obtiene KPIs principales
        get_alerts(): Obtiene alertas del sistema
        get_tasks(): Obtiene tareas pendientes
        get_integrations(): Obtiene estado de integraciones
    """

    @staticmethod
    def get_stats() -> Dict[str, int]:
        """
        Obtiene estadísticas generales del sistema.
        
        Returns:
            Dict: Diccionario con estadísticas:
                - total_candidates: Total de candidatos
                - active_jobs: Trabajos activos
                - new_applications: Nuevas aplicaciones
                - hires_last_month: Contrataciones del mes pasado
        """
        return DashboardUtils.get_general_stats()

    @staticmethod
    def get_kpis() -> Dict[str, float]:
        """
        Obtiene los KPIs principales del sistema.
        
        Returns:
            Dict: Diccionario con KPIs:
                - conversion_rate: Tasa de conversión
                - avg_days: Días promedio
                - engagement_rate: Tasa de engagement
        """
        return DashboardUtils.get_kpis()

    @staticmethod
    def get_alerts() -> List[Dict[str, str]]:
        """
        Obtiene las alertas del sistema.
        
        Returns:
            List[Dict]: Lista de alertas con:
                - type: Tipo de alerta (success, warning, error)
                - title: Título de la alerta
                - message: Mensaje detallado
                - timestamp: Timestamp de la alerta
        """
        alerts = []
        
        # Alertas de contratación
        hires = Application.objects.filter(
            status='hired',
            updated_at__gte=timezone.now() - timedelta(days=1)
        ).select_related('user', 'vacancy')
        
        for hire in hires:
            alerts.append({
                'type': 'success',
                'title': 'Contratación Exitosa',
                'message': f'Nuevo empleado contratado: {hire.user.get_full_name()} para {hire.vacancy.title}',
                'timestamp': hire.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Alertas de problemas
        problems = Application.objects.filter(
            Q(status='rejected') | Q(status='in_review')
        ).annotate(
            days_in_status=ExtractDay(F('updated_at') - F('created_at'))
        ).filter(
            days_in_status__gt=30
        ).select_related('user', 'vacancy')
        
        for problem in problems:
            alerts.append({
                'type': 'warning',
                'title': 'Proceso Lento',
                'message': f'Aplicación estancada: {problem.user.get_full_name()} para {problem.vacancy.title}',
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return alerts

    @staticmethod
    def get_tasks() -> List[Dict[str, Any]]:
        """
        Obtiene las tareas pendientes del sistema.
        
        Returns:
            List[Dict]: Lista de tareas con:
                - priority: Prioridad de la tarea (high, medium, low)
                - title: Título de la tarea
                - description: Descripción detallada
                - deadline: Fecha límite
        """
        tasks = []
        
        # Tareas de revisión
        pending_reviews = Application.objects.filter(
            status='in_review'
        ).order_by('created_at')[:5].select_related('user', 'vacancy')
        
        for app in pending_reviews:
            days_pending = (timezone.now() - app.created_at).days
            priority = 'high' if days_pending > 7 else 'medium'
            
            tasks.append({
                'priority': priority,
                'title': f'Revisar aplicación de {app.user.get_full_name()}',
                'description': f'Aplicación para {app.vacancy.title} pendiente desde {days_pending} días',
                'deadline': (app.created_at + timedelta(days=14)).strftime('%Y-%m-%d')
            })
        
        # Tareas de seguimiento
        interviews = Application.objects.filter(
            status='interview',
            interview_date__gte=timezone.now()
        ).order_by('interview_date')[:5].select_related('user', 'vacancy')
        
        for interview in interviews:
            days_until = (interview.interview_date - timezone.now().date()).days
            priority = 'high' if days_until <= 3 else 'medium'
            
            tasks.append({
                'priority': priority,
                'title': f'Seguimiento de entrevista {interview.user.get_full_name()}',
                'description': f'Entrevista programada para {interview.interview_date.strftime("%Y-%m-%d")}',
                'deadline': interview.interview_date.strftime('%Y-%m-%d')
            })
        
        return tasks

    @staticmethod
    def get_integrations() -> List[Dict[str, str]]:
        """
        Obtiene el estado de las integraciones.
        
        Returns:
            List[Dict]: Lista de integraciones con:
                - name: Nombre de la integración
                - status: Estado (success, warning, error)
                - last_update: Timestamp de última actualización
        """
        integrations = []
        
        # Estado de APIs
        api_status = {
            'whatsapp': 'success',
            'telegram': 'success',
            'messenger': 'success',
            'instagram': 'success',
            'meta': 'success'
        }
        
        for api, status in api_status.items():
            integrations.append({
                'name': api.capitalize(),
                'status': status,
                'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return integrations

    @staticmethod
    def get_alerts():
        """Obtiene las alertas del sistema."""
        alerts = []
        
        # Alertas de contratación
        hires = Application.objects.filter(
            status='hired',
            updated_at__gte=timezone.now() - timedelta(days=1)
        )
        for hire in hires:
            alerts.append({
                'type': 'success',
                'title': 'Contratación Exitosa',
                'message': f'Nuevo empleado contratado: {hire.user.get_full_name()} para {hire.vacancy.title}',
                'timestamp': hire.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Alertas de problemas
        problems = Application.objects.filter(
            Q(status='rejected') | Q(status='in_review')
        ).annotate(
            days_in_status=ExtractDay(F('updated_at') - F('created_at'))
        ).filter(
            days_in_status__gt=30
        )
        
        for problem in problems:
            alerts.append({
                'type': 'warning',
                'title': 'Proceso Lento',
                'message': f'Aplicación estancada: {problem.user.get_full_name()} para {problem.vacancy.title}',
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return alerts

    @staticmethod
    def get_tasks():
        """Obtiene las tareas pendientes del sistema."""
        tasks = []
        
        # Tareas de revisión
        pending_reviews = Application.objects.filter(
            status='in_review'
        ).order_by('created_at')[:5]
        
        for app in pending_reviews:
            days_pending = (timezone.now() - app.created_at).days
            priority = 'high' if days_pending > 7 else 'medium'
            
            tasks.append({
                'priority': priority,
                'title': f'Revisar aplicación de {app.user.get_full_name()}',
                'description': f'Aplicación para {app.vacancy.title} pendiente desde {days_pending} días',
                'deadline': (app.created_at + timedelta(days=14)).strftime('%Y-%m-%d')
            })
        
        # Tareas de seguimiento
        interviews = Application.objects.filter(
            status='interview',
            interview_date__gte=timezone.now()
        ).order_by('interview_date')[:5]
        
        for interview in interviews:
            days_until = (interview.interview_date - timezone.now().date()).days
            priority = 'high' if days_until <= 3 else 'medium'
            
            tasks.append({
                'priority': priority,
                'title': f'Seguimiento de entrevista {interview.user.get_full_name()}',
                'description': f'Entrevista programada para {interview.interview_date.strftime("%Y-%m-%d")}',
                'deadline': interview.interview_date.strftime('%Y-%m-%d')
            })
        
        return tasks

    @staticmethod
    def get_integrations():
        """Obtiene el estado de las integraciones."""
        integrations = []
        
        # Estado de APIs
        api_status = {
            'whatsapp': 'success',
            'telegram': 'success',
            'messenger': 'success',
            'instagram': 'success',
            'meta': 'success'
        }
        
        for api, status in api_status.items():
            integrations.append({
                'name': api.capitalize(),
                'status': status,
                'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return integrations
