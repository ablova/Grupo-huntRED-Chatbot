# Ubicacion SEXSI -- /home/pablollh/app/sexsi/models.py

from django.db import models
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import User
import uuid

class SexsiConfig(models.Model):
    """
    Configuración exclusiva para el flujo SEXSI.
    Almacena los datos de integración para Hellosign y PayPal.
    """
    # Relacionado al Business Unit si se requiere, o puede ser global para SEXSI.
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
    """Modelo de Acuerdo de Consentimiento con doble validación de firma."""
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_agreements')
    invitee_contact = models.CharField(max_length=50, help_text="Número o identificador del canal")
    agreement_text = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_of_encounter = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    
    # Firma y validaciones
    is_signed_by_creator = models.BooleanField(default=False)
    is_signed_by_invitee = models.BooleanField(default=False)
    creator_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    invitee_signature = models.ImageField(upload_to='signatures/', null=True, blank=True)
    creator_selfie = models.ImageField(upload_to='selfies/', null=True, blank=True)
    invitee_selfie = models.ImageField(upload_to='selfies/', null=True, blank=True)
    
    # OTP y verificación de identidad
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    creator_id_document = models.ImageField(upload_to='id_documents/', null=True, blank=True)
    invitee_id_document = models.ImageField(upload_to='id_documents/', null=True, blank=True)
    
    # Seguridad y control de token
    def get_token_expiry():
        return now() + timedelta(hours=36)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_expiry = models.DateTimeField(default=get_token_expiry)
    
    def generate_otp(self):
        """Genera un código OTP de 6 dígitos y lo almacena con una validez de 10 minutos."""
        self.otp_code = str(uuid.uuid4().int)[:6]
        self.otp_expiry = now() + timedelta(minutes=10)
        self.save()
        return self.otp_code
    
    def verify_otp(self, otp_input):
        """Verifica si el OTP ingresado es válido."""
        return self.otp_code == otp_input and now() < self.otp_expiry
    
    def __str__(self):
        return f"Acuerdo {self.id} - {self.creator.username}"

class PaymentTransaction(models.Model):
    """
    Modelo para registrar la transacción de pago asociada al Acuerdo SEXSI.
    Permite almacenar el método, monto, ID de transacción (por PayPal u otro),
    y el estado del pago.
    """
    agreement = models.ForeignKey(ConsentAgreement, on_delete=models.CASCADE, related_name="payment_transactions")
    # Método de firma elegido para esta transacción, para referencia:
    signature_method = models.CharField(
        max_length=20, 
        choices=(("hellosign", "Hellosign"), ("internal", "Desarrollo Interno"))
    )
    # Si se usa PayPal, se registra el ID de transacción
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