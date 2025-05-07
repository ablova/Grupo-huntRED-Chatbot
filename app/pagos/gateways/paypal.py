import os
from paypalrestsdk import Api, Payment, Payout
from django.conf import settings
from app.pagos.models import Pago

class PayPalGateway:
    def __init__(self):
        self.api = Api({
            'mode': settings.PAYPAL_MODE,  # 'sandbox' o 'live'
            'client_id': settings.PAYPAL_CLIENT_ID,
            'client_secret': settings.PAYPAL_CLIENT_SECRET,
        })

    def crear_pago(self, pago: Pago):
        """Crea un pago en PayPal"""
        payment = Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [{
                "amount": {
                    "total": str(pago.monto),
                    "currency": pago.moneda
                },
                "description": pago.descripcion or f"Pago para {pago.empleado.nombre}"
            }],
            "redirect_urls": {
                "return_url": settings.PAYPAL_RETURN_URL,
                "cancel_url": settings.PAYPAL_CANCEL_URL
            }
        })

        if payment.create():
            pago.id_transaccion = payment.id
            pago.url_webhook = payment.links[0].href
            pago.save()
            return True, payment
        return False, payment.error

    def ejecutar_pago(self, pago_id, payer_id):
        """Ejecuta un pago después de que el usuario aprueba"""
        payment = Payment.find(pago_id)
        if payment.execute({"payer_id": payer_id}):
            pago = Pago.objects.get(id_transaccion=pago_id)
            pago.marcar_como_completado(payment.id)
            return True, payment
        return False, payment.error

    def crear_payout(self, pagos: list):
        """Crea un payout para múltiples pagos"""
        payout = Payout({
            "sender_batch_header": {
                "sender_batch_id": f"PAYOUT_BATCH_{timezone.now().strftime('%Y%m%d%H%M%S')}",
                "email_subject": "Pago de Grupo huntRED"
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": str(pago.monto),
                        "currency": pago.moneda
                    },
                    "note": f"Pago para {pago.empleado.nombre}",
                    "sender_item_id": f"ITEM_{pago.id}",
                    "receiver": pago.empleado.email
                }
                for pago in pagos
            ]
        })

        if payout.create():
            for pago in pagos:
                pago.id_transaccion = payout.batch_header.payout_batch_id
                pago.save()
            return True, payout
        return False, payout.error

    def verificar_webhook(self, request_body):
        """Verifica la validez de un webhook de PayPal"""
        return self.api.verify_webhook_signature(
            request_body['transmission_id'],
            request_body['transmission_time'],
            request_body['webhook_id'],
            request_body['event_type'],
            request_body['resource'],
            request_body['cert_url'],
            request_body['auth_algo'],
            request_body['transmission_sig']
        )
