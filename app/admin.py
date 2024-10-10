# /home/amigro/app/admin.py

import json
from django.urls import path, reverse
from django.contrib import admin
from django.utils.html import format_html
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import (
    MetaAPI, WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI,
    Person, Pregunta, Worker, Buttons, Etapa, SubPregunta, GptApi,
    SmtpConfig, Chat, FlowModel, ChatState, Configuracion,
    MilkyLeak
)

# Definición personalizada del AdminSite
class CustomAdminSite(admin.AdminSite):
    site_header = "Amigro Admin"
    site_title = "Amigro Admin Portal"
    index_title = "Bienvenido a Amigro.org parte de Grupo huntRED®"

    def each_context(self, request):
        context = super().each_context(request)
        context['admin_css'] = 'admin/css/custom_admin.css'  # Estilos personalizados, si tienes alguno.
        return context

# Instancia de CustomAdminSite
admin_site = CustomAdminSite(name='custom_admin')

# Registrar los modelos con CustomAdminSite
@admin.register(Configuracion, site=admin_site)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('secret_key', 'debug_mode', 'sentry_dsn')
    
@admin.register(Person, site=admin_site)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'apellido_paterno', 'apellido_materno', 'phone', 'nationality', 'skills', 'ubication', 'email', 'preferred_language')
    search_fields = ('name', 'apellido_paterno', 'phone', 'email', 'nationality')

@admin.register(Worker, site=admin_site)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_id', 'company', 'job_type', 'salary', 'address', 'experience_required')
    search_fields = ('name', 'company', 'job_type')

@admin.register(Pregunta, site=admin_site)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('name', 'etapa', 'option', 'input_type', 'requires_response')
    search_fields = ('name', 'etapa__nombre')  # Asegúrate de que 'nombre' exista en Etapa

@admin.register(SubPregunta, site=admin_site)
class SubPreguntaAdmin(admin.ModelAdmin):
    list_display = ('name', 'option', 'input_type', 'requires_response')
    search_fields = ('name', 'parent_sub_pregunta__name')

@admin.register(ChatState, site=admin_site)
class ChatStateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'platform', 'current_question', 'last_interaction', 'context')
    search_fields = ('user_id', 'platform')

@admin.register(FlowModel, site=admin_site)
class FlowModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(TelegramAPI, site=admin_site)
class TelegramAPIAdmin(admin.ModelAdmin):
    list_display = ('bot_name', 'api_key')

@admin.register(WhatsAppAPI, site=admin_site)
class WhatsAppAPIAdmin(admin.ModelAdmin):
    list_display = ('phoneID', 'api_token')

@admin.register(MessengerAPI, site=admin_site)
class MessengerAPIAdmin(admin.ModelAdmin):
    list_display = ('page_access_token',)

@admin.register(InstagramAPI, site=admin_site)
class InstagramAPIAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'access_token', 'instagram_account_id')

@admin.register(MetaAPI, site=admin_site)
class MetaAPIAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'app_secret', 'verify_token')

@admin.register(GptApi, site=admin_site)
class GptApiAdmin(admin.ModelAdmin):
    list_display = ('api_token', 'model', 'organization')
    search_fields = ('model', 'organization')

@admin.register(Buttons, site=admin_site)
class ButtonsAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    search_fields = ('name',)

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

#________________________________________________________________________________________________
#Esto es para la aplicación de Milkyleak, independiente del chatbot de amigro, solo se utiliza el servidor.
class MilkyLeakAdmin(admin.ModelAdmin):
    list_display = ('twitter_api_key', 'mega_email', 'folder_location', 'image_counter', 'min_interval', 'max_interval')
    fields = (
        'twitter_api_key', 'twitter_api_secret_key', 'twitter_access_token', 'twitter_access_token_secret',
        'mega_email', 'mega_password', 'folder_location', 'image_prefix', 'local_directory', 
        'image_counter', 'min_interval', 'max_interval'
    )
    readonly_fields = ['image_counter']  # Solo lectura para el contador, ya que se actualiza automáticamente
