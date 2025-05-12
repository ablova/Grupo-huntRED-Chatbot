# Ubicación del archivo: /home/pablo/app/admin_config.py
# ARCHIVO OBSOLETO - NO USAR - Mayo 2025
"""
Este archivo está OBSOLETO y se mantiene temporalmente por compatibilidad.
Todo el código ha sido migrado a una estructura más modular siguiendo
las reglas globales de Grupo huntRED® para configuración de administradores.

Las nuevas ubicaciones son:
- app/com/utils/admin_base.py: Clases base y mixins reutilizables
- app/com/utils/admin_utils.py: Implementaciones específicas de ModelAdmin
- app/com/utils/admin_registry.py: Registro centralizado de configuraciones

Para agregar nuevas configuraciones de administrador, por favor utiliza
la estructura modular en lugar de modificar este archivo.
"""

# Importando solo lo necesario para mantener compatibilidad
import warnings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from app.models import (
    Person, Application, Vacante, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState, WorkflowStage,
    GamificationAchievement, GamificationBadge, GamificationEvent
)

# Emitiendo advertencia de deprecación
warnings.warn(
    "El archivo admin_config.py está obsoleto y será eliminado en futuras versiones. "
    "Utilice la nueva estructura modular en app/com/utils/admin_*.py",
    DeprecationWarning, stacklevel=2
)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
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

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'candidate', 'vacancy', 'status', 'created_at', 'last_updated',
        'interview_date', 'score', 'get_cv_link'
    )
    list_filter = ('status', 'vacancy', 'created_at', 'last_updated')
    search_fields = ('candidate__email', 'vacancy__title')
    readonly_fields = ('created_at', 'last_updated', 'score')
    
    def get_cv_link(self, obj):
        if obj.cv_file:
            return format_html(
                '<a href="{}" target="_blank">Ver CV</a>',
                obj.cv_file.url
            )
        return '-'
    get_cv_link.short_description = _('CV')

@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
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
        return obj.application_set.count()
    applications_count.short_description = _('Aplicaciones')

@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'active', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

@admin.register(EnhancedNetworkGamificationProfile)
class GamificationProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'points', 'level', 'experience',
        'last_activity', 'created_at'
    )
    list_filter = ('level', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)

@admin.register(ChatState)
class ChatStateAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'current_state', 'last_message',
        'last_interaction', 'created_at'
    )
    list_filter = ('current_state', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at',)

@admin.register(WorkflowStage)
class WorkflowStageAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'order', 'duration_days', 'is_active',
        'created_at', 'last_updated'
    )
    list_filter = ('is_active', 'created_at', 'last_updated')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'last_updated')

@admin.register(GamificationAchievement)
class GamificationAchievementAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'description', 'points', 'type',
        'created_at', 'last_updated'
    )
    list_filter = ('type', 'created_at', 'last_updated')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'last_updated')

@admin.register(GamificationBadge)
class GamificationBadgeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'description', 'points_required',
        'created_at', 'last_updated'
    )
    list_filter = ('created_at', 'last_updated')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'last_updated')

@admin.register(GamificationEvent)
class GamificationEventAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'achievement', 'points', 'created_at'
    )
    list_filter = ('created_at',)
    search_fields = (
        'user__email', 'user__full_name',
        'achievement__name'
    )
    readonly_fields = ('created_at',)
