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
        'business_unit',
        'active',
        'created_at',
        'updated_at'
    )
    
    list_filter = (
        'active',
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
                'active'
            )
        }),
        ('Unidad de Negocio', {
            'fields': (
                'business_unit',
            )
        })
    )

@admin.register(PricePoint)
class PricePointAdmin(admin.ModelAdmin):
    """Administración de Puntos de Precio"""
    
    list_display = (
        'strategy',
        'service_type',
        'base_price',
        'currency',
        'min_duration',
        'max_duration'
    )
    
    list_filter = (
        'service_type',
        'currency'
    )
    
    search_fields = (
        'strategy__name',
        'service_type'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'strategy',
                'service_type',
                'base_price',
                'currency'
            )
        }),
        ('Duración', {
            'fields': (
                'min_duration',
                'max_duration'
            )
        })
    )

@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    """Administración de Reglas de Descuento"""
    
    list_display = (
        'strategy',
        'service_type',
        'discount_type',
        'discount_value',
        'min_amount',
        'max_amount',
        'active'
    )
    
    list_filter = (
        'service_type',
        'discount_type',
        'active'
    )
    
    search_fields = (
        'strategy__name',
        'service_type'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'strategy',
                'service_type',
                'discount_type',
                'discount_value',
                'active'
            )
        }),
        ('Límites', {
            'fields': (
                'min_amount',
                'max_amount'
            )
        })
    )

@admin.register(ReferralFee)
class ReferralFeeAdmin(admin.ModelAdmin):
    """Administración de Comisiones por Referidos"""
    
    list_display = (
        'strategy',
        'service_type',
        'fee_type',
        'fee_value',
        'min_amount',
        'max_amount',
        'active'
    )
    
    list_filter = (
        'service_type',
        'fee_type',
        'active'
    )
    
    search_fields = (
        'strategy__name',
        'service_type'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'strategy',
                'service_type',
                'fee_type',
                'fee_value',
                'active'
            )
        }),
        ('Límites', {
            'fields': (
                'min_amount',
                'max_amount'
            )
        })
    )

@admin.register(PricingCalculation)
class PricingCalculationAdmin(admin.ModelAdmin):
    """Administración de Cálculos de Precio"""
    
    list_display = (
        'business_unit',
        'service_type',
        'base_price',
        'discounts',
        'referral_fees',
        'total',
        'currency',
        'created_at'
    )
    
    list_filter = (
        'service_type',
        'currency',
        'created_at'
    )
    
    search_fields = (
        'business_unit__name',
        'service_type'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'business_unit',
                'service_type',
                'base_price',
                'currency'
            )
        }),
        ('Cálculos', {
            'fields': (
                'discounts',
                'referral_fees',
                'total'
            )
        }),
        ('Metadatos', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': (
                'created_at',
                'updated_at'
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
            )
        }),
        ('Metadatos', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
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
                'oportunidad',
                'titulo',
                'descripcion',
                'estado'
            )
        }),
        ('Detalles Financieros', {
            'fields': (
                'monto_total',
                'moneda'
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
                'fecha_envio',
                'fecha_aprobacion',
                'fecha_rechazo'
            )
        }),
        ('Metadatos', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
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
                'contenido',
                'orden'
            )
        }),
        ('Metadatos', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        })
    )

@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    """Administración de Plantillas de Propuesta"""
    
    list_display = (
        'nombre',
        'business_unit',
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
                'activo',
                'business_unit'
            )
        }),
        ('Secciones', {
            'fields': (
                'secciones',
            )
        }),
        ('Metadatos', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion'
            )
        })
    ) 