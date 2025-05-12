# /home/pablo/app/views/chatbot/admin/flow_views.py
#
# Vista para el módulo. Implementa la lógica de presentación y manejo de peticiones HTTP.

from django.contrib import admin
from django import forms
from django.db import models
from django.utils.html import format_html
from app.models import (
    BusinessUnit, ChatState, IntentPattern,
    StateTransition, IntentTransition, ContextCondition
)

class IntentPatternAdminForm(forms.ModelForm):
    class Meta:
        model = IntentPattern
        fields = '__all__'
        widgets = {
            'patterns': forms.Textarea(attrs={'rows': 5}),
            'responses': forms.Textarea(attrs={'rows': 5}),
            'business_units': forms.CheckboxSelectMultiple()
        }

class IntentPatternAdmin(admin.ModelAdmin):
    form = IntentPatternAdminForm
    list_display = ('name', 'priority', 'enabled', 'business_units_list')
    list_filter = ('enabled', 'business_units__name')
    search_fields = ('name', 'patterns')
    ordering = ('-priority',)

    def business_units_list(self, obj):
        return ", ".join([bu.name for bu in obj.business_units.all()])
    business_units_list.short_description = 'Unidades de Negocio'

class StateTransitionAdmin(admin.ModelAdmin):
    list_display = ('current_state', 'next_state', 'conditions', 'business_unit')
    list_filter = ('business_unit__name',)
    search_fields = ('current_state', 'next_state')
    ordering = ('business_unit__name', 'current_state')

class IntentTransitionAdmin(admin.ModelAdmin):
    list_display = ('current_intent', 'next_intent', 'conditions', 'business_unit')
    list_filter = ('business_unit__name',)
    search_fields = ('current_intent', 'next_intent')
    ordering = ('business_unit__name', 'current_intent')

class ContextConditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'value')
    list_filter = ('type',)
    search_fields = ('name', 'value')

admin.site.register(IntentPattern, IntentPatternAdmin)
admin.site.register(StateTransition, StateTransitionAdmin)
admin.site.register(IntentTransition, IntentTransitionAdmin)
admin.site.register(ContextCondition, ContextConditionAdmin)
