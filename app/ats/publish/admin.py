# app/ats/publish/admin.py
"""
Admin de Django Avanzado para el Sistema de Publicación.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Sum, Avg
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta

from app.ats.publish.models import (
    MarketingCampaign, CampaignApproval, CampaignMetrics, 
    CampaignAuditLog, AudienceSegment, ContentTemplate,
    RetargetingCampaign, MarketingEvent, JobBoard
)

class CampaignStatusFilter(SimpleListFilter):
    """
    Filtro personalizado para estado de campañas.
    """
    title = 'Estado de Campaña'
    parameter_name = 'campaign_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Activas'),
            ('pending', 'Pendientes'),
            ('completed', 'Completadas'),
            ('cancelled', 'Canceladas'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status='active')
        elif self.value() == 'pending':
            return queryset.filter(status='pending')
        elif self.value() == 'completed':
            return queryset.filter(status='completed')
        elif self.value() == 'cancelled':
            return queryset.filter(status='cancelled')

class ApprovalStatusFilter(SimpleListFilter):
    """
    Filtro personalizado para estado de aprobaciones.
    """
    title = 'Estado de Aprobación'
    parameter_name = 'approval_status'

    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pendiente'),
            ('reviewing', 'En Revisión'),
            ('approved', 'Aprobada'),
            ('rejected', 'Rechazada'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())

@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    """
    Admin avanzado para campañas de marketing.
    """
    list_display = [
        'name', 'campaign_type', 'status', 'start_date', 
        'end_date', 'budget', 'created_at'
    ]
    list_filter = ['status', 'campaign_type', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = [
        'created_at', 'updated_at'
    ]
    


@admin.register(CampaignApproval)
class CampaignApprovalAdmin(admin.ModelAdmin):
    """
    Admin para workflow de aprobación.
    """
    list_display = [
        'campaign_name', 'status', 'required_level', 'created_by', 
        'created_at', 'approved_by', 'approved_at'
    ]
    list_filter = ['status', 'required_level', 'created_at']
    search_fields = ['campaign__name', 'created_by__username', 'approved_by__username']
    readonly_fields = [
        'created_at', 'submitted_at', 
        'reviewed_at', 'approved_at'
    ]
    
    def campaign_name(self, obj):
        """Nombre de la campaña con link."""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:app_marketingcampaign_change', args=[obj.campaign.id]),
            obj.campaign.name
        )
    campaign_name.short_description = 'Campaña'
    


@admin.register(CampaignMetrics)
class CampaignMetricsAdmin(admin.ModelAdmin):
    """
    Admin para métricas de campañas.
    """
    list_display = [
        'campaign_name', 'measurement_date', 'engagement_score', 
        'open_rate', 'click_rate', 'conversion_rate', 'roi'
    ]
    list_filter = ['measurement_date', 'campaign__campaign_type']
    search_fields = ['campaign__name']
    readonly_fields = [
        'engagement_score', 'roi', 'cost_per_conversion', 
        'aura_prediction_accuracy', 'aura_optimization_impact'
    ]
    
    def campaign_name(self, obj):
        """Nombre de la campaña con link."""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:app_marketingcampaign_change', args=[obj.campaign.id]),
            obj.campaign.name
        )
    campaign_name.short_description = 'Campaña'
    
    def engagement_score(self, obj):
        """Score de engagement con color."""
        score = obj.engagement_score
        if score > 7:
            color = 'green'
        elif score > 5:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color, score
        )
    engagement_score.short_description = 'Engagement'

@admin.register(CampaignAuditLog)
class CampaignAuditLogAdmin(admin.ModelAdmin):
    """
    Admin para log de auditoría.
    """
    list_display = [
        'campaign_name', 'action', 'user', 'action_timestamp', 
        'ip_address', 'changes_summary'
    ]
    list_filter = ['action', 'action_timestamp', 'campaign__campaign_type']
    search_fields = ['campaign__name', 'user__username', 'notes']
    readonly_fields = [
        'campaign', 'user', 'action', 'action_timestamp', 
        'ip_address', 'user_agent', 'previous_state', 'new_state', 
        'changes_summary', 'notes'
    ]
    
    def campaign_name(self, obj):
        """Nombre de la campaña con link."""
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:app_marketingcampaign_change', args=[obj.campaign.id]),
            obj.campaign.name
        )
    campaign_name.short_description = 'Campaña'
    
    def has_add_permission(self, request):
        """No permitir agregar logs manualmente."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar logs."""
        return request.user.is_superuser

@admin.register(AudienceSegment)
class AudienceSegmentAdmin(admin.ModelAdmin):
    """
    Admin para segmentos de audiencia.
    """
    list_display = ['name', 'segment_type', 'active', 'predicted_size', 'created_at']
    list_filter = ['segment_type', 'active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(ContentTemplate)
class ContentTemplateAdmin(admin.ModelAdmin):
    """
    Admin para plantillas de contenido.
    """
    list_display = ['name', 'template_type', 'active', 'created_at']
    list_filter = ['template_type', 'active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(RetargetingCampaign)
class RetargetingCampaignAdmin(admin.ModelAdmin):
    """
    Admin para campañas de retargeting.
    """
    list_display = ['name', 'retargeting_type', 'active', 'lookback_days', 'budget']
    list_filter = ['retargeting_type', 'active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(MarketingEvent)
class MarketingEventAdmin(admin.ModelAdmin):
    """
    Admin para eventos de marketing.
    """
    list_display = ['title', 'event_type', 'start_datetime', 'location', 'status']
    list_filter = ['event_type', 'status', 'start_datetime']
    search_fields = ['title', 'description']

@admin.register(JobBoard)
class JobBoardAdmin(admin.ModelAdmin):
    """
    Admin para job boards.
    """
    list_display = ['name', 'job_board_type', 'active', 'api_configured']
    list_filter = ['job_board_type', 'active']
    search_fields = ['name', 'description']
    
    def api_configured(self, obj):
        """Indica si la API está configurada."""
        if obj.api_key and obj.api_secret:
            return format_html('<span style="color: green;">✓ Configurada</span>')
        return format_html('<span style="color: red;">✗ No Configurada</span>')
    api_configured.short_description = 'API Configurada'

# Personalización del admin
admin.site.site_header = "Grupo huntRED - Sistema de Administración de Talento & IA"
admin.site.site_title = "huntRED Admin"
admin.site.index_title = "Panel de Administración"

# Agregar acciones personalizadas
@admin.action(description="Aprobar campañas seleccionadas")
def approve_campaigns(modeladmin, request, queryset):
    """Aprobar múltiples campañas."""
    for campaign in queryset:
        if campaign.approvals.filter(status='pending').exists():
            approval = campaign.approvals.filter(status='pending').first()
            try:
                approval.approve(
                    user=request.user,
                    notes='Aprobación masiva desde admin',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            except Exception as e:
                modeladmin.message_user(request, f"Error aprobando {campaign.name}: {str(e)}")

@admin.action(description="Activar campañas seleccionadas")
def activate_campaigns(modeladmin, request, queryset):
    """Activar múltiples campañas."""
    updated = queryset.update(status='active')
    modeladmin.message_user(request, f"{updated} campañas activadas.")

@admin.action(description="Pausar campañas seleccionadas")
def pause_campaigns(modeladmin, request, queryset):
    """Pausar múltiples campañas."""
    updated = queryset.update(status='paused')
    modeladmin.message_user(request, f"{updated} campañas pausadas.")

# Agregar acciones a MarketingCampaignAdmin
MarketingCampaignAdmin.actions = [
    approve_campaigns, 
    activate_campaigns, 
    pause_campaigns
]
