from django.contrib import admin
from app.ats.pricing.models import PricingStrategy, PricePoint, DiscountRule, ReferralFee

@admin.register(PricingStrategy)
class PricingStrategyAdmin(admin.ModelAdmin):
    """Administración de Estrategias de Precios"""
    
    list_display = (
        'name',
        'type',
        'status',
        'created_at',
        'last_updated'
    )
    
    list_filter = (
        'type',
        'status',
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
                'type',
                'status',
                'description'
            )
        }),
        ('Configuración', {
            'fields': (
                'base_price',
                'currency',
                'pricing_model'
            )
        }),
        ('Reglas', {
            'fields': (
                'discount_rules',
                'referral_fees',
                'conditions'
            )
        }),
        ('Métricas', {
            'fields': (
                'success_rate',
                'conversion_rate',
                'revenue_impact'
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
        'valid_from',
        'valid_to'
    )
    
    search_fields = (
        'strategy__name',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'strategy',
                'amount',
                'currency'
            )
        }),
        ('Validez', {
            'fields': (
                'valid_from',
                'valid_to'
            )
        }),
        ('Condiciones', {
            'fields': (
                'conditions',
                'description'
            )
        })
    )

@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    """Administración de Reglas de Descuento"""
    
    list_display = (
        'name',
        'type',
        'discount_amount',
        'is_active',
        'valid_from'
    )
    
    list_filter = (
        'type',
        'is_active',
        'valid_from'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'type',
                'is_active'
            )
        }),
        ('Descuento', {
            'fields': (
                'discount_amount',
                'discount_type',
                'max_discount'
            )
        }),
        ('Validez', {
            'fields': (
                'valid_from',
                'valid_to',
                'usage_limit'
            )
        }),
        ('Condiciones', {
            'fields': (
                'conditions',
                'description'
            )
        })
    )

@admin.register(ReferralFee)
class ReferralFeeAdmin(admin.ModelAdmin):
    """Administración de Comisiones por Referidos"""
    
    list_display = (
        'name',
        'fee_type',
        'amount',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'fee_type',
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
                'fee_type',
                'is_active'
            )
        }),
        ('Comisión', {
            'fields': (
                'amount',
                'currency',
                'payment_terms'
            )
        }),
        ('Condiciones', {
            'fields': (
                'conditions',
                'description'
            )
        })
    ) 