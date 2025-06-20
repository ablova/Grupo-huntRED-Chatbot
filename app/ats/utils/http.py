"""
Utilidades HTTP y APIs para Grupo huntRED®.
Funciones compartidas para comunicación HTTP, APIs y solicitudes asíncronas.
"""

import logging
import aiohttp
import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union
from django.conf import settings

logger = logging.getLogger(__name__)

async def fetch_data_async(url: str, headers: Dict = None, timeout: int = 30) -> Dict:
    """
    Realiza una petición HTTP GET asíncrona.
    
    Args:
        url: URL a consultar
        headers: Cabeceras HTTP opcionales
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        dict: Respuesta JSON o error
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Error en fetch_data_async: {response.status} - {url}")
                    return {"error": f"Status code: {response.status}"}
    except Exception as e:
        logger.error(f"Excepción en fetch_data_async: {str(e)} - {url}")
        return {"error": str(e)}


async def post_data_async(url: str, data: Dict, headers: Dict = None, timeout: int = 30) -> Dict:
    """
    Realiza una petición HTTP POST asíncrona.
    
    Args:
        url: URL a consultar
        data: Datos a enviar (serán convertidos a JSON)
        headers: Cabeceras HTTP opcionales
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        dict: Respuesta JSON o error
    """
    try:
        if not headers:
            headers = {"Content-Type": "application/json"}
        elif "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=timeout) as response:
                if response.status in (200, 201, 202):
                    return await response.json()
                else:
                    logger.error(f"Error en post_data_async: {response.status} - {url}")
                    return {"error": f"Status code: {response.status}"}
    except Exception as e:
        logger.error(f"Excepción en post_data_async: {str(e)} - {url}")
        return {"error": str(e)}


def handle_api_response(response, default_value=None):
    """
    Maneja respuestas de API, extraer datos o manejar errores.
    
    Args:
        response: Respuesta de API
        default_value: Valor por defecto si hay error
        
    Returns:
        object: Datos extraídos o valor por defecto
    """
    if isinstance(response, dict) and "error" in response:
        logger.error(f"Error en respuesta API: {response['error']}")
        return default_value
    
    return response


async def retry_request(func, *args, max_retries=3, backoff_factor=1.5, **kwargs):
    """
    Reintenta una solicitud HTTP con backoff exponencial.
    
    Args:
        func: Función asíncrona a reintentar
        *args: Argumentos para la función
        max_retries: Número máximo de reintentos
        backoff_factor: Factor de espera entre reintentos
        **kwargs: Argumentos de palabra clave para la función
        
    Returns:
        object: Respuesta de la función o error
    """
    retry = 0
    last_exception = None
    
    while retry < max_retries:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            retry += 1
            last_exception = e
            
            # Si es el último intento, propagar la excepción
            if retry >= max_retries:
                logger.error(f"Error después de {max_retries} intentos: {str(e)}")
                break
            
            # Esperar con backoff exponencial
            wait_time = backoff_factor * (2 ** (retry - 1))
            logger.warning(f"Reintento {retry}/{max_retries} después de {wait_time:.1f}s: {str(e)}")
            await asyncio.sleep(wait_time)
    
    # Si llegamos aquí, todos los intentos fallaron
    return {"error": f"Max retries exceeded: {str(last_exception)}"}
