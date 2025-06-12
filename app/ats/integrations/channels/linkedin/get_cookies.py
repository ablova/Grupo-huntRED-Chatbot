"""
Módulo para obtener y gestionar cookies de LinkedIn.
"""
import os
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

def get_linkedin_cookies(email: str, password: str, cookies_path: str = 'linkedin_cookies.json') -> bool:
    """
    Obtiene cookies de LinkedIn mediante login.
    
    Args:
        email: Email de LinkedIn
        password: Contraseña de LinkedIn
        cookies_path: Ruta donde guardar las cookies
        
    Returns:
        bool: True si se obtuvieron las cookies exitosamente
    """
    try:
        # Configurar opciones del navegador
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Inicializar driver
        driver = webdriver.Chrome(options=options)
        
        try:
            # Ir a LinkedIn
            driver.get('https://www.linkedin.com/login')
            
            # Esperar y llenar formulario de login
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            email_field.send_keys(email)
            
            password_field = driver.find_element(By.ID, 'password')
            password_field.send_keys(password)
            
            # Hacer click en login
            driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
            
            # Esperar a que se complete el login
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.feed-identity-module'))
            )
            
            # Obtener cookies
            cookies = driver.get_cookies()
            
            # Guardar cookies
            with open(cookies_path, 'w') as f:
                json.dump(cookies, f)
                
            logger.info("Cookies de LinkedIn obtenidas exitosamente")
            return True
            
        except TimeoutException:
            logger.error("Timeout al intentar obtener cookies de LinkedIn")
            return False
            
        except Exception as e:
            logger.error(f"Error al obtener cookies de LinkedIn: {str(e)}")
            return False
            
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error en get_linkedin_cookies: {str(e)}")
        return False

def load_linkedin_cookies(cookies_path: str = 'linkedin_cookies.json') -> list:
    """
    Carga cookies de LinkedIn desde archivo.
    
    Args:
        cookies_path: Ruta del archivo de cookies
        
    Returns:
        list: Lista de cookies o lista vacía si hay error
    """
    try:
        if os.path.exists(cookies_path):
            with open(cookies_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error cargando cookies de LinkedIn: {str(e)}")
        return []

def are_cookies_valid(cookies_path: str = 'linkedin_cookies.json') -> bool:
    """
    Verifica si las cookies de LinkedIn son válidas.
    
    Args:
        cookies_path: Ruta del archivo de cookies
        
    Returns:
        bool: True si las cookies son válidas
    """
    try:
        cookies = load_linkedin_cookies(cookies_path)
        if not cookies:
            return False
            
        # Configurar opciones del navegador
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Inicializar driver
        driver = webdriver.Chrome(options=options)
        
        try:
            # Ir a LinkedIn
            driver.get('https://www.linkedin.com')
            
            # Añadir cookies
            for cookie in cookies:
                driver.add_cookie(cookie)
                
            # Recargar página
            driver.get('https://www.linkedin.com/feed/')
            
            # Verificar si estamos logueados
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.feed-identity-module'))
                )
                return True
            except TimeoutException:
                return False
                
        finally:
            driver.quit()
            
    except Exception as e:
        logger.error(f"Error verificando cookies de LinkedIn: {str(e)}")
        return False 