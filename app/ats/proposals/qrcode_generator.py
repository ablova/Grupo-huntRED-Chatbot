import qrcode
from django.conf import settings
from django.core.files.storage import default_storage
import os
from datetime import datetime

class QRCodeGenerator:
    def __init__(self, proposal):
        self.proposal = proposal
        self.qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
    def generate_qr_code(self):
        """
        Genera un QR code para la propuesta.
        """
        # Crear el contenido del QR
        qr_content = f"https://{settings.DOMAIN}/proposals/{self.proposal.id}/"
        
        # Generar el QR
        self.qr.add_data(qr_content)
        self.qr.make(fit=True)
        
        # Crear imagen del QR
        qr_image = self.qr.make_image(fill_color="black", back_color="white")
        
        # Guardar el QR en el storage
        filename = f"proposals/qr/{self.proposal.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = default_storage.save(filename, qr_image.get_image())
        
        # Actualizar el modelo con la ruta del QR
        self.proposal.qr_code = filepath
        self.proposal.save()
        
        return filepath

    def get_qr_code_url(self):
        """
        Obtiene la URL completa del QR code.
        """
        if self.proposal.qr_code:
            return f"https://{settings.DOMAIN}{settings.MEDIA_URL}{self.proposal.qr_code}"
        return None
