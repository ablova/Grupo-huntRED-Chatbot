# /home/pablo/app/admin/business_unit.py
from django.contrib import admin
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from app.models import (
    BusinessUnit, 
    ConfiguracionBU, 
    WhatsAppAPIInline, 
    MessengerAPIInline, 
    TelegramAPIInline, 
    InstagramAPIInline, 
    DominioScrapingInline, 
    ConfiguracionBUInline
)
from .mixins import AdminMixin, AuditMixin, ValidationMixin

class BusinessUnitAdmin(AdminMixin, AuditMixin, ValidationMixin, admin.ModelAdmin):
    """Administración de Business Units con funcionalidades extendidas"""
    
    list_display = (
        'name',
        'description',
        'admin_phone',
        'has_wordpress_config',
        'active_channels',
        'status'
    )
    
    search_fields = (
        'name',
        'description',
        'admin_phone'
    )
    
    list_filter = (
        'whatsapp_enabled',
        'telegram_enabled',
        'messenger_enabled',
        'instagram_enabled',
        'scrapping_enabled',
        'status'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'description',
                'status'
            )
        }),
        ('Canales Habilitados', {
            'fields': (
                'whatsapp_enabled',
                'telegram_enabled',
                'messenger_enabled',
                'instagram_enabled'
            ),
            'classes': ('collapse',)
        }),
        ('Configuración de Scraping', {
            'fields': (
                'scrapping_enabled',
                'scraping_domains'
            ),
            'classes': ('collapse',)
        }),
        ('Información de Contacto', {
            'fields': ('admin_phone',)
        }),
        ('Auditoría', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by',
                'updated_by'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [
        ConfiguracionBUInline,
        WhatsAppAPIInline,
        MessengerAPIInline,
        TelegramAPIInline,
        InstagramAPIInline,
        DominioScrapingInline
    ]
    
    def has_wordpress_config(self, obj):
        """Indica si la Business Unit tiene configuración de WordPress"""
        try:
            config = obj.configuracionbu
            return bool(config.dominio_bu and config.jwt_token)
        except ConfiguracionBU.DoesNotExist:
            return False
    has_wordpress_config.boolean = True
    has_wordpress_config.short_description = 'WP Config'
    
    def active_channels(self, obj):
        """Muestra los canales activos de la Business Unit"""
        channels = []
        if obj.whatsapp_enabled:
            channels.append('WhatsApp')
        if obj.telegram_enabled:
            channels.append('Telegram')
        if obj.messenger_enabled:
            channels.append('Messenger')
        if obj.instagram_enabled:
            channels.append('Instagram')
        return ', '.join(channels) if channels else '-'
    active_channels.short_description = 'Canales Activos'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Vista personalizada de detalle con funcionalidades adicionales"""
        extra_context = extra_context or {}
        business_unit = self.get_object(request, object_id)
        
        # Añadir botón de sincronización
        try:
            config = business_unit.configuracionbu
            extra_context['config'] = config
            extra_context['sync_button'] = render_to_string(
                'admin/sync_button.html',
                {
                    'business_unit': business_unit,
                    'config': config,
                    'csrf_token': request.COOKIES.get('csrftoken')
                }
            )
        except ConfiguracionBU.DoesNotExist:
            extra_context['sync_button'] = ''
        
        # Añadir métricas y estadísticas
        extra_context['metrics'] = self.get_business_unit_metrics(business_unit)
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def get_business_unit_metrics(self, business_unit):
        """Obtiene métricas y estadísticas de la Business Unit"""
        return {
            'total_candidates': business_unit.candidate_set.count(),
            'active_jobs': business_unit.job_set.filter(status='active').count(),
            'total_interviews': business_unit.interview_set.count(),
            'channel_stats': self.get_channel_statistics(business_unit)
        }
    
    def get_channel_statistics(self, business_unit):
        """Obtiene estadísticas de los canales de la Business Unit"""
        return {
            'whatsapp': {
                'enabled': business_unit.whatsapp_enabled,
                'messages': business_unit.whatsappmessage_set.count() if business_unit.whatsapp_enabled else 0
            },
            'telegram': {
                'enabled': business_unit.telegram_enabled,
                'messages': business_unit.telegrammessage_set.count() if business_unit.telegram_enabled else 0
            },
            'messenger': {
                'enabled': business_unit.messenger_enabled,
                'messages': business_unit.messengermessage_set.count() if business_unit.messenger_enabled else 0
            },
            'instagram': {
                'enabled': business_unit.instagram_enabled,
                'messages': business_unit.instagrammessage_set.count() if business_unit.instagram_enabled else 0
            }
        }
    
    def get_queryset(self, request):
        """Filtra el queryset según los permisos del usuario"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(users=request.user)
    
    def save_model(self, request, obj, form, change):
        """Guarda el modelo con información de auditoría"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
        # Notificar cambios
        self.notify_business_unit_changes(obj, change)
    
    def notify_business_unit_changes(self, business_unit, is_change):
        """Notifica cambios en la Business Unit"""
        action = 'actualizada' if is_change else 'creada'
        messages.success(
            request,
            f'Business Unit {business_unit.name} {action} exitosamente.'
        )

# Registrar el administrador
admin.site.register(BusinessUnit, BusinessUnitAdmin)
