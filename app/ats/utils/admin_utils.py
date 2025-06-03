# Ubicación del archivo: /home/pablo/app/com/utils/admin_utils.py

# Django Core Imports
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

# Importing admin base classes
from app.ats.utils.admin_base import BaseModelAdmin, TokenMaskingMixin

# Comprehensive model imports
from app.models import (
    # Core models
    Person,
    Vacante,
    BusinessUnit,
    Application,
    
    # Chatbot models
    IntentPattern,
    StateTransition,
    ChatState,
    UserInteractionLog,
    Chat,
    
    # Scraping models
    DominioScraping,
    RegistroScraping,
    
    # Configuration models
    ConfiguracionBU,
    GptApi,
    Worker,
    
    # Additional models from admin_config.py
    EnhancedNetworkGamificationProfile,
    WorkflowStage,
    GamificationAchievement,
    GamificationBadge,
    GamificationEvent,
    Configuracion
)

class BusinessUnitFilter(SimpleListFilter):
    title = _('Unidad de Negocio')
    parameter_name = 'business_unit'

    def lookups(self, request, model_admin):
        return BusinessUnit.objects.values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(business_unit_id=self.value())
        return queryset

class StateFilter(SimpleListFilter):
    title = _('Estado')
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Activo')),
            ('completed', _('Completado')),
            ('rejected', _('Rechazado')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status__in=['applied', 'screening', 'interview'])
        elif self.value() == 'completed':
            return queryset.filter(status='hired')
        elif self.value() == 'rejected':
            return queryset.filter(status='rejected')
        return queryset


# Clases Admin desde admin_config.py que se migran aquí
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


class OptimizedApplicationAdmin(BaseModelAdmin):
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


class OptimizedVacanteAdmin(BaseModelAdmin):
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


class OptimizedBusinessUnitAdmin(BaseModelAdmin):
    """Admin para gestión de unidades de negocio"""
    list_display = ('name', 'description', 'active', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)


class GamificationProfileAdmin(BaseModelAdmin):
    """Admin para gestión de perfiles de gamificación"""
    list_display = (
        'user', 'points', 'level', 'experience',
        'last_activity', 'created_at'
    )
    list_filter = ('level', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)


class ChatStateAdmin(BaseModelAdmin):
    """Admin para gestión de estados de chat"""
    list_display = (
        'user', 'current_state', 'last_message',
        'last_interaction', 'created_at'
    )
    list_filter = ('current_state', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)


class WorkflowStageAdmin(BaseModelAdmin):
    """Admin para gestión de etapas de workflow"""
    list_display = (
        'name', 'order', 'duration_days', 'is_active',
        'created_at', 'last_updated'
    )
    list_filter = ('is_active', 'created_at', 'last_updated')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'last_updated')


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


class ConfiguracionAdmin(TokenMaskingMixin, BaseModelAdmin):
    """Admin para gestión de configuraciones del sistema con tokens enmascarados"""
    token_fields = ['secret_key', 'sentry_dsn']
    list_display = ('secret_key', 'debug_mode', 'sentry_dsn')


# Función para el registro centralizado de administradores
def register_admin_configurations():
    """Registrando configuraciones de administración de manera centralizada"""
    
    # Core Models Admins
    admin.site.register(Person, PersonAdmin)
    
    # Reemplazando admin existentes si es necesario
    try:
        admin.site.unregister(Application)
        admin.site.register(Application, OptimizedApplicationAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(Application, OptimizedApplicationAdmin)
        
    try:
        admin.site.unregister(Vacante)
        admin.site.register(Vacante, OptimizedVacanteAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(Vacante, OptimizedVacanteAdmin)
        
    try:
        admin.site.unregister(BusinessUnit)
        admin.site.register(BusinessUnit, OptimizedBusinessUnitAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(BusinessUnit, OptimizedBusinessUnitAdmin)
        
    # Gamification Models Admins
    try:
        admin.site.unregister(EnhancedNetworkGamificationProfile)
        admin.site.register(EnhancedNetworkGamificationProfile, GamificationProfileAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(EnhancedNetworkGamificationProfile, GamificationProfileAdmin)
        
    try:
        admin.site.unregister(GamificationAchievement)
        admin.site.register(GamificationAchievement, GamificationAchievementAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(GamificationAchievement, GamificationAchievementAdmin)
        
    try:
        admin.site.unregister(GamificationBadge)
        admin.site.register(GamificationBadge, GamificationBadgeAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(GamificationBadge, GamificationBadgeAdmin)
        
    try:
        admin.site.unregister(GamificationEvent)
        admin.site.register(GamificationEvent, GamificationEventAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(GamificationEvent, GamificationEventAdmin)
        
    # Workflow Models Admins
    try:
        admin.site.unregister(WorkflowStage)
        admin.site.register(WorkflowStage, WorkflowStageAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(WorkflowStage, WorkflowStageAdmin)
        
    try:
        admin.site.unregister(ChatState)
        admin.site.register(ChatState, ChatStateAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(ChatState, ChatStateAdmin)
        
    # Configuration Models Admins
    try:
        admin.site.unregister(Configuracion)
        admin.site.register(Configuracion, ConfiguracionAdmin)
    except admin.sites.NotRegistered:
        admin.site.register(Configuracion, ConfiguracionAdmin)
