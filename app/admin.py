# Ubicación del archivo: /home/pablollh/app/admin.py
from django.contrib import admin, messages
from django.db import models  # Añadimos esta importación
from django.urls import reverse, path
from django.template.response import TemplateResponse
from django.shortcuts import render, redirect
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import json

from django import forms

from app.models import (
    BusinessUnit, ApiConfig, MetaAPI, WhatsAppAPI, TelegramAPI, MessengerAPI, InstagramAPI,
    Person, Worker, GptApi, Skill, Division,
    SmtpConfig, Chat, Configuracion, ConfiguracionBU, DominioScraping, Vacante, RegistroScraping, ReporteScraping,
    Template, ChatState, Application, Invitacion, Interview, UserInteractionLog,
    ModelTrainingLog, QuarterlyInsight, MigrantSupportPlatform, EnhancedNetworkGamificationProfile, EnhancedMLProfile
)
from app.tasks import (
    execute_ml_and_scraping,
    ejecutar_scraping,
    verificar_dominios_scraping,
    train_ml_task,
    process_linkedin_csv_task
)
from app.chatbot.integrations.services import send_message
from app.utilidades.vacantes import VacanteManager
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import user_passes_test

admin.site.site_header = "Administración de Grupo huntRED®"
admin.site.site_title = "Portal Administrativo"
admin.site.index_title = "Bienvenido al Panel de Administración"

# Token Masking Mixin
class TokenMaskingMixin:
    """Mixin para enmascarar campos sensibles en el admin"""
    token_fields = []
    visible_prefix_length = 6
    visible_suffix_length = 4

    def get_masked_value(self, value):
        if not value:
            return "-"
        if len(value) <= (self.visible_prefix_length + self.visible_suffix_length):
            return "..." + value[-self.visible_suffix_length:]
        return f"{value[:self.visible_prefix_length]}...{value[-self.visible_suffix_length:]}"

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if isinstance(list_display, tuple):
            list_display = list(list_display)
            
        for field in self.token_fields:
            if field in list_display:
                mask_method_name = f'get_masked_{field}'
                if not hasattr(self, mask_method_name):
                    setattr(self, mask_method_name, 
                           lambda obj, field=field: self.get_masked_value(getattr(obj, field)))
                    getattr(self, mask_method_name).short_description = field.replace('_', ' ').title()
                list_display[list_display.index(field)] = mask_method_name
                
        return list_display

@admin.register(Configuracion)
class ConfiguracionAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['secret_key', 'sentry_dsn']
    list_display = ('secret_key', 'debug_mode', 'sentry_dsn')
    
@admin.register(DominioScraping)
class DominioScrapingAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'plataforma', 'verificado', 'ultima_verificacion', 'estado')
    search_fields = ('empresa', 'dominio', 'plataforma')
    list_filter = ('estado', 'plataforma')
    ordering = ("-id",)
    list_editable = ("plataforma", "estado")
    actions = ["marcar_como_definido", "ejecutar_scraping_action", "desactivar_dominios_invalidos"]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.dashboard_view), name='dashboard'),
            path("<int:dominio_id>/ejecutar-scraping/", self.admin_site.admin_view(self.ejecutar_scraping_view), name="ejecutar_scraping",),
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        total_dominios = DominioScraping.objects.count()
        total_vacantes = Vacante.objects.count()
        scraping_activo = DominioScraping.objects.filter(estado="definido").count()

        # Estadísticas de Scraping
        exitosos = RegistroScraping.objects.filter(estado='exitoso').count()
        fallidos = RegistroScraping.objects.filter(estado='fallido').count()
        parciales = RegistroScraping.objects.filter(estado='parcial').count()

        # Gráfico de barras
        plt.figure(figsize=(6, 4))
        estados = ['Exitoso', 'Fallido', 'Parcial']
        cantidades = [exitosos, fallidos, parciales]
        plt.bar(estados, cantidades, color=['green', 'red', 'orange'])
        plt.title("Registros de Scraping por Estado")
        plt.xlabel("Estado")
        plt.ylabel("Cantidad")
        plt.tight_layout()
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        grafico_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()

        context = {
            'total_dominios': total_dominios,
            'total_vacantes': total_vacantes,
            'scraping_activo': scraping_activo,
            'grafico_vacantes': grafico_base64,
        }
        return TemplateResponse(request, "admin/dashboard.html", context)

    def ejecutar_scraping_view(self, request, dominio_id):
        try:
            dominio = DominioScraping.objects.get(pk=dominio_id)
            ejecutar_scraping.delay()
            self.message_user(request, f"Scraping iniciado para: {dominio.empresa} ({dominio.dominio}).", level=messages.SUCCESS)
        except DominioScraping.DoesNotExist:
            self.message_user(request, "El dominio especificado no existe.", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error al iniciar el scraping: {str(e)}.", level=messages.ERROR)
        return redirect("admin:app_dominioscraping_changelist")

    @admin.action(description="Ejecutar scraping para dominios seleccionados")
    def ejecutar_scraping_action(self, request, queryset):
        for dominio in queryset:
            ejecutar_scraping.delay(dominio.id)  # Pasa el dominio_id como argumento
        self.message_user(request, f"Scraping iniciado para {queryset.count()} dominios.")
    
    @admin.action(description="Marcar seleccionados como 'definidos'")
    def marcar_como_definido(self, request, queryset):
        queryset.update(estado="definido")
        self.message_user(request, f"{queryset.count()} dominios marcados como 'definidos'.")

    @admin.action(description="Desactivar dominios no válidos")
    def desactivar_dominios_invalidos(self, request, queryset):
        desactivados = 0
        for dominio in queryset:
            # Aquí podrías validar si el dominio es válido
            # Suponiendo que no lo es, lo marcamos como libre
            dominio.estado = "libre"
            dominio.save()
            desactivados += 1
        self.message_user(request, f"{desactivados} dominios desactivados.")

@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'ubicacion', 'modalidad', 'activa', 'fecha_publicacion')
    search_fields = ('titulo', 'empresa', 'ubicacion')
    list_filter = ('activa', 'modalidad', 'dominio_origen')
    actions = ['toggle_activa_status']

    fieldsets = (
        (None, {
            'fields': ('titulo', 'empresa', 'ubicacion', 'modalidad', 'activa', 'fecha_publicacion')
        }),
        ('Detalles Adicionales', {
            'fields': ('descripcion', 'requisitos', 'salario')
        }),
    )

@admin.register(RegistroScraping)
class RegistroScrapingAdmin(admin.ModelAdmin):
    list_display = ('dominio', 'estado', 'fecha_inicio', 'fecha_fin', 'vacantes_encontradas')
    search_fields = ('dominio__empresa', 'dominio__url')
    list_filter = ('estado', 'fecha_inicio', 'vacantes_encontradas')

@admin.register(ReporteScraping)
class ReporteScrapingAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'fecha', 'vacantes_creadas', 'exitosos', 'fallidos', 'parciales')
    list_filter = ('business_unit', 'fecha')
    search_fields = ('business_unit__name',)
    readonly_fields = ('business_unit', 'fecha', 'vacantes_creadas', 'exitosos', 'fallidos', 'parciales')
    actions = ['generar_reporte_pdf']

    def generar_reporte_pdf(self, request, queryset):
        """
        Genera un reporte PDF de los registros seleccionados.
        """
        import io
        from django.http import FileResponse
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 800, "Reporte de Scraping")
        y = 750
        for reporte in queryset:
            p.drawString(100, y, f"Unidad de Negocio: {reporte.business_unit.name}")
            p.drawString(100, y-20, f"Fecha: {reporte.fecha}")
            p.drawString(100, y-40, f"Vacantes Creadas: {reporte.vacantes_creadas}")
            p.drawString(100, y-60, f"Exitosos: {reporte.exitosos}")
            p.drawString(100, y-80, f"Fallidos: {reporte.fallidos}")
            p.drawString(100, y-100, f"Parciales: {reporte.parciales}")
            y -= 140
            if y < 100:
                p.showPage()
                y = 800
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='reporte_scraping.pdf')

    generar_reporte_pdf.short_description = "Generar reporte PDF de los seleccionados"

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = '__all__'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise forms.ValidationError("Ingresa un email válido.")
        return email

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('skills',)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonForm
    list_display = ('nombre', 'apellido_paterno', 'apellido_materno', 'phone', 'email', 'job_search_status')
    search_fields = ('nombre', 'apellido_paterno', 'phone', 'email')
    list_filter = ('job_search_status', 'preferred_language')
    actions = ['export_as_csv', 'send_email']

    def export_as_csv(self, request, queryset):
        """
        Exporta las personas seleccionadas como un archivo CSV.
        """
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=personas.csv'
        writer = csv.writer(response)

        # Escribir encabezados
        writer.writerow(['Nombre', 'Apellido Paterno', 'Apellido Materno', 'Teléfono', 'Email', 'Estado de Búsqueda'])

        # Escribir datos
        for person in queryset:
            writer.writerow([person.nombre, person.apellido_paterno, person.apellido_materno, person.phone, person.email, person.job_search_status])

        self.message_user(request, "CSV exportado exitosamente.")
        return response

    export_as_csv.short_description = "Exportar seleccionados como CSV"

    @admin.action(description="Enviar correo a los seleccionados")
    def send_email(self, request, queryset):
        for person in queryset:
            # Lógica para enviar correo
            send_mail(
                'Asunto del Correo',
                'Cuerpo del correo',
                'from@example.com',
                [person.email],
            )
        self.message_user(request, f"Correo enviado a {queryset.count()} personas.")

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_id', 'company', 'job_type', 'salary', 'address', 'experience_required')
    search_fields = ('name', 'company', 'job_type')

@admin.register(ChatState)
class ChatStateAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'platform', 'applied', 'interviewed', 'last_interaction_at')
    search_fields = ('user_id', 'platform')

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('person', 'job', 'interview_date', 'interview_type', 'candidate_confirmed', 'location_verified')
    search_fields = ('person__nombre', 'job__name')
    list_filter = ('interview_type', 'candidate_confirmed', 'location_verified')
    actions = ['send_reminder_messages']

    @admin.action(description="Enviar recordatorio de entrevista")
    def send_reminder_messages(self, request, queryset):
        for interview in queryset:
            send_follow_up_messages.delay(interview.id)
        self.message_user(request, f"Recordatorios enviados para {queryset.count()} entrevistas.")

@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'invitado', 'created_at')
    search_fields = ('referrer__name', 'invitado__name')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'vacancy', 'status', 'applied_at', 'updated_at')
    search_fields = ('user__nombre', 'vacancy__titulo')
    list_filter = ('status', 'vacancy__business_unit')
    actions = ['change_status_to_hired']

    @admin.action(description="Marcar seleccionados como 'Contratado'")
    def change_status_to_hired(self, request, queryset):
        updated = queryset.update(status='hired')
        self.message_user(request, f"{updated} aplicaciones marcadas como 'Contratado'.")

@admin.register(ApiConfig)
class ApiConfigAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['api_key', 'api_secret']
    list_display = ('business_unit', 'api_type', 'api_key')
    list_filter = ('business_unit', 'api_type')

@admin.register(MetaAPI)
class MetaAPIAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['app_secret', 'verify_token']
    list_display = ('business_unit', 'app_id', 'app_secret', 'verify_token')
    search_fields = ('app_id', 'business_unit__name')
    list_filter = ('business_unit',)

@admin.register(WhatsAppAPI)
class WhatsAppAPIAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['api_token']
    list_display = ('name', 'business_unit', 'phoneID', 'api_token', 'is_active')
    search_fields = ('name', 'phoneID')
    list_filter = ('business_unit', 'is_active')

    inlines = []  # TemplateInline si se desea

@admin.register(MessengerAPI)
class MessengerAPIAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['page_access_token']
    list_display = ('business_unit', 'page_access_token', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('page_access_token',)

@admin.register(InstagramAPI)
class InstagramAPIAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['access_token']
    list_display = ('business_unit', 'app_id', 'access_token', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('app_id',)

@admin.register(TelegramAPI)
class TelegramAPIAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['api_key']
    list_display = ('bot_name', 'business_unit', 'api_key', 'is_active')
    list_filter = ('business_unit', 'is_active')
    search_fields = ('bot_name', 'api_key')

@admin.register(GptApi)
class GptApiAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['api_token']
    list_display = ('api_token', 'model', 'organization')
    search_fields = ('model', 'organization')

@admin.register(SmtpConfig)
class SmtpConfigAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['password']
    list_display = ('host', 'port', 'username', 'password', 'use_tls', 'use_ssl')
    search_fields = ('host',)

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'language_code', 'whatsapp_api')
    search_fields = ('name', 'whatsapp_api__name')
    list_filter = ('template_type', 'language_code', 'whatsapp_api')

class WhatsAppAPIInline(admin.TabularInline):
    model = WhatsAppAPI
    extra = 1
    readonly_fields = ('api_token',)  # Proteger campos sensibles

class MessengerAPIInline(admin.TabularInline):
    model = MessengerAPI
    extra = 1

class TelegramAPIInline(admin.TabularInline):
    model = TelegramAPI
    extra = 1

class InstagramAPIInline(admin.TabularInline):
    model = InstagramAPI
    extra = 1

class DominioScrapingInline(admin.TabularInline):
    model = ConfiguracionBU.scraping_domains.through
    extra = 1
    verbose_name = "Dominio de Scraping"
    verbose_name_plural = "Dominios de Scraping"

class ConfiguracionBUInline(admin.StackedInline):  # O admin.TabularInline
    model = ConfiguracionBU
    extra = 1  # Número de formularios vacíos que se mostrarán

    # Campos para la configuración general
    fields = ('direccion_bu', 'telefono_bu', 'correo_bu', 'logo_url', 'jwt_token', 'dominio_bu', 'dominio_rest_api')  # Campos generales

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj) or ()
        additional_fields = (
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 
            'smtp_use_tls', 'smtp_use_ssl', 'weight_location', 
            'weight_hard_skills', 'weight_soft_skills', 'weight_contract'
        )
        return fields + additional_fields

@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'get_admin_email', 'whatsapp_enabled', 'telegram_enabled', 'messenger_enabled', 'instagram_enabled', 'scrapping_enabled')
    list_editable = ('whatsapp_enabled', 'telegram_enabled', 'messenger_enabled', 'instagram_enabled', 'scrapping_enabled')
    filter_horizontal = ('scraping_domains',)
    search_fields = ['name', 'description']

    def get_admin_email(self, obj):
        return obj.admin_email
    get_admin_email.short_description = 'Admin Email'

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
    inlines = [ConfiguracionBUInline, WhatsAppAPIInline, MessengerAPIInline, TelegramAPIInline, InstagramAPIInline]

@admin.register(QuarterlyInsight)
class QuarterlyInsightAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'created_at')
    search_fields = ('business_unit__name',)
    list_filter = ('business_unit', 'created_at')
    readonly_fields = ('insights_data',)

    def changelist_view(self, request, extra_context=None):
        # Agregar gráficos o visualizaciones de insights
        # Lógica para generar gráficos
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(ModelTrainingLog)
class ModelTrainingLogAdmin(admin.ModelAdmin):
    list_display = ('business_unit', 'accuracy', 'trained_at', 'model_version')
    search_fields = ('business_unit__name', 'model_version')
    list_filter = ('business_unit', 'trained_at')
    readonly_fields = ('accuracy', 'trained_at', 'model_version')

    def changelist_view(self, request, extra_context=None):
        # Agregar estadísticas adicionales al changelist
        extra_context = extra_context or {}
        insights = QuarterlyInsight.objects.filter(business_unit__in=BusinessUnit.objects.all())
        extra_context['insights'] = insights
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(EnhancedNetworkGamificationProfile)
class EnhancedNetworkGamificationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'professional_points', 'skill_endorsements', 'network_expansion_level')
    search_fields = ('user__nombre', 'user__email')
    list_filter = ('network_expansion_level',)
    actions = ['reset_points', 'award_bonus_points']

    @admin.action(description="Resetear puntos profesionales")
    def reset_points(self, request, queryset):
        queryset.update(professional_points=0)
        self.message_user(request, "Puntos profesionales reseteados a 0 para los perfiles seleccionados.")

    @admin.action(description="Otorgar puntos de bonificación")
    def award_bonus_points(self, request, queryset):
        for profile in queryset:
            profile.professional_points += 100  # Otorgar 100 puntos como bonificación
            profile.save()
        self.message_user(request, "100 puntos de bonificación otorgados a los perfiles seleccionados.")

@admin.register(UserInteractionLog)
class UserInteractionLogAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'platform', 'business_unit', 'timestamp', 'message_direction')
    list_filter = ('platform', 'business_unit', 'message_direction')
    search_fields = ('user_id',)
    readonly_fields = ('user_id', 'platform', 'business_unit', 'timestamp', 'message_direction')

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('From', 'To', 'ProfileName', 'created_at')
    search_fields = ('From', 'To', 'ProfileName')
    readonly_fields = ('From', 'To', 'ProfileName', 'body', 'SmsStatus', 'ChannelPrefix', 'MessageSid', 'created_at', 'updated_at', 'message_count')

@admin.register(EnhancedMLProfile)
class EnhancedMLProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'performance_score', 'model_version', 'last_prediction_timestamp')
    search_fields = ('user__nombre', 'user__apellido_paterno', 'user__email')
    list_filter = ('model_version',)
    readonly_fields = ('model_version', 'last_prediction_timestamp')

class TaskExecution(models.Model):
    class Meta:
        verbose_name = "Ejecución Manual de Tareas"
        verbose_name_plural = "Ejecuciones Manuales de Tareas"
class TaskExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_action_buttons']

    def get_action_buttons(self, obj):
        return format_html(
            '<a class="button" href="{}">Ejecutar ML y Scraping</a> '
            '<a class="button" href="{}">Ejecutar solo Scraping</a> '
            '<a class="button" href="{}">Verificar Dominios</a> '
            '<a class="button" href="{}">Entrenar ML</a> '
            '<a class="button" href="{}">Procesar CSV LinkedIn</a>',
            reverse('admin:execute-task', args=['ml_scraping']),
            reverse('admin:execute-task', args=['scraping']),
            reverse('admin:execute-task', args=['verify_domains']),
            reverse('admin:execute-task', args=['train_ml']),
            reverse('admin:execute-task', args=['process_csv'])
        )
    get_action_buttons.short_description = 'Acciones'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('execute-task/<str:task_name>/',
                 self.admin_site.admin_view(self.execute_task),
                 name='execute-task'),
        ]
        return custom_urls + urls

    @user_passes_test(lambda u: u.is_superuser)
    def execute_task(self, request, task_name):
        try:
            if task_name == 'ml_scraping':
                execute_ml_and_scraping.delay()
                messages.success(request, "Tarea ML y Scraping iniciada")
            elif task_name == 'scraping':
                ejecutar_scraping.delay()
                messages.success(request, "Tarea de Scraping iniciada")
            elif task_name == 'verify_domains':
                verificar_dominios_scraping.delay()
                messages.success(request, "Verificación de dominios iniciada")
            elif task_name == 'train_ml':
                train_ml_task.delay()
                messages.success(request, "Entrenamiento de ML iniciado")
            elif task_name == 'process_csv':
                csv_path = "/home/pablollh/connections.csv"  # Ajusta esta ruta
                process_linkedin_csv_task.delay(csv_path)
                messages.success(request, "Procesamiento de CSV LinkedIn iniciado")
        except Exception as e:
            messages.error(request, f"Error ejecutando tarea: {str(e)}")

        return redirect('admin:django_celery_beat_periodictask_changelist')