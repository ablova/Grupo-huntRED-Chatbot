# /home/pablo/app/ats/admin/pricing/unified_admin.py
"""
Admin unificado para Pricing & Pagos de Grupo huntRED®.

Este módulo proporciona interfaces administrativas unificadas para gestionar
todos los aspectos del sistema de precios y pagos.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum, Count, Q
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.safestring import mark_safe

from app.models import (
    Service, PaymentSchedule, Payment, PaymentTransaction,
    PaymentNotification, BusinessUnit, Person
)
from app.ats.pricing.models import (
    PricingCalculation, PricingPayment,
    PricingStrategy, PricePoint, DiscountRule
)
from app.ats.pricing.services import UnifiedPricingService

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Administración de Servicios"""
    
    list_display = (
        'name',
        'service_type',
        'billing_type',
        'business_unit',
        'base_price',
        'currency',
        'status',
        'created_at'
    )
    
    list_filter = (
        'service_type',
        'billing_type',
        'status',
        'business_unit',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description',
        'business_unit__name'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'service_type',
                'billing_type',
                'status'
            )
        }),
        ('Pricing', {
            'fields': (
                'base_price',
                'currency',
                'pricing_config'
            )
        }),
        ('Unidad de Negocio', {
            'fields': (
                'business_unit',
                'created_by'
            )
        }),
        ('Características', {
            'fields': (
                'features',
                'requirements',
                'deliverables'
            ),
            'classes': ('collapse',)
        }),
        ('Configuración de Pagos', {
            'fields': (
                'payment_terms',
                'payment_methods',
                'default_milestones'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('business_unit', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    """Administración de Programaciones de Pago"""
    
    list_display = (
        'service',
        'client',
        'total_amount',
        'schedule_type',
        'status',
        'start_date',
        'payment_count',
        'paid_amount'
    )
    
    list_filter = (
        'schedule_type',
        'status',
        'frequency',
        'service__business_unit',
        'start_date'
    )
    
    search_fields = (
        'service__name',
        'client__nombre',
        'client__email'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'payment_count',
        'paid_amount',
        'pending_amount'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'service',
                'client',
                'total_amount'
            )
        }),
        ('Configuración', {
            'fields': (
                'schedule_type',
                'start_date',
                'end_date',
                'frequency'
            )
        }),
        ('Estado', {
            'fields': (
                'status',
                'payment_count',
                'paid_amount',
                'pending_amount'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def payment_count(self, obj):
        return obj.payments.count()
    payment_count.short_description = 'Pagos'
    
    def paid_amount(self, obj):
        paid = obj.payments.filter(status='PAID').aggregate(
            total=Sum('amount')
        )['total'] or 0
        return f"{paid} {obj.service.currency}"
    paid_amount.short_description = 'Pagado'
    
    def pending_amount(self, obj):
        pending = obj.payments.filter(status='PENDING').aggregate(
            total=Sum('amount')
        )['total'] or 0
        return f"{pending} {obj.service.currency}"
    pending_amount.short_description = 'Pendiente'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Administración de Pagos Individuales"""
    
    list_display = (
        'schedule',
        'amount',
        'due_date',
        'payment_method',
        'status',
        'payment_date',
        'days_overdue'
    )
    
    list_filter = (
        'status',
        'payment_method',
        'due_date',
        'schedule__service__business_unit'
    )
    
    search_fields = (
        'schedule__service__name',
        'schedule__client__nombre',
        'transaction_id'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'days_overdue'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'schedule',
                'amount',
                'due_date'
            )
        }),
        ('Pago', {
            'fields': (
                'payment_method',
                'status',
                'payment_date',
                'transaction_id'
            )
        }),
        ('Detalles', {
            'fields': (
                'notes',
                'days_overdue'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def days_overdue(self, obj):
        if obj.status == 'PENDING' and obj.due_date < timezone.now().date():
            return (timezone.now().date() - obj.due_date).days
        return 0
    days_overdue.short_description = 'Días Vencido'
    
    actions = ['mark_as_paid', 'send_reminder']
    
    def mark_as_paid(self, request, queryset):
        """Marca pagos como pagados"""
        updated = queryset.update(
            status='PAID',
            payment_date=timezone.now()
        )
        messages.success(request, f"{updated} pagos marcados como pagados.")
    mark_as_paid.short_description = "Marcar como pagados"
    
    def send_reminder(self, request, queryset):
        """Envía recordatorios de pago"""
        service = UnifiedPricingService()
        notifications = []
        
        for payment in queryset.filter(status='PENDING'):
            notification = service._send_payment_reminder(payment)
            if notification:
                notifications.append(notification)
        
        messages.success(request, f"Se enviaron {len(notifications)} recordatorios.")
    send_reminder.short_description = "Enviar recordatorios"

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    """Administración de Transacciones de Pago"""
    
    list_display = (
        'transaction_id',
        'user',
        'amount',
        'currency',
        'payment_method',
        'status',
        'created_at'
    )
    
    list_filter = (
        'status',
        'payment_method',
        'currency',
        'created_at'
    )
    
    search_fields = (
        'transaction_id',
        'user__username',
        'user__email'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Transacción', {
            'fields': (
                'transaction_id',
                'user',
                'amount',
                'currency'
            )
        }),
        ('Método de Pago', {
            'fields': (
                'payment_method',
                'status',
                'payment_details'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

@admin.register(PaymentNotification)
class PaymentNotificationAdmin(admin.ModelAdmin):
    """Administración de Notificaciones de Pago"""
    
    list_display = (
        'payment',
        'notification_type',
        'recipient',
        'status',
        'sent_at'
    )
    
    list_filter = (
        'notification_type',
        'status',
        'sent_at'
    )
    
    search_fields = (
        'payment__schedule__service__name',
        'recipient__nombre',
        'recipient__email'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Notificación', {
            'fields': (
                'payment',
                'notification_type',
                'recipient'
            )
        }),
        ('Contenido', {
            'fields': (
                'message',
                'status',
                'sent_at'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

# Dashboard personalizado para Pricing & Pagos
class PricingPaymentDashboard(admin.ModelAdmin):
    """Dashboard para Pricing & Pagos"""
    
    def changelist_view(self, request, extra_context=None):
        """Vista personalizada del dashboard"""
        # Obtener estadísticas
        service = UnifiedPricingService()
        
        # Estadísticas generales
        total_services = Service.objects.count()
        active_services = Service.objects.filter(status='active').count()
        
        # Estadísticas de pagos
        payment_stats = service.get_payment_dashboard_data()
        
        # Pagos próximos a vencer
        upcoming_payments = Payment.objects.filter(
            due_date__lte=timezone.now().date() + timezone.timedelta(days=7),
            status='PENDING'
        ).count()
        
        # Pagos vencidos
        overdue_payments = Payment.objects.filter(
            due_date__lt=timezone.now().date(),
            status='PENDING'
        ).count()
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_services': total_services,
            'active_services': active_services,
            'payment_stats': payment_stats,
            'upcoming_payments': upcoming_payments,
            'overdue_payments': overdue_payments,
            'title': 'Dashboard de Pricing & Pagos'
        })
        
        return super().changelist_view(request, extra_context)

# Registrar el dashboard
admin.site.register(Service, PricingPaymentDashboard) 