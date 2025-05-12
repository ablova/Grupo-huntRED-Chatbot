# Ubicación del archivo: /home/pablo/app/config/admin_pricing.py
"""
Clases de administración para el módulo de Pricing.

Este módulo implementa las clases de administración para el módulo de Pricing
descrito en las reglas globales de Grupo huntRED®, con soporte para PricingBaseline,
Addons, Coupons y PaymentMilestones.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.admin import SimpleListFilter
from django.db.models import Sum, Count, Q
import json

from .admin_base import BaseModelAdmin, OptimizedQuerysetMixin
from .admin_cache import CachedAdminMixin

# Importaciones de modelos (asumiendo que ya existen según la estructura de memoria)
from app.models import (
    PricingBaseline, Addons, Coupons, PaymentMilestones, 
    BusinessUnit, Vacante, Opportunity
)

class BusinessUnitFilter(SimpleListFilter):
    """Filtro por Business Unit para modelos de pricing."""
    title = _('Business Unit')
    parameter_name = 'bu'
    
    def lookups(self, request, model_admin):
        """Generando opciones del filtro con todas las BUs activas."""
        return BusinessUnit.objects.filter(active=True).values_list('id', 'name')
    
    def queryset(self, request, queryset):
        """Aplicando filtro al queryset."""
        if self.value():
            return queryset.filter(bu_id=self.value())
        return queryset

class PricingBaselineAdmin(BaseModelAdmin, OptimizedQuerysetMixin):
    """Admin para configuración de precios base por BU y modelo."""
    list_display = (
        'bu', 'model', 'base_price', 'percentage', 'last_updated'
    )
    list_filter = (
        BusinessUnitFilter, 'model', 'last_updated'
    )
    search_fields = ('bu__name', 'model')
    readonly_fields = ('created_at', 'last_updated')
    
    # Campos para optimización de consultas
    optimized_select_related = ['bu']
    
    fieldsets = (
        (None, {
            'fields': ('bu', 'model')
        }),
        (_('Configuración de Precios'), {
            'fields': ('base_price', 'percentage')
        }),
        (_('Metadatos'), {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personalizando campos de selección en formularios."""
        if db_field.name == "bu":
            kwargs["queryset"] = BusinessUnit.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class AddonsAdmin(BaseModelAdmin):
    """Admin para gestión de complementos (addons) de precios."""
    list_display = (
        'name', 'price', 'max_per_vacancy', 'active', 'for_ai_model',
        'last_updated'
    )
    list_filter = ('active', 'for_ai_model', 'last_updated')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'last_updated')
    list_editable = ('active', 'price')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'active')
        }),
        (_('Configuración de Precios'), {
            'fields': ('price', 'max_per_vacancy', 'for_ai_model')
        }),
        (_('Metadatos'), {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Personalizando formulario con validaciones adicionales."""
        form = super().get_form(request, obj, **kwargs)
        
        # Validación para price
        form.base_fields['price'].validators = [
            self.validate_positive_price
        ]
        
        # Validación para max_per_vacancy
        form.base_fields['max_per_vacancy'].validators = [
            self.validate_non_negative_max
        ]
        
        return form
    
    def validate_positive_price(self, value):
        """Validando que el precio sea positivo."""
        if value <= 0:
            raise forms.ValidationError(_("El precio debe ser mayor que cero."))
        return value
    
    def validate_non_negative_max(self, value):
        """Validando que el máximo por vacante no sea negativo."""
        if value < 0:
            raise forms.ValidationError(_("El máximo por vacante no puede ser negativo."))
        return value

class CouponTypeFilter(SimpleListFilter):
    """Filtro por tipo de cupón."""
    title = _('Tipo de Cupón')
    parameter_name = 'coupon_type'
    
    def lookups(self, request, model_admin):
        """Definiendo opciones del filtro."""
        return (
            ('fixed', _('Monto Fijo')),
            ('percentage', _('Porcentaje')),
        )
    
    def queryset(self, request, queryset):
        """Aplicando filtro al queryset."""
        if self.value():
            return queryset.filter(type=self.value())
        return queryset

class CouponsAdmin(BaseModelAdmin):
    """Admin para gestión de cupones de descuento."""
    list_display = (
        'code', 'type', 'get_value_display', 'valid_until', 
        'max_uses', 'current_uses', 'is_valid', 'last_updated'
    )
    list_filter = (
        CouponTypeFilter, 'valid_until', 'is_active'
    )
    search_fields = ('code', 'description')
    readonly_fields = ('created_at', 'last_updated', 'current_uses')
    
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'is_active')
        }),
        (_('Configuración de Descuento'), {
            'fields': ('type', 'value', 'valid_until', 'max_uses')
        }),
        (_('Uso'), {
            'fields': ('current_uses',)
        }),
        (_('Metadatos'), {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_value_display(self, obj):
        """Formateando valor del cupón según su tipo."""
        if obj.type == 'fixed':
            return f"${obj.value:,.2f}"
        else:  # percentage
            return f"{obj.value}%"
    get_value_display.short_description = _('Valor')
    
    def is_valid(self, obj):
        """Verificando si el cupón es válido (activo, no expirado, usos disponibles)."""
        if not obj.is_active:
            return False
            
        from django.utils import timezone
        
        if obj.valid_until and obj.valid_until < timezone.now():
            return False
            
        if obj.max_uses > 0 and obj.current_uses >= obj.max_uses:
            return False
            
        return True
    is_valid.boolean = True
    is_valid.short_description = _('Válido')
    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        """Personalizando campos de selección."""
        if db_field.name == "type":
            kwargs['choices'] = (
                ('fixed', _('Monto Fijo ($)')),
                ('percentage', _('Porcentaje (%)')),
            )
        return super().formfield_for_choice_field(db_field, request, **kwargs)

class PaymentMilestonesAdmin(BaseModelAdmin, OptimizedQuerysetMixin):
    """Admin para gestión de hitos de pago por BU."""
    list_display = (
        'bu', 'milestone_name', 'percentage', 'trigger_event',
        'due_date_offset', 'last_updated'
    )
    list_filter = (
        BusinessUnitFilter, 'trigger_event', 'last_updated'
    )
    search_fields = ('milestone_name', 'bu__name')
    readonly_fields = ('created_at', 'last_updated')
    
    # Campos para optimización de consultas
    optimized_select_related = ['bu']
    
    fieldsets = (
        (None, {
            'fields': ('bu', 'milestone_name', 'description')
        }),
        (_('Configuración de Pago'), {
            'fields': ('percentage', 'trigger_event', 'due_date_offset')
        }),
        (_('Metadatos'), {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        })
    )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personalizando campos de selección en formularios."""
        if db_field.name == "bu":
            kwargs["queryset"] = BusinessUnit.objects.filter(active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_form(self, request, obj=None, **kwargs):
        """Personalizando formulario con validaciones adicionales."""
        form = super().get_form(request, obj, **kwargs)
        
        # Validación para percentage
        form.base_fields['percentage'].validators = [
            self.validate_percentage
        ]
        
        return form
    
    def validate_percentage(self, value):
        """Validando que el porcentaje esté entre 0 y 100."""
        if value < 0 or value > 100:
            raise forms.ValidationError(_("El porcentaje debe estar entre 0 y 100."))
        return value

class PricingSimulatorForm(forms.Form):
    """Formulario para simulador de precios en panel admin."""
    business_unit = forms.ModelChoiceField(
        queryset=BusinessUnit.objects.filter(active=True),
        label=_("Unidad de Negocio")
    )
    model = forms.ChoiceField(
        choices=[
            ('fixed', _('Precio Fijo')),
            ('percentage', _('Porcentaje')),
            ('ai', _('Modelo AI'))
        ],
        label=_("Modelo de Pricing")
    )
    num_vacancies = forms.IntegerField(
        min_value=1, max_value=100, initial=1,
        label=_("Número de Vacantes")
    )
    salary_range = forms.ChoiceField(
        choices=[
            ('15000-25000', _('$15,000 - $25,000')),
            ('25000-35000', _('$25,000 - $35,000')),
            ('35000-50000', _('$35,000 - $50,000')),
            ('50000-80000', _('$50,000 - $80,000')),
            ('80000+', _('$80,000+')),
        ],
        label=_("Rango Salarial")
    )
    addons = forms.ModelMultipleChoiceField(
        queryset=Addons.objects.filter(active=True),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple(
            verbose_name=_("Complementos"),
            is_stacked=False
        ),
        label=_("Complementos (Addons)")
    )
    coupon_code = forms.CharField(
        max_length=50, required=False,
        label=_("Código de Cupón")
    )

class PricingSimulatorAdmin(admin.ModelAdmin):
    """Admin para simulador de precios."""
    # Esta clase no tiene modelo asociado, es solo para UI
    
    # Creando pseudo-model
    class Meta:
        model = type('PricingSimulator', (object,), {})
        
    change_list_template = "admin/pricing_simulator.html"
    
    def get_urls(self):
        from django.urls import path
        
        urls = super().get_urls()
        custom_urls = [
            path('simulator/', 
                 self.admin_site.admin_view(self.simulator_view),
                 name='pricing_simulator'),
        ]
        return custom_urls + urls
    
    def simulator_view(self, request):
        """Vista para simulador de precios."""
        from django.template.response import TemplateResponse
        
        # Procesando formulario
        if request.method == 'POST':
            form = PricingSimulatorForm(request.POST)
            if form.is_valid():
                result = self.calculate_pricing(form.cleaned_data)
            else:
                result = None
        else:
            form = PricingSimulatorForm()
            result = None
        
        # Contexto para la plantilla
        context = {
            'title': _("Simulador de Precios"),
            'form': form,
            'result': result,
            **self.admin_site.each_context(request),
        }
        
        return TemplateResponse(request, "admin/pricing_simulator.html", context)
    
    def calculate_pricing(self, data):
        """Calcula el precio según los datos del formulario."""
        # Este método simularía el cálculo real de precios
        # En una implementación real, usaría el modelo de pricing
        
        business_unit = data['business_unit']
        model = data['model']
        num_vacancies = data['num_vacancies']
        
        # Calculando precio base
        try:
            pricing_baseline = PricingBaseline.objects.get(
                bu=business_unit,
                model=model
            )
            
            if model == 'fixed':
                base_price = pricing_baseline.base_price * num_vacancies
            elif model == 'percentage':
                # Simulando cálculo de porcentaje del salario
                salary_range = data['salary_range']
                salary_mid = self._get_salary_midpoint(salary_range)
                base_price = salary_mid * pricing_baseline.percentage / 100 * num_vacancies
            else:  # ai
                base_price = pricing_baseline.base_price * num_vacancies * 1.5  # Premium para AI
                
        except PricingBaseline.DoesNotExist:
            # Valores por defecto si no hay configuración
            if model == 'fixed':
                base_price = 10000 * num_vacancies
            elif model == 'percentage':
                salary_range = data['salary_range']
                salary_mid = self._get_salary_midpoint(salary_range)
                base_price = salary_mid * 0.15 * num_vacancies  # 15% por defecto
            else:  # ai
                base_price = 15000 * num_vacancies
        
        # Calculando precio de addons
        addons_price = 0
        addons_detail = []
        
        if data['addons']:
            for addon in data['addons']:
                if model == 'ai' and not addon.for_ai_model:
                    continue  # Ignorando addons no compatibles con AI
                    
                addon_total = addon.price * num_vacancies
                addons_price += addon_total
                
                addons_detail.append({
                    'name': addon.name,
                    'price': addon.price,
                    'total': addon_total
                })
        
        # Calculando descuento del cupón
        discount = 0
        coupon = None
        
        if data['coupon_code']:
            try:
                from django.utils import timezone
                
                coupon = Coupons.objects.get(
                    code=data['coupon_code'],
                    is_active=True,
                    valid_until__gt=timezone.now()
                )
                
                if coupon.max_uses == 0 or coupon.current_uses < coupon.max_uses:
                    if coupon.type == 'fixed':
                        discount = coupon.value
                    else:  # percentage
                        discount = (base_price + addons_price) * coupon.value / 100
            except Coupons.DoesNotExist:
                pass
        
        # Calculando total
        subtotal = base_price + addons_price
        total = subtotal - discount
        
        # Hitos de pago
        payment_milestones = []
        
        try:
            milestones = PaymentMilestones.objects.filter(bu=business_unit)
            
            for milestone in milestones:
                milestone_amount = total * milestone.percentage / 100
                payment_milestones.append({
                    'name': milestone.milestone_name,
                    'percentage': milestone.percentage,
                    'amount': milestone_amount,
                    'trigger': milestone.trigger_event,
                    'due_days': milestone.due_date_offset
                })
        except:
            # Hitos por defecto
            payment_milestones = [
                {
                    'name': _('Firma de Contrato'),
                    'percentage': 50,
                    'amount': total * 0.5,
                    'trigger': 'contract_signed',
                    'due_days': 15
                },
                {
                    'name': _('Contratación'),
                    'percentage': 50,
                    'amount': total * 0.5,
                    'trigger': 'hiring',
                    'due_days': 30
                }
            ]
        
        # Resultado final
        return {
            'business_unit': business_unit.name,
            'model': self._get_model_display(model),
            'num_vacancies': num_vacancies,
            'base_price': base_price,
            'addons_price': addons_price,
            'addons_detail': addons_detail,
            'subtotal': subtotal,
            'coupon': coupon.code if coupon else None,
            'discount': discount,
            'total': total,
            'payment_milestones': payment_milestones
        }
    
    def _get_salary_midpoint(self, salary_range):
        """Obtiene el punto medio del rango salarial."""
        if salary_range == '15000-25000':
            return 20000
        elif salary_range == '25000-35000':
            return 30000
        elif salary_range == '35000-50000':
            return 42500
        elif salary_range == '50000-80000':
            return 65000
        else:  # 80000+
            return 100000
    
    def _get_model_display(self, model):
        """Obtiene el nombre de display para el modelo."""
        model_names = {
            'fixed': _('Precio Fijo'),
            'percentage': _('Porcentaje'),
            'ai': _('Modelo AI')
        }
        return model_names.get(model, model)
