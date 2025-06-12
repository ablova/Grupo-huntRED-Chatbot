"""
Módulo para gestionar mensajes de LinkedIn.
"""
import logging
import time
from typing import Optional, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .channel import LinkedInChannel
from app.ats.integrations.ai.insights import generate_personalized_message

logger = logging.getLogger(__name__)

class LinkedInMessaging:
    """
    Clase para gestionar mensajes de LinkedIn.
    """
    
    def __init__(self, channel: LinkedInChannel):
        """
        Inicializa el gestor de mensajes.
        
        Args:
            channel: Canal de LinkedIn
        """
        self.channel = channel
        
    def send_message(self, profile_url: str, message: str) -> bool:
        """
        Envía un mensaje a un perfil de LinkedIn.
        
        Args:
            profile_url: URL del perfil
            message: Mensaje a enviar
            
        Returns:
            bool: True si el mensaje se envió exitosamente
        """
        try:
            # Ir al perfil
            self.channel.driver.get(profile_url)
            time.sleep(2)  # Esperar a que cargue
            
            # Hacer click en el botón de mensaje
            message_button = WebDriverWait(self.channel.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="mensaje"]'))
            )
            message_button.click()
            
            # Esperar a que se abra el chat
            message_input = WebDriverWait(self.channel.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]'))
            )
            
            # Escribir mensaje
            message_input.send_keys(message)
            
            # Enviar mensaje
            send_button = self.channel.driver.find_element(
                By.CSS_SELECTOR, 
                'button[aria-label*="enviar"]'
            )
            send_button.click()
            
            # Esperar a que se envíe
            time.sleep(2)
            
            logger.info(f"Mensaje enviado exitosamente a {profile_url}")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout al enviar mensaje a {profile_url}")
            return False
            
        except NoSuchElementException:
            logger.error(f"No se encontró el botón de mensaje en {profile_url}")
            return False
            
        except Exception as e:
            logger.error(f"Error al enviar mensaje a {profile_url}: {str(e)}")
            return False
            
    def send_connection_request(
        self, 
        profile_url: str, 
        message: Optional[str] = None,
        template: Optional[str] = None
    ) -> bool:
        """
        Envía una solicitud de conexión con mensaje personalizado.
        
        Args:
            profile_url: URL del perfil
            message: Mensaje personalizado (opcional)
            template: Template para generar mensaje (opcional)
            
        Returns:
            bool: True si la solicitud se envió exitosamente
        """
        try:
            # Ir al perfil
            self.channel.driver.get(profile_url)
            time.sleep(2)  # Esperar a que cargue
            
            # Obtener información del perfil
            profile_info = self.channel.get_profile_info(profile_url)
            if not profile_info:
                logger.error(f"No se pudo obtener información del perfil {profile_url}")
                return False
                
            # Generar mensaje si no se proporciona
            if not message and template:
                message = generate_personalized_message(profile_info, template)
            elif not message:
                message = f"Hola {profile_info.get('name', '')}, me gustaría conectar contigo en LinkedIn."
                
            # Hacer click en conectar
            connect_button = WebDriverWait(self.channel.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="conectar"]'))
            )
            connect_button.click()
            
            # Esperar a que se abra el modal
            time.sleep(1)
            
            # Añadir nota
            add_note_button = WebDriverWait(self.channel.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="añadir nota"]'))
            )
            add_note_button.click()
            
            # Escribir mensaje
            message_input = WebDriverWait(self.channel.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[aria-label*="mensaje"]'))
            )
            message_input.send_keys(message)
            
            # Enviar solicitud
            send_button = self.channel.driver.find_element(
                By.CSS_SELECTOR, 
                'button[aria-label*="enviar"]'
            )
            send_button.click()
            
            # Esperar a que se envíe
            time.sleep(2)
            
            logger.info(f"Solicitud de conexión enviada exitosamente a {profile_url}")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout al enviar solicitud a {profile_url}")
            return False
            
        except NoSuchElementException:
            logger.error(f"No se encontró el botón de conectar en {profile_url}")
            return False
            
        except Exception as e:
            logger.error(f"Error al enviar solicitud a {profile_url}: {str(e)}")
            return False 