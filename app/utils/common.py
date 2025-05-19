"""
Utilidades comunes para Grupo huntRED®.
Funciones de uso general compartidas entre múltiples módulos.
"""

import logging
import re
from typing import Optional, Any, Dict, Union
from django.conf import settings
from django.db.models import Q
from app.models import BusinessUnit

logger = logging.getLogger(__name__)

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


def get_business_unit(business_unit_id=None, default_name="huntred"):
    """
    Obtiene un objeto BusinessUnit por su ID o nombre.
    Utilidad compartida entre diferentes módulos.
    
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


def sanitize_string(text: str, allow_html: bool = False) -> str:
    """
    Sanitiza un string para prevenir inyección de código.
    
    Args:
        text: Texto a sanitizar
        allow_html: Si se permiten etiquetas HTML básicas
        
    Returns:
        str: Texto sanitizado
    """
    if not text:
        return ""
    
    # Eliminar caracteres potencialmente peligrosos
    if not allow_html:
        # Eliminar todas las etiquetas HTML
        text = re.sub(r'<[^>]*>', '', text)
        
        # Eliminar scripts y otros elementos peligrosos
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    else:
        # Permitir solo etiquetas HTML seguras
        allowed_tags = ['b', 'i', 'u', 'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'strong', 'em', 'a', 'span']
        
        # Reemplazar todas las etiquetas excepto las permitidas
        for tag in re.findall(r'<\/?([a-z][a-z0-9]*)\b[^>]*>', text, re.IGNORECASE):
            if tag.lower() not in allowed_tags:
                text = re.sub(r'<\/?{}\b[^>]*>'.format(tag), '', text, flags=re.IGNORECASE)
        
        # Eliminar scripts y eventos
        text = re.sub(r'<script\b[^>]*>(.*?)<\/script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'on\w+\s*=\s*(["\']).*?\1', '', text, flags=re.IGNORECASE)
    
    return text


def generate_unique_token(prefix: str = '', length: int = 32) -> str:
    """
    Genera un token único aleatorio para identificación segura.
    Optimizado para reducir colisiones y mejorar la seguridad.
    
    Args:
        prefix: Prefijo opcional para el token
        length: Longitud deseada del token (sin contar prefijo)
        
    Returns:
        str: Token único generado
    """
    import uuid
    import hashlib
    import time
    
    # Combinar UUID, timestamp y salt para mayor unicidad
    unique_id = str(uuid.uuid4())
    timestamp = str(time.time())
    salt = str(hash(prefix or 'huntred'))
    
    # Crear hash usando SHA-256
    token_seed = f"{unique_id}-{timestamp}-{salt}"
    token_hash = hashlib.sha256(token_seed.encode()).hexdigest()
    
    # Truncar a la longitud deseada y añadir prefijo
    if prefix:
        return f"{prefix}_{token_hash[:length]}"
    
    return token_hash[:length]


def generate_qr_code(data: str, size: int = 200, error_correction: str = 'H') -> str:
    """
    Genera un código QR como imagen en formato base64 para inclusión directa en HTML.
    Optimizado para bajo uso de CPU mediante caché de resultados frecuentes.
    
    Args:
        data: Datos a codificar en el QR (generalmente una URL)
        size: Tamaño en píxeles del código QR (altura y anchura)
        error_correction: Nivel de corrección de errores ('L', 'M', 'Q', 'H')
        
    Returns:
        str: Imagen del código QR en formato base64 (data URI)
    """
    try:
        import qrcode
        import base64
        from io import BytesIO
        import hashlib
        from django.core.cache import cache
        
        # Generar una clave de caché basada en los parámetros
        cache_key = f"qr_code_{hashlib.md5(data.encode()).hexdigest()}_{size}_{error_correction}"
        
        # Verificar si ya existe en caché
        cached_qr = cache.get(cache_key)
        if cached_qr:
            return cached_qr
        
        # Mapear nivel de corrección de errores
        error_levels = {
            'L': qrcode.constants.ERROR_CORRECT_L,  # 7% de recuperación
            'M': qrcode.constants.ERROR_CORRECT_M,  # 15% de recuperación
            'Q': qrcode.constants.ERROR_CORRECT_Q,  # 25% de recuperación
            'H': qrcode.constants.ERROR_CORRECT_H   # 30% de recuperación
        }
        ec_level = error_levels.get(error_correction, error_levels['H'])
        
        # Crear código QR
        qr = qrcode.QRCode(
            version=None,  # Automático
            error_correction=ec_level,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Redimensionar si es necesario
        if size != 200:  # Si no es el tamaño por defecto
            img = img.resize((size, size))
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Formato data URI para inclusión en HTML
        data_uri = f"data:image/png;base64,{img_str}"
        
        # Guardar en caché por 1 día (86400 segundos)
        cache.set(cache_key, data_uri, 86400)
        
        return data_uri
    except Exception as e:
        logger.error(f"Error generando código QR: {str(e)}")
        # Retornar una URL de imagen de error o placeholder
        return ""


def validate_email(email: str) -> bool:
    """
    Valida si un email tiene formato correcto.
    
    Args:
        email: Dirección de email a validar
        
    Returns:
        bool: True si el formato es válido, False en caso contrario
    """
    if not email:
        return False
    
    # Patrón básico de validación de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Valida si un número de teléfono tiene formato correcto.
    Acepta formatos internacionales y nacionales comunes.
    
    Args:
        phone: Número telefónico a validar
        
    Returns:
        bool: True si el formato es válido, False en caso contrario
    """
    if not phone:
        return False
    
    # Eliminar caracteres no numéricos excepto + al inicio
    cleaned_phone = re.sub(r'[^0-9+]', '', phone)
    
    # Verificar si comienza con + (formato internacional)
    if cleaned_phone.startswith('+'):
        # Debe tener entre 8 y 15 dígitos después del +
        return bool(re.match(r'^\+[0-9]{8,15}$', cleaned_phone))
    
    # Para números sin código internacional, aceptar 8-10 dígitos
    return bool(re.match(r'^[0-9]{8,10}$', cleaned_phone))
    
    return text


def format_currency(amount: Union[int, float], currency: str = "MXN") -> str:
    """
    Formatea una cantidad como moneda.
    
    Args:
        amount: Cantidad a formatear
        currency: Código de moneda (MXN, USD, etc.)
        
    Returns:
        str: Cantidad formateada como moneda
    """
    if amount is None:
        return "0.00"
    
    # Formatear según moneda
    if currency == "MXN":
        return f"${amount:,.2f} MXN"
    elif currency == "USD":
        return f"${amount:,.2f} USD"
    else:
        return f"{amount:,.2f} {currency}"
