# /home/pablo/app/com/omnichannel.py
#
# Gestiona la comunicación omnicanal para el módulo ATS.
#
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import requests
import logging
from typing import Dict, List, Optional
from app.models import Person
from app.ats.config import ATS_CONFIG

logger = logging.getLogger('app.ats.omnichannel')

class Omnichannel:
    """
    Gestiona la comunicación a través de múltiples canales.
    
    Esta clase maneja el envío de mensajes y notificaciones a través de
    diferentes canales de comunicación (email, WhatsApp, X, etc.).
    """
    
    def __init__(self):
        """Inicializa el sistema de comunicación omnicanal."""
        self.channels = {
            'email': self.send_email,
            'whatsapp': self.send_whatsapp,
            'x': self.send_x_dm
        }
        
        # Cargar configuraciones
        self.channel_config = ATS_CONFIG['COMMUNICATION']['CHANNELS']
        self.notification_config = ATS_CONFIG['COMMUNICATION']['NOTIFICATIONS']
        self.integration_config = ATS_CONFIG['COMMUNICATION']['INTEGRATIONS']
        
    def send_email(
        self,
        recipient: Person,
        message: str,
        subject: Optional[str] = None,
        template: Optional[str] = None
    ) -> bool:
        """
        Envía un correo electrónico.
        
        Args:
            recipient: Objeto Person con la información del destinatario
            message: Contenido del mensaje
            subject: Asunto del correo (opcional)
            template: Plantilla a usar (opcional)
            
        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            if not recipient.email:
                logger.warning(f"Destinatario {recipient.id} no tiene email")
                return False
                
            # Configurar asunto
            if not subject:
                subject = self.notification_config['channels']['email']['subject_prefix']
                
            # Enviar correo
            send_mail(
                subject=subject,
                message=message,
                from_email=self.notification_config['channels']['email']['from_email'],
                recipient_list=[recipient.email],
                fail_silently=False
            )
            
            logger.info(f"Email enviado exitosamente a {recipient.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            return False
        
    def send_whatsapp(
        self,
        phone: str,
        message: str,
        template: Optional[str] = None
    ) -> bool:
        """
        Envía un mensaje por WhatsApp.
        
        Args:
            phone: Número de teléfono
            message: Contenido del mensaje
            template: Plantilla a usar (opcional)
            
        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            if not phone:
                logger.warning("Número de teléfono no proporcionado")
                return False
                
            # Verificar configuración
            whatsapp_config = self.integration_config['whatsapp']
            if not whatsapp_config['enabled']:
                logger.warning("Integración de WhatsApp deshabilitada")
                return False
                
            # Preparar mensaje
            if template:
                message = self.notification_config['channels']['whatsapp']['template_prefix'] + message
                
            # Enviar mensaje (simulado por ahora)
            print(f"Enviando WhatsApp a {phone}: {message[:50]}...")
            
            logger.info(f"WhatsApp enviado exitosamente a {phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando WhatsApp: {str(e)}")
            return False
        
    def send_x_dm(
        self,
        handle: str,
        message: str,
        template: Optional[str] = None
    ) -> bool:
        """
        Envía un DM en X.
        
        Args:
            handle: Nombre de usuario en X
            message: Contenido del mensaje
            template: Plantilla a usar (opcional)
            
        Returns:
            bool: True si el envío fue exitoso
        """
        try:
            if not handle:
                logger.warning("Handle de X no proporcionado")
                return False
                
            # Verificar configuración
            x_config = self.integration_config['x']
            if not x_config['enabled']:
                logger.warning("Integración de X deshabilitada")
                return False
                
            # Preparar mensaje
            if template:
                message = self.notification_config['channels']['x']['template_prefix'] + message
                
            # Enviar mensaje (simulado por ahora)
            print(f"Enviando DM a {handle}: {message[:50]}...")
            
            logger.info(f"DM de X enviado exitosamente a {handle}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando DM de X: {str(e)}")
            return False
        
    def send_notification(
        self,
        recipient: Person,
        message: str,
        channels: Optional[List[str]] = None,
        template: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, bool]:
        """
        Envía una notificación a través de múltiples canales.
        
        Args:
            recipient: Objeto Person con la información del destinatario
            message: Contenido del mensaje
            channels: Lista de canales a usar (opcional)
            template: Plantilla a usar (opcional)
            metadata: Metadatos adicionales (opcional)
            
        Returns:
            Dict con resultados por canal
        """
        results = {}
        
        # Determinar canales a usar
        if not channels:
            channels = list(self.channels.keys())
            
        # Enviar por cada canal
        for channel in channels:
            if channel not in self.channels:
                logger.warning(f"Canal no soportado: {channel}")
                results[channel] = False
                continue
                
            if not self.channel_config[channel]['enabled']:
                logger.warning(f"Canal deshabilitado: {channel}")
                results[channel] = False
                continue
                
            try:
                if channel == 'email':
                    success = self.send_email(recipient, message, template=template)
                elif channel == 'whatsapp':
                    success = self.send_whatsapp(recipient.phone, message, template=template)
                elif channel == 'x':
                    success = self.send_x_dm(
                        recipient.social_handles.get('x'),
                        message,
                        template=template
                    )
                    
                results[channel] = success
                
            except Exception as e:
                logger.error(f"Error enviando por {channel}: {str(e)}")
                results[channel] = False
                
        return results
