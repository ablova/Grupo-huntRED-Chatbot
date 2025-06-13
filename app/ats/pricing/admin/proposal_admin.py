# /home/pablo/app/ats/pricing/admin/proposal_admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from app.ats.pricing.models.proposal import PricingProposal, ProposalSection, ProposalTemplate

@admin.register(PricingProposal)
class PricingProposalAdmin(admin.ModelAdmin):
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
    
    readonly_fields = ('fecha_creacion', 'fecha_envio', 'fecha_aprobacion', 'fecha_rechazo')
    
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
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_envio', 'fecha_aprobacion', 'fecha_rechazo')
        }),
        ('Metadatos', {
            'fields': ('metadata',),
            'classes': ('collapse',)
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
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(business_unit__in=request.user.business_units.all())
        return qs
    
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.business_unit in request.user.business_units.all()
    
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.business_unit in request.user.business_units.all()
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != 'BORRADOR':
            return self.readonly_fields + ('status', 'total_value', 'discounts_applied')
        return self.readonly_fields
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:proposal_id>/export/',
                self.admin_site.admin_view(self.export_proposal),
                name='pricing_proposal_export',
            ),
        ]
        return custom_urls + urls
    
    def export_proposal(self, request, proposal_id):
        from django.http import HttpResponse
        from django.template.loader import render_to_string
        from weasyprint import HTML
        
        proposal = self.get_object(request, proposal_id)
        if proposal is None:
            return HttpResponse('Propuesta no encontrada', status=404)
        
        html_string = render_to_string('admin/pricing/proposal_export.html', {
            'proposal': proposal,
            'sections': proposal.sections.all().order_by('order'),
            'opts': self.model._meta,
        })
        
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="propuesta_{proposal.id}.pdf"'
        return response
    
    def get_list_display_links(self, request, list_display):
        return ['business_unit']
    
    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if not request.user.is_superuser:
            filters = list(filters)
            if 'business_unit' not in filters:
                filters.append('business_unit')
        return filters
    
    def get_search_fields(self, request):
        search_fields = super().get_search_fields(request)
        if not request.user.is_superuser:
            search_fields = list(search_fields)
            if 'business_unit__name' not in search_fields:
                search_fields.append('business_unit__name')
        return search_fields

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
    
    ordering = ('proposal', 'order')
    
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
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(proposal__business_unit__in=request.user.business_units.all())
        return qs

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
    
    readonly_fields = ('created_at', 'updated_at')
    
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
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def usage_count(self, obj):
        """Muestra uso de la plantilla"""
        return obj.usage_count or 0 