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
    SmtpConfig, Chat, FlowModel
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

admin_site = CustomAdminSite(name='custom_admin')

admin.site.site_header = "Amigro Admin"
admin.site.site_title = "Amigro Admin Portal"
admin.site.index_title = "Bienvenido a Amigro.org parte de Grupo huntRED®"


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'lastname', 'phone', 'nationality', 'skills', 'ubication', 'email', 'preferred_language')
    search_fields = ('name', 'lastname', 'phone', 'email', 'nationality')

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_id', 'company', 'job_type', 'salary', 'address', 'experience_required')
    search_fields = ('name', 'company', 'job_type')

@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('name', 'etapa', 'option', 'input_type', 'requires_response')
    search_fields = ('name', 'etapa__name')

@admin.register(SubPregunta)
class SubPreguntaAdmin(admin.ModelAdmin):
    list_display = ('name', 'option', 'input_type', 'requires_response')
    search_fields = ('name', 'parent_sub_pregunta__name')

@admin.register(ChatState)
class ChatStateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'platform', 'current_question', 'last_interaction', 'context')
    search_fields = ('user_id', 'platform')

@admin.register(FlowModel)
class FlowModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(TelegramAPI)
class TelegramAPIAdmin(admin.ModelAdmin):
    list_display = ('bot_name', 'api_key')

@admin.register(WhatsAppAPI)
class WhatsAppAPIAdmin(admin.ModelAdmin):
    list_display = ('phoneID', 'api_token')

@admin.register(MessengerAPI)
class MessengerAPIAdmin(admin.ModelAdmin):
    list_display = ('page_access_token',)

@admin.register(InstagramAPI)
class InstagramAPIAdmin(admin.ModelAdmin):
    list_display = ('app_id', 'access_token', 'instagram_account_id')
