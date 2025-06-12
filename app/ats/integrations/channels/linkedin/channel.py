from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import time
import random
import logging
from typing import List, Dict, Optional
from app.models import USER_AGENTS

logger = logging.getLogger(__name__)

class LinkedInChannel:
    """Canal de LinkedIn para envío de mensajes y conexiones."""
    
    def __init__(self, cookies_path: str):
        """
        Inicializa el canal de LinkedIn.
        
        Args:
            cookies_path: Ruta al archivo de cookies
        """
        self.cookies_path = cookies_path
        self.driver = None
        self._setup_driver()
        
    def _setup_driver(self):
        """Configura el driver de Selenium con un USER_AGENT aleatorio."""
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
        self.driver = webdriver.Chrome(options=options)
        
    def _load_cookies(self):
        """Carga las cookies de sesión."""
        try:
            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)
                
            for cookie in cookies:
                self.driver.add_cookie(cookie)
                
            return True
        except Exception as e:
            logger.error(f"Error al cargar cookies: {str(e)}")
            return False
            
    def _random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Agrega un delay aleatorio para evitar detección."""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def send_connection_request(self, profile_url: str, message: str) -> bool:
        """
        Envía una solicitud de conexión con mensaje personalizado.
        
        Args:
            profile_url: URL del perfil de LinkedIn
            message: Mensaje personalizado para la solicitud
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            self.driver.get(profile_url)
            self._random_delay()
            
            # Hacer clic en "Conectar"
            connect_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-button--secondary"))
            )
            connect_button.click()
            
            self._random_delay()
            
            # Agregar nota
            add_note_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-button--secondary"))
            )
            add_note_button.click()
            
            self._random_delay()
            
            # Escribir mensaje
            message_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea#custom-message"))
            )
            message_input.send_keys(message)
            
            self._random_delay()
            
            # Enviar solicitud
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button.artdeco-button--primary")
            send_button.click()
            
            logger.info(f"Solicitud enviada a {profile_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar solicitud a {profile_url}: {str(e)}")
            return False
            
    def send_message(self, profile_url: str, message: str) -> bool:
        """
        Envía un mensaje a un contacto existente.
        
        Args:
            profile_url: URL del perfil de LinkedIn
            message: Mensaje a enviar
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            self.driver.get(profile_url)
            self._random_delay()
            
            # Hacer clic en "Mensaje"
            message_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-button--secondary"))
            )
            message_button.click()
            
            self._random_delay()
            
            # Escribir mensaje
            message_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.msg-form__contenteditable"))
            )
            message_input.send_keys(message)
            
            self._random_delay()
            
            # Enviar mensaje
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button.msg-form__send-button")
            send_button.click()
            
            logger.info(f"Mensaje enviado a {profile_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar mensaje a {profile_url}: {str(e)}")
            return False
            
    def get_profile_info(self, profile_url: str) -> Optional[Dict]:
        """
        Obtiene información básica del perfil.
        
        Args:
            profile_url: URL del perfil de LinkedIn
            
        Returns:
            Dict con información del perfil o None si hay error
        """
        try:
            self.driver.get(profile_url)
            self._random_delay()
            
            info = {
                'name': self.driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge").text,
                'headline': self.driver.find_element(By.CSS_SELECTOR, "div.text-body-medium").text,
                'location': self.driver.find_element(By.CSS_SELECTOR, "span.text-body-small").text,
                'last_activity': None
            }
            
            # Intentar obtener última actividad
            try:
                activity = self.driver.find_element(By.CSS_SELECTOR, "span.text-body-small").text
                if "actividad" in activity.lower():
                    info['last_activity'] = activity
            except:
                pass
                
            return info
            
        except Exception as e:
            logger.error(f"Error al obtener información de {profile_url}: {str(e)}")
            return None
            
    def close(self):
        """Cierra el driver de Selenium."""
        if self.driver:
            self.driver.quit() 