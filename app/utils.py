"""
Archivo de compatibilidad para utilidades de Grupo huntRED®.
Este archivo importa funciones desde los módulos específicos en app/utils/
para mantener compatibilidad con el código existente.

NOTA: Este archivo será eliminado eventualmente. Todo el código nuevo debe
usar directamente los módulos específicos.
"""

import os
import re
import json
import pytz
import requests
import hashlib
import logging
import base64
from io import BytesIO
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import RemovedInNextVersionWarning
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from app.models import BusinessUnit, Vacante, Person
import warnings

# Advertencia de deprecación
warnings.warn(
    "El archivo app/utils.py está obsoleto. Usa los módulos específicos en app/utils/",
    RemovedInNextVersionWarning, stacklevel=2
)

# Configuración de logging
logger = logging.getLogger(__name__)

# Notificar la carga del archivo deprecado
logger.warning(
    "El archivo app/utils.py está obsoleto. Se recomienda usar los módulos específicos en app/utils/"
)

# Importar desde módulos específicos para mantener compatibilidad
from app.ats.utils.common import (
    format_duration, truncate_text, get_business_unit,
    sanitize_string, format_currency
)

from app.ats.utils.http import (
    fetch_data_async, post_data_async,
    handle_api_response, retry_request
)

from app.ats.utils.date import (
    get_local_now, format_date_for_locale,
    get_next_business_day, calculate_date_difference
)

from app.ats.utils.analysis import (
    calculate_similarity_score, extract_keywords,
    analyze_text_sentiment
)

class SystemUtils:
    @staticmethod
    def get_user_metrics(user: Person) -> Dict[str, int]:
        """Obtiene métricas del usuario."""
        return {
            'applications': user.application_set.count(),
            'active_applications': user.application_set.filter(
                status__in=['applied', 'in_review', 'interview']
            ).count(),
            'hired': user.application_set.filter(status='hired').count(),
            'rejected': user.application_set.filter(status='rejected').count(),
            'gamification_score': user.gamification_profile.points
        }

    @staticmethod
    def get_system_metrics() -> Dict[str, int]:
        """Obtiene métricas del sistema."""
        return {
            'total_users': Person.objects.count(),
            'active_users': Person.objects.filter(
                last_updated__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'total_applications': Application.objects.count(),
            'active_applications': Application.objects.filter(
                status__in=['applied', 'in_review', 'interview']
            ).count(),
            'total_vacancies': Vacante.objects.count(),
            'active_vacancies': Vacante.objects.filter(
                status__in=['active', 'in_progress']
            ).count()
        }

    @staticmethod
    def get_business_unit_metrics(bu: BusinessUnit) -> Dict[str, int]:
        """Obtiene métricas por unidad de negocio."""
        return {
            'total_applications': Application.objects.filter(
                vacancy__business_unit=bu
            ).count(),
            'active_applications': Application.objects.filter(
                vacancy__business_unit=bu,
                status__in=['applied', 'in_review', 'interview']
            ).count(),
            'total_vacancies': Vacante.objects.filter(business_unit=bu).count(),
            'active_vacancies': Vacante.objects.filter(
                business_unit=bu,
                status__in=['active', 'in_progress']
            ).count(),
            'total_hires': Application.objects.filter(
                vacancy__business_unit=bu,
                status='hired'
            ).count()
        }

    @staticmethod
    def get_workflow_metrics() -> Dict[str, Dict]:
        """Obtiene métricas del flujo de trabajo."""
        metrics = {}
        for stage in WorkflowStage.objects.all():
            metrics[stage.name] = {
                'applications': Application.objects.filter(
                    status=stage.name
                ).count(),
                'average_days': Application.objects.filter(
                    status=stage.name
                ).annotate(
                    days=ExtractDay(F('updated_at') - F('created_at'))
                ).aggregate(avg=Avg('days'))['avg'] or 0
            }
        return metrics

    @staticmethod
    def get_gamification_metrics() -> Dict[str, int]:
        """Obtiene métricas de gamificación."""
        return {
            'total_points': EnhancedNetworkGamificationProfile.objects.aggregate(
                total_points=Sum('points')
            )['total_points'] or 0,
            'total_badges': GamificationBadge.objects.count(),
            'total_achievements': GamificationAchievement.objects.count(),
            'active_users': EnhancedNetworkGamificationProfile.objects.filter(
                last_activity__gte=timezone.now() - timedelta(days=30)
            ).count()
        }

    @staticmethod
    def get_chat_metrics() -> Dict[str, int]:
        """Obtiene métricas del chat."""
        return {
            'total_users': ChatState.objects.count(),
            'active_users': ChatState.objects.filter(
                last_interaction__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'total_messages': ChatState.objects.aggregate(
                total_messages=Sum('message_count')
            )['total_messages'] or 0,
            'average_messages': ChatState.objects.aggregate(
                avg_messages=Avg('message_count')
            )['avg_messages'] or 0
        }

    @staticmethod
    def get_user_engagement(user: Person) -> Dict[str, float]:
        """Obtiene métricas de engagement del usuario."""
        now = timezone.now()
        
        # Interacciones recientes
        interactions = ChatState.objects.filter(
            user=user,
            last_interaction__gte=now - timedelta(days=30)
        ).count()
        
        # Aplicaciones recientes
        applications = Application.objects.filter(
            user=user,
            created_at__gte=now - timedelta(days=30)
        ).count()
        
        # Tiempo promedio de respuesta
        avg_response_time = ChatState.objects.filter(
            user=user
        ).annotate(
            response_time=ExtractDay(F('last_interaction') - F('created_at'))
        ).aggregate(avg=Avg('response_time'))['avg'] or 0
        
        return {
            'interactions': interactions,
            'applications': applications,
            'avg_response_time': avg_response_time,
            'engagement_score': (interactions + applications) / (avg_response_time + 1)
        }

    @staticmethod
    def get_system_engagement() -> Dict[str, float]:
        """Obtiene métricas de engagement del sistema."""
        now = timezone.now()
        
        # Interacciones totales
        interactions = ChatState.objects.filter(
            last_interaction__gte=now - timedelta(days=30)
        ).count()
        
        # Aplicaciones totales
        applications = Application.objects.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()
        
        # Tiempo promedio de respuesta
        avg_response_time = ChatState.objects.annotate(
            response_time=ExtractDay(F('last_interaction') - F('created_at'))
        ).aggregate(avg=Avg('response_time'))['avg'] or 0
        
        return {
            'total_interactions': interactions,
            'total_applications': applications,
            'avg_response_time': avg_response_time,
            'engagement_score': (interactions + applications) / (avg_response_time + 1)
        }

    @staticmethod
    def get_conversion_metrics() -> Dict[str, float]:
        """Obtiene métricas de conversión."""
        total_applications = Application.objects.count()
        total_hires = Application.objects.filter(status='hired').count()
        
        return {
            'conversion_rate': (total_hires / total_applications * 100) if total_applications else 0,
            'applications_per_hire': (total_applications / total_hires) if total_hires else 0,
            'hires_per_month': Application.objects.filter(
                status='hired',
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
        }

    @staticmethod
    def get_application_metrics() -> Dict[str, int]:
        """Obtiene métricas de aplicaciones."""
        return {
            'total': Application.objects.count(),
            'applied': Application.objects.filter(status='applied').count(),
            'in_review': Application.objects.filter(status='in_review').count(),
            'interview': Application.objects.filter(status='interview').count(),
            'hired': Application.objects.filter(status='hired').count(),
            'rejected': Application.objects.filter(status='rejected').count()
        }

    @staticmethod
    def get_vacancy_metrics() -> Dict[str, int]:
        """Obtiene métricas de vacantes."""
        return {
            'total': Vacante.objects.count(),
            'active': Vacante.objects.filter(status='active').count(),
            'in_progress': Vacante.objects.filter(status='in_progress').count(),
            'closed': Vacante.objects.filter(status='closed').count(),
            'draft': Vacante.objects.filter(status='draft').count()
        }

    @staticmethod
    def get_skill_distribution() -> Dict[str, int]:
        """Obtiene la distribución de habilidades."""
        skills = {}
        for person in Person.objects.all():
            for skill in person.skills:
                skills[skill] = skills.get(skill, 0) + 1
        return dict(sorted(skills.items(), key=lambda x: x[1], reverse=True)[:10])

    @staticmethod
    def get_experience_distribution() -> Dict[str, int]:
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
    def get_salary_distribution() -> Dict[str, int]:
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
    def get_education_distribution() -> Dict[str, int]:
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
    def get_location_distribution() -> Dict[str, int]:
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
    def get_application_status_distribution() -> Dict[str, int]:
        """Obtiene la distribución de estados de aplicaciones."""
        status = {}
        for app in Application.objects.all():
            if app.status not in status:
                status[app.status] = 0
            status[app.status] += 1
        return dict(sorted(status.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def get_vacancy_status_distribution() -> Dict[str, int]:
        """Obtiene la distribución de estados de vacantes."""
        status = {}
        for vacancy in Vacante.objects.all():
            if vacancy.status not in status:
                status[vacancy.status] = 0
            status[vacancy.status] += 1
        return dict(sorted(status.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def get_gamification_leaderboard() -> List[Dict]:
        """Obtiene el ranking de gamificación."""
        return EnhancedNetworkGamificationProfile.objects.all().order_by('-points')[:10]

    @staticmethod
    def get_recent_activity() -> List[Dict]:
        """Obtiene la actividad reciente del sistema."""
        return Application.objects.filter(
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-updated_at')[:10]

    @staticmethod
    def get_top_performers() -> List[Dict]:
        """Obtiene los mejores candidatos según su perfil."""
        return Person.objects.all().order_by('-gamification_score')[:10]

    @staticmethod
    def get_top_vacancies() -> List[Dict]:
        """Obtiene las vacantes más populares."""
        return Vacante.objects.annotate(
            applications_count=Count('application')
        ).order_by('-applications_count')[:10]
