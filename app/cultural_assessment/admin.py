"""
Administración de evaluaciones culturales para Grupo huntRED®.

Proporciona interfaces administrativas para invitación, carga y gestión
de evaluaciones culturales, optimizado siguiendo reglas globales.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.conf import settings
from django import forms
from django.db import transaction
from django.contrib import messages
import csv
import io
from datetime import timedelta
import logging

from app.models import (
    CulturalAssessment, OrganizationalCulture, CulturalDimension, 
    CulturalValue, CulturalProfile, CulturalReport, Person, BusinessUnit, Organization, Team, Department
)


logger = logging.getLogger(__name__)

class CulturalAssessmentUploadForm(forms.Form):
    """Formulario para cargar participantes a una evaluación cultural"""
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label="Organización",
        help_text="Seleccione la organización para la evaluación cultural"
    )
    business_unit = forms.ModelChoiceField(
        queryset=BusinessUnit.objects.filter(active=True),
        label="Unidad de negocio",
        help_text="Seleccione la unidad de negocio que gestiona la evaluación"
    )
    csv_file = forms.FileField(
        label="Archivo CSV",
        help_text="Formato: nombre,apellido,correo,teléfono,cargo,departamento,equipo"
    )
    send_invitations = forms.BooleanField(
        label="Enviar invitaciones inmediatamente",
        required=False,
        initial=True
    )
    expiration_days = forms.IntegerField(
        label="Días para expiración",
        initial=14,
        min_value=1,
        max_value=90,
        help_text="Número de días hasta que expire la invitación"
    )

class CulturalDimensionAdmin(admin.ModelAdmin):
    """Administración de dimensiones culturales"""
    list_display = ('name', 'category', 'business_unit', 'weight', 'active')
    list_filter = ('category', 'business_unit', 'active')
    search_fields = ('name', 'description')
    ordering = ('category', 'name')

class CulturalValueAdmin(admin.ModelAdmin):
    """Administración de valores culturales"""
    list_display = ('name', 'dimension', 'weight', 'active')
    list_filter = ('dimension', 'dimension__category', 'active')
    search_fields = ('name', 'description', 'positive_statement')
    ordering = ('dimension', 'name')

class CulturalAssessmentAdmin(admin.ModelAdmin):
    """Administración de evaluaciones culturales"""
    list_display = ('person_name', 'organization_name', 'status', 'completion_percentage', 'risk_indicator', 'started_at')
    list_filter = ('status', 'organization', 'team', 'department')
    search_fields = ('person__first_name', 'person__last_name', 'person__email')
    readonly_fields = ('started_at', 'completed_at', 'last_interaction')
    ordering = ('-last_interaction',)
    actions = ['send_invitation_reminder', 'generate_access_links', 'mark_as_expired']
    list_per_page = 50
    
    # Añadir botones de acción personalizados
    change_list_template = 'admin/cultural_assessment_change_list.html'
    
    def person_name(self, obj):
        return f"{obj.person.first_name} {obj.person.last_name}"
    person_name.short_description = "Participante"
    
    def organization_name(self, obj):
        return obj.organization.name
    organization_name.short_description = "Organización"
    
    def risk_indicator(self, obj):
        """Muestra un indicador visual de factor de riesgo"""
        if obj.risk_factor is None:
            return "N/A"
        
        risk = obj.risk_factor
        if risk < 20:
            color = "green"
            label = "Bajo"
        elif risk < 50:
            color = "orange"
            label = "Medio"
        else:
            color = "red"
            label = "Alto"
            
        return format_html(
            '<span style="color:white; background-color:{}; padding:3px 10px; border-radius:10px;">{} ({}%)</span>',
            color, label, int(risk)
        )
    risk_indicator.short_description = "Riesgo"
    
    def send_invitation_reminder(self, request, queryset):
        """Envía recordatorios de invitación a los participantes seleccionados"""
        invited_count = 0
        for assessment in queryset:
            if assessment.status in ['invited', 'pending']:
                # Regenerar token si es necesario
                if not assessment.invitation_token:
                    assessment.generate_invitation_token()
                
                # Enviar recordatorio
                from app.tasks.notifications import send_cultural_invitation_task
                send_cultural_invitation_task.delay(
                    assessment_id=assessment.id,
                    is_reminder=True
                )
                invited_count += 1
        
        self.message_user(
            request, 
            f"Se enviaron {invited_count} recordatorios de invitación.",
            messages.SUCCESS
        )
    send_invitation_reminder.short_description = "Enviar recordatorio de invitación"
    
    def generate_access_links(self, request, queryset):
        """Genera enlaces de acceso para participantes seleccionados"""
        links = []
        for assessment in queryset:
            if not assessment.invitation_token:
                assessment.generate_invitation_token()
            
            base_url = settings.BASE_URL or 'https://app.grupohr.io'
            access_url = f"{base_url}/cultural-assessment/{assessment.invitation_token}/"
            links.append((assessment.person.email, access_url))
        
        # Renderizar template con enlaces
        context = {
            'title': 'Enlaces de acceso a evaluación cultural',
            'links': links,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/cultural_assessment_links.html', context)
    generate_access_links.short_description = "Generar enlaces de acceso"
    
    def mark_as_expired(self, request, queryset):
        """Marca evaluaciones seleccionadas como expiradas"""
        expired_count = queryset.filter(status__in=['invited', 'pending']).update(
            status='expired'
        )
        self.message_user(
            request,
            f"Se marcaron {expired_count} evaluaciones como expiradas.",
            messages.SUCCESS
        )
    mark_as_expired.short_description = "Marcar como expiradas"
    
    # Añadir URLs personalizadas para el admin
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'upload-participants/',
                self.admin_site.admin_view(self.upload_participants_view),
                name='cultural-assessment-upload'
            ),
        ]
        return custom_urls + urls
    
    def upload_participants_view(self, request):
        """Vista para cargar participantes desde CSV"""
        # Inicializar el formulario
        form = CulturalAssessmentUploadForm()
        
        if request.method == 'POST':
            form = CulturalAssessmentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                # Procesar el archivo CSV
                try:
                    csv_file = request.FILES['csv_file']
                    decoded_file = csv_file.read().decode('utf-8')
                    io_string = io.StringIO(decoded_file)
                    reader = csv.reader(io_string)
                    next(reader)  # Saltar la cabecera
                    
                    organization = form.cleaned_data['organization']
                    business_unit = form.cleaned_data['business_unit']
                    send_invitations = form.cleaned_data['send_invitations']
                    expiration_days = form.cleaned_data['expiration_days']
                    
                    # Obtener o crear el perfil cultural organizacional
                    org_culture, created = OrganizationalCulture.objects.get_or_create(
                        organization=organization,
                        business_unit=business_unit,
                        is_current=True,
                        defaults={
                            'status': 'not_started',
                            'completion_percentage': 0
                        }
                    )
                    
                    # Procesar cada fila del CSV
                    assessments_created = 0
                    with transaction.atomic():
                        for row in reader:
                            if len(row) < 3:  # Al menos nombre, apellido y email
                                continue
                                
                            first_name, last_name, email = row[0], row[1], row[2]
                            phone = row[3] if len(row) > 3 else None
                            position = row[4] if len(row) > 4 else None
                            dept_name = row[5] if len(row) > 5 else None
                            team_name = row[6] if len(row) > 6 else None
                            
                            # Crear o actualizar persona
                            person, person_created = Person.objects.get_or_create(
                                email=email,
                                defaults={
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'phone': phone,
                                    'position': position
                                }
                            )
                            
                            # Actualizar datos si la persona ya existía
                            if not person_created:
                                person.first_name = first_name
                                person.last_name = last_name
                                if phone:
                                    person.phone = phone
                                if position:
                                    person.position = position
                                person.save()
                            
                            # Obtener o crear departamento y equipo
                            department = None
                            if dept_name:
                                department, _ = Department.objects.get_or_create(
                                    name=dept_name,
                                    organization=organization,
                                    defaults={'active': True}
                                )
                            
                            team = None
                            if team_name:
                                team, _ = Team.objects.get_or_create(
                                    name=team_name,
                                    organization=organization,
                                    department=department,
                                    defaults={'active': True}
                                )
                            
                            # Crear evaluación cultural
                            assessment, created = CulturalAssessment.objects.get_or_create(
                                person=person,
                                organization=organization,
                                organizational_culture=org_culture,
                                defaults={
                                    'business_unit': business_unit,
                                    'department': department,
                                    'team': team,
                                    'status': 'invited',
                                    'completion_percentage': 0,
                                    'expiration_date': timezone.now() + timedelta(days=expiration_days)
                                }
                            )
                            
                            if created:
                                assessments_created += 1
                                # Generar token de invitación
                                assessment.generate_invitation_token()
                                
                                # Enviar invitación si se solicitó
                                if send_invitations:
                                    from app.tasks.notifications import send_cultural_invitation_task
                                    send_cultural_invitation_task.delay(assessment_id=assessment.id)
                    
                    self.message_user(
                        request,
                        f"Se crearon {assessments_created} evaluaciones culturales para {organization.name}.",
                        messages.SUCCESS
                    )
                    return redirect('admin:models_cultural_culturalassessment_changelist')
                except Exception as e:
                    logger.error(f"Error procesando CSV: {str(e)}")
                    self.message_user(
                        request,
                        f"Error procesando el archivo: {str(e)}",
                        messages.ERROR
                    )
        
        # Renderizar el formulario
        context = {
            'form': form,
            'title': 'Cargar participantes para evaluación cultural',
        }
        return TemplateResponse(request, 'admin/cultural_assessment_upload.html', context)

class OrganizationalCultureAdmin(admin.ModelAdmin):
    """Administración de perfiles culturales organizacionales"""
    list_display = ('organization', 'business_unit', 'status', 'completion_percentage', 'is_current', 'updated_at')
    list_filter = ('status', 'business_unit', 'is_current')
    search_fields = ('organization__name',)
    readonly_fields = ('created_at', 'updated_at', 'last_assessment_date')
    ordering = ('-is_current', '-updated_at')
    actions = ['generate_preliminary_report', 'generate_complete_report']
    
    def generate_preliminary_report(self, request, queryset):
        """Genera un reporte preliminar (80% de datos)"""
        for culture in queryset:
            if culture.completion_percentage >= 80:
                from app.tasks.reports import generate_cultural_report_task
                generate_cultural_report_task.delay(
                    organizational_culture_id=culture.id,
                    report_type='preliminary',
                    created_by_id=request.user.id if request.user.is_authenticated else None
                )
                self.message_user(
                    request,
                    f"Generando reporte preliminar para {culture.organization.name}.",
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"{culture.organization.name} no tiene suficientes datos (mínimo 80%).",
                    messages.WARNING
                )
    generate_preliminary_report.short_description = "Generar reporte preliminar (80%)"
    
    def generate_complete_report(self, request, queryset):
        """Genera un reporte completo (100% de datos)"""
        for culture in queryset:
            if culture.status == 'complete':
                from app.tasks.reports import generate_cultural_report_task
                generate_cultural_report_task.delay(
                    organizational_culture_id=culture.id,
                    report_type='complete',
                    created_by_id=request.user.id if request.user.is_authenticated else None
                )
                self.message_user(
                    request,
                    f"Generando reporte completo para {culture.organization.name}.",
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request,
                    f"{culture.organization.name} no tiene datos completos.",
                    messages.WARNING
                )
    generate_complete_report.short_description = "Generar reporte completo (100%)"

class CulturalReportAdmin(admin.ModelAdmin):
    """Administración de reportes culturales"""
    list_display = ('title', 'organization', 'report_type', 'report_date', 'participant_count', 'created_at')
    list_filter = ('report_type', 'organization', 'report_date')
    search_fields = ('title', 'organization__name')
    readonly_fields = ('created_at', 'report_date', 'participant_count', 'completion_percentage')
    ordering = ('-report_date',)
    
    actions = ['regenerate_report_pdf', 'share_report_with_organization']
    
    def regenerate_report_pdf(self, request, queryset):
        """Regenera el PDF de los reportes seleccionados"""
        for report in queryset:
            from app.tasks.reports import generate_cultural_report_pdf_task
            generate_cultural_report_pdf_task.delay(report_id=report.id)
            
        self.message_user(
            request,
            f"Se han programado {queryset.count()} reportes para regeneración de PDF.",
            messages.SUCCESS
        )
    regenerate_report_pdf.short_description = "Regenerar PDF del reporte"
    
    def share_report_with_organization(self, request, queryset):
        """Comparte los reportes seleccionados con la organización"""
        shared_count = 0
        for report in queryset:
            if not report.is_public:
                report.is_public = True
                if not report.access_token:
                    report.generate_access_token()
                report.save()
                
                # Enviar notificación al contacto principal
                from app.tasks.notifications import send_report_notification_task
                send_report_notification_task.delay(report_id=report.id)
                
                shared_count += 1
        
        self.message_user(
            request,
            f"Se compartieron {shared_count} reportes con las organizaciones correspondientes.",
            messages.SUCCESS
        )
    share_report_with_organization.short_description = "Compartir con organización"

# Registrar los modelos en el admin
admin.site.register(CulturalDimension, CulturalDimensionAdmin)
admin.site.register(CulturalValue, CulturalValueAdmin)
admin.site.register(CulturalAssessment, CulturalAssessmentAdmin)
admin.site.register(OrganizationalCulture, OrganizationalCultureAdmin)
admin.site.register(CulturalReport, CulturalReportAdmin)
