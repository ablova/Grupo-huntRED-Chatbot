import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.template.loader import render_to_string
from app.models import Company, Proposal, Vacante
from app.ats.pricing.models import ServiceCalculation

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_key = settings.WHATSAPP_API_KEY
        self.api_url = settings.WHATSAPP_API_URL
        self.template_dir = 'app/templates/whatsapp'

    async def send_proposal_notification(self, proposal: Proposal) -> bool:
        """
        Envía una notificación por WhatsApp sobre una nueva propuesta.
        
        Args:
            proposal: Instancia de Proposal
            
        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            # Preparar datos para la plantilla
            context = {
                'company': proposal.company,
                'contact_person': proposal.contact_person,
                'vacancy': proposal.vacancies.first(),
                'proposal_url': f"{settings.BASE_URL}/proposals/{proposal.id}",
                'consultant': proposal.consultant
            }
            
            # Renderizar plantilla
            template = 'proposal_notification.txt'
            message = render_to_string(f"{self.template_dir}/{template}", context)
            
            # Enviar mensaje
            return await self._send_message(
                phone=proposal.contact_person.phone,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp proposal notification: {str(e)}")
            return False

    async def send_payment_reminder(self, payment: ServiceCalculation) -> bool:
        """
        Envía un recordatorio de pago por WhatsApp.
        
        Args:
            payment: Instancia de ServiceCalculation
            
        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            # Preparar datos para la plantilla
            context = {
                'company': payment.company,
                'contact_person': payment.contact_person,
                'amount': payment.total_fee,
                'due_date': payment.due_date,
                'payment_url': f"{settings.BASE_URL}/payments/{payment.id}"
            }
            
            # Renderizar plantilla
            template = 'payment_reminder.txt'
            message = render_to_string(f"{self.template_dir}/{template}", context)
            
            # Enviar mensaje
            return await self._send_message(
                phone=payment.contact_person.phone,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp payment reminder: {str(e)}")
            return False

    async def send_interview_reminder(self, interview: Dict) -> bool:
        """
        Envía un recordatorio de entrevista por WhatsApp.
        
        Args:
            interview: Diccionario con datos de la entrevista
            
        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            # Preparar datos para la plantilla
            context = {
                'candidate': interview['candidate'],
                'company': interview['company'],
                'position': interview['position'],
                'date': interview['date'],
                'time': interview['time'],
                'location': interview['location'],
                'interview_url': f"{settings.BASE_URL}/interviews/{interview['id']}"
            }
            
            # Renderizar plantilla
            template = 'interview_reminder.txt'
            message = render_to_string(f"{self.template_dir}/{template}", context)
            
            # Enviar mensaje
            return await self._send_message(
                phone=interview['candidate'].phone,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp interview reminder: {str(e)}")
            return False

    async def _send_message(self, phone: str, message: str) -> bool:
        """
        Envía un mensaje por WhatsApp usando la API.
        
        Args:
            phone: Número de teléfono del destinatario
            message: Mensaje a enviar
            
        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            # Formatear número de teléfono
            formatted_phone = self._format_phone_number(phone)
            
            # Preparar payload
            payload = {
                'phone': formatted_phone,
                'message': message,
                'api_key': self.api_key
            }
            
            # Enviar mensaje
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.error(f"Error sending WhatsApp message: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error in WhatsApp message sending: {str(e)}")
            return False

    def _format_phone_number(self, phone: str) -> str:
        """
        Formatea el número de teléfono para la API de WhatsApp.
        
        Args:
            phone: Número de teléfono a formatear
            
        Returns:
            str: Número formateado
        """
        # Eliminar caracteres no numéricos
        phone = ''.join(filter(str.isdigit, phone))
        
        # Asegurar que comience con el código de país
        if not phone.startswith('52'):
            phone = '52' + phone
            
        return phone 