# /home/amigro/app/admin.py
import json
from django.urls import path, reverse, re_path
from django.utils.html import format_html
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django import forms
from asgiref.sync import async_to_sync, sync_to_async
from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from app.integrations.services import send_message
from app.chatbot import ChatBotHandler
from app.models import (
    BusinessUnit, ApiConfig, MetaAPI, WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI,
    Person, Pregunta, Worker, Buttons, Etapa, SubPregunta, GptApi,
    SmtpConfig, Chat, FlowModel, ChatState, Configuracion,
    MilkyLeak
)
from app.views import (
    CreateFlowView,
    edit_flow,
    save_flow_structure,
    export_chatbot_flow,
    load_flow_data,
)

# Definición personalizada del AdminSite
class CustomAdminSite(admin.AdminSite):
    site_header = "Chatbots Admin"
    site_title = "Chatbots Admin Portal"
    index_title = "Bienvenido al Administrador de Chatbot de Grupo huntRED®"

    def each_context(self, request):
        context = super().each_context(request)
        context['admin_css'] = 'admin/css/custom_admin.css'  # Estilos personalizados, si tienes alguno.
        return context

# Instancia de CustomAdminSite
admin_site = CustomAdminSite(name='grupo_huntred_admin')



# Registrar los modelos con CustomAdminSite
@admin.register(Configuracion, site=admin_site)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('secret_key', 'debug_mode', 'sentry_dsn')

# Instanciamos el ChatBotHandler
chatbot_handler = ChatBotHandler()

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'apellido_paterno', 'apellido_materno', 'phone', 'email')
    search_fields = ('name', 'apellido_paterno', 'phone', 'email')

    @admin.action(description='Enviar Recap por WhatsApp')
    def enviar_recap(self, request, queryset):
        for person in queryset:
            if person.phone:
                recap_message = async_to_sync(chatbot_handler.recap_information)(person)
                async_to_sync(send_message)('whatsapp', person.phone, recap_message)
                self.message_user(request, f"Recap enviado a {person.name}.")
            else:
                self.message_user(request, f"{person.name} no tiene un número de teléfono válido.", level=messages.ERROR)

    @admin.action(description='Enviar Vacantes por WhatsApp')
    def enviar_vacantes(self, request, queryset):
        for person in queryset:
            if person.phone:
                recommended_jobs = async_to_sync(VacanteManager.match_person_with_jobs)(person)

                if recommended_jobs:
                    vacantes_message = "Estas son las vacantes recomendadas para ti:\n"
                    for idx, (job, score) in enumerate(recommended_jobs[:5]):
                        vacantes_message += f"{idx + 1}. {job['title']} en {job['company']}\n"
                    vacantes_message += "Por favor, responde con el número de la vacante que te interesa."

                    async_to_sync(send_message)('whatsapp', person.phone, vacantes_message)
                    self.message_user(request, f"Vacantes enviadas a {person.name}.")
                else:
                    self.message_user(request, f"No se encontraron vacantes para {person.name}.", level=messages.WARNING)
            else:
                self.message_user(request, f"{person.name} no tiene un número de teléfono válido.", level=messages.ERROR)

    actions = ['enviar_recap', 'enviar_vacantes']

@admin.register(Worker, site=admin_site)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_id', 'company', 'job_type', 'salary', 'address', 'experience_required')
    search_fields = ('name', 'company', 'job_type')

# Definir el formulario para seleccionar una nueva etapa
class BulkEditEtapaForm(forms.Form):
    etapa = forms.ModelChoiceField(queryset=Etapa.objects.all(), label="Nueva Etapa", required=True)

# Definir la acción personalizada para cambiar la etapa
def cambiar_etapa(modeladmin, request, queryset):
    form = None

    if 'apply' in request.POST:
        form = BulkEditEtapaForm(request.POST)

        if form.is_valid():
            nueva_etapa = form.cleaned_data['etapa']
            queryset.update(etapa=nueva_etapa)
            modeladmin.message_user(request, f"{queryset.count()} preguntas actualizadas con la nueva etapa.")
            return

    if not form:
        form = BulkEditEtapaForm()

    return render(request, 'admin/cambiar_etapa.html', {'form': form, 'preguntas': queryset})

cambiar_etapa.short_description = "Cambiar la etapa de las preguntas seleccionadas"

@admin.register(Pregunta, site=admin_site)
class PreguntaAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Información de la Pregunta', {
            'fields': (('flow', 'etapa', 'name'), ('option', 'action_type', 'input_type')),
        }),
        ('Opciones y Contenidos', {
            'fields': (('content', 'valid', 'active', 'requires_response', 'multi_select', 'buttons')),
        }),
        ('Conexiónes y SubPreguntas', {
            'fields': (('next_si', 'next_no'), ('sub_pregunta'))
        }),
        ('Potencialmente obsoletos', {
            'fields': (('condiciones', 'decision', 'field_person'))
        })
    ]
    list_display = ['flow', 'name', 'action_type', 'multi_select', 'requires_response', 'mostrar_botones', 'next_si', 'next_no']
    list_filter = ['flow', 'action_type', 'requires_response', 'multi_select', 'buttons', 'input_type']
    search_fields = ['flow', 'name', 'content']
    actions = [cambiar_etapa]

    def mostrar_botones(self, obj):
        return ", ".join([button.name for button in obj.botones_pregunta.all()])
    mostrar_botones.short_description = 'Botones'
    
    def get_help_text(self):
        placeholders_info = """
        <strong>Placeholders disponibles:</strong><br>
        {name}, {apellido_paterno}, {apellido_materno}, {sexo}, {email}, {phone}, {nacionalidad}, {fecha_nacimiento}
        """
        return placeholders_info

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(PreguntaAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'action_type':
            field.widget.attrs['onchange'] = 'updateFields(this.value);'
        return field
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'flow':
            kwargs["queryset"] = FlowModel.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['content'].help_text = self.get_help_text()
        return super().render_change_form(request, context, *args, **kwargs)

@admin.register(SubPregunta, site=admin_site)
class SubPreguntaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent_sub_pregunta', 'option', 'input_type', 'requires_response')
    search_fields = ('name', 'parent_sub_pregunta__name')

@admin.register(Buttons, site=admin_site)
class ButtonsAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'mostrar_preguntas', 'mostrar_subpreguntas')
    search_fields = ('name',)

    def mostrar_preguntas(self, obj):
        return ", ".join([pregunta.name for pregunta in obj.pregunta.all()])
    mostrar_preguntas.short_description = 'Preguntas'

    def mostrar_subpreguntas(self, obj):
        return ", ".join([subpregunta.name for subpregunta in obj.subpregunta.all()])
    mostrar_subpreguntas.short_description = 'SubPreguntas'

@admin.register(ChatState, site=admin_site)
class ChatStateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'platform', 'current_question', 'last_interaction', 'context')
    search_fields = ('user_id', 'platform')


# # Definir inlines para mostrar las APIs en el panel de cada unidad de negocio
# Definición de inlines para las APIs
class MetaAPIInline(admin.TabularInline):
    model = MetaAPI
    extra = 1

class WhatsAppAPIInline(admin.TabularInline):
    model = WhatsAppAPI
    extra = 1
    fields = ('name', 'phoneID', 'associated_flow', 'is_active')
    readonly_fields = ('phoneID',)
    can_delete = False

class TelegramAPIInline(admin.TabularInline):
    model = TelegramAPI
    extra = 1
    fields = ('bot_name', 'api_key', 'associated_flow', 'is_active')
    readonly_fields = ('bot_name',)
    can_delete = False

class MessengerAPIInline(admin.TabularInline):
    model = MessengerAPI
    extra = 1
    fields = ('page_access_token', 'associated_flow', 'is_active')
    readonly_fields = ('page_access_token',)
    can_delete = False

class InstagramAPIInline(admin.TabularInline):
    model = InstagramAPI
    extra = 1
    fields = ('app_id', 'access_token', 'associated_flow', 'is_active')
    readonly_fields = ('app_id', 'access_token')
    can_delete = False

# Admin para Unidad de Negocio
@admin.register(BusinessUnit, site=admin_site)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'description', 'whatsapp_enabled', 'telegram_enabled', 
        'messenger_enabled', 'instagram_enabled', 'whatsapp_status', 
        'telegram_status', 'messenger_status', 'instagram_status', 
        'scraping_domains', 'scrapping_enabled'  # Agregamos este campo
    )
    inlines = [MetaAPIInline, WhatsAppAPIInline, TelegramAPIInline, MessengerAPIInline, InstagramAPIInline]
    list_editable = (
        'whatsapp_enabled', 'telegram_enabled', 
        'messenger_enabled', 'instagram_enabled', 'scrapping_enabled'
    )
    fields = (
        'name', 'description', 'whatsapp_enabled', 'telegram_enabled', 
        'messenger_enabled', 'instagram_enabled', 'scrapping_enabled', 
        'scraping_domains'
    )
    search_fields = ['name', 'description']

    def whatsapp_status(self, obj):
        return "Activo" if obj.whatsapp_enabled else "Inactivo"
    whatsapp_status.short_description = 'WhatsApp Activo'

    def telegram_status(self, obj):
        return "Activo" if obj.telegram_enabled else "Inactivo"
    telegram_status.short_description = 'Telegram Activo'

    def messenger_status(self, obj):
        return "Activo" if obj.messenger_enabled else "Inactivo"
    messenger_status.short_description = 'Messenger Activo'

    def instagram_status(self, obj):
        return "Activo" if obj.instagram_enabled else "Inactivo"
    instagram_status.short_description = 'Instagram Activo'

    def save_model(self, request, obj, form, change):
        # Validar que no haya configuraciones duplicadas para la misma BusinessUnit y app_id
        existing_meta_api = MetaAPI.objects.filter(business_unit=obj.business_unit, app_id=obj.app_id).exclude(pk=obj.pk)
        if existing_meta_api.exists():
            messages.error(request, f"Ya existe una configuración de MetaAPI para {obj.business_unit} con app_id {obj.app_id}.")
            return
        super().save_model(request, obj, form, change)

@admin.register(FlowModel, site=admin_site)
class FlowModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

    # Mostrar solo flujos asociados a la unidad de negocio seleccionada en el formulario de creación
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'business_unit':
            kwargs['queryset'] = BusinessUnit.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def render_change_form(self, request, context, *args, **kwargs):
        obj = kwargs.get('obj', None)
        if obj and obj.pk:
            context['edit_flow_url'] = reverse('edit_flow', args=[obj.pk])
        else:
            context['edit_flow_url'] = None
        return super().render_change_form(request, context, *args, **kwargs)

@admin.register(TelegramAPI, site=admin_site)
class TelegramAPIAdmin(admin.ModelAdmin):
    list_display = ('bot_name', 'business_unit', 'api_key', 'associated_flow', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('bot_name', 'api_key')

@admin.register(WhatsAppAPI, site=admin_site)
class WhatsAppAPIAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_unit', 'phoneID', 'associated_flow', 'is_active')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'associated_flow':
            kwargs["queryset"] = FlowModel.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Validar si el phoneID está registrado en MetaAPI
        meta_api = MetaAPI.objects.filter(phoneID=obj.phoneID).first()
        if not meta_api:
            messages.error(request, f"El phoneID {obj.phoneID} no está registrado en MetaAPI.")
            return
        super().save_model(request, obj, form, change)

@admin.register(MessengerAPI, site=admin_site)
class MessengerAPIAdmin(admin.ModelAdmin):
    list_display = ('page_access_token', 'business_unit', 'associated_flow', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('page_access_token',)

@admin.register(InstagramAPI, site=admin_site)
class InstagramAPIAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'business_unit', 'associated_flow', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('app_id',)

@admin.register(MetaAPI, site=admin_site)
class MetaAPIAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'app_id', 'app_secret', 'verify_token')
    search_fields = ('app_id', 'business_unit__name')
    list_filter = ('business_unit',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'business_unit':
            kwargs["queryset"] = BusinessUnit.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(GptApi, site=admin_site)
class GptApiAdmin(admin.ModelAdmin):
    list_display = ('api_token', 'model', 'organization')
    search_fields = ('model', 'organization')

@admin.register(ApiConfig, site=admin_site)
class ApiConfigAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'api_type', 'api_key')
    list_filter = ('business_unit', 'api_type')

@admin.register(Etapa, site=admin_site)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activo')  # Asegúrate de que 'nombre' y 'descripcion' existan en Etapa
    search_fields = ('nombre', 'descripcion')

@admin.register(SmtpConfig, site=admin_site)
class SmtpConfigAdmin(admin.ModelAdmin):
    list_display = ('host', 'port', 'use_tls', 'use_ssl')
    search_fields = ('host',)

@admin.register(Chat, site=admin_site)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('From', 'To', 'ProfileName', 'created_at')  # Ajusta según los campos en Chat
    search_fields = ('From', 'To')

# Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
@admin.register(MilkyLeak, site=admin_site)
class MilkyLeakAdmin(admin.ModelAdmin):
    list_display = ['id', 'twitter_api_key', 'storage_service']
    fields = ['twitter_api_key', 'twitter_api_secret_key', 'twitter_access_token', 
              'twitter_access_token_secret', 'mega_email', 'mega_password', 
              'dropbox_access_token', 'folder_location', 'image_prefix', 
              'local_directory', 'storage_service', 'min_interval', 
              'max_interval']
    readonly_fields = ['image_counter']
    
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj and obj.storage_service == 'mega':
            fields += ['mega_email', 'mega_password']
        elif obj and obj.storage_service == 'dropbox':
            fields += ['dropbox_access_token']
        return fields
    
    def reset_image_counter(self, request, queryset):
        queryset.update(image_counter=1)  # Reiniciar el contador a 1
        self.message_user(request, "El contador de imágenes ha sido reiniciado.", level=messages.SUCCESS)

    reset_image_counter.short_description = "Reiniciar el contador de imágenes"