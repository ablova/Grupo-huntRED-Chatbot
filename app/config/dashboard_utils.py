from django.db.models import Count, Q, Avg, F, ExtractDay, Subquery, OuterRef
from django.utils import timezone
from datetime import timedelta
from app.models import (
    Person, Application, Vacante, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState
)
import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

class DashboardUtils:
    """
    Clase utilitaria para el dashboard que proporciona métodos para calcular estadísticas y métricas.
    
    Métodos:
        get_general_stats(): Obtiene estadísticas generales del sistema
        get_kpis(): Obtiene KPIs principales
        get_business_unit_stats(): Obtiene estadísticas por unidad de negocio
        get_skill_distribution(): Obtiene distribución de habilidades
        get_experience_distribution(): Obtiene distribución de experiencia
        get_salary_distribution(): Obtiene distribución de salarios
        get_education_distribution(): Obtiene distribución educativa
        get_location_distribution(): Obtiene distribución geográfica
        get_application_status_distribution(): Obtiene distribución de estados de aplicaciones
        get_vacancy_status_distribution(): Obtiene distribución de estados de vacantes
        get_gamification_leaderboard(): Obtiene ranking de gamificación
        get_recent_activity(): Obtiene actividad reciente
        get_top_performers(): Obtiene mejores candidatos
        get_top_vacancies(): Obtiene vacantes más populares
    """

    @staticmethod
    def get_general_stats() -> Dict[str, int]:
        """
        Obtiene estadísticas generales del sistema.
        
        Returns:
            Dict: Diccionario con estadísticas:
                - total_candidates: Total de candidatos
                - active_jobs: Trabajos activos
                - new_applications: Nuevas aplicaciones
                - hires_last_month: Contrataciones del mes pasado
        """
        now = timezone.now()
        one_month_ago = now - timedelta(days=30)

        # Optimizar consultas usando annotate y values
        stats = Application.objects.aggregate(
            total_candidates=Count('user', distinct=True),
            active_jobs=Count('vacancy', filter=Q(vacancy__status__in=['active', 'in_progress']), distinct=True),
            new_applications=Count('id', filter=Q(created_at__gte=one_month_ago)),
            hires_last_month=Count('id', filter=Q(status='hired', created_at__gte=one_month_ago))
        )

        return stats

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
        # Optimizar consultas usando subqueries y evitar múltiples consultas
        now = timezone.now()
        one_week_ago = now - timedelta(days=7)

        # Subqueries para mejorar el rendimiento
        total_applications = Application.objects.count()
        total_hires = Application.objects.filter(status='hired').count()
        
        # Usar subquery para calcular días promedio
        days_subquery = Application.objects.filter(
            status='hired'
        ).annotate(
            days=ExtractDay(F('created_at') - F('updated_at'))
        ).values('days')
        
        avg_days = days_subquery.aggregate(avg=Avg('days'))['avg'] or 0

        # Usar subquery para calcular engagement
        total_candidates = Person.objects.count()
        active_applications = Application.objects.filter(
            created_at__gte=one_week_ago
        ).count()
        
        engagement_rate = (active_applications / total_candidates * 100) if total_candidates else 0

        # Calcular conversion rate
        conversion_rate = (total_hires / total_applications * 100) if total_applications else 0

        # Ajustar umbrales dinámicamente
        from app.config.dashboard_constants import calculate_alert_thresholds
        thresholds = calculate_alert_thresholds(total_applications)
        
        # Añadir alertas si se superan los umbrales
        alerts = []
        if conversion_rate < thresholds['conversion_rate']['low']:
            alerts.append({
                'type': 'warning',
                'title': 'Baja tasa de conversión',
                'message': f'La tasa de conversión ({conversion_rate:.1f}%) está por debajo del umbral ({thresholds["conversion_rate"]["low"]}%)'
            })
        
        if avg_days > thresholds['avg_days']['high']:
            alerts.append({
                'type': 'warning',
                'title': 'Tiempo de contratación elevado',
                'message': f'Los días promedio de contratación ({avg_days:.1f}) superan el umbral ({thresholds["avg_days"]["high"]})'
            })
        
        if engagement_rate < thresholds['engagement_rate']['low']:
            alerts.append({
                'type': 'warning',
                'title': 'Bajo engagement',
                'message': f'La tasa de engagement ({engagement_rate:.1f}%) está por debajo del umbral ({thresholds["engagement_rate"]["low"]}%)'
            })

        return {
            'conversion_rate': round(conversion_rate, 2),
            'avg_days': round(avg_days, 1),
            'engagement_rate': round(engagement_rate, 2),
            'alerts': alerts
        }

    @staticmethod
    def get_business_unit_stats(bu: BusinessUnit):
        """Obtiene estadísticas específicas por unidad de negocio."""
        return {
            'total_applications': Application.objects.filter(
                vacancy__business_unit=bu
            ).count(),
            'active_jobs': Vacante.objects.filter(
                business_unit=bu,
                status__in=['active', 'in_progress']
            ).count(),
            'hires_last_month': Application.objects.filter(
                vacancy__business_unit=bu,
                status='hired',
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'conversion_rate': DashboardUtils.calculate_conversion_rate_for_bu(bu)
        }

    @staticmethod
    def calculate_conversion_rate_for_bu(bu: BusinessUnit):
        """Calcula la tasa de conversión para una unidad de negocio específica."""
        total_applications = Application.objects.filter(
            vacancy__business_unit=bu
        ).count()
        total_hires = Application.objects.filter(
            vacancy__business_unit=bu,
            status='hired'
        ).count()
        return (total_hires / total_applications * 100) if total_applications else 0

    @staticmethod
    def get_skill_distribution():
        """Obtiene la distribución de habilidades entre candidatos."""
        skills = {}
        for person in Person.objects.all():
            for skill in person.skills:
                skills[skill] = skills.get(skill, 0) + 1
        return dict(sorted(skills.items(), key=lambda x: x[1], reverse=True)[:10])

    @staticmethod
    def get_experience_distribution():
        """Obtiene la distribución de años de experiencia."""
        experience = {}
        for person in Person.objects.all():
            years = person.experience_years
            if years:
                if years not in experience:
                    experience[years] = 0
                experience[years] += 1
        return dict(sorted(experience.items()))

    @staticmethod
    def get_salary_distribution():
        """Obtiene la distribución de salarios esperados."""
        salaries = {}
        for person in Person.objects.all():
            salary = person.expected_salary
            if salary:
                range_key = f'{salary//1000*1000}-{(salary//1000+1)*1000-1}'
                if range_key not in salaries:
                    salaries[range_key] = 0
                salaries[range_key] += 1
        return dict(sorted(salaries.items()))

    @staticmethod
    def get_education_distribution():
        """Obtiene la distribución de niveles educativos."""
        education = {}
        for person in Person.objects.all():
            level = person.education
            if level:
                if level not in education:
                    education[level] = 0
                education[level] += 1
        return dict(sorted(education.items()))

    @staticmethod
    def get_location_distribution():
        """Obtiene la distribución geográfica de candidatos."""
        locations = {}
        for person in Person.objects.all():
            location = person.location
            if location:
                if location not in locations:
                    locations[location] = 0
                locations[location] += 1
        return dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10])

    @staticmethod
    def get_application_status_distribution():
        """Obtiene la distribución de estados de aplicaciones."""
        status = {}
        for app in Application.objects.all():
            if app.status not in status:
                status[app.status] = 0
            status[app.status] += 1
        return dict(sorted(status.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def get_vacancy_status_distribution():
        """Obtiene la distribución de estados de vacantes."""
        status = {}
        for vacancy in Vacante.objects.all():
            if vacancy.status not in status:
                status[vacancy.status] = 0
            status[vacancy.status] += 1
        return dict(sorted(status.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def get_gamification_leaderboard():
        """Obtiene el ranking de gamificación."""
        return EnhancedNetworkGamificationProfile.objects.all().order_by('-points')[:10]

    @staticmethod
    def get_recent_activity():
        """Obtiene la actividad reciente del sistema."""
        return Application.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-updated_at')[:10]

    @staticmethod
    def get_top_performers():
        """Obtiene los mejores candidatos según su perfil."""
        return Person.objects.all().order_by('-gamification_score')[:10]

    @staticmethod
    def get_top_vacancies():
        """Obtiene las vacantes más populares."""
        return Vacante.objects.annotate(
            applications_count=Count('application')
        ).order_by('-applications_count')[:10]
