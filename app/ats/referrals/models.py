from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import random
import string

from app.models import Person, Proposal, BusinessUnit

class ReferralProgram(models.Model):
    """
    Modelo para gestionar el programa de referidos.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('validated', 'Validado'),
        ('completed', 'Completado'),
        ('rejected', 'Rechazado')
    ]

    referrer = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name='referrals_made',
        help_text="Persona que hace la referencia"
    )
    referred_company = models.CharField(
        max_length=200,
        help_text="Nombre de la empresa referida"
    )
    referral_code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Código único de referencia"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    commission_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(8), MaxValueValidator(15)],
        help_text="Porcentaje de comisión (8-15%)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Información adicional de la referencia"
    )

    class Meta:
        verbose_name = "Programa de Referidos"
        verbose_name_plural = "Programas de Referidos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referrer']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at'])
        ]

    def __str__(self):
        return f"Referido: {self.referred_company} por {self.referrer}"

    def generate_referral_code(self):
        """
        Genera un código de referencia único basado en el referidor.
        """
        base = f"REF-{self.referrer.id}-"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{base}{suffix}"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    def validate_referral(self):
        """
        Valida la referencia y actualiza su estado.
        """
        if self.status == 'pending':
            self.status = 'validated'
            self.validated_at = timezone.now()
            self.save()

    def complete_referral(self):
        """
        Marca la referencia como completada.
        """
        if self.status == 'validated':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()

    def reject_referral(self):
        """
        Rechaza la referencia.
        """
        if self.status in ['pending', 'validated']:
            self.status = 'rejected'
            self.save()

    def calculate_commission(self, amount):
        """
        Calcula la comisión basada en el monto.
        """
        return (amount * self.commission_percentage) / 100

    def is_valid(self):
        """
        Verifica si la referencia es válida.
        """
        return self.status in ['validated', 'completed']

    def get_status_display(self):
        """
        Obtiene el estado legible de la referencia.
        """
        return dict(self.STATUS_CHOICES).get(self.status, self.status) 