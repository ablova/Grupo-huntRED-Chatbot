"""
Módulo de utilidades para tareas en Grupo huntRED.
Contiene funciones comunes que pueden ser utilizadas por múltiples tipos de tareas.
Optimizado para bajo uso de CPU y eficiencia.
"""

import logging
import json
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List, Union
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from app.models import BusinessUnit

# Configuración de logging
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

def get_business_unit(business_unit_id=None, default_name="huntred"):
    """
    Obtiene un objeto BusinessUnit por su ID o nombre.
    Utilidad compartida entre diferentes módulos de tareas.
    
    Args:
        business_unit_id: ID opcional de la unidad de negocio
        default_name: Nombre por defecto si no se proporciona ID
        
    Returns:
        BusinessUnit: Objeto BusinessUnit
    """
    try:
        if business_unit_id:
            return BusinessUnit.objects.get(id=business_unit_id)
        return BusinessUnit.objects.get(name__iexact=default_name)
    except BusinessUnit.DoesNotExist:
        logger.error(f"BusinessUnit no encontrada: ID={business_unit_id}, default={default_name}")
        # Intentar obtener cualquier BU activa
        try:
            return BusinessUnit.objects.filter(active=True).first()
        except:
            return None

def format_duration(seconds: float) -> str:
    """
    Formatea una duración en segundos a formato legible.
    
    Args:
        seconds: Duración en segundos
        
    Returns:
        str: Duración formateada (e.g., "1h 30m 45s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{int(minutes)}m {int(seconds)}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Trunca un texto a una longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        
    Returns:
        str: Texto truncado con indicador "..." si fue truncado
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."
