# Ubicación del archivo: /home/pablo/app/admin.py
"""
Centro principal de configuración administrativa de Django para Grupo huntRED®.

Este módulo utiliza la estructura modular centralizada en app/config para 
registrar y configurar todas las clases de administración de Django del sistema.
"""

# Django Core Imports
from django.contrib import admin, messages
from django.db import models
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.template.loader import select_template
from django.template.response import TemplateResponse
from django import forms
from django.core.mail import send_mail
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _

# Module Imports
# Importaciones directas sin usar __init__.py
from app.com.chatbot.core.gpt import PromptManager, GPTHandler
from app.com.chatbot.core.intents_handler import detect_intents
from app.com.utils.scraping import enrich_with_gpt

# Utility Imports
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import json
import re

# Importing Admin modules from apps
from app.sexsi.admin import *

# Model Imports - Consolidated from admin.py and admin_config.py
from app.models import (
    ApiConfig, Application, Chat, ChatState,
    Division, DominioScraping, EnhancedMLProfile,
    EnhancedNetworkGamificationProfile, GptApi, InstagramAPI, Interview, Provider,
    Invitacion, MetaAPI, MessengerAPI, ModelTrainingLog,
    Person, ProfessionalDNA, QuarterlyInsight, RegistroScraping, ReporteScraping, Skill,
    SmtpConfig, SuccessionCandidate, SuccessionPlan, SuccessionReadinessAssessment, 
    TelegramAPI, Template, UserInteractionLog, Vacante, WhatsAppAPI,
    Worker, IntentPattern, StateTransition, IntentTransition, 
    WorkflowStage
)
from app.com.chatbot.components.chat_state_manager import ContextCondition

# Admin Mixins
from app.admin.mixins import EnhancedAdminMixin, BulkActionsMixin, DateRangeFilter, StatusFilter

# Service Imports
from app.com.chatbot.integrations.services import send_email, send_message

# Utility Imports for Specific Functionalidades
from app.com.utils.vacantes import VacanteManager
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import user_passes_test

# Importando el sistema centralizado de administración
from app.config.admin_registry import initialize_admin
from app.config.admin_base import BaseModelAdmin, TokenMaskingMixin, ReadOnlyAdminMixin

# Inicializando la configuración administrativa centralizada
# Esto registra todos los modelos con sus clases admin correspondientes
# y configura el sitio admin con los valores adecuados
initialize_admin(force_register=True)

# Las clases TokenMaskingMixin y ConfiguracionAdmin ahora están centralizadas
# en app/config/admin_base.py y app/config/admin_core.py respectivamente

# El registro de ConfiguracionAdmin ahora se maneja en app/config/admin_registry.py

# Importar el admin de BusinessUnit desde su módulo específico
from app.admin.business_unit import BusinessUnitAdmin

# Personalizar el admin site
admin.site.site_header = "Grupo huntRED® Admin"
admin.site.site_title = "Grupo huntRED® Admin"
admin.site.index_title = "Bienvenido al Panel de Administración"

# Clases de admin específicas que usan los mixins
class CustomAdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        try:
            # Obtener la Business Unit actual
            business_unit = BusinessUnit.objects.get(name=request.session.get('business_unit', 'huntRED'))
            context['business_unit'] = business_unit
        except BusinessUnit.DoesNotExist:
            context['business_unit'] = None
        return context

# Instanciar el sitio admin personalizado
admin_site = CustomAdminSite(name='myadmin')

# Registrar los modelos con el nuevo sitio admin
admin_site.register(BusinessUnit, BusinessUnitAdmin)

# Clases de admin específicas que usan los mixins
class VacanteAdmin(EnhancedAdminMixin, BulkActionsMixin):
    list_display = ADMIN_CONFIG['Vacante']['list_display']
    list_filter = ADMIN_CONFIG['Vacante']['list_filter']
    search_fields = ADMIN_CONFIG['Vacante']['search_fields']
    date_hierarchy = ADMIN_CONFIG['Vacante']['date_hierarchy']
    actions = ['bulk_change_status', 'bulk_export']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['business_unit'] = request.session.get('business_unit', 'huntRED')
        return super().changelist_view(request, extra_context=extra_context)

class ApplicationAdmin(EnhancedAdminMixin, BulkActionsMixin):
    list_display = ADMIN_CONFIG['Application']['list_display']
    list_filter = ADMIN_CONFIG['Application']['list_filter']
    search_fields = ADMIN_CONFIG['Application']['search_fields']
    date_hierarchy = ADMIN_CONFIG['Application']['date_hierarchy']
    actions = ['bulk_change_status', 'bulk_export']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['business_unit'] = request.session.get('business_unit', 'huntRED')
        return super().changelist_view(request, extra_context=extra_context)

class PersonAdmin(EnhancedAdminMixin, BulkActionsMixin):
    list_display = ADMIN_CONFIG['Person']['list_display']
    list_filter = ADMIN_CONFIG['Person']['list_filter']
    search_fields = ADMIN_CONFIG['Person']['search_fields']
    date_hierarchy = ADMIN_CONFIG['Person']['date_hierarchy']
    actions = ['bulk_change_status', 'bulk_export']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['business_unit'] = request.session.get('business_unit', 'huntRED')
        return super().changelist_view(request, extra_context=extra_context)

class ChatStateAdmin(EnhancedAdminMixin, BulkActionsMixin):
    list_display = ADMIN_CONFIG['ChatState']['list_display']
    list_filter = ADMIN_CONFIG['ChatState']['list_filter']
    search_fields = ADMIN_CONFIG['ChatState']['search_fields']
    date_hierarchy = ADMIN_CONFIG['ChatState']['date_hierarchy']
    actions = ['bulk_change_status', 'bulk_export']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['business_unit'] = request.session.get('business_unit', 'huntRED')
        return super().changelist_view(request, extra_context=extra_context)

class UserInteractionLogAdmin(EnhancedAdminMixin, BulkActionsMixin):
    list_display = ADMIN_CONFIG['UserInteractionLog']['list_display']
    list_filter = ADMIN_CONFIG['UserInteractionLog']['list_filter']
    search_fields = ADMIN_CONFIG['UserInteractionLog']['search_fields']
    date_hierarchy = ADMIN_CONFIG['UserInteractionLog']['date_hierarchy']
    actions = ['bulk_change_status', 'bulk_export']

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['business_unit'] = request.session.get('business_unit', 'huntRED')
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(DominioScraping)
class DominioScrapingAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'plataforma', 'verificado', 'email_scraping_enabled', 'valid_senders', 'ultima_verificacion', 'estado')
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
        from app.models import DominioScraping, Vacante, RegistroScraping
        def generate_dashboard_graph():
            total_dominios = DominioScraping.objects.count()
            total_vacantes = Vacante.objects.count()
            scraping_activo = DominioScraping.objects.filter(estado="definido").count()
            exitosos = RegistroScraping.objects.filter(estado='exitoso').count()
            fallidos = RegistroScraping.objects.filter(estado='fallido').count()
            parciales = RegistroScraping.objects.filter(estado='parcial').count()

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
            return grafico_base64

        from app.tasks import generate_dashboard_graph
        result = generate_dashboard_graph.delay()
        grafico_base64 = result.get(timeout=10)
        context = {
            'total_dominios': DominioScraping.objects.count(),
            'total_vacantes': Vacante.objects.count(),
            'scraping_activo': DominioScraping.objects.filter(estado="definido").count(),
            'grafico_vacantes': grafico_base64,
        }
        return render(request, 'admin/scraping_dashboard.html', context)

    def ejecutar_scraping_view(self, request, dominio_id):
        from app.models import DominioScraping
        from app.tasks import ejecutar_scraping
        try:
            dominio = DominioScraping.objects.get(pk=dominio_id)
            ejecutar_scraping.delay(dominio.id)
            self.message_user(request, f"Scraping iniciado para: {dominio.empresa} ({dominio.dominio}).", level=messages.SUCCESS)
        except DominioScraping.DoesNotExist:
            self.message_user(request, "El dominio especificado no existe.", level=messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Error al iniciar el scraping: {str(e)}.", level=messages.ERROR)
        return redirect("admin:app_dominioscraping_changelist")


    @admin.action(description="Ejecutar scraping para dominios seleccionados")
    def ejecutar_scraping_action(self, request, queryset):
        from app.tasks import ejecutar_scraping
        for dominio in queryset:
            ejecutar_scraping.delay(dominio.id)
        self.message_user(request, f"Scraping iniciado para {queryset.count()} dominios.")
    
    @admin.action(description="Ejecutar Email Scraping en JOBS para dominios seleccionados")
    def ejecutar_email_scraper_action(self, request, queryset):
        from app.tasks import execute_email_scraper
        for dominio in queryset:
            execute_email_scraper.delay(dominio.id)
        self.message_user(request, f"Scraping iniciado para {queryset.count()} dominios.")
    
    @admin.action(description="Marcar seleccionados como 'definidos'")
    def marcar_como_definido(self, request, queryset):
        queryset.update(estado="definido")
        self.message_user(request, f"{queryset.count()} dominios marcados como 'definidos'.")

    @admin.action(description="Desactivar dominios no válidos")
    def desactivar_dominios_invalidos(self, request, queryset):
        desactivados = queryset.update(estado="libre")
        self.message_user(request, f"{desactivados} dominios desactivados.")
@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'empresa', 'ubicacion', 'modalidad', 'activa', 'business_unit', 'fecha_publicacion', 'url_original')
    search_fields = ('titulo', 'empresa', 'ubicacion')
    list_filter = ('activa', 'modalidad', 'dominio_origen', 'business_unit')
    actions = ['toggle_activa_status', 'change_business_unit', 'enrich_with_gpt']

    fieldsets = (
        (None, {
            'fields': ('titulo', 'empresa', 'ubicacion', 'modalidad', 'activa', 'fecha_publicacion', 'business_unit', 'url_original')
        }),
        ('Detalles Adicionales', {
            'fields': ('descripcion', 'requisitos', 'skills_required', 'salario')
        }),
    )
    readonly_fields = ('fecha_scraping',)
    autocomplete_fields = ['business_unit', 'empresa']

    def save_model(self, request, obj, form, change):
        from app.com.chatbot.gpt import GPTHandler
        if not obj.descripcion:
            prompt = (
                f"Genera una descripción profesional para un puesto de trabajo con el título '{obj.titulo}' "
                f"en la empresa '{obj.empresa}' ubicado en '{obj.ubicacion}' con modalidad '{obj.modalidad}'."
            )
            try:
                gpt_handler = GPTHandler()
                import asyncio
                asyncio.run(gpt_handler.initialize())
                description = gpt_handler.generate_response_sync(prompt, business_unit=obj.business_unit)
                obj.descripcion = description
            except Exception as e:
                obj.descripcion = "No se pudo generar la descripción automáticamente."
                print(f"Error al generar descripción con GPT: {e}")
        super().save_model(request, obj, form, change)

    def toggle_activa_status(self, request, queryset):
        for vacante in queryset:
            vacante.activa = not vacante.activa
            vacante.save()
        self.message_user(request, "El estado de las vacantes seleccionadas ha sido actualizado.")
    toggle_activa_status.short_description = "Cambiar estado activa/inactiva"

    def change_business_unit(self, request, queryset):
        from django import forms
        from app.models import BusinessUnit

        class BusinessUnitForm(forms.Form):
            business_unit = forms.ModelChoiceField(queryset=BusinessUnit.objects.all(), label="Unidad de Negocio")

        if request.POST.get('post'):
            form = BusinessUnitForm(request.POST)
            if form.is_valid():
                new_business_unit = form.cleaned_data['business_unit']
                updated = queryset.update(business_unit=new_business_unit)
                self.message_user(request, f"Se actualizó la unidad de negocio de {updated} vacantes a {new_business_unit}.")
                return redirect(reverse('admin:app_vacante_changelist'))
        else:
            form = BusinessUnitForm()
            return self.render_change_form(request, context={'form': form, 'queryset': queryset}, add=False, change=True, form_url='')

    change_business_unit.short_description = "Cambiar unidad de negocio"

    def enrich_with_gpt(self, request, queryset):
        """Acción para enriquecer vacantes sin descripción usando GPT."""
        gpt_handler = GPTHandler()
        async_to_sync(gpt_handler.initialize)()
        for vacante in queryset:
            if not vacante.descripcion or vacante.descripcion == "No disponible":
                success = async_to_sync(enrich_with_gpt)(vacante, gpt_handler)
                if success:
                    self.message_user(request, f"Vacante '{vacante.titulo}' enriquecida con GPT.")
                else:
                    self.message_user(request, f"Error al enriquecer vacante '{vacante.titulo}' con GPT.")
            else:
                self.message_user(request, f"Vacante '{vacante.titulo}' ya tiene descripción, omitida.")
    
    enrich_with_gpt.short_description = "Enriquecer vacantes sin descripción con GPT"

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

# Base form for Person model
class PersonForm(forms.ModelForm):
    """Formulario base para el modelo Person con validación de email"""
    class Meta:
        model = Person
        fields = '__all__'

    def clean_email(self):
        # Validating email uniqueness except for internal emails
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@grupo-huntred.com') and Person.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya existe en nuestra base de datos.")
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
    list_display = ('nombre', 'apellido_paterno', 'apellido_materno', 'phone', 'email', 'job_search_status', 'fecha_creacion')
    search_fields = ('nombre', 'apellido_paterno', 'phone', 'email', 'fecha_creacion')
    list_filter = ('job_search_status', 'preferred_language', 'fecha_creacion')
    ordering = ['fecha_creacion', 'apellido_paterno']
    actions = ['export_as_csv', 'send_email', 'prepare_email']

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
                'hola@huntred.com',
                [person.email],
            )
        self.message_user(request, f"Correo enviado a {queryset.count()} personas.")

    # Acción personalizada para preparar el envío de correos
    @admin.action(description="Preparar envío de correos")
    def prepare_email(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "No hay candidatos seleccionados para enviar correos.", level=messages.WARNING)
            return

        # Guardar los IDs seleccionados en la sesión para procesarlos en la vista
        request.session['selected_candidates'] = list(queryset.values_list('id', flat=True))
        return redirect('admin:send_custom_email')

    # URL personalizada para la vista intermedia
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-custom-email/',
                self.admin_site.admin_view(self.send_custom_email),
                name='send_custom_email',
            ),
        ]
        return custom_urls + urls

    # Vista para la página intermedia
    def send_custom_email(self, request):
        if request.method == 'POST':
            # Procesar el formulario y enviar correos
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            business_unit_name = request.POST.get('business_unit', 'huntRED®')

            # Obtener candidatos seleccionados
            candidate_ids = request.session.get('selected_candidates', [])
            candidates = self.model.objects.filter(id__in=candidate_ids)
            errores = []
            enviados = 0

            # Enviar correos
            for person in candidates:
                if not person.email or '@' not in person.email:
                    errores.append(f"{person.nombre} (Email no válido)")
                    continue
                
                try:
                    resultado = send_email(
                        business_unit_name=business_unit_name,
                        subject=subject,
                        to_email=person.email,
                        body=message,
                    )
                    if resultado["status"] == "success":
                        enviados += 1
                    else:
                        errores.append(f"{person.nombre} ({resultado['message']})")
                except Exception as e:
                    errores.append(f"{person.nombre} ({str(e)})")

            # Mensajes al usuario
            self.message_user(request, f"Correo enviado a {enviados} personas.")
            if errores:
                self.message_user(request, f"Errores en {len(errores)} registros: {', '.join(errores)}", level=messages.WARNING)

            # Limpiar la sesión
            request.session.pop('selected_candidates', None)
            return redirect('..')  # Redirigir a la lista de candidatos

        # Obtener todas las unidades de negocio para el formulario
        business_units = BusinessUnit.objects.all()
        
        # Seleccionar la plantilla según la unidad de negocio
        selected_business_unit = request.GET.get('business_unit', 'huntRED®').lower()
        template_name = f"email/template_{selected_business_unit}.html"

        # Verificar si la plantilla existe; usar la predeterminada si no
        try:
            select_template([template_name])
        except:
            template_name = "admin/email/template_huntred.html"  # Default

        return render(request, template_name, {
            'business_units': business_units,
        })

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

# Succession Planning Admin
class SuccessionCandidateInline(admin.TabularInline):
    model = SuccessionCandidate
    extra = 0
    readonly_fields = ('readiness_level', 'readiness_score', 'view_candidate')
    fields = ('candidate', 'readiness_level', 'readiness_score', 'view_candidate')
    @admin.action(description="Marcar seleccionados como 'Contratado'")
    def change_status_to_hired(self, request, queryset):
        updated = queryset.update(status='hired')
        self.message_user(request, f"{updated} aplicaciones marcadas como 'Contratado'.")

@admin.register(ApiConfig)
class ApiConfigAdmin(TokenMaskingMixin, admin.ModelAdmin):
    token_fields = ['api_key', 'api_secret']
    list_display = (
        'is_global',
        'business_unit',
        'api_type',
        'category',
        'api_key',
        'api_secret',
        'enabled',
        'description',
        'created_at'
    )
    list_filter = (
        'is_global',
        'business_unit',
        'api_type',
        'category',
        'enabled',
        'created_at'
    )
    search_fields = (
        'business_unit__name',
        'api_type',
        'category',
        'api_key',
        'description'
    )
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    def api_key(self, obj):
        return format_html("<span style='color: #666;'>{}</span>", obj.api_key[:5] + "..." + obj.api_key[-5:])
    api_key.short_description = 'API Key'
    
    def api_secret(self, obj):
        return format_html("<span style='color: #666;'>{}</span>", obj.api_secret[:5] + "..." + obj.api_secret[-5:] if obj.api_secret else '-')
    api_secret.short_description = 'API Secret'
    
    def is_global(self, obj):
        return not bool(obj.business_unit)
    is_global.boolean = True
    is_global.short_description = 'Global'
    
    def get_queryset(self, request):
        """Agrupa por business unit y api_type"""
        queryset = super().get_queryset(request)
        return queryset.order_by('business_unit__name', 'api_type')
    
    def has_delete_permission(self, request, obj=None):
        """Previene la eliminación accidental de configuraciones"""
        return False
    
    def get_actions(self, request):
        """Elimina la acción de borrar"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_form(self, request, obj=None, **kwargs):
        """Personaliza el formulario para mostrar campos según sea global o no"""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.business_unit is None:
            form.base_fields['business_unit'].widget.attrs['disabled'] = 'disabled'
        return form

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

    def prompts_preview(self, obj):
        return "Sin prompts configurados"
    prompts_preview.short_description = "Vista previa de prompts"

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            GptApi.objects.filter(is_active=True).exclude(id=obj.id).update(is_active=False)
        super().save_model(request, obj, form, change)

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_endpoint', 'models_endpoint')
    search_fields = ('name',)

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
        from app.tasks import (
        execute_ml_and_scraping, ejecutar_scraping, verificar_dominios_scraping,
        train_ml_task, process_linkedin_csv_task
    )
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
                csv_path = "/home/pablo/connections.csv"  # Ajusta esta ruta
                process_linkedin_csv_task.delay(csv_path)
                messages.success(request, "Procesamiento de CSV LinkedIn iniciado")
        except Exception as e:
            messages.error(request, f"Error ejecutando tarea: {str(e)}")

        return redirect('admin:django_celery_beat_periodictask_changelist')


# Succession Planning Admin
class SuccessionCandidateInline(admin.TabularInline):
    model = SuccessionCandidate
    extra = 0
    readonly_fields = ('readiness_level', 'readiness_score', 'view_candidate')
    fields = ('candidate', 'readiness_level', 'readiness_score', 'view_candidate')
    
    def view_candidate(self, obj):
        if obj.id:
            url = reverse('admin:app_successioncandidate_change', args=[obj.id])
            return format_html('<a href="{}">Ver Detalles</a>', url)
        return ""
    view_candidate.short_description = "Acciones"


@admin.register(ProfessionalDNA)
class ProfessionalDNAAdmin(admin.ModelAdmin):
    list_display = ('person', 'potential', 'last_updated')
    list_filter = ('potential', 'last_updated')
    search_fields = ('person__nombre', 'person__email')
    readonly_fields = ('created_at', 'last_updated')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('person', 'potential', 'leadership_style')
        }),
        ('Habilidades y Competencias', {
            'fields': ('skills', 'competencies'),
            'classes': ('collapse',)
        }),
        ('Rasgos de Personalidad', {
            'fields': ('personality_traits', 'development_areas'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'last_updated', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.updated_by = request.user
        obj.save()


@admin.register(SuccessionPlan)
class SuccessionPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'business_unit', 'status', 'start_date', 'target_date')
    list_filter = ('status', 'business_unit', 'start_date', 'target_date')
    search_fields = ('title', 'position__titulo', 'position__empresa__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SuccessionCandidateInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'position', 'business_unit', 'status')
        }),
        ('Fechas', {
            'fields': ('start_date', 'target_date')
        }),
        ('Requisitos Clave', {
            'fields': ('key_requirements',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()


class SuccessionReadinessAssessmentInline(admin.TabularInline):
    model = SuccessionReadinessAssessment
    extra = 0
    readonly_fields = ('assessment_date', 'readiness_level', 'readiness_score', 'view_assessment')
    fields = ('assessment_date', 'readiness_level', 'readiness_score', 'assessed_by', 'view_assessment')
    
    def view_assessment(self, obj):
        if obj.id:
            url = reverse('admin:app_successionreadinessassessment_change', args=[obj.id])
            return format_html('<a href="{}">Ver Detalles</a>', url)
        return ""
    view_assessment.short_description = "Acciones"


@admin.register(SuccessionCandidate)
class SuccessionCandidateAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'plan', 'readiness_level', 'readiness_score', 'last_assessed')
    list_filter = ('readiness_level', 'plan__status', 'last_assessed')
    search_fields = ('candidate__nombre', 'plan__title', 'plan__position__titulo')
    readonly_fields = ('added_at', 'last_assessed', 'development_plan_progress')
    inlines = [SuccessionReadinessAssessmentInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('plan', 'candidate', 'added_by', 'added_at')
        }),
        ('Estado de Preparación', {
            'fields': ('readiness_level', 'readiness_score', 'last_assessed', 'development_plan_progress')
        }),
        ('Análisis', {
            'fields': ('key_gaps', 'development_plan', 'risk_factors'),
            'classes': ('collapse',)
        }),
    )
    
    def development_plan_progress(self, obj):
        progress = obj.get_development_plan_progress()
        color = "green" if progress > 66 else "orange" if progress > 33 else "red"
        return mark_safe(
            f'<div style="width:100%; background:#f0f0f0; border-radius:5px;">'
            f'<div style="width:{progress}%; background:{color}; color:white; text-align:center; border-radius:5px;">'
            f'{progress}%</div></div>'
        )
    development_plan_progress.short_description = 'Progreso del Plan de Desarrollo'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.added_by = request.user
        obj.save()


@admin.register(SuccessionReadinessAssessment)
class SuccessionReadinessAssessmentAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'assessment_date', 'readiness_level', 'readiness_score', 'assessed_by')
    list_filter = ('readiness_level', 'assessment_date')
    search_fields = ('candidate__candidate__nombre', 'candidate__plan__title')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('candidate', 'assessed_by', 'assessment_date')
        }),
        ('Resultados', {
            'fields': ('readiness_level', 'readiness_score')
        }),
        ('Análisis Detallado', {
            'fields': ('strengths', 'development_areas', 'risk_factors'),
            'classes': ('collapse',)
        }),
        ('Recomendaciones', {
            'fields': ('recommendations',)
        }),
        ('Auditoría', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.assessed_by = request.user
        obj.save()