# /home/pablo/app/admin/business_unit.py
from django.contrib import admin
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from app.models import BusinessUnit, ConfiguracionBU, WhatsAppAPIInline, MessengerAPIInline, TelegramAPIInline, InstagramAPIInline, DominioScrapingInline, ConfiguracionBUInline

@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'admin_phone', 'has_wordpress_config')
    search_fields = ('name', 'description')
    list_filter = ('whatsapp_enabled', 'telegram_enabled', 'messenger_enabled', 'instagram_enabled', 'scrapping_enabled')
    
    def has_wordpress_config(self, obj):
        """Indica si la Business Unit tiene configuración de WordPress"""
        try:
            config = obj.configuracionbu
            return bool(config.dominio_bu and config.jwt_token)
        except ConfiguracionBU.DoesNotExist:
            return False
    has_wordpress_config.boolean = True
    has_wordpress_config.short_description = 'WP Config'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Añade el botón de sincronización a la vista de detalle"""
        extra_context = extra_context or {}
        business_unit = self.get_object(request, object_id)
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
        
        return super().change_view(request, object_id, form_url, extra_context)

    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Canales Habilitados', {
            'fields': ('whatsapp_enabled', 'telegram_enabled', 'messenger_enabled', 'instagram_enabled'),
        }),
        ('Configuración de Scraping', {
            'fields': ('scrapping_enabled', 'scraping_domains'),
        }),
        ('Información de Contacto', {
            'fields': ('admin_phone',),
        }),
    )
    inlines = [ConfiguracionBUInline, WhatsAppAPIInline, MessengerAPIInline, TelegramAPIInline, InstagramAPIInline, DominioScrapingInline]
