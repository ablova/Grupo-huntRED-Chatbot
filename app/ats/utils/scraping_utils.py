# app/ats/utils/scraping_utils.py
# Utilidades básicas para scraping usando Playwright
import logging
import random
import time
import asyncio
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class PlaywrightAntiDeteccion:
    """
    Clase que proporciona métodos para evitar la detección durante el web scraping.
    """
    @staticmethod
    async def simular_comportamiento_humano(page) -> None:
        """
        Simula comportamiento humano básico en la página para evitar detección.
        
        Args:
            page: Objeto Page de Playwright
        """
        try:
            # Simular scroll aleatorio
            await page.evaluate("""
                () => {
                    const scrollAmount = Math.floor(Math.random() * 200) + 100;
                    window.scrollBy(0, scrollAmount);
                }
            """)
            
            # Esperar un tiempo aleatorio
            await asyncio.sleep(random.uniform(1, 3))
            
            # Mover el ratón a una posición aleatoria
            width = await page.evaluate('() => window.innerWidth')
            height = await page.evaluate('() => window.innerHeight')
            x = random.randint(0, width)
            y = random.randint(0, height)
            await page.mouse.move(x, y)
            
            logger.debug("Comportamiento humano simulado exitosamente")
            
        except Exception as e:
            logger.error(f"Error simulando comportamiento humano: {e}")


async def inicializar_contexto_playwright(browser, user_agent=None, cookies=None, viewport=None):
    """
    Inicializa un nuevo contexto de navegación en Playwright con configuraciones personalizadas.
    
    Args:
        browser: Objeto Browser de Playwright
        user_agent: User-Agent personalizado
        cookies: Cookies preexistentes
        viewport: Tamaño de viewport personalizado
    
    Returns:
        Un contexto de navegación configurado
    """
    try:
        context_options = {}
        
        # Configurar user agent
        if user_agent:
            context_options['user_agent'] = user_agent
        
        # Configurar viewport
        if viewport:
            context_options['viewport'] = viewport
        else:
            # Viewport aleatorio realista
            context_options['viewport'] = {
                'width': random.choice([1366, 1440, 1536, 1600, 1920]),
                'height': random.choice([768, 800, 900, 1080])
            }
            
        # Crear contexto
        context = await browser.new_context(**context_options)
        
        # Añadir cookies si existen
        if cookies:
            await context.add_cookies(cookies)
            
        logger.debug("Contexto de Playwright inicializado correctamente")
        return context
        
    except Exception as e:
        logger.error(f"Error inicializando contexto Playwright: {e}")
        raise


async def visitar_pagina_humanizada(page, url, timeout=30000):
    """
    Visita una página web simulando comportamiento humano.
    
    Args:
        page: Objeto Page de Playwright
        url: URL a visitar
        timeout: Tiempo de espera máximo en milisegundos
    
    Returns:
        True si la visita fue exitosa, False en caso contrario
    """
    try:
        # Navegar a la URL
        await page.goto(url, timeout=timeout)
        
        # Esperar un tiempo aleatorio
        await asyncio.sleep(random.uniform(1, 3))
        
        # Simular comportamiento humano
        await PlaywrightAntiDeteccion.simular_comportamiento_humano(page)
        
        logger.debug(f"Página {url} visitada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error visitando página {url}: {e}")
        return False


async def extraer_y_guardar_cookies(context, archivo_cookies=None):
    """
    Extrae las cookies del contexto actual y opcionalmente las guarda en un archivo.
    
    Args:
        context: Contexto de navegación de Playwright
        archivo_cookies: Ruta al archivo donde guardar las cookies (opcional)
    
    Returns:
        Lista de cookies extraídas
    """
    try:
        cookies = await context.cookies()
        
        if archivo_cookies:
            import json
            with open(archivo_cookies, 'w') as f:
                json.dump(cookies, f)
            logger.debug(f"Cookies guardadas en {archivo_cookies}")
            
        return cookies
        
    except Exception as e:
        logger.error(f"Error extrayendo/guardando cookies: {e}")
        return []
