# Ubicacion SEXSI -- /home/pablollh/app/sexsi/sexsi_flow.py


import uuid
import math
from asgiref.sync import async_to_sync
from app.chatbot.integrations.services import send_message
from forex_python.converter import CurrencyRates
from django.utils.timezone import now
from app.sexsi.models import ConsentAgreement, SexsiConfig, DiscountCoupon

# -------------------------
# CONFIGURACIÓN DE REDONDEO
# -------------------------
# Variable para activar o desactivar el redondeo a 50 centavos
REDONDEAR_PRECIO = True

def redondear_a_50_centavos(valor, redondear=REDONDEAR_PRECIO):
    """
    Redondea el valor hacia arriba al múltiplo de 0.50 más cercano si 'redondear' es True.
    Por ejemplo: 12.33 -> 12.50, 12.51 -> 13.00.
    """
    if not redondear:
        return valor
    # Multiplicamos por 2, redondeamos hacia arriba y dividimos por 2
    return math.ceil(valor * 2) / 2

# -------------------------
# MÓDULO DE PRECIOS Y CONVERSIÓN DINÁMICA
# -------------------------

IVA_RATE = 0.16  # 16% de IVA

def calcular_precio_con_iva(precio_base):
    """Calcula el precio total en USD incluyendo IVA."""
    return round(precio_base * (1 + IVA_RATE), 2)

def obtener_tasa_conversion(base_currency="USD", target_currency="MXN"):
    """
    Consulta la tasa de conversión actual utilizando forex-python.
    """
    try:
        c = CurrencyRates()
        rate = c.get_rate(base_currency, target_currency)
        return rate
    except Exception as e:
        # En caso de error, se utiliza una tasa de respaldo.
        return 20.53

def convertir_usd_a_mxn(precio_usd):
    """
    Convierte un precio en USD a MXN usando la tasa de cambio actual.
    """
    rate = obtener_tasa_conversion("USD", "MXN")
    precio_mxn = round(precio_usd * rate, 2)
    return redondear_a_50_centavos(precio_mxn)

# Definir los precios en USD para cada opción.
# Ejemplo: Hellosign 7 USD y Desarrollo Interno 5 USD.
PRICING_OPTIONS_USD = {
    "hellosign": {
        "precio_base": 7.00,  # en USD
        "precio_total": calcular_precio_con_iva(7.00)
    },
    "internal": {
        "precio_base": 5.00,  # en USD
        "precio_total": calcular_precio_con_iva(5.00)
    }
}

def obtener_pricing_options():
    """
    Genera un diccionario de precios que incluye el precio total en USD (con IVA)
    y el precio convertido a MXN redondeado a 50 centavos, según la tasa actual.
    """
    pricing_options = {}
    for key, data in PRICING_OPTIONS_USD.items():
        precio_total_usd = data["precio_total"]
        precio_total_mxn = convertir_usd_a_mxn(precio_total_usd)
        pricing_options[key] = {
            "precio_base_usd": data["precio_base"],
            "precio_total_usd": precio_total_usd,
            "precio_total_mxn": precio_total_mxn
        }
    return pricing_options

# Obtenemos las opciones de precios con la conversión y redondeo.
PRICING_OPTIONS = obtener_pricing_options()

# -------------------------
# FUNCIONES DEL FLUJO SEXSI
# -------------------------

def process_sexsi_payment(user, amount, payment_details=None):
    """
    Función simulada para procesar el pago mediante PayPal (o similar).
    Devuelve (True, transaction_id) si es exitoso, o (False, None) si falla.
    """
    transaction_id = str(uuid.uuid4())  # Simula un ID de transacción
    return True, transaction_id

def iniciar_flujo_sexsi(phone_id, user, business_unit, context):
    """
    Inicia el flujo SEXSI, mostrando al usuario las opciones con precios en USD y su conversión a MXN.
    """
    mensaje = (
        "Bienvenido al flujo SEXSI. Por favor, elige tu opción para firmar el contrato:\n"
        f"1. Firma electrónica a través de Hellosign (Precio: ${PRICING_OPTIONS['hellosign']['precio_total_usd']} USD, "
        f"{PRICING_OPTIONS['hellosign']['precio_total_mxn']} MXN).\n"
        f"2. Firma electrónica con nuestro desarrollo interno (Precio: ${PRICING_OPTIONS['internal']['precio_total_usd']} USD, "
        f"{PRICING_OPTIONS['internal']['precio_total_mxn']} MXN).\n"
        "Responde con '1' o '2'."
    )
    async_to_sync(send_message)("whatsapp", phone_id, mensaje, business_unit)
    context['operacion_sexsi'] = {
        'pending_choice': True,
        'pricing': PRICING_OPTIONS
    }
    return "Flujo SEXSI iniciado. Esperando elección de método."

def confirmar_pago_sexsi(phone_id, user, business_unit, context, choice):
    """
    Procesa el pago según la opción elegida por el cliente. 'choice' debe ser '1' (Hellosign) o '2' (Desarrollo Interno).
    """
    operacion = context.get('operacion_sexsi', {})
    if not operacion.get('pending_choice'):
        async_to_sync(send_message)("whatsapp", phone_id, "No hay una operación pendiente.", business_unit)
        return False, None

    if choice == '1':
        pricing = operacion.get('pricing', {}).get('hellosign', {})
        amount = pricing.get('precio_total_usd', 0)
        signature_method = "hellosign"
    elif choice == '2':
        pricing = operacion.get('pricing', {}).get('internal', {})
        amount = pricing.get('precio_total_usd', 0)
        signature_method = "internal"
    else:
        async_to_sync(send_message)("whatsapp", phone_id, "Opción inválida. Por favor, responde '1' o '2'.", business_unit)
        return False, None

    pago_exitoso, transaction_id = process_sexsi_payment(user, amount)
    if pago_exitoso:
        operacion['pending_choice'] = False
        operacion['transaction_id'] = transaction_id
        operacion['signature_method'] = signature_method
        context['operacion_sexsi'] = operacion

        mensaje_pago = (
            f"Pago procesado con éxito (ID: {transaction_id}). "
            f"Has elegido el método de firma: {signature_method.capitalize()}.\n"
            "Ahora, por favor, completa la información para el acuerdo SEXSI."
        )
        async_to_sync(send_message)("whatsapp", phone_id, mensaje_pago, business_unit)
        return True, transaction_id
    else:
        async_to_sync(send_message)("whatsapp", phone_id, "El pago no se pudo procesar. Inténtalo de nuevo.", business_unit)
        return False, None
    
def is_token_valid(agreement, token):
    """Verifica si el token es válido y no ha expirado."""
    return agreement.token == token and agreement.token_expiry > now()

# Notificación Automática si el Acuerdo no se ha firmado

def send_signature_reminder(agreement):
    """Envía recordatorios si el acuerdo no se ha firmado en X tiempo."""
    if not agreement.is_signed_by_creator or not agreement.is_signed_by_invitee:
        invitation_link = reverse("sexsi:agreement_detail", args=[agreement.id]) + f"?token={agreement.token}"
        platform = "whatsapp"
        business_unit = agreement.creator.businessunit_set.first() if agreement.creator.businessunit_set.exists() else None
        message = ("Recordatorio: Tienes un acuerdo pendiente de firma. "
                   f"Por favor, revisa y firma en: {invitation_link}")
        async_to_sync(send_message)(platform, agreement.invitee_contact, message, business_unit)

# Ejecutar Recordatorios para Acuerdos Pendientes

def process_pending_agreements():
    """Ejecuta recordatorios para acuerdos no firmados en más de 12 horas."""
    twelve_hours_ago = now() - datetime.timedelta(hours=12)
    pending_agreements = ConsentAgreement.objects.filter(
        is_signed_by_creator=False, date_created__lte=twelve_hours_ago
    ) | ConsentAgreement.objects.filter(
        is_signed_by_invitee=False, date_created__lte=twelve_hours_ago
    )
    for agreement in pending_agreements:
        send_signature_reminder(agreement)


def apply_discount_coupon(user, original_price):
    """Aplica un cupón de descuento válido al precio original."""
    valid_coupons = DiscountCoupon.objects.filter(user=user, is_used=False, expiration_date__gt=now())
    
    if valid_coupons.exists():
        coupon = valid_coupons.first()
        discounted_price = original_price * (1 - (coupon.discount_percentage / 100))
        coupon.is_used = True
        coupon.save()
        return discounted_price, coupon.code
    
    return original_price, None