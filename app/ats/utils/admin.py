from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from app.models import (
    Person,
    Vacante,
    BusinessUnit,
    Application,
    IntentPattern,
    StateTransition,
    ChatState,
    UserInteractionLog,
    Chat,
    DominioScraping,
    RegistroScraping,
    ConfiguracionBU,
    GptApi,
    Worker
)

from app.ats.utils.admin_business_unit import BusinessUnitFilter

class StateFilter(SimpleListFilter):
    title = _('Estado')
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Activo')),
            ('completed', _('Completado')),
            ('rejected', _('Rechazado')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status__in=['applied', 'screening', 'interview'])
        elif self.value() == 'completed':
            return queryset.filter(status='hired')
        elif self.value() == 'rejected':
            return queryset.filter(status='rejected')
        return queryset

class ApplicationAdminForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = '__all__'
        widgets = {
            'person': forms.Select(attrs={'class': 'form-control'}),
            'vacancy': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ApplicationAdmin(admin.ModelAdmin):
    form = ApplicationAdminForm
    list_display = (
        'id',
        'candidate_link',
        'vacancy_link',
        'business_unit',
        'status',
        'created_at',
        'updated_at',
        'duration',
        'success_rate',
        'state_transitions',
    )
    list_filter = (BusinessUnitFilter, StateFilter, 'created_at')
    search_fields = (
        'person__nombre',
        'vacancy__titulo',
        'vacancy__business_unit__name',
        'status',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'duration',
        'success_rate',
        'state_transitions',
    )
    ordering = ('-created_at',)

    def candidate_link(self, obj):
        url = reverse('admin:app_person_change', args=[obj.person.id])
        return format_html('<a href="{}">{}</a>', url, obj.person.nombre)
    candidate_link.short_description = _('Candidato')

    def vacancy_link(self, obj):
        url = reverse('admin:app_vacante_change', args=[obj.vacancy.id])
        return format_html('<a href="{}">{}</a>', url, obj.vacancy.titulo)
    vacancy_link.short_description = _('Vacante')

    def business_unit(self, obj):
        return obj.vacancy.business_unit.name
    business_unit.short_description = _('Unidad de Negocio')

    def duration(self, obj):
        if obj.created_at and obj.updated_at:
            delta = obj.updated_at - obj.created_at
            return f"{delta.days} días"
        return "-"
    duration.short_description = _('Duración')

    def success_rate(self, obj):
        if obj.status == 'hired':
            return format_html('<span class="text-success">100%</span>')
        elif obj.status == 'rejected':
            return format_html('<span class="text-danger">0%</span>')
        return "-"
    success_rate.short_description = _('Tasa de Éxito')

    def state_transitions(self, obj):
        transitions = obj.get_state_transitions()
        if transitions:
            return format_html(
                '<div style="max-height: 150px; overflow-y: auto;">{}</div>',
                '<br>'.join(transitions)
            )
        return "-"
    state_transitions.short_description = _('Transiciones de Estado')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            state_transitions_count=Count('state_transitions')
        )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_applications = qs.count()
            success_rate = qs.filter(status='hired').count() / total_applications * 100 if total_applications else 0
            average_duration = qs.filter(updated_at__isnull=False, created_at__isnull=False).annotate(
                duration=(
                    (lambda x: x.updated_at - x.created_at)
                )
            ).aggregate(avg_duration=('duration'))['avg_duration']

            extra_context = extra_context or {}
            extra_context.update({
                'total_applications': total_applications,
                'success_rate': f"{success_rate:.2f}%",
                'average_duration': str(average_duration) if average_duration else "-",
            })
        except (AttributeError, KeyError):
            pass
        return response

admin.site.register(Application, ApplicationAdmin)

class PersonAdminForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    list_display = (
        'id',
        'nombre',
        'email',
        'phone',
        'applications_count',
        'success_rate',
        'last_application',
        'status',
        'skills_summary',
    )
    list_filter = (
        'applications__status',
        'applications__vacancy__business_unit__name',
        'created_at',
    )
    search_fields = (
        'nombre',
        'email',
        'phone',
        'skills',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'applications_count',
        'success_rate',
        'last_application',
        'status',
        'skills_summary',
    )
    ordering = ('nombre',)

    def applications_count(self, obj):
        return obj.applications.count()
    applications_count.short_description = _('Solicitudes')

    def success_rate(self, obj):
        total = obj.applications.count()
        success = obj.applications.filter(status='hired').count()
        rate = success / total * 100 if total else 0
        return f"{rate:.2f}%"
    success_rate.short_description = _('Tasa de Éxito')

    def last_application(self, obj):
        last_app = obj.applications.order_by('-updated_at').first()
        if last_app:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_application_change', args=[last_app.id]),
                last_app.vacancy.titulo
            )
        return "-"
    last_application.short_description = _('Última Solicitud')

    def status(self, obj):
        last_app = obj.applications.order_by('-updated_at').first()
        if last_app:
            status = last_app.status
            if status == 'hired':
                return format_html('<span class="text-success">Contratado</span>')
            elif status == 'rejected':
                return format_html('<span class="text-danger">Rechazado</span>')
            return status
        return "-"
    status.short_description = _('Estado')

    def skills_summary(self, obj):
        skills = obj.skills.split(',') if obj.skills else []
        return format_html(
            '<div style="max-height: 100px; overflow-y: auto;">{}</div>',
            '<br>'.join(skills)
        )
    skills_summary.short_description = _('Habilidades')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            applications_count=Count('applications')
        )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_persons = qs.count()
            active_persons = qs.filter(applications__status__in=['applied', 'screening', 'interview']).distinct().count()
            success_rate = qs.filter(applications__status='hired').distinct().count() / total_persons * 100 if total_persons else 0

            extra_context = extra_context or {}
            extra_context.update({
                'total_persons': total_persons,
                'active_persons': active_persons,
                'success_rate': f"{success_rate:.2f}%",
            })
        except (AttributeError, KeyError):
            pass
        return response

admin.site.register(Person, PersonAdmin)

class VacanteAdminForm(forms.ModelForm):
    class Meta:
        model = Vacante
        fields = '__all__'
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'business_unit': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control'}),
            'required_skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class VacanteAdmin(admin.ModelAdmin):
    form = VacanteAdminForm
    list_display = (
        'id',
        'titulo',
        'business_unit',
        'location',
        'salary_range',
        'status',
        'applications_count',
        'success_rate',
        'last_application',
        'priority',
        'skills_summary',
    )
    list_filter = (
        BusinessUnitFilter,
        'status',
        'location',
        'created_at',
    )
    search_fields = (
        'titulo',
        'business_unit__name',
        'location',
        'required_skills',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'applications_count',
        'success_rate',
        'last_application',
        'priority',
        'skills_summary',
    )
    ordering = ('-priority', 'titulo')

    def applications_count(self, obj):
        return obj.applications.count()
    applications_count.short_description = _('Solicitudes')

    def success_rate(self, obj):
        total = obj.applications.count()
        success = obj.applications.filter(status='hired').count()
        rate = success / total * 100 if total else 0
        return f"{rate:.2f}%"
    success_rate.short_description = _('Tasa de Éxito')

    def last_application(self, obj):
        last_app = obj.applications.order_by('-updated_at').first()
        if last_app:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:app_application_change', args=[last_app.id]),
                last_app.person.nombre
            )
        return "-"
    last_application.short_description = _('Última Solicitud')

    def priority(self, obj):
        if obj.priority == 'high':
            return format_html('<span class="text-danger">Alta</span>')
        elif obj.priority == 'medium':
            return format_html('<span class="text-warning">Media</span>')
        return format_html('<span class="text-success">Baja</span>')
    priority.short_description = _('Prioridad')

    def skills_summary(self, obj):
        skills = obj.required_skills.split(',') if obj.required_skills else []
        return format_html(
            '<div style="max-height: 100px; overflow-y: auto;">{}</div>',
            '<br>'.join(skills)
        )
    skills_summary.short_description = _('Habilidades Requeridas')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            applications_count=Count('applications')
        )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_vacancies = qs.count()
            open_vacancies = qs.filter(status='open').count()
            success_rate = qs.filter(applications__status='hired').distinct().count() / total_vacancies * 100 if total_vacancies else 0

            extra_context = extra_context or {}
            extra_context.update({
                'total_vacancies': total_vacancies,
                'open_vacancies': open_vacancies,
                'success_rate': f"{success_rate:.2f}%",
            })
        except (AttributeError, KeyError):
            pass
        return response

admin.site.register(Vacante, VacanteAdmin)


