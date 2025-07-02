from django import forms
from django.forms import ModelForm, Form
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from app.models import Person, Vacante, BusinessUnit
from app.ats.chatbot.workflow.assessments.succession_planning.models import (
    ProfessionalDNA, 
    SuccessionPlan, 
    SuccessionCandidate, 
    SuccessionReadinessAssessment
)


class SuccessionPlanForm(ModelForm):
    """Formulario para crear y editar planes de sucesión."""
    class Meta:
        model = SuccessionPlan
        fields = [
            'title', 'position', 'business_unit', 'status', 
            'start_date', 'target_date', 'key_requirements'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'key_requirements': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar posiciones y unidades de negocio según los permisos del usuario
        if user and not user.is_superuser:
            self.fields['position'].queryset = Vacante.objects.filter(
                Q(empresa__in=user.companies.all()) |
                Q(created_by=user)
            ).distinct()
            
            self.fields['business_unit'].queryset = BusinessUnit.objects.filter(
                id__in=user.business_units.values_list('id', flat=True)
            )
        
        # Agregar clases de Bootstrap a los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
            if field.required:
                field.label = f"{field.label} *"
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        target_date = cleaned_data.get('target_date')
        
        if start_date and target_date and start_date > target_date:
            self.add_error(
                'target_date',
                'La fecha objetivo debe ser posterior a la fecha de inicio.'
            )
        
        return cleaned_data


class SuccessionCandidateForm(ModelForm):
    """Formulario para agregar candidatos a un plan de sucesión."""
    candidate_email = forms.EmailField(
        label=_('Correo del Candidato'),
        required=True,
        help_text=_('Ingrese el correo electrónico del candidato')
    )
    
    class Meta:
        model = SuccessionCandidate
        fields = ['candidate_email']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)
        
        # Configurar el campo de búsqueda de candidatos
        self.fields['candidate_email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Buscar por correo electrónico...',
            'data-url': '/succession-planning/api/candidates/search/'
        })
    
    def clean_candidate_email(self):
        email = self.cleaned_data.get('candidate_email')
        
        # Verificar si el candidato existe
        try:
            candidate = Person.objects.get(email=email)
        except Person.DoesNotExist:
            raise forms.ValidationError(
                'No se encontró ningún candidato con este correo electrónico.'
            )
        
        # Verificar si el candidato ya está en el plan
        if self.plan and self.plan.candidates.filter(candidate=candidate).exists():
            raise forms.ValidationError(
                'Este candidato ya está incluido en el plan de sucesión.'
            )
        
        return candidate
    
    def save(self, commit=True):
        candidate = SuccessionCandidate()
        candidate.candidate = self.cleaned_data['candidate_email']
        candidate.plan = self.plan
        candidate.added_by = self.user
        
        if commit:
            candidate.save()
        
        return candidate


class ReadinessAssessmentForm(ModelForm):
    """Formulario para evaluar la preparación de un candidato."""
    class Meta:
        model = SuccessionReadinessAssessment
        fields = [
            'readiness_level', 'readiness_score', 
            'strengths', 'development_areas',
            'risk_factors', 'recommendations'
        ]
        widgets = {
            'strengths': forms.Textarea(attrs={'rows': 3}),
            'development_areas': forms.Textarea(attrs={'rows': 3}),
            'risk_factors': forms.Textarea(attrs={'rows': 3}),
            'recommendations': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.candidate = kwargs.pop('candidate', None)
        super().__init__(*args, **kwargs)
        
        # Configurar opciones para el nivel de preparación
        self.fields['readiness_level'].choices = [
            ('', '---------'),
            *SuccessionReadinessAssessment._meta.get_field('readiness_level').choices
        ]
        
        # Configurar el campo de puntuación
        self.fields['readiness_score'].widget.attrs.update({
            'min': 0,
            'max': 100,
            'step': 0.1
        })
        
        # Agregar clases de Bootstrap a los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
            if field.required:
                field.label = f"{field.label} *"
    
    def clean(self):
        cleaned_data = super().clean()
        readiness_level = cleaned_data.get('readiness_level')
        readiness_score = cleaned_data.get('readiness_score')
        
        # Validar que la puntuación sea coherente con el nivel de preparación
        if readiness_level and readiness_score is not None:
            score_ranges = {
                'ready_now': (80, 100),
                'one_to_two_years': (60, 80),
                'three_to_five_years': (40, 60),
                'not_feasible': (0, 40),
                'not_assessed': (0, 100)
            }
            
            min_score, max_score = score_ranges.get(readiness_level, (0, 100))
            
            if not (min_score <= readiness_score <= max_score):
                self.add_error(
                    'readiness_score',
                    f'La puntuación debe estar entre {min_score} y {max_score} para el nivel de preparación seleccionado.'
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        assessment = super().save(commit=False)
        assessment.candidate = self.candidate
        assessment.assessed_by = self.user
        
        if commit:
            assessment.save()
        
        return assessment


class GapAnalysisFilterForm(Form):
    """Formulario para filtrar el análisis de brechas."""
    business_unit = forms.ModelChoiceField(
        queryset=BusinessUnit.objects.all(),
        required=False,
        label=_('Unidad de Negocio'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    plan = forms.ModelChoiceField(
        queryset=SuccessionPlan.objects.all(),
        required=False,
        label=_('Plan de Sucesión'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar planes según los permisos del usuario
        if user and not user.is_superuser:
            self.fields['business_unit'].queryset = BusinessUnit.objects.filter(
                id__in=user.business_units.values_list('id', flat=True)
            )
            
            self.fields['plan'].queryset = SuccessionPlan.objects.filter(
                Q(created_by=user) |
                Q(business_unit__in=user.business_units.all())
            )
        
        # Hacer que los campos sean opcionales
        for field_name, field in self.fields.items():
            field.required = False
