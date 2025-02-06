# Ubicacion SEXSI -- /home/pablollh/app/sexsi/models.py

from django.db import models
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
    """
    Modelo que representa el acuerdo de consentimiento SEXSI.
    Se incluirá un campo para definir el método de firma (hellosign o interno)
    y se puede relacionar con las transacciones de pago.
    """
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_agreements'
    )
    invitee_contact = models.CharField(
        max_length=50, 
        help_text="Número o identificador del canal (WhatsApp, Telegram, etc.)"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_of_encounter = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    agreement_text = models.TextField(
        default="Ambas partes están de acuerdo en tener un encuentro íntimo..."
    )
    consensual_activities = models.JSONField(default=dict, help_text="Actividades aceptadas por ambas partes")
    is_signed_by_creator = models.BooleanField(default=False)
    is_signed_by_invitee = models.BooleanField(default=False)
    creator_signature = models.ImageField(
        upload_to='signatures/', 
        null=True, 
        blank=True,
        help_text="Firma electrónica del creador"
    )
    invitee_signature = models.ImageField(
        upload_to='signatures/', 
        null=True, 
        blank=True,
        help_text="Firma electrónica del invitado"
    )
    # Opción elegida para la firma: 'hellosign' o 'internal'
    signature_method = models.CharField(
        max_length=20, 
        choices=(("hellosign", "Hellosign"), ("internal", "Desarrollo Interno")),
        default="internal",
        help_text="Método de firma elegido"
    )
        # Nuevo campo para registro de aceptación de TOS
    tos_accepted = models.BooleanField(default=False)
    tos_accepted_timestamp = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Consentimiento #{self.id} - {self.creator.username}"

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
    """Modelo para almacenar cupones de descuento."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_coupons')
    code = models.CharField(max_length=10, unique=True)
    discount_percentage = models.PositiveIntegerField(default=50)
    expiration_date = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.is_used and self.expiration_date > now()
    
    def __str__(self):
        return f"Cupon {self.code} - {'Usado' if self.is_used else 'Disponible'}"