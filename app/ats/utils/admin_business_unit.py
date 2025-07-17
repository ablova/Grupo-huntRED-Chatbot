from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django import forms

from app.models import BusinessUnit, Application

class BusinessUnitAdminForm(forms.ModelForm):
    class Meta:
        model = BusinessUnit
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BusinessUnitAdmin(admin.ModelAdmin):
    form = BusinessUnitAdminForm
    list_display = (
        'id',
        'name',
        'location',
        'industry',
        'active_vacancies',
        'applications_count',
        'success_rate',
        'priority',
        'status',
    )
    list_filter = (
        'location',
        'industry',
        'status',
        'created_at',
    )
    search_fields = (
        'name',
        'location',
        'industry',
        'description',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'active_vacancies',
        'applications_count',
        'success_rate',
        'priority',
        'status',
    )
    ordering = ('name',)

    def active_vacancies(self, obj):
        return obj.vacancies.filter(status='open').count()
    active_vacancies.short_description = _('Vacantes Activas')

    def applications_count(self, obj):
        return Application.objects.filter(vacancy__business_unit=obj).count()
    applications_count.short_description = _('Solicitudes')

    def success_rate(self, obj):
        total = Application.objects.filter(vacancy__business_unit=obj).count()
        success = Application.objects.filter(vacancy__business_unit=obj, status='hired').count()
        rate = success / total * 100 if total else 0
        return f"{rate:.2f}%"
    success_rate.short_description = _('Tasa de Éxito')

    def priority(self, obj):
        if obj.priority == 'high':
            return format_html('<span class="text-danger">Alta</span>')
        elif obj.priority == 'medium':
            return format_html('<span class="text-warning">Media</span>')
        return format_html('<span class="text-success">Baja</span>')
    priority.short_description = _('Prioridad')

    def status(self, obj):
        if obj.status == 'active':
            return format_html('<span class="text-success">Activa</span>')
        elif obj.status == 'inactive':
            return format_html('<span class="text-danger">Inactiva</span>')
        return format_html('<span class="text-warning">En Espera</span>')
    status.short_description = _('Estado')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            active_vacancies_count=Count('vacancies', filter=Q(vacancies__status='open'))
        )

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            total_units = qs.count()
            active_units = qs.filter(status='active').count()
            success_rate = qs.filter(vacancies__applications__status='hired').distinct().count() / total_units * 100 if total_units else 0

            extra_context = extra_context or {}
            extra_context.update({
                'total_units': total_units,
                'active_units': active_units,
                'success_rate': f"{success_rate:.2f}%",
            })
        except (AttributeError, KeyError):
            pass
        return response

# Comentado para evitar conflicto con app/admin/business_unit.py
# admin.site.register(BusinessUnit, BusinessUnitAdmin)
