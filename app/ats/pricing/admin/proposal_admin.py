from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from app.ats.pricing.models.proposal import Proposal
from app.ats.pricing.models.proposal_section import ProposalSection
from app.ats.pricing.models.proposal_template import ProposalTemplate

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Administración de Propuestas"""
    
    list_display = (
        'business_unit',
        'status',
        'total_value',
        'discounts_applied',
        'created_at',
        'actions'
    )
    
    list_filter = (
        'status',
        'created_at',
        'business_unit'
    )
    
    search_fields = (
        'business_unit__name',
        'sections__content'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'business_unit',
                'status',
                'template'
            )
        }),
        ('Contenido', {
            'fields': (
                'sections',
                'addons'
            )
        }),
        ('Precios', {
            'fields': (
                'base_value',
                'discounts',
                'final_value'
            )
        }),
        ('Métricas', {
            'fields': (
                'conversion_rate',
                'effectiveness'
            )
        })
    )
    
    def total_value(self, obj):
        """Muestra valor total"""
        return f"${obj.final_value:,.2f}"
    
    def discounts_applied(self, obj):
        """Muestra descuentos aplicados"""
        return f"{len(obj.discounts)} descuentos"
    
    def actions(self, obj):
        """Acciones disponibles"""
        return format_html(
            '<a href="{}" class="button">Ver</a> '
            '<a href="{}" class="button">Editar</a> '
            '<a href="{}" class="button">Exportar</a>',
            reverse('admin:pricing_proposal_change', args=[obj.id]),
            reverse('admin:pricing_proposal_change', args=[obj.id]),
            reverse('admin:pricing_proposal_export', args=[obj.id])
        )

@admin.register(ProposalSection)
class ProposalSectionAdmin(admin.ModelAdmin):
    """Administración de Secciones de Propuesta"""
    
    list_display = (
        'proposal',
        'title',
        'order',
        'content_preview'
    )
    
    list_filter = (
        'proposal__status',
        'proposal__business_unit'
    )
    
    search_fields = (
        'title',
        'content'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'proposal',
                'title',
                'order'
            )
        }),
        ('Contenido', {
            'fields': (
                'content',
                'variables'
            )
        }),
        ('Configuración', {
            'fields': (
                'is_required',
                'is_customizable'
            )
        })
    )
    
    def content_preview(self, obj):
        """Muestra vista previa del contenido"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content

@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    """Administración de Plantillas de Propuesta"""
    
    list_display = (
        'name',
        'is_active',
        'usage_count',
        'created_at'
    )
    
    list_filter = (
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'is_active'
            )
        }),
        ('Estructura', {
            'fields': (
                'sections',
                'variables'
            )
        }),
        ('Configuración', {
            'fields': (
                'default_values',
                'customization_options'
            )
        }),
        ('Métricas', {
            'fields': (
                'usage_count',
                'success_rate'
            )
        })
    )
    
    def usage_count(self, obj):
        """Muestra uso de la plantilla"""
        return obj.usage_count or 0 