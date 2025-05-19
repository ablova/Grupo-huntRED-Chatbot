# Ubicacion SEXSI -- /home/pablo/app/sexsi/models.py

from django.db import models
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import User
import uuid
from django.urls import reverse
from datetime import date

# Importación diferida para evitar problemas circulares
#Person = apps.get_model('app', 'Person')

def calculate_age(birth_date):
    """Calcula la edad dada una fecha de nacimiento."""
    today = date.today()
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    return age

class SexsiConfig(models.Model):
    """
    Configuración exclusiva para el flujo SEXSI.
    Almacena los datos de integración para Hellosign y PayPal.
    """
    name = models.CharField(max_length=100, default="SEXSI Configuración")
    
    # Integración Hellosign
    hellosign_api_key = models.CharField(max_length=255, blank=True, null=True, help_text="API Key para Hellosign")
    hellosign_template_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID de plantilla en Hellosign")
    
    # Integración PayPal (o similar)
    paypal_client_id = models.CharField(max_length=255, blank=True, null=True, help_text="Client ID de PayPal")
    paypal_client_secret = models.CharField(max_length=255, blank=True, null=True, help_text="Client Secret de PayPal")
    
    def __str__(self):
        return self.name

class ConsentAgreement(models.Model):
    """
    Modelo de Acuerdo de Consentimiento con doble validación de firma.
    """
    STATUS_CHOICES = [
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('signed_by_creator', 'Firmado por Anfitrión'),
        ('signed_by_invitee', 'Firmado por Invitado'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado')
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_agreements')
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invited_agreements', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_of_encounter = models.DateTimeField()
    location = models.CharField(max_length=200)
    agreement_text = models.TextField()
    
    # Preferencias y prácticas
    preferences = models.ManyToManyField('Preference', related_name='agreements')
    
    # Firma y validaciones
    is_signed_by_creator = models.BooleanField(default=False)
    is_signed_by_invitee = models.BooleanField(default=False)
    creator_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    invitee_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    creator_selfie = models.ImageField(upload_to='selfies/', null=True, blank=True, help_text="Selfie del creador con identificación")
    invitee_selfie = models.ImageField(upload_to='selfies/', null=True, blank=True, help_text="Selfie del invitado con identificación")
    signature_method = models.CharField(
        max_length=20, 
        choices=(("hellosign", "Hellosign"), ("internal", "Desarrollo Interno")),
        default="internal",
        help_text="Método de firma elegido"
    )
    tos_accepted = models.BooleanField(default=False)
    
    # OTP y verificación de identidad
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    creator_id_document = models.ImageField(upload_to='id_documents/', null=True, blank=True)
    invitee_id_document = models.ImageField(upload_to='id_documents/', null=True, blank=True)
    
    # Seguridad y control de token
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    def default_token_expiry():
        return now() + timedelta(hours=36)

    token_expiry = models.DateTimeField(default=default_token_expiry)
    
    def clean(self):
        """Validaciones adicionales"""
        # Validaciones de duración
        if self.duration_type != 'single' and not self.duration_amount:
            raise ValidationError("Debe especificar la cantidad de duración para acuerdos no puntuales")
        if self.duration_type != 'single' and not self.duration_unit:
            raise ValidationError("Debe especificar la unidad de duración para acuerdos no puntuales")

        # Validaciones de edad
        if self.creator_date_of_birth and self.creator_age_verified:
            age = calculate_age(self.creator_date_of_birth)
            if age < 18:
                raise ValidationError("El creador debe ser mayor de 18 años")

        if self.invitee_date_of_birth and self.invitee_age_verified:
            age = calculate_age(self.invitee_date_of_birth)
            if age < 18:
                raise ValidationError("El invitado debe ser mayor de 18 años")

        # Validaciones de fecha de verificación
        if self.creator_age_verified and not self.creator_age_verification_date:
            raise ValidationError("Falta la fecha de verificación de edad del creador")
        if self.invitee_age_verified and not self.invitee_age_verification_date:
            raise ValidationError("Falta la fecha de verificación de edad del invitado")

    def get_status_display(self):
        """Obtiene la representación legible del estado."""
        return dict(self.STATUS_CHOICES).get(self.status, 'Desconocido')

    def get_duration_display(self):
        """Obtiene la representación legible de la duración."""
        if self.duration_type == 'single':
            return "Interacción de Una Sola Vez"
        return f"{self.duration_amount} {self.duration_unit}"

    def get_absolute_url(self):
        """Obtiene la URL absoluta para este acuerdo."""
        return reverse('sexsi:agreement_detail', kwargs={'pk': self.pk})

    def generate_otp(self):
        """Genera un código OTP de 6 dígitos y lo almacena con una validez de 10 minutos."""
        self.otp_code = str(uuid.uuid4().int)[:6]
        self.otp_expiry = now() + timedelta(minutes=10)
        self.save()
        return self.otp_code

    def verify_otp(self, otp_input):
        """Verifica si el OTP ingresado es válido."""
        return self.otp_code == otp_input and now() < self.otp_expiry

    def is_valid_for_duration(self, preference):
        """Verifica si el acuerdo es válido para la duración de la preferencia."""
        if preference.duration == 'single' and self.duration_type != 'single':
            return False
        if preference.duration in ['short_term', 'long_term'] and self.duration_type == 'single':
            return False
        return True

    def __str__(self):
        return f"Acuerdo #{self.id} - {self.creator.username}"

class PaymentTransaction(models.Model):
    """
    Modelo para registrar la transacción de pago asociada al Acuerdo SEXSI.
    Permite almacenar el método, monto, ID de transacción (por PayPal u otro),
    y el estado del pago.
    """
    agreement = models.ForeignKey(ConsentAgreement, on_delete=models.CASCADE, related_name="payment_transactions")
    signature_method = models.CharField(
        max_length=20, 
        choices=(("hellosign", "Hellosign"), ("internal", "Desarrollo Interno")),
        default="internal"  
    )
    paypal_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_status = models.CharField(max_length=50, default="pending", help_text="Estado del pago")
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Pago {self.id} para Acuerdo #{self.agreement.id}"

class DiscountCoupon(models.Model):
    """Modelo para almacenar cupones de descuento con diferentes porcentajes y un cupón de 100%."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_coupons')
    code = models.CharField(max_length=10, unique=True)
    discount_percentage = models.PositiveIntegerField()
    expiration_date = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.is_used and self.expiration_date > now()
    
    def __str__(self):
        return f"Cupon {self.code} - {self.discount_percentage}% - {'Usado' if self.is_used else 'Disponible'}"

# Modelo de relación intermedia para manejar las preferencias en los acuerdos
class AgreementPreference(models.Model):
    """
    Modelo que representa la relación entre un acuerdo y sus preferencias,
    permitiendo almacenar información adicional sobre cada preferencia en el contexto del acuerdo.
    """
    agreement = models.ForeignKey('ConsentAgreement', on_delete=models.CASCADE)
    preference = models.ForeignKey('Preference', on_delete=models.CASCADE)
    is_required = models.BooleanField(default=True, help_text="Indica si esta preferencia es obligatoria para el acuerdo")
    notes = models.TextField(blank=True, null=True, help_text="Notas adicionales sobre esta preferencia en el contexto del acuerdo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('agreement', 'preference')
        ordering = ['preference__category', 'preference__name']

    def __str__(self):
        return f"{self.agreement} - {self.preference}"

# Actualizar el modelo ConsentAgreement para incluir las nuevas funcionalidades
# Eliminar la clase duplicada ConsentmentAgreement

class Preference(models.Model):
    """
    Modelo para almacenar preferencias de intimidad y prácticas.
    """
    PREFERENCE_TYPES = [
        ('common', 'Preferencias Comunes'),
        ('discrete', 'Preferencias Discretas'),
        ('advanced', 'Exploraciones Avanzadas'),
        ('exotic', 'Exploraciones Exóticas')
    ]

    code = models.CharField(max_length=10, unique=True, help_text="Código único de la preferencia")
    name = models.CharField(max_length=100, help_text="Nombre descriptivo de la preferencia")
    description = models.TextField(help_text="Descripción detallada de la preferencia")
    category = models.CharField(max_length=20, choices=PREFERENCE_TYPES)
    complexity_level = models.CharField(max_length=20, help_text="Nivel de complejidad de la práctica")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def get_absolute_url(self):
        return reverse('sexsi:preference_detail', kwargs={'pk': self.pk})

    def is_compatible_with_duration(self, duration_type):
        """Verifica si esta preferencia es compatible con el tipo de duración del acuerdo."""
        if self.duration == 'single' and duration_type != 'single':
            return False
        if self.duration in ['short_term', 'long_term'] and duration_type == 'single':
            return False
        return True

    def get_category_display(self):
        """Obtiene la representación legible de la categoría."""
        return dict(self.PREFERENCE_TYPES).get(self.category, 'Desconocido')

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def get_absolute_url(self):
        return reverse('sexsi:preference_detail', kwargs={'pk': self.pk})