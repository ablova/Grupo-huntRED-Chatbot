from typing import Optional, List, Dict, Union, Any
from app.models import BusinessUnit
from app.com.chatbot.integrations.services import MessageService

async def send_message(platform: str, user_id: str, message: str, business_unit: Optional[str] = None) -> bool:
    """Wrapper para enviar mensajes de forma asíncrona."""
    if not business_unit:
        business_unit = "default"  # Unidad por defecto
    
    try:
        bu = BusinessUnit.objects.get(name__iexact=business_unit)
        service = MessageService(bu)
        return await service.send_message(platform, user_id, message)
    except BusinessUnit.DoesNotExist:
        logger.error(f"Unidad de negocio no encontrada: {business_unit}")
        return False

async def send_menu(platform: str, user_id: str, business_unit: Optional[str] = None) -> bool:
    """Wrapper para enviar el menú principal."""
    if not business_unit:
        business_unit = "default"
    
    try:
        bu = BusinessUnit.objects.get(name__iexact=business_unit)
        service = MessageService(bu)
        return await service.send_menu(platform, user_id)
    except BusinessUnit.DoesNotExist:
        logger.error(f"Unidad de negocio no encontrada: {business_unit}")
        return False

async def send_image(platform: str, user_id: str, message: str, image_url: str, business_unit: Optional[str] = None) -> bool:
    """Wrapper para enviar imágenes."""
    if not business_unit:
        business_unit = "default"
    
    try:
        bu = BusinessUnit.objects.get(name__iexact=business_unit)
        service = MessageService(bu)
        return await service.send_image(platform, user_id, message, image_url)
    except BusinessUnit.DoesNotExist:
        logger.error(f"Unidad de negocio no encontrada: {business_unit}")
        return False

async def send_options(platform: str, user_id: str, message: str, buttons: Optional[List[Dict]] = None, business_unit: Optional[str] = None) -> bool:
    """Wrapper para enviar opciones interactivas."""
    if not business_unit:
        business_unit = "default"
    
    try:
        bu = BusinessUnit.objects.get(name__iexact=business_unit)
        service = MessageService(bu)
        return await service.send_options(platform, user_id, message, buttons)
    except BusinessUnit.DoesNotExist:
        logger.error(f"Unidad de negocio no encontrada: {business_unit}")
        return False
