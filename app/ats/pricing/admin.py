# /home/pablo/app/pricing/admin.py
"""
Configuración del panel de administración para el módulo de precios.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from app.ats.pricing.models import DiscountCoupon, TeamEvaluation, PromotionBanner


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
