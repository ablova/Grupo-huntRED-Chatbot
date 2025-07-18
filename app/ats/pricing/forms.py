# app/ats/pricing/forms.py
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
    BusinessUnit, Opportunity, Person, Company, 
    TalentAnalysisRequest
)
from app.ats.pricing.models import (
    PricingStrategy, PricePoint, DiscountRule, ReferralFee,
    PricingCalculation, PricingPayment, PricingProposal,
    ProposalSection, ProposalTemplate
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
        queryset=Person.objects.all(),
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
        label="Descripción adicional",
        required=False,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    class Meta:
        model = TalentAnalysisRequest
        fields = [
            'user_count', 'description', 'send_proposal_email',
            'status'
        ]
        widgets = {
            'status': Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar queryset de contactos si se ha seleccionado una empresa
        if 'company' in self.data:
            try:
                company_id = int(self.data.get('company'))
                self.fields['contact'].queryset = Person.objects.filter(company_id=company_id)
            except (ValueError, TypeError):
                pass
    
    def clean_promotion_code(self):
        """Validar que el código promocional sea válido."""
        code = self.cleaned_data.get('promotion_code')
        if not code:
            return code
        
        # Por ahora, simplemente validar que el código no esté vacío
        # En el futuro, se puede implementar validación contra cupones de descuento
        if len(code) < 3:
            raise ValidationError("El código promocional debe tener al menos 3 caracteres.")
        
        return code
    
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
    
    signer = forms.ModelChoiceField(queryset=Person.objects.all(), required=False, label="Firmante de propuesta")
    payment_responsible = forms.ModelChoiceField(queryset=Person.objects.all(), required=False, label="Responsable de pagos")
    fiscal_responsible = forms.ModelChoiceField(queryset=Person.objects.all(), required=False, label="Responsable fiscal")
    process_responsible = forms.ModelChoiceField(queryset=Person.objects.all(), required=False, label="Responsable del proceso")
    report_invitees = forms.ModelMultipleChoiceField(queryset=Person.objects.all(), required=False, label="Invitados a reportes")
    notification_preferences = forms.CharField(required=False, label="Preferencias de notificación", widget=Textarea(attrs={'class': 'form-control', 'rows': 2}))

    class Meta:
        model = Company
        # TODO: Temporal - campos fiscales deshabilitados hasta que se apliquen las migraciones
        try:
            # Verificar si los campos fiscales existen en el modelo
            Company._meta.get_field('tax_id')
            fields = ['name', 'legal_name', 'tax_id', 'industry', 'size', 'website', 'address', 'city', 'state', 'country',
                      'signer', 'payment_responsible', 'fiscal_responsible', 'process_responsible', 'report_invitees', 'notification_preferences']
            widgets = {
                'name': TextInput(attrs={'class': 'form-control'}),
                'legal_name': TextInput(attrs={'class': 'form-control'}),
                'tax_id': TextInput(attrs={'class': 'form-control'}),
                'industry': TextInput(attrs={'class': 'form-control'}),
                'size': TextInput(attrs={'class': 'form-control'}),
                'website': TextInput(attrs={'class': 'form-control'}),
                'address': Textarea(attrs={'class': 'form-control', 'rows': 2}),
                'city': TextInput(attrs={'class': 'form-control'}),
                'state': TextInput(attrs={'class': 'form-control'}),
                'country': TextInput(attrs={'class': 'form-control'}),
            }
        except:
            # Si los campos fiscales no existen, usar solo campos básicos
            fields = ['name', 'industry', 'size', 'website',
                      'signer', 'payment_responsible', 'fiscal_responsible', 'process_responsible', 'report_invitees', 'notification_preferences']
            widgets = {
                'name': TextInput(attrs={'class': 'form-control'}),
                'industry': TextInput(attrs={'class': 'form-control'}),
                'size': TextInput(attrs={'class': 'form-control'}),
                'website': TextInput(attrs={'class': 'form-control'}),
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


class ContactForm(forms.ModelForm):
    """Formulario para crear/editar contactos."""
    
    class Meta:
        model = Person
        fields = ['nombre', 'apellido_paterno', 'apellido_materno', 'email', 'phone']
        widgets = {
            'nombre': TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido_paterno': TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido paterno'}),
            'apellido_materno': TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido materno'}),
            'email': TextInput(attrs={'class': 'form-control', 'type': 'email', 'placeholder': 'Correo electrónico'}),
            'phone': TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'})
        }
