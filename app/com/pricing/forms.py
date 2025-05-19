# /home/pablo/app/com/pricing/forms.py
"""
Formularios para el módulo de pricing de Grupo huntRED®.

Este módulo contiene los formularios para gestionar propuestas, promociones especiales
y añadir empresas y contactos directamente desde la interfaz de usuario, facilitando 
la generación de propuestas para análisis de Talento 360°.
"""

from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.forms.widgets import TextInput, Textarea, Select, CheckboxInput, NumberInput
from django.db.models import Q

from app.models import (
    BusinessUnit, Opportunity, Contact, Company, 
    TalentAnalysisRequest, Promotion
)


class Talent360RequestForm(forms.ModelForm):
    """Formulario para solicitudes de Análisis de Talento 360°."""
    
    # Campos adicionales para crear una oportunidad si no existe
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        label="Empresa",
        required=True,
        widget=Select(attrs={'class': 'form-select select2'})
    )
    
    contact = forms.ModelChoiceField(
        queryset=Contact.objects.all(),
        label="Contacto",
        required=False,
        widget=Select(attrs={'class': 'form-select select2'})
    )
    
    business_unit = forms.ModelChoiceField(
        queryset=BusinessUnit.objects.all(),
        label="Business Unit",
        required=True,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    # Campo para código promocional
    promotion_code = forms.CharField(
        label="Código promocional (opcional)",
        required=False,
        max_length=20,
        widget=TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese código promocional si tiene uno'})
    )
    
    # Opción para generar propuesta automáticamente
    generate_proposal = forms.BooleanField(
        label="Generar propuesta automáticamente",
        required=False,
        initial=True,
        widget=CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Opción para enviar propuesta por email
    send_proposal_email = forms.BooleanField(
        label="Enviar propuesta por email al contacto",
        required=False,
        initial=True,
        widget=CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Campos específicos para el análisis de talento
    user_count = forms.IntegerField(
        label="Número de usuarios a evaluar",
        min_value=1,
        initial=10,
        widget=NumberInput(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        label="Descripción o notas",
        required=False,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = TalentAnalysisRequest
        fields = [
            'user_count', 'description', 'send_proposal_email',
            'status', 'priority'
        ]
        widgets = {
            'status': Select(attrs={'class': 'form-select'}),
            'priority': Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar queryset de contactos si se ha seleccionado una empresa
        if 'company' in self.data:
            try:
                company_id = int(self.data.get('company'))
                self.fields['contact'].queryset = Contact.objects.filter(company_id=company_id)
            except (ValueError, TypeError):
                pass
    
    def clean_promotion_code(self):
        """Validar que el código promocional sea válido."""
        code = self.cleaned_data.get('promotion_code')
        if not code:
            return code
        
        try:
            promotion = Promotion.objects.get(
                code=code, 
                is_active=True,
                valid_until__gte=timezone.now().date()
            )
            
            # Verificar que la promoción sea para análisis de talento
            if promotion.service_type != 'talent_analysis':
                raise ValidationError(
                    "Este código promocional no es válido para Análisis de Talento 360°."
                )
                
            # Verificar límite de usos
            if promotion.max_uses and promotion.times_used >= promotion.max_uses:
                raise ValidationError(
                    "Este código promocional ha alcanzado su límite máximo de usos."
                )
            
            return code
            
        except Promotion.DoesNotExist:
            raise ValidationError(
                "El código promocional no es válido o ha expirado."
            )
    
    def save(self, commit=True):
        instance = super().save(False)
        
        # Crear o actualizar oportunidad
        company = self.cleaned_data['company']
        contact = self.cleaned_data['contact']
        business_unit = self.cleaned_data['business_unit']
        
        # Buscar si ya existe una oportunidad para esta empresa/servicio
        try:
            opportunity = Opportunity.objects.get(
                company=company,
                service_type='talent_analysis',
                status__in=['new', 'in_progress']
            )
        except Opportunity.DoesNotExist:
            # Crear nueva oportunidad
            opportunity = Opportunity.objects.create(
                company=company,
                company_name=company.name,
                contact=contact,
                business_unit=business_unit,
                name=f"Análisis de Talento 360° - {company.name}",
                description=self.cleaned_data['description'] or f"Solicitud de Análisis de Talento 360° para {company.name}",
                service_type='talent_analysis',
                headcount=self.cleaned_data['user_count'],
                requires_proposal=True
            )
        
        # Asignar oportunidad a la solicitud
        instance.opportunity = opportunity
        
        if commit:
            instance.save()
            
        return instance


class CompanyForm(forms.ModelForm):
    """Formulario para crear/editar empresas."""
    
    class Meta:
        model = Company
        fields = ['name', 'legal_name', 'tax_id', 'industry', 'size', 'website', 'address', 'city', 'state', 'country']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'legal_name': TextInput(attrs={'class': 'form-control'}),
            'tax_id': TextInput(attrs={'class': 'form-control'}),
            'industry': Select(attrs={'class': 'form-select'}),
            'size': Select(attrs={'class': 'form-select'}),
            'website': TextInput(attrs={'class': 'form-control'}),
            'address': Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': TextInput(attrs={'class': 'form-control'}),
            'state': TextInput(attrs={'class': 'form-control'}),
            'country': Select(attrs={'class': 'form-select'}),
        }


class ContactForm(forms.ModelForm):
    """Formulario para crear/editar contactos."""
    
    class Meta:
        model = Contact
        fields = ['name', 'position', 'email', 'phone', 'company', 'is_primary']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'position': TextInput(attrs={'class': 'form-control'}),
            'email': TextInput(attrs={'class': 'form-control', 'type': 'email'}),
            'phone': TextInput(attrs={'class': 'form-control'}),
            'company': Select(attrs={'class': 'form-select select2'}),
            'is_primary': CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BulkAnalysisRequestForm(forms.Form):
    """Formulario para crear múltiples solicitudes de análisis en lote."""
    
    business_unit = forms.ModelChoiceField(
        queryset=BusinessUnit.objects.all(),
        label="Business Unit",
        required=True,
        widget=Select(attrs={'class': 'form-select'})
    )
    
    file = forms.FileField(
        label="Archivo CSV/Excel con empresas y contactos",
        help_text="El archivo debe contener las columnas: Empresa, Contacto, Email, Teléfono, Usuarios",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    promotion_code = forms.CharField(
        label="Código promocional (se aplicará a todas las solicitudes)",
        required=False,
        max_length=20,
        widget=TextInput(attrs={'class': 'form-control'})
    )
    
    generate_proposals = forms.BooleanField(
        label="Generar propuestas automáticamente",
        required=False,
        initial=True,
        widget=CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    send_emails = forms.BooleanField(
        label="Enviar propuestas por email a los contactos",
        required=False,
        initial=False,
        widget=CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PromotionCodeForm(forms.ModelForm):
    """Formulario para crear/editar códigos promocionales."""
    
    class Meta:
        model = Promotion
        fields = [
            'code', 'name', 'description', 'discount_percentage', 
            'service_type', 'valid_from', 'valid_until', 
            'max_uses', 'is_active'
        ]
        widgets = {
            'code': TextInput(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'}),
            'description': Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'discount_percentage': NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}),
            'service_type': Select(attrs={'class': 'form-select'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_uses': NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        
        if valid_from and valid_until and valid_from > valid_until:
            raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
        
        return cleaned_data
