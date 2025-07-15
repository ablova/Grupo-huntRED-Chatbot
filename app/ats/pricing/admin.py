"""
Admin para el módulo de pricing unificado.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    # Modelos de pricing
    PricingStrategy, PricePoint, DiscountRule, ReferralFee,
    
    # Modelos de gateways y pagos
    PaymentGateway, BankAccount, PaymentTransaction, PACConfiguration,
    
    # Modelos migrados
    Empleador, Empleado, Oportunidad, PagoRecurrente,
    SincronizacionLog, SincronizacionError,
    
    # Modelos de CFDI en exhibiciones
    CFDIExhibition, PartialPayment,
    
    # Modelos de pagos programados
    ScheduledPayment, ScheduledPaymentExecution,
)

# Importar Person desde app.models.py
from app.models import Person, Company


# ============================================================================
# ADMIN DE PRICING
# ============================================================================

# Desregistrar si ya está registrado para evitar conflictos
try:
    admin.site.unregister(PricingStrategy)
except admin.sites.NotRegistered:
    pass

@admin.register(PricingStrategy)
class PricingStrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'status', 'base_price', 'currency', 'success_rate', 'created_at']
    list_filter = ['type', 'status', 'currency', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'last_updated']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'type', 'status', 'description')
        }),
        ('Precios', {
            'fields': ('base_price', 'currency', 'pricing_model')
        }),
        ('Reglas y Comisiones', {
            'fields': ('discount_rules', 'referral_fees', 'conditions')
        }),
        ('Métricas', {
            'fields': ('success_rate', 'conversion_rate', 'revenue_impact')
        }),
        ('Fechas', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


# Desregistrar si ya está registrado para evitar conflictos
try:
    admin.site.unregister(PricePoint)
except admin.sites.NotRegistered:
    pass

@admin.register(PricePoint)
class PricePointAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'amount', 'currency', 'valid_from', 'valid_to']
    list_filter = ['currency', 'valid_from', 'valid_to']
    search_fields = ['strategy__name']
    date_hierarchy = 'valid_from'


# Desregistrar si ya está registrado para evitar conflictos
try:
    admin.site.unregister(DiscountRule)
except admin.sites.NotRegistered:
    pass

@admin.register(DiscountRule)
class DiscountRuleAdmin(admin.ModelAdmin):
    list_display = ['type', 'value', 'is_active', 'valid_from', 'valid_to']
    list_filter = ['type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['type']


# Desregistrar si ya está registrado para evitar conflictos
try:
    admin.site.unregister(ReferralFee)
except admin.sites.NotRegistered:
    pass

@admin.register(ReferralFee)
class ReferralFeeAdmin(admin.ModelAdmin):
    list_display = ['type', 'value', 'is_active', 'valid_from', 'valid_to']
    list_filter = ['type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['type']


# ============================================================================
# ADMIN DE GATEWAYS Y PAGOS
# ============================================================================

@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'gateway_type', 'status', 'business_unit', 'processing_fee_percentage', 'created_at']
    list_filter = ['gateway_type', 'status', 'business_unit', 'pac_integration', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'gateway_type', 'status', 'business_unit')
        }),
        ('Configuración API', {
            'fields': ('api_key', 'api_secret', 'webhook_url', 'webhook_secret')
        }),
        ('Configuración de Pagos', {
            'fields': ('supported_currencies', 'supported_payment_methods', 'processing_fee_percentage', 'processing_fee_fixed')
        }),
        ('Facturación Electrónica', {
            'fields': ('pac_integration', 'pac_config')
        }),
        ('Configuración Específica', {
            'fields': ('config',)
        }),
        ('Metadatos', {
            'fields': ('description', 'notes')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['account_name', 'bank', 'account_type', 'is_active', 'is_primary', 'business_unit']
    list_filter = ['bank', 'account_type', 'is_active', 'is_primary', 'business_unit']
    search_fields = ['account_name', 'account_number', 'clabe']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'transaction_type', 'status', 'amount', 'currency', 'payment_method', 'created_at']
    list_filter = ['transaction_type', 'status', 'payment_method', 'currency', 'created_at']
    search_fields = ['transaction_id', 'external_id', 'description']
    readonly_fields = ['transaction_id', 'created_at', 'processed_at', 'completed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('transaction_id', 'external_id', 'transaction_type', 'status')
        }),
        ('Relaciones', {
            'fields': ('invoice', 'gateway', 'bank_account')
        }),
        ('Montos', {
            'fields': ('amount', 'processing_fee', 'net_amount', 'currency')
        }),
        ('Método de Pago', {
            'fields': ('payment_method', 'payment_details')
        }),
        ('Fechas', {
            'fields': ('created_at', 'processed_at', 'completed_at')
        }),
        ('Respuesta del Gateway', {
            'fields': ('gateway_response', 'error_message')
        }),
        ('Metadatos', {
            'fields': ('description', 'notes')
        }),
    )


@admin.register(PACConfiguration)
class PACConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'pac_type', 'status', 'business_unit', 'created_at']
    list_filter = ['pac_type', 'status', 'business_unit', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# ADMIN DE MODELOS MIGRADOS
# ============================================================================

@admin.register(Empleador)
class EmpleadorAdmin(admin.ModelAdmin):
    list_display = ['razon_social', 'rfc', 'banco', 'estado', 'fecha_registro']
    list_filter = ['estado', 'banco', 'fecha_registro']
    search_fields = ['razon_social', 'rfc', 'persona__nombre', 'persona__apellido_paterno']
    readonly_fields = ['fecha_registro', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('persona', 'whatsapp')
        }),
        ('Información Fiscal', {
            'fields': ('razon_social', 'rfc', 'direccion_fiscal')
        }),
        ('Información Bancaria', {
            'fields': ('clabe', 'banco')
        }),
        ('Información de Contacto', {
            'fields': ('img_company', 'sitio_web', 'telefono_oficina', 'address')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Documentos', {
            'fields': ('documento_identidad', 'comprobante_domicilio')
        }),
        ('Campos Adicionales', {
            'fields': ('job_id', 'url_name', 'salary', 'job_type', 'longitude', 'latitude', 'required_skills', 'experience_required', 'job_description', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['persona', 'nss', 'ocupacion', 'banco', 'estado', 'fecha_registro']
    list_filter = ['estado', 'banco', 'fecha_registro']
    search_fields = ['persona__nombre', 'persona__apellido_paterno', 'nss', 'ocupacion']
    readonly_fields = ['fecha_registro', 'fecha_actualizacion']


@admin.register(Oportunidad)
class OportunidadAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'empleador', 'tipo_contrato', 'salario_minimo', 'salario_maximo', 'modalidad', 'estado', 'fecha_creacion']
    list_filter = ['tipo_contrato', 'modalidad', 'estado', 'pais', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion', 'empleador__razon_social']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


@admin.register(PagoRecurrente)
class PagoRecurrenteAdmin(admin.ModelAdmin):
    list_display = ['pago_base', 'frecuencia', 'fecha_proximo_pago', 'activo']
    list_filter = ['frecuencia', 'activo', 'fecha_proximo_pago']
    search_fields = ['pago_base__description']


@admin.register(SincronizacionLog)
class SincronizacionLogAdmin(admin.ModelAdmin):
    list_display = ['oportunidad', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['oportunidad__titulo']


@admin.register(SincronizacionError)
class SincronizacionErrorAdmin(admin.ModelAdmin):
    list_display = ['oportunidad', 'mensaje', 'intento', 'resuelto', 'fecha_creacion']
    list_filter = ['resuelto', 'intento', 'fecha_creacion']
    search_fields = ['oportunidad__titulo', 'mensaje']


# ============================================================================
# ADMIN DE CFDI EN EXHIBICIONES
# ============================================================================

@admin.register(CFDIExhibition)
class CFDIExhibitionAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'exhibition_type', 'payment_status', 'total_amount', 'paid_amount', 'remaining_amount', 'due_date']
    list_filter = ['exhibition_type', 'payment_status', 'due_date', 'created_at']
    search_fields = ['invoice__invoice_number']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('invoice', 'exhibition_type', 'payment_status')
        }),
        ('Montos', {
            'fields': ('total_amount', 'paid_amount', 'remaining_amount')
        }),
        ('Fechas', {
            'fields': ('created_at', 'due_date', 'completed_at')
        }),
        ('Pagos Parciales', {
            'fields': ('partial_payments', 'payment_schedule')
        }),
        ('Notas', {
            'fields': ('notes',)
        }),
    )


@admin.register(PartialPayment)
class PartialPaymentAdmin(admin.ModelAdmin):
    list_display = ['cfdi_exhibition', 'amount', 'payment_method', 'payment_date', 'is_verified']
    list_filter = ['payment_method', 'is_verified', 'payment_date']
    search_fields = ['reference_number', 'notes']
    readonly_fields = ['created_at', 'updated_at']


# ============================================================================
# ADMIN DE PAGOS PROGRAMADOS
# ============================================================================

@admin.register(ScheduledPayment)
class ScheduledPaymentAdmin(admin.ModelAdmin):
    list_display = ['name', 'payment_type', 'amount', 'currency', 'frequency', 'status', 'next_payment_date', 'business_unit']
    list_filter = ['payment_type', 'frequency', 'status', 'currency', 'business_unit']
    search_fields = ['name', 'beneficiary_name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'payment_type', 'business_unit', 'status', 'is_active')
        }),
        ('Configuración de Pago', {
            'fields': ('amount', 'currency', 'frequency', 'custom_frequency_days')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date', 'next_payment_date')
        }),
        ('Beneficiario', {
            'fields': ('beneficiary_name', 'beneficiary_account', 'beneficiary_bank', 'beneficiary_clabe')
        }),
        ('Cuenta de Origen', {
            'fields': ('source_account',)
        }),
        ('Metadatos', {
            'fields': ('description', 'reference')
        }),
        ('Control', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('business_unit', 'source_account', 'created_by')


@admin.register(ScheduledPaymentExecution)
class ScheduledPaymentExecutionAdmin(admin.ModelAdmin):
    list_display = ['scheduled_payment', 'scheduled_date', 'executed_date', 'amount', 'status', 'success']
    list_filter = ['status', 'success', 'scheduled_date', 'executed_date']
    search_fields = ['scheduled_payment__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('scheduled_payment', 'transaction', 'status', 'success')
        }),
        ('Fechas', {
            'fields': ('scheduled_date', 'executed_date')
        }),
        ('Monto', {
            'fields': ('amount',)
        }),
        ('Resultado', {
            'fields': ('error_message', 'execution_log')
        }),
        ('Control', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# DASHBOARD PERSONALIZADO
# ============================================================================

class PricingDashboardAdmin(admin.ModelAdmin):
    """Dashboard personalizado para el módulo de pricing."""
    
    def changelist_view(self, request, extra_context=None):
        # Estadísticas de pricing
        total_strategies = PricingStrategy.objects.count()
        active_strategies = PricingStrategy.objects.filter(status='active').count()
        
        # Estadísticas de pagos
        total_transactions = PaymentTransaction.objects.count()
        completed_transactions = PaymentTransaction.objects.filter(status='completed').count()
        total_amount = PaymentTransaction.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
        
        # Estadísticas de gateways
        active_gateways = PaymentGateway.objects.filter(status='active').count()
        
        # Estadísticas de pagos programados
        active_scheduled_payments = ScheduledPayment.objects.filter(status='active').count()
        pending_executions = ScheduledPaymentExecution.objects.filter(status='pending').count()
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_strategies': total_strategies,
            'active_strategies': active_strategies,
            'total_transactions': total_transactions,
            'completed_transactions': completed_transactions,
            'total_amount': total_amount,
            'active_gateways': active_gateways,
            'active_scheduled_payments': active_scheduled_payments,
            'pending_executions': pending_executions,
        })
        
        return super().changelist_view(request, extra_context)


# El modelo PricingStrategy ya está registrado con @admin.register


# ============================================================================
# ADMIN DE COMPANY
# ============================================================================

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'legal_name', 'industry', 'size', 'location', 'created_at')
    search_fields = ('name', 'legal_name', 'tax_id', 'industry')
    list_filter = ('industry', 'size', 'country', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'legal_name', 'tax_id', 'industry', 'size')
        }),
        ('Ubicación', {
            'fields': ('location', 'address', 'city', 'state', 'country')
        }),
        ('Contacto', {
            'fields': ('website', 'description')
        }),
        ('Roles de Contacto', {
            'fields': ('signer', 'payment_responsible', 'fiscal_responsible', 'process_responsible', 'report_invitees')
        }),
        ('Notificaciones', {
            'fields': ('notification_preferences',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# ADMIN DE PERSON
# ============================================================================

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'signer', 'payment_responsible', 'fiscal_responsible', 'process_responsible')
    search_fields = ('name', 'signer__nombre', 'payment_responsible__nombre', 'fiscal_responsible__nombre', 'process_responsible__nombre')
    filter_horizontal = ('report_invitees',)
    fieldsets = (
        (None, {
            'fields': ('name', 'legal_name', 'tax_id', 'industry', 'size', 'website', 'address', 'city', 'state', 'country')
        }),
        ('Contactos y notificaciones', {
            'fields': ('signer', 'payment_responsible', 'fiscal_responsible', 'process_responsible', 'report_invitees', 'notification_preferences')
        }),
    ) 