# /Users/pablollh/MEGA/GitHub/Grupo-huntRED-Chatbot/app/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from app.models import (
    WorkflowStage, Application, Vacante,
    Person, EnhancedNetworkGamificationProfile, UserPermission
)
from app.ats.accounts.models import CustomUser
import logging
from datetime import datetime

# Choices para roles
ROLE_CHOICES = [
    ('SUPER_ADMIN', 'Super Administrador'),
    ('BU_COMPLETE', 'Consultor BU Completo'),
    ('BU_DIVISION', 'Consultor BU División')
]

# Choices para estados de usuario
USER_STATUS_CHOICES = [
    ('ACTIVE', 'Activo'),
    ('INACTIVE', 'Inactivo'),
    ('PENDING_APPROVAL', 'Pendiente de Aprobación')
]

# Choices para estados de verificación
VERIFICATION_STATUS_CHOICES = [
    ('PENDING', 'Pendiente'),
    ('APPROVED', 'Aprobado'),
    ('REJECTED', 'Rechazado')
]

# Choices para tipos de documento
DOCUMENT_TYPE_CHOICES = [
    ('ID', 'Identificación'),
    ('CURP', 'CURP'),
    ('RFC', 'RFC'),
    ('PASSPORT', 'Pasaporte')
]

logger = logging.getLogger(__name__)

class WorkflowStageForm(forms.ModelForm):
    """Formulario para gestionar etapas del workflow."""
    
    class Meta:
        model = WorkflowStage
        fields = ['name', 'description', 'order', 'duration_days', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'duration_days': forms.NumberInput(attrs={'min': 1, 'max': 365}),
        }

    def clean_name(self):
        """Valida que el nombre sea único."""
        name = self.cleaned_data['name']
        if WorkflowStage.objects.filter(name=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('Ya existe una etapa con este nombre'))
        return name

    def clean_order(self):
        """Valida que el orden sea único y secuencial."""
        order = self.cleaned_data['order']
        if order <= 0:
            raise ValidationError(_('El orden debe ser mayor a 0'))
        
        existing_orders = WorkflowStage.objects.values_list('order', flat=True)
        if order in existing_orders and self.instance.pk not in existing_orders:
            raise ValidationError(_('Este orden ya está en uso'))
        return order

class ApplicationForm(forms.ModelForm):
    """Formulario para gestionar aplicaciones."""
    
    class Meta:
        model = Application
        fields = [
            'user', 'vacancy', 'status', 'notes', 'interview_date',
            'expected_salary', 'current_salary', 'skills', 'experience_years'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
            'interview_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_salary': forms.NumberInput(attrs={'step': '1000'}),
            'current_salary': forms.NumberInput(attrs={'step': '1000'}),
            'skills': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        """Validaciones adicionales."""
        cleaned_data = super().clean()
        
        status = cleaned_data.get('status')
        interview_date = cleaned_data.get('interview_date')
        expected_salary = cleaned_data.get('expected_salary')
        current_salary = cleaned_data.get('current_salary')
        
        if status == 'interview' and not interview_date:
            raise ValidationError(_('La fecha de entrevista es requerida'))
            
        if expected_salary and current_salary:
            if expected_salary < current_salary:
                raise ValidationError(_(
                    'El salario esperado no puede ser menor al actual'
                ))
                
        return cleaned_data

class VacancyForm(forms.ModelForm):
    """Formulario para gestionar vacantes."""
    
    class Meta:
        model = Vacante
        fields = [
            'title', 'description', 'requirements', 'business_unit',
            'location', 'salary_range', 'status', 'skills_required',
            'experience_required', 'education_required', 'languages'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
            'skills_required': forms.Textarea(attrs={'rows': 3}),
            'salary_range': forms.TextInput(attrs={'placeholder': 'Ej: 30000-50000 MXN'}),
        }

    def clean_salary_range(self):
        """Valida que el rango de salario sea válido."""
        salary_range = self.cleaned_data['salary_range']
        if salary_range:
            try:
                min_salary, max_salary = map(int, salary_range.split('-'))
                if min_salary >= max_salary:
                    raise ValidationError(_(
                        'El salario mínimo debe ser menor al máximo'
                    ))
            except ValueError:
                raise ValidationError(_(
                    'Formato de rango de salario inválido. '
                    'Use el formato: min-max'
                ))
        return salary_range

class PersonForm(forms.ModelForm):
    """Formulario para gestionar perfiles de candidatos."""
    
    class Meta:
        model = Person
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'business_unit',
            'current_position', 'current_company', 'current_salary',
            'expected_salary', 'skills', 'experience_years', 'education',
            'languages', 'location', 'availability_date'
        ]
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3}),
            'education': forms.Textarea(attrs={'rows': 2}),
            'languages': forms.Textarea(attrs={'rows': 2}),
            'availability_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_email(self):
        """Valida que el email sea único."""
        email = self.cleaned_data['email']
        if Person.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('Este email ya está registrado'))
        return email

    def clean_phone(self):
        """Valida que el teléfono sea único y tenga el formato correcto."""
        phone = self.cleaned_data['phone']
        if not phone.startswith(('+52', '+1')):
            raise ValidationError(_('El número debe incluir el código del país'))
            
        if Person.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('Este número de teléfono ya está registrado'))
        return phone

    def save(self, commit=True):
        """Guarda el perfil y actualiza el perfil de gamificación."""
        person = super().save(commit=False)
        if commit:
            person.save()
            
            # Actualizar perfil de gamificación
            gamification_profile = person.enhancednetworkgamificationprofile
            gamification_profile.update_profile(
                skills=self.cleaned_data['skills'],
                experience=self.cleaned_data['experience_years'],
                education=self.cleaned_data['education']
            )
            gamification_profile.save()
            
        return person

class GamificationProfileForm(forms.ModelForm):
    class Meta:
        model = EnhancedNetworkGamificationProfile
        fields = [
            'points', 'level', 'badges', 'achievements',
            'last_activity', 'engagement_score'
        ]
        widgets = {
            'achievements': forms.Textarea(attrs={'rows': 3}),
            'badges': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_points(self):
        """Valida que los puntos no sean negativos."""
        points = self.cleaned_data['points']
        if points < 0:
            raise ValidationError(_('Los puntos no pueden ser negativos'))
        return points

    def clean_level(self):
        """Valida que el nivel sea válido."""
        level = self.cleaned_data['level']
        if level < 1 or level > 100:
            raise ValidationError(_('El nivel debe estar entre 1 y 100'))
        return level

    def save(self, commit=True):
        """Guarda el perfil y actualiza el ranking."""
        profile = super().save(commit=False)
        if commit:
            profile.save()
            
            # Actualizar ranking
            # Aquí implementar la lógica de ranking
            
        return profile

# Formularios de autenticación
class CustomUserCreationForm(forms.ModelForm):
    """Formulario para crear nuevos usuarios."""
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label=_('Password confirmation'),
        widget=forms.PasswordInput
    )

    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'role',
            'business_unit', 'division', 'phone_number'
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('Las contraseñas no coinciden'))
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_('Este email ya está registrado'))
        return email

class CustomUserChangeForm(forms.ModelForm):
    """Formulario para editar usuarios existentes."""
    class Meta:
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name', 'role',
            'business_unit', 'division', 'phone_number',
            'status', 'verification_status'
        ]

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('Este email ya está registrado'))
        return email

class DocumentVerificationForm(forms.ModelForm):
    """Formulario para verificar documentos."""
    class Meta:
        model = DocumentVerification
        fields = [
            'document_type', 'document_number',
            'document_front', 'document_back', 'selfie'
        ]
        widgets = {
            'document_front': forms.FileInput(attrs={'accept': 'image/*'}),
            'document_back': forms.FileInput(attrs={'accept': 'image/*'}),
            'selfie': forms.FileInput(attrs={'accept': 'image/*'})
        }

    def clean_document_number(self):
        document_number = self.cleaned_data['document_number']
        if DocumentVerification.objects.filter(
            document_number=document_number,
            user=self.instance.user
        ).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('Este número de documento ya está registrado'))
        return document_number

class UserPermissionForm(forms.ModelForm):
    """Formulario para gestionar permisos de usuario."""
    class Meta:
        model = UserPermission
        fields = ['permission', 'business_unit', 'division']

    def clean(self):
        cleaned_data = super().clean()
        permission = cleaned_data.get('permission')
        business_unit = cleaned_data.get('business_unit')
        division = cleaned_data.get('division')

        if permission == 'DIVISION_ACCESS' and not division:
            raise ValidationError(_('La división es requerida para permisos de división'))

        if permission == 'BU_ACCESS' and not business_unit:
            raise ValidationError(_('La unidad de negocio es requerida para permisos de BU'))

        return cleaned_data

    def save(self, commit=True):
        permission = super().save(commit=False)
        if commit:
            permission.save()
        return permission
    """Formulario para gestionar perfiles de gamificación."""
    
    class Meta:
        model = EnhancedNetworkGamificationProfile
        fields = [
            'points', 'level', 'badges', 'achievements',
            'last_activity', 'engagement_score'
        ]
        widgets = {
            'achievements': forms.Textarea(attrs={'rows': 3}),
            'badges': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_points(self):
        """Valida que los puntos no sean negativos."""
        points = self.cleaned_data['points']
        if points < 0:
            raise ValidationError(_('Los puntos no pueden ser negativos'))
        return points

    def clean_level(self):
        """Valida que el nivel sea válido."""
        level = self.cleaned_data['level']
        if level < 1 or level > 100:
            raise ValidationError(_('El nivel debe estar entre 1 y 100'))
        return level

    def save(self, commit=True):
        """Guarda el perfil y actualiza el ranking."""
        profile = super().save(commit=False)
        if commit:
            profile.save()
            
            # Actualizar ranking
            profile.update_ranking()
            
        return profile