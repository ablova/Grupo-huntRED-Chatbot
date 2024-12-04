# /home/amigro/app/admin.py

import json
from django.urls import reverse, path
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django import forms
from asgiref.sync import async_to_sync
from django.contrib import admin, messages
from app.models import (
    BusinessUnit, ApiConfig, MetaAPI, WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI,
    Person, Pregunta, Worker, Buttons, Etapa, GptApi,
    SmtpConfig, Chat, FlowModel, ChatState, Configuracion, ConfiguracionBU, DominioScraping, Vacante, RegistroScraping,
    MilkyLeak, Template
)
from app.chatbot import ChatBotHandler
from app.vacantes import VacanteManager
from app.tasks import ejecutar_scraping, validar_url, send_message
from django.template.response import TemplateResponse
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import nested_admin  # Importa nested_admin

# Configuración del encabezado del admin
admin.site.site_header = "Administración de Chatbots y servicios de Grupo huntRED®"
admin.site.site_title = "Portal Administrativo de Grupo huntRED®"
admin.site.index_title = "Bienvenido al Panel de Administración de Grupo huntRED®"

# Registrar los modelos
@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('secret_key', 'debug_mode', 'sentry_dsn')

@admin.register(DominioScraping)
class DominioScrapingAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'plataforma', 'verificado', 'ultima_verificacion', 'estado')
    search_fields = ('empresa', 'dominio', 'plataforma')
    list_filter = ('estado', 'plataforma')
    ordering = ("-id",)
    list_editable = ("plataforma", "estado")
    actions = ["marcar_como_definido", "ejecutar_scraping_action", "desactivar_dominios_invalidos"]

    def verificar_scraping_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Ejecutar Scraping</a>',
            reverse("admin:ejecutar_scraping", args=[obj.id])
        )
    verificar_scraping_button.short_description = "Ejecutar Scraping"
    verificar_scraping_button.allow_tags = True

    def get_urls(self):
        # Añadir la URL personalizada para ejecutar scraping
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='dashboard'),
            path("<int:dominio_id>/ejecutar-scraping/", self.admin_site.admin_view(self.ejecutar_scraping_view), name="ejecutar_scraping",),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        # Datos para el gráfico
        total_dominios = DominioScraping.objects.count()
        total_vacantes = Vacante.objects.count()
        scraping_activo = DominioScraping.objects.filter(estado="definido").count()
        vacantes_por_estado = Vacante.objects.values('estado').annotate(count=models.Count('estado'))

        # Gráfico de Vacantes por Estado
        estados = [item['estado'] for item in vacantes_por_estado]
        cantidades = [item['count'] for item in vacantes_por_estado]

        plt.figure(figsize=(6, 4))
        plt.bar(estados, cantidades, color="skyblue")
        plt.title("Vacantes por Estado")
        plt.xlabel("Estado")
        plt.ylabel("Cantidad")
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        grafico_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()

        # Contexto para la plantilla
        context = {
            'total_dominios': total_dominios,
            'total_vacantes': total_vacantes,
            'scraping_activo': scraping_activo,
            'grafico_vacantes': grafico_base64,
            'estados': json.dumps(estados),
            'cantidades': json.dumps(cantidades),
        }
        return TemplateResponse(request, "admin/dashboard.html", context)

    def dashboard_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">Ver Dashboard</a>',
            reverse('admin:dashboard')
        )
    dashboard_link.short_description = "Dashboard"

    def ejecutar_scraping_view(self, request, dominio_id):
        try:
            dominio = DominioScraping.objects.get(pk=dominio_id)
            ejecutar_scraping.delay()
            self.message_user(request, f"Scraping iniciado para el dominio: {dominio.empresa} ({dominio.dominio}).", level=messages.SUCCESS)
        except DominioScraping.DoesNotExist:
            self.message_user(request, "El dominio especificado no existe.", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error al iniciar el scraping: {str(e)}.", level=messages.ERROR)
        return redirect("admin:app_dominioscraping_changelist")

    def desactivar_dominios_invalidos(self, request, queryset):
        desactivados = 0
        for dominio in queryset:
            # Llamar a validar_url de forma asíncrona
            is_valid = async_to_sync(validar_url)(dominio.dominio)
            if not is_valid:
                dominio.estado = "libre"
                dominio.save()
                desactivados += 1
        self.message_user(request, f"{desactivados} dominios desactivados por ser no válidos.")
    desactivar_dominios_invalidos.short_description = "Desactivar dominios no válidos"

    def marcar_como_definido(self, request, queryset):
        queryset.update(estado="definido")
        self.message_user(request, f"{queryset.count()} dominios marcados como 'definidos'.")
    marcar_como_definido.short_description = "Marcar seleccionados como definidos"

    def ejecutar_scraping_action(self, request, queryset):
        # Acción para ejecutar scraping desde la lista
        for dominio in queryset:
            ejecutar_scraping.delay()  # Ejecutar la tarea de scraping
        self.message_user(request, f"Scraping iniciado para {queryset.count()} dominios seleccionados.")
    ejecutar_scraping_action.short_description = "Ejecutar scraping para dominios seleccionados"

class ScrapingScheduleAdmin(admin.ModelAdmin):
    list_filter = ('activo', 'dia')
    list_display = ('dominio', 'dia', 'activo')

@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'ubicacion', 'modalidad', 'activa', 'fecha_publicacion')
    search_fields = ('titulo', 'empresa', 'ubicacion')
    list_filter = ('activa', 'modalidad', 'dominio_origen')

@admin.register(RegistroScraping)
class RegistroScrapingAdmin(admin.ModelAdmin):
    list_display = ('dominio', 'estado', 'fecha_inicio', 'fecha_fin', 'vacantes_encontradas')
    search_fields = ('dominio__empresa',)
    list_filter = ('estado', 'fecha_inicio')

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
                # Obtener vacantes recomendadas
                recommended_jobs = VacanteManager.match_person_with_jobs(person)

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

@admin.register(Worker)
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

@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Información de la Pregunta', {
            'fields': (('flow', 'etapa', 'name'), ('option', 'action_type', 'input_type')),
        }),
        ('Opciones y Contenidos', {
            'fields': (('content', 'valid', 'active', 'requires_response', 'multi_select', 'buttons')),
        }),
        ('Conexiones', {
            'fields': (('next_si', 'next_no',))
        }),
        ('Potencialmente obsoletos', {
            'fields': (('condiciones', 'decision', 'field_person'),)
        })
    ]
    list_display = ['id','flow', 'name', 'action_type', 'multi_select', 'requires_response', 'mostrar_botones', 'next_si', 'next_no']
    list_filter = ['flow', 'action_type', 'requires_response', 'multi_select', 'buttons', 'input_type']
    search_fields = ['flow__name', 'name', 'content']
    ordering = ('id',)
    actions = [cambiar_etapa]

    def mostrar_botones(self, obj):
        return ", ".join([button.name for button in obj.buttons.all()])
    mostrar_botones.short_description = 'Botones'

    def get_help_text(self):
        placeholders_info = """
        <strong>Placeholders disponibles:</strong><br>
        {name}, {apellido_paterno}, {apellido_materno}, {sexo}, {email}, {phone}, {nacionalidad}, {fecha_nacimiento}
        """
        return placeholders_info

    def render_change_form(self, request, context, *args, **kwargs):
        context['adminform'].form.fields['content'].help_text = self.get_help_text()
        return super().render_change_form(request, context, *args, **kwargs)

@admin.register(Buttons)
class ButtonsAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'mostrar_preguntas', )
    search_fields = ('name',)

    def mostrar_preguntas(self, obj):
        return ", ".join([pregunta.name for pregunta in obj.pregunta.all()])
    mostrar_preguntas.short_description = 'Preguntas'

@admin.register(ChatState)
class ChatStateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'platform', 'current_question', 'last_interaction')
    search_fields = ('user_id', 'platform')

# Definir inlines para mostrar las APIs en el panel de cada unidad de negocio
class MetaAPIInline(admin.StackedInline):
    model = MetaAPI
    extra = 0

class WhatsAppAPIInline(admin.StackedInline):
    model = WhatsAppAPI
    extra = 0
    fields = ('name', 'phoneID', 'associated_flow', 'is_active')

class TelegramAPIInline(admin.StackedInline):
    model = TelegramAPI
    extra = 0
    fields = ('bot_name', 'api_key', 'associated_flow', 'is_active')

class MessengerAPIInline(admin.StackedInline):
    model = MessengerAPI
    extra = 0
    fields = ('page_access_token', 'associated_flow', 'is_active')

class InstagramAPIInline(admin.StackedInline):
    model = InstagramAPI
    extra = 0
    fields = ('app_id', 'access_token', 'associated_flow', 'is_active')

# Inline para Template dentro de WhatsAppAPI
class TemplateInline(admin.StackedInline):
    model = Template
    extra = 1
    fields = ('name', 'template_type', 'image_url', 'language_code')
    show_change_link = True

# Inline para ConfiguracionBU con Templates anidados (si deseas gestionarlo desde ConfiguracionBU)
class ConfiguracionBUInline(nested_admin.NestedStackedInline):
    model = ConfiguracionBU
    can_delete = False  # Evitar borrar directamente desde el inline
    verbose_name = "Configuración de Unidad de Negocio"
    verbose_name_plural = "Configuraciones de Unidad de Negocio"
    fk_name = 'business_unit'  # Indica que el campo `business_unit` es la clave foránea
    fieldsets = (
        ('Información General', {
            'fields': ('logo_url', 'direccion_bu', 'telefono_bu', 'correo_bu')
        }),
        ('Integración y Configuración', {
            'fields': ('dominio_bu', 'dominio_rest_api', 'jwt_token', 'scraping_domains')
        }),
        ('Configuración SMTP', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_tls', 'smtp_use_ssl')
        }),
    )
    readonly_fields = ('jwt_token',)  # Ejemplo de campos solo lectura si es necesario
    inlines = [TemplateInline]  # Anidar TemplateInline si decides gestionarlo desde ConfiguracionBU

    def regenerate_jwt_token(self, request, queryset):
        for configuracion in queryset:
            configuracion.jwt_token = generate_new_token()
            configuracion.save()
        self.message_user(request, "Tokens JWT regenerados exitosamente.")
    regenerate_jwt_token.short_description = "Regenerar tokens JWT"

# Admin para Unidad de Negocio con inlines anidados
@admin.register(BusinessUnit)
class BusinessUnitAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        'name', 'description', 'whatsapp_enabled', 'telegram_enabled',
        'messenger_enabled', 'instagram_enabled', 'scrapping_enabled'
    )
    inlines = [
        ConfiguracionBUInline,  # Configuración de Unidad de Negocio con Templates
        MetaAPIInline, 
        WhatsAppAPIInline, 
        TelegramAPIInline,
        MessengerAPIInline, 
        InstagramAPIInline
    ]
    list_editable = (
        'whatsapp_enabled', 'telegram_enabled',
        'messenger_enabled', 'instagram_enabled', 'scrapping_enabled'
    )
    fields = (
        'name', 'description', 'whatsapp_enabled', 'telegram_enabled',
        'messenger_enabled', 'instagram_enabled', 'scrapping_enabled',
        'scraping_domains'
    )
    filter_horizontal = ('scraping_domains',)  # Widget para facilitar selección múltiple
    search_fields = ['name', 'description']

@admin.register(FlowModel)
class FlowModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_unit', 'description', 'editar_flujo')
    search_fields = ('name',)
    list_filter = ('business_unit',)

    def editar_flujo(self, obj):
        url = reverse('admin:edit_flow', args=[obj.pk])
        return format_html('<a class="button" href="{}">Editar Flujo</a>', url)
    editar_flujo.short_description = 'Editar Flujo'
    editar_flujo.allow_tags = True

    # Mostrar solo flujos asociados a la unidad de negocio seleccionada en el formulario de creación
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'business_unit':
            kwargs['queryset'] = BusinessUnit.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(TelegramAPI)
class TelegramAPIAdmin(admin.ModelAdmin):
    list_display = ('bot_name', 'business_unit', 'api_key', 'associated_flow', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('bot_name', 'api_key')

@admin.register(WhatsAppAPI)
class WhatsAppAPIAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_unit', 'phoneID', 'associated_flow', 'is_active')

    inlines = [TemplateInline]  # Añadir TemplateInline aquí si deseas gestionarlo desde WhatsAppAPI

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'associated_flow':
            kwargs["queryset"] = FlowModel.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Validar si el phoneID está registrado en MetaAPI
        meta_api = MetaAPI.objects.filter(business_unit=obj.business_unit).first()
        if not meta_api:
            messages.error(request, f"No existe una MetaAPI asociada a la unidad de negocio {obj.business_unit}.")
            return
        super().save_model(request, obj, form, change)

@admin.register(MessengerAPI)
class MessengerAPIAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'page_access_token', 'associated_flow', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('page_access_token',)

@admin.register(InstagramAPI)
class InstagramAPIAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'app_id', 'associated_flow', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('app_id',)

@admin.register(MetaAPI)
class MetaAPIAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'app_id', 'app_secret', 'verify_token')
    search_fields = ('app_id', 'business_unit__name')
    list_filter = ('business_unit',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'business_unit':
            kwargs["queryset"] = BusinessUnit.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(GptApi)
class GptApiAdmin(admin.ModelAdmin):
    list_display = ('api_token', 'model', 'organization')
    search_fields = ('model', 'organization')

@admin.register(ApiConfig)
class ApiConfigAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'api_type', 'api_key')
    list_filter = ('business_unit', 'api_type')

@admin.register(Etapa)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activo')
    search_fields = ('nombre', 'descripcion')

@admin.register(SmtpConfig)
class SmtpConfigAdmin(admin.ModelAdmin):
    list_display = ('host', 'port', 'use_tls', 'use_ssl')
    search_fields = ('host',)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('From', 'To', 'ProfileName', 'created_at')
    search_fields = ('From', 'To')

@admin.register(MilkyLeak)
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