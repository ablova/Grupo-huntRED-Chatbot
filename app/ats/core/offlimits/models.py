from django.db import models
from django.utils import timezone
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ServiceType(models.TextChoices):
    HUMAN = 'humano', 'Servicio por humanos'
    HYBRID = 'hibrido', 'Servicio híbrido'
    AI = 'ai', 'Servicio por AI'


class OffLimitsRestriction(models.Model):
    """
    Modelo que representa una restricción OffLimits/Cooling Period para una empresa cliente.
    Define el período durante el cual no se deben buscar candidatos de esta empresa.
    """
    client = models.ForeignKey('ats.Client', on_delete=models.CASCADE, related_name='offlimits_restrictions')
    business_unit = models.ForeignKey('ats.BusinessUnit', on_delete=models.CASCADE, related_name='offlimits_restrictions')
    service_type = models.CharField(max_length=16, choices=ServiceType.choices)
    process = models.ForeignKey('ats.RecruitmentProcess', on_delete=models.CASCADE, related_name='offlimits_restrictions')
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='created_offlimits')
    
    class Meta:
        indexes = [
            models.Index(fields=['client', 'business_unit', 'service_type', 'is_active']),
            models.Index(fields=['end_date']),
        ]
        verbose_name = 'Restricción OffLimits'
        verbose_name_plural = 'Restricciones OffLimits'
    
    def __str__(self):
        return f"{self.client} - {self.get_business_unit_display()} - {self.get_service_type_display()} - Hasta: {self.end_date}"
    
    def save(self, *args, **kwargs):
        # Si es una creación nueva y no se ha establecido end_date, calcular automáticamente
        if not self.pk and not self.end_date:
            months = get_offlimits_period(
                self.business_unit.code, 
                self.service_type
            )
            self.end_date = timezone.now().date() + relativedelta(months=months)
        super().save(*args, **kwargs)


class CandidateInitiatedContact(models.Model):
    """
    Registra cuando un candidato inicia contacto, lo que constituye una excepción
    a las restricciones OffLimits.
    """
    candidate = models.ForeignKey('ats.Candidate', on_delete=models.CASCADE, related_name='initiated_contacts')
    client = models.ForeignKey('ats.Client', on_delete=models.CASCADE, related_name='candidate_initiated_contacts')
    timestamp = models.DateTimeField(auto_now_add=True)
    evidence_type = models.CharField(
        max_length=50,
        choices=[
            ('application', 'Aplicación espontánea'),
            ('email', 'Email iniciado por candidato'),
            ('call', 'Llamada iniciada por candidato'),
            ('website', 'Registro en sitio web'),
            ('other', 'Otro'),
        ]
    )
    evidence_reference = models.CharField(max_length=255, help_text='URL o referencia al documento/evidencia')
    verified_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='verified_contacts')
    verification_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['candidate', 'client']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['verification_date']),
        ]
        verbose_name = 'Contacto Iniciado por Candidato'
        verbose_name_plural = 'Contactos Iniciados por Candidatos'
    
    def __str__(self):
        return f"{self.candidate} - {self.client} - {self.evidence_type} - {self.timestamp.date()}"
    
    def verify(self, user):
        """Marca esta excepción como verificada por un usuario"""
        self.verified_by = user
        self.verification_date = timezone.now()
        self.save()


class OffLimitsAudit(models.Model):
    """
    Registra acciones relacionadas con OffLimits para fines de auditoría.
    """
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    candidate = models.ForeignKey('ats.Candidate', on_delete=models.CASCADE)
    client = models.ForeignKey('ats.Client', on_delete=models.CASCADE)
    business_unit = models.ForeignKey('ats.BusinessUnit', on_delete=models.CASCADE)
    action_type = models.CharField(
        max_length=50,
        choices=[
            ('check', 'Verificación de OffLimits'),
            ('override', 'Anulación manual de OffLimits'),
            ('create_restriction', 'Creación de restricción'),
            ('approve_exception', 'Aprobación de excepción'),
            ('contact_offlimits', 'Contacto con candidato en OffLimits'),
        ]
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    restriction = models.ForeignKey(OffLimitsRestriction, on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['action_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['client', 'business_unit']),
        ]
    
    def __str__(self):
        return f"{self.action_type} - {self.candidate} - {self.client} - {self.timestamp}"


def get_offlimits_period(business_unit_code, service_type):
    """
    Devuelve el período de OffLimits en meses según la unidad de negocio y tipo de servicio.
    """
    mapping = {
        ('huntRED_executive', 'humano'): 18,
        ('huntRED_executive', 'hibrido'): 12,
        ('huntRED_executive', 'ai'): 8,
        ('huntRED', 'humano'): 12,
        ('huntRED', 'hibrido'): 6,
        ('huntRED', 'ai'): 4,
        ('huntU', 'ai'): 4,
        ('amigro', 'ai'): 3,
    }
    return mapping.get((business_unit_code, service_type), 0)


def get_guarantee_period(business_unit_code):
    """
    Devuelve el período de garantía en meses según la unidad de negocio.
    """
    mapping = {
        'huntRED_executive': 3,
        'huntRED': 2,
        'huntU': 1,
        'amigro': 0,
    }
    return mapping.get(business_unit_code, 0)
