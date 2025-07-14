# /home/pablo/app/ats/admin/pricing/__init__.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum, Avg

from app.ats.pricing.models import (
    PricingStrategy,
    PricePoint,
    DiscountRule,
    ReferralFee,
    PricingCalculation,
    PricingPayment,
    PricingProposal,
    ProposalSection,
    ProposalTemplate
)

@admin.register(PricingStrategy)
class PricingStrategyAdmin(admin.ModelAdmin):
    """Administración de Estrategias de Precios"""
    
    list_display = (
        'name',
        'type',
        'status',
        'base_price',
        'currency',
        'created_at'
    )
    
    list_filter = (
        'type',
        'status',
        'currency'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    readonly_fields = (
        'created_at',
        'last_updated'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'type',
                'status',
                'description'
            )
        }),
        ('Precios', {
            'fields': (
                'base_price',
                'currency'
            )
        }),
        ('Configuración', {
            'fields': (
                'pricing_model',
                'conditions'
            )
        }),
        ('Métricas', {
            'fields': (
                'success_rate',
                'conversion_rate',
                'revenue_impact'
            )
        }),
        ('Temporal', {
            'fields': (
                'created_at',
                'last_updated'
            )
        })
    )

@admin.register(PricePoint)
class PricePointAdmin(admin.ModelAdmin):
    """Administración de Puntos de Precio"""
    
    list_display = (
        'strategy',
        'amount',
        'currency',
        'valid_from',
        'valid_to'
    )
    
    list_filter = (
        'currency',
        'valid_from'
    )
    
    search_fields = (
        'strategy__name',
        'description'
    )
    
    readonly_fields = (
        'valid_from',
        'valid_to'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'strategy',
                'amount',
                'currency',
                'description'
            )
        }),
        ('Vigencia', {
            'fields': (
                'valid_from',
                'valid_to'
            )
        }),
        ('Configuración', {
            'fields': (
                'conditions',
            )
        })
    )

@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    """Administración de Reglas de Descuento"""
    
    list_display = (
        'type',
        'value',
        'is_active',
        'valid_from',
        'valid_to'
    )
    
    list_filter = (
        'type',
        'is_active',
        'valid_from'
    )
    
    search_fields = (
        'type',
    )
    
    readonly_fields = (
        'valid_from',
        'valid_to'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'type',
                'value',
                'is_active'
            )
        }),
        ('Vigencia', {
            'fields': (
                'valid_from',
                'valid_to'
            )
        }),
        ('Configuración', {
            'fields': (
                'conditions',
            )
        })
    )

@admin.register(ReferralFee)
class ReferralFeeAdmin(admin.ModelAdmin):
    """Administración de Comisiones por Referidos"""
    
    list_display = (
        'type',
        'value',
        'is_active',
        'valid_from',
        'valid_to'
    )
    
    list_filter = (
        'type',
        'is_active',
        'valid_from'
    )
    
    search_fields = (
        'type',
    )
    
    readonly_fields = (
        'valid_from',
        'valid_to'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'type',
                'value',
                'is_active'
            )
        }),
        ('Vigencia', {
            'fields': (
                'valid_from',
                'valid_to'
            )
        }),
        ('Configuración', {
            'fields': (
                'conditions',
            )
        })
    )

@admin.register(PricingCalculation)
class PricingCalculationAdmin(admin.ModelAdmin):
    """Administración de Cálculos de Precio"""
    
    list_display = (
        'id',
        'created_at'
    )
    
    readonly_fields = (
        'created_at',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'created_at',
            )
        })
    )

@admin.register(PricingPayment)
class PricingPaymentAdmin(admin.ModelAdmin):
    """Administración de Pagos"""
    
    list_display = (
        'calculo',
        'estado',
        'monto',
        'moneda',
        'metodo',
        'fecha_creacion'
    )
    
    list_filter = (
        'estado',
        'moneda',
        'metodo',
        'fecha_creacion'
    )
    
    search_fields = (
        'calculo__business_unit__name',
        'id_transaccion'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'calculo',
                'estado',
                'monto',
                'moneda',
                'metodo'
            )
        }),
        ('Transacción', {
            'fields': (
                'id_transaccion',
                'referencia_pago'
            )
        }),
        ('Temporal', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion'
            )
        })
    )

@admin.register(PricingProposal)
class PricingProposalAdmin(admin.ModelAdmin):
    """Administración de Propuestas"""
    
    list_display = (
        'titulo',
        'oportunidad',
        'estado',
        'monto_total',
        'moneda',
        'fecha_creacion'
    )
    
    list_filter = (
        'estado',
        'moneda',
        'fecha_creacion'
    )
    
    search_fields = (
        'titulo',
        'descripcion',
        'oportunidad__nombre'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_envio',
        'fecha_aprobacion',
        'fecha_rechazo'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'titulo',
                'descripcion',
                'oportunidad',
                'estado'
            )
        }),
        ('Precios', {
            'fields': (
                'monto_total',
                'moneda',
                'descuentos',
                'comisiones'
            )
        }),
        ('Temporal', {
            'fields': (
                'fecha_creacion',
                'fecha_envio',
                'fecha_aprobacion',
                'fecha_rechazo'
            )
        })
    )

@admin.register(ProposalSection)
class ProposalSectionAdmin(admin.ModelAdmin):
    """Administración de Secciones de Propuesta"""
    
    list_display = (
        'propuesta',
        'tipo',
        'titulo',
        'orden'
    )
    
    list_filter = (
        'tipo',
        'propuesta__estado'
    )
    
    search_fields = (
        'titulo',
        'contenido',
        'propuesta__titulo'
    )
    
    ordering = (
        'propuesta',
        'orden'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'propuesta',
                'tipo',
                'titulo',
                'orden'
            )
        }),
        ('Contenido', {
            'fields': (
                'contenido',
            )
        })
    )

@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    """Administración de Plantillas de Propuesta"""
    
    list_display = (
        'nombre',
        'activo',
        'fecha_creacion'
    )
    
    list_filter = (
        'activo',
        'fecha_creacion'
    )
    
    search_fields = (
        'nombre',
        'descripcion'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'nombre',
                'descripcion',
                'activo'
            )
        }),
        ('Contenido', {
            'fields': (
                'contenido',
            )
        }),
        ('Temporal', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion'
            )
        })
    ) 