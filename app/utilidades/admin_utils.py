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

class BusinessUnitFilter(SimpleListFilter):
    title = _('Unidad de Negocio')
    parameter_name = 'business_unit'

    def lookups(self, request, model_admin):
        return BusinessUnit.objects.values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(business_unit_id=self.value())
        return queryset

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
