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
    DiscountCoupon,
    TeamEvaluation,
    PromotionBanner,
    PremiumAddon,
    BusinessUnitAddon
)

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
        'type',
        'value',
        'is_active',
        'valid_from',
        'valid_to'
    )
    
    list_filter = (
        'type',
        'is_active',
        'valid_from',
        'valid_to'
    )
    
    search_fields = (
        'conditions',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'type',
                'value',
                'is_active'
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
        'valid_from',
        'valid_to'
    )
    
    search_fields = (
        'conditions',
        'description'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'type',
                'value',
                'is_active'
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

@admin.register(DiscountCoupon)
class DiscountCouponAdmin(admin.ModelAdmin):
    """Administración de cupones de descuento."""
    list_display = (
        'code', 'discount_percentage', 'user', 'is_used', 'created_at', 
        'expiration_date', 'days_remaining'
    )
    list_filter = ('is_used', 'created_at', 'expiration_date')
    search_fields = ('code', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'used_at', 'days_remaining_display')
    fieldsets = (
        ('Información Básica', {
            'fields': ('code', 'user', 'discount_percentage', 'description')
        }),
        ('Estado', {
            'fields': ('is_used', 'used_at', 'max_uses', 'use_count')
        }),
        ('Vigencia', {
            'fields': ('created_at', 'expiration_date', 'days_remaining_display')
        }),
    )
    
    def days_remaining_display(self, obj):
        """Muestra los días restantes para la expiración."""
        return obj.days_remaining()
    days_remaining_display.short_description = 'Días restantes'

@admin.register(TeamEvaluation)
class TeamEvaluationAdmin(admin.ModelAdmin):
    """Administración de evaluaciones de equipo."""
    list_display = (
        'id', 'user', 'team_size', 'status', 'discount_percentage', 
        'created_at', 'expires_at', 'is_expired'
    )
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = (
        'user__email', 'user__first_name', 'user__last_name', 
        'coupon__code'
    )
    readonly_fields = ('created_at', 'updated_at', 'is_expired_display')
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'team_size', 'status', 'notes')
        }),
        ('Cupón de Descuento', {
            'fields': ('coupon', 'discount_percentage')
        }),
        ('Fechas', {
            'fields': ('created_at', 'expires_at', 'is_expired_display')
        }),
    )
    
    def is_expired_display(self, obj):
        """Muestra si la evaluación ha expirado."""
        return obj.is_expired()
    is_expired_display.boolean = True
    is_expired_display.short_description = '¿Expirada?'

@admin.register(PromotionBanner)
class PromotionBannerAdmin(admin.ModelAdmin):
    """Administración de banners promocionales."""
    list_display = (
        'title', 'is_active', 'priority', 'start_date', 
        'end_date', 'days_remaining', 'is_currently_active_display'
    )
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('title', 'subtitle', 'content')
    readonly_fields = ('created_at', 'days_remaining_display', 'is_currently_active_display')
    fieldsets = (
        ('Contenido', {
            'fields': ('title', 'subtitle', 'content', 'image')
        }),
        ('Configuración', {
            'fields': ('is_active', 'priority', 'badge_text', 'badge_style')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date', 'days_remaining_display')
        }),
        ('Enlaces', {
            'fields': ('button_text', 'target_url')
        }),
        ('Estado', {
            'fields': ('is_currently_active_display',)
        }),
    )
    
    def days_remaining_display(self, obj):
        """Muestra los días restantes para que finalice la promoción."""
        return f"{obj.days_remaining()} días"
    days_remaining_display.short_description = 'Días restantes'
    
    def is_currently_active_display(self, obj):
        """Muestra si el banner está actualmente activo."""
        return obj.is_currently_active()
    is_currently_active_display.boolean = True
    is_currently_active_display.short_description = '¿Activo ahora?'
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo y limpia la caché de promociones."""
        from django.core.cache import cache
        cache.delete('active_promotions')
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Elimina el modelo y limpia la caché de promociones."""
        from django.core.cache import cache
        cache.delete('active_promotions')
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Elimina múltiples modelos y limpia la caché de promociones."""
        from django.core.cache import cache
        cache.delete('active_promotions')
        super().delete_queryset(request, queryset)

@admin.register(PremiumAddon)
class PremiumAddonAdmin(admin.ModelAdmin):
    """Administración de Addons Premium"""
    
    list_display = (
        'name',
        'type',
        'price',
        'is_active',
        'active_subscriptions',
        'revenue',
        'created_at'
    )
    
    list_filter = (
        'type',
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
                'type',
                'description',
                'price',
                'is_active'
            )
        }),
        ('Configuración', {
            'fields': (
                'features',
                'benefits',
                'requirements'
            )
        }),
        ('Métricas', {
            'fields': (
                'success_metrics',
                'activation_criteria'
            )
        })
    )
    
    def active_subscriptions(self, obj):
        """Muestra suscripciones activas"""
        count = BusinessUnitAddon.objects.filter(
            addon=obj,
            is_active=True
        ).count()
        return format_html(
            '<a href="{}?addon__id__exact={}">{}</a>',
            reverse('admin:pricing_businessunitaddon_changelist'),
            obj.id,
            count
        )
    
    def revenue(self, obj):
        """Calcula ingresos totales"""
        total = BusinessUnitAddon.objects.filter(
            addon=obj,
            is_active=True
        ).aggregate(
            total=Sum('addon__price')
        )['total'] or 0
        return f"${total:,.2f}"

@admin.register(BusinessUnitAddon)
class BusinessUnitAddonAdmin(admin.ModelAdmin):
    """Administración de Addons por Unidad de Negocio"""
    
    list_display = (
        'business_unit',
        'addon',
        'start_date',
        'end_date',
        'is_active',
        'price',
        'discounts_applied',
        'referral_fees'
    )
    
    list_filter = (
        'is_active',
        'start_date',
        'end_date',
        'addon__type'
    )
    
    search_fields = (
        'business_unit__name',
        'addon__name'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'business_unit',
                'addon',
                'start_date',
                'end_date',
                'is_active'
            )
        }),
        ('Precios y Descuentos', {
            'fields': (
                'price',
                'discounts',
                'referral_fees'
            )
        }),
        ('Métricas', {
            'fields': (
                'usage_metrics',
                'satisfaction_metrics'
            )
        })
    )
    
    def discounts_applied(self, obj):
        """Muestra descuentos aplicados"""
        discounts = DiscountRule.objects.filter(
            business_unit_addon=obj,
            is_active=True
        )
        return format_html(
            '<a href="{}?business_unit_addon__id__exact={}">{}</a>',
            reverse('admin:pricing_discountrule_changelist'),
            obj.id,
            len(discounts)
        )
    
    def referral_fees(self, obj):
        """Muestra fees de referidos"""
        fees = ReferralFee.objects.filter(
            business_unit_addon=obj,
            is_active=True
        )
        return format_html(
            '<a href="{}?business_unit_addon__id__exact={}">{}</a>',
            reverse('admin:pricing_referralfee_changelist'),
            obj.id,
            len(fees)
        ) 