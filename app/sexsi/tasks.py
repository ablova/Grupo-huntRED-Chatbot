# Ubicacion SEXSI -- /home/pablo/app/sexsi/tasks.py

from celery import shared_task
from django.utils.timezone import now, timedelta
from app.sexsi.models import ConsentAgreement
from app.sexsi.sexsi_flow import send_signature_reminder
from app.chatbot.integrations.services import send_message
from django.contrib.auth.models import User
from app.sexsi.models import DiscountCoupon # Modelo de cupones

@shared_task
def send_signature_reminder_intervals():
    """Envía recordatorios de firma a los 10, 30 y 45 minutos, cancelando el acuerdo a los 55 minutos si no se firma."""
    ten_minutes_ago = now() - timedelta(minutes=10)
    thirty_minutes_ago = now() - timedelta(minutes=30)
    forty_five_minutes_ago = now() - timedelta(minutes=45)
    fifty_five_minutes_ago = now() - timedelta(minutes=55)
    
    pending_agreements = ConsentAgreement.objects.filter(
        is_signed_by_creator=False, is_signed_by_invitee=False, date_created__lte=forty_five_minutes_ago
    )
    
    for agreement in pending_agreements:
        if not agreement.is_signed_by_creator and not agreement.is_signed_by_invitee:
            send_signature_reminder(agreement)
        elif agreement.is_signed_by_creator and not agreement.is_signed_by_invitee:
            send_message("whatsapp", agreement.invitee_contact, "Recuerda que aún no has firmado el acuerdo. Tienes 55 minutos en total para hacerlo. De lo contrario, el proceso será cancelado y recibirás un cupón del 50% de descuento para un próximo uso.", None)
        elif agreement.is_signed_by_invitee and not agreement.is_signed_by_creator:
            send_message("whatsapp", agreement.creator.username, "Recuerda que aún no has firmado el acuerdo. Tienes 55 minutos en total para hacerlo. De lo contrario, el proceso será cancelado y recibirás un cupón del 50% de descuento para un próximo uso.", None)
    
    # Cancelar acuerdos no firmados después de 55 minutos
    expired_agreements = ConsentAgreement.objects.filter(
        is_signed_by_creator=False, is_signed_by_invitee=False, date_created__lte=fifty_five_minutes_ago
    )
    for agreement in expired_agreements:
        coupon_code = generate_discount_coupon(agreement.creator)
        send_message("whatsapp", agreement.creator.username, f"El acuerdo ha sido cancelado debido a la falta de firma. Tu pago no es reembolsable, pero te ofrecemos un cupón del 50% de descuento para un próximo uso: {coupon_code}", None)
        send_message("whatsapp", agreement.invitee_contact, "El acuerdo ha sido cancelado debido a la falta de firma. Esperamos poder servirte y ayudarte pronto.", None)
    count = expired_agreements.count()
    expired_agreements.delete()
    
    return f"Recordatorios enviados. Acuerdos cancelados: {count}."

@shared_task
def generate_discount_coupon(user):
    """Genera un cupón de descuento válido por 45 días y lo almacena en la base de datos."""
    coupon_code = str(uuid.uuid4())[:8].upper()
    expiration_date = now() + timedelta(days=45)
    coupon = DiscountCoupon.objects.create(
        user=user,
        code=coupon_code,
        discount_percentage=50,
        expiration_date=expiration_date,
        is_used=False
    )
    return coupon

@shared_task
def delete_expired_otps_and_tokens():
    """Elimina OTPs, tokens expirados y cupones vencidos automáticamente."""
    expired_agreements = ConsentAgreement.objects.filter(
        otp_expiry__lt=now()
    )
    count_otps = expired_agreements.count()
    expired_agreements.update(otp_code=None, otp_expiry=None)
    
    expired_tokens = ConsentAgreement.objects.filter(
        token_expiry__lt=now()
    )
    count_tokens = expired_tokens.count()
    expired_tokens.update(token=None)
    
    expired_coupons = DiscountCoupon.objects.filter(expiration_date__lt=now(), is_used=False)
    count_coupons = expired_coupons.count()
    expired_coupons.update(is_used=True)
    
    logger.info(f"{count_otps} OTPs eliminados, {count_tokens} tokens eliminados, {count_coupons} cupones expirados.")
    return f"{count_otps} OTPs eliminados, {count_tokens} tokens eliminados, {count_coupons} cupones expirados."