# Ubicación del archivo: /home/pablo/app/config/admin_core.py
"""
Módulo central con implementaciones de administradores para modelos principales.

Este módulo contiene las clases de administración de Django para los modelos
principales del sistema, siguiendo las reglas globales de Grupo huntRED®.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from app.config.admin_base import BaseModelAdmin, TokenMaskingMixin

# Importaciones de modelos principales
from app.models import (
    # Core models
    Person, 
    Application, 
    Vacante, 
    BusinessUnit,
    
    # Configuration models
    Configuracion,
    
    # Gamification models
    EnhancedNetworkGamificationProfile,
    GamificationAchievement, 
    GamificationBadge, 
    GamificationEvent,
    
    # Workflow models
    WorkflowStage,
    ChatState
)

# ===== CORE MODELS ADMIN CLASSES =====

class PersonAdmin(BaseModelAdmin):
    """Admin para gestión de candidatos y profesionales"""
    list_display = (
        'full_name', 'email', 'phone', 'status', 'gamification_score',
        'created_at', 'last_updated'
    )
    list_filter = (
        'status', 'education', 'location', 'created_at', 'last_updated'
    )
    search_fields = ('email', 'phone', 'full_name')
    readonly_fields = ('created_at', 'last_updated')
    fieldsets = (
        (_('Información Personal'), {
            'fields': (
                'full_name', 'email', 'phone', 'location',
                'photo', 'date_of_birth', 'gender'
            )
        }),
        (_('Información Profesional'), {
            'fields': (
                'education', 'experience_years', 'current_position',
                'expected_salary', 'skills', 'languages'
            )
        }),
        (_('Estado y Gamificación'), {
            'fields': (
                'status', 'gamification_score', 'gamification_profile',
                'created_at', 'last_updated'
            )
        })
    )


class ApplicationAdmin(BaseModelAdmin):
    """Admin para gestión de aplicaciones a vacantes"""
    list_display = (
        'candidate', 'vacancy', 'status', 'created_at', 'last_updated',
        'interview_date', 'score', 'get_cv_link'
    )
    list_filter = ('status', 'vacancy', 'created_at', 'last_updated')
    search_fields = ('candidate__email', 'vacancy__title')
    readonly_fields = ('created_at', 'last_updated', 'score')
    
    def get_cv_link(self, obj):
        """Generando enlace para visualizar CV del candidato"""
        if obj.cv_file:
            return format_html(
                '<a href="{}" target="_blank">Ver CV</a>',
                obj.cv_file.url
            )
        return '-'
    get_cv_link.short_description = _('CV')


class VacanteAdmin(BaseModelAdmin):
    """Admin para gestión de vacantes"""
    list_display = (
        'title', 'business_unit', 'status', 'salary_range',
        'applications_count', 'created_at', 'last_updated'
    )
    list_filter = (
        'status', 'business_unit', 'salary_range',
        'created_at', 'last_updated'
    )
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'last_updated')
    
    def applications_count(self, obj):
        """Contando número de aplicaciones para esta vacante"""
        return obj.application_set.count()
    applications_count.short_description = _('Aplicaciones')


class BusinessUnitAdmin(BaseModelAdmin):
    """Admin para gestión de unidades de negocio"""
    list_display = ('name', 'description', 'active', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


# ===== GAMIFICATION MODELS ADMIN CLASSES =====

class GamificationProfileAdmin(BaseModelAdmin):
    """Admin para gestión de perfiles de gamificación"""
    list_display = (
        'user', 'points', 'level', 'experience',
        'last_activity', 'created_at'
    )
    list_filter = ('level', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)


class GamificationAchievementAdmin(BaseModelAdmin):
    """Admin para gestión de logros de gamificación"""
    list_display = (
        'name', 'description', 'points', 'type',
        'created_at', 'last_updated'
    )
    list_filter = ('type', 'created_at', 'last_updated')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'last_updated')


class GamificationBadgeAdmin(BaseModelAdmin):
    """Admin para gestión de insignias de gamificación"""
    list_display = (
        'name', 'description', 'points_required',
        'created_at', 'last_updated'
    )
    list_filter = ('created_at', 'last_updated')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'last_updated')


class GamificationEventAdmin(BaseModelAdmin):
    """Admin para gestión de eventos de gamificación"""
    list_display = (
        'user', 'achievement', 'points', 'created_at'
    )
    list_filter = ('created_at',)
    search_fields = (
        'user__email', 'user__full_name',
        'achievement__name'
    )
    readonly_fields = ('created_at',)


# ===== WORKFLOW MODELS ADMIN CLASSES =====

class WorkflowStageAdmin(BaseModelAdmin):
    """Admin para gestión de etapas de workflow"""
    list_display = (
        'name', 'order', 'duration_days', 'is_active',
        'created_at', 'last_updated'
    )
    list_filter = ('is_active', 'created_at', 'last_updated')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'last_updated')


class ChatStateAdmin(BaseModelAdmin):
    """Admin para gestión de estados de chat"""
    list_display = (
        'user', 'current_state', 'last_message',
        'last_interaction', 'created_at'
    )
    list_filter = ('current_state', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)


# ===== CONFIGURATION MODELS ADMIN CLASSES =====

class ConfiguracionAdmin(TokenMaskingMixin, BaseModelAdmin):
    """Admin para gestión de configuraciones del sistema con tokens enmascarados"""
    token_fields = ['secret_key', 'sentry_dsn']
    list_display = ('secret_key', 'debug_mode', 'sentry_dsn')
