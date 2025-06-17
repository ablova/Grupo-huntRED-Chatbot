# app/ats/utils/formatters.py
from typing import Union, Optional
from datetime import datetime
import locale
import re

def format_currency(amount: Union[int, float], currency: str = 'MXN') -> str:
    """
    Formatea un número como moneda.
    
    Args:
        amount: Cantidad a formatear
        currency: Código de moneda (por defecto 'MXN')
        
    Returns:
        str: Cantidad formateada como moneda
    """
    try:
        locale.setlocale(locale.LC_ALL, 'es_MX.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'es_MX')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, '')
    
    return locale.currency(amount, grouping=True, symbol=True)

def format_date(date: Union[str, datetime], format_str: str = '%d/%m/%Y') -> str:
    """
    Formatea una fecha según el formato especificado.
    
    Args:
        date: Fecha a formatear (string o datetime)
        format_str: Formato de salida (por defecto '%d/%m/%Y')
        
    Returns:
        str: Fecha formateada
    """
    if isinstance(date, str):
        try:
            # Intentar parsear la fecha en varios formatos comunes
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                try:
                    date = datetime.strptime(date, fmt)
                    break
                except ValueError:
                    continue
            if isinstance(date, str):
                raise ValueError(f"No se pudo parsear la fecha: {date}")
        except ValueError as e:
            raise ValueError(f"Formato de fecha inválido: {str(e)}")
    
    return date.strftime(format_str)

def format_phone(phone: str, country_code: str = '+52') -> str:
    """
    Formatea un número de teléfono.
    
    Args:
        phone: Número de teléfono a formatear
        country_code: Código de país (por defecto '+52' para México)
        
    Returns:
        str: Número formateado
    """
    # Eliminar todos los caracteres no numéricos
    numbers = re.sub(r'\D', '', phone)
    
    # Si el número ya incluye código de país, no lo añadimos
    if phone.startswith('+'):
        country_code = ''
    
    # Formatear según la longitud
    if len(numbers) == 10:  # Número nacional
        return f"{country_code} {numbers[:3]} {numbers[3:7]} {numbers[7:]}"
    elif len(numbers) == 12:  # Número con código de país
        return f"+{numbers[:2]} {numbers[2:5]} {numbers[5:9]} {numbers[9:]}"
    else:
        return phone

def format_rfc(rfc: str) -> str:
    """
    Formatea un RFC mexicano.
    
    Args:
        rfc: RFC a formatear
        
    Returns:
        str: RFC formateado
    """
    rfc = rfc.upper().strip()
    if len(rfc) == 13:  # Persona física
        return f"{rfc[:4]}-{rfc[4:10]}-{rfc[10:]}"
    elif len(rfc) == 12:  # Persona moral
        return f"{rfc[:3]}-{rfc[3:9]}-{rfc[9:]}"
    return rfc

def format_cp(cp: str) -> str:
    """
    Formatea un código postal mexicano.
    
    Args:
        cp: Código postal a formatear
        
    Returns:
        str: Código postal formateado
    """
    cp = re.sub(r'\D', '', cp)
    if len(cp) == 5:
        return f"{cp[:2]}-{cp[2:]}"
    return cp

def format_percentage(value: Union[int, float], decimals: int = 2) -> str:
    """
    Formatea un número como porcentaje.
    
    Args:
        value: Valor a formatear
        decimals: Número de decimales (por defecto 2)
        
    Returns:
        str: Valor formateado como porcentaje
    """
    return f"{value:.{decimals}f}%"

def format_number(number: Union[int, float], decimals: int = 2, thousands_sep: str = ',', decimal_sep: str = '.') -> str:
    """
    Formatea un número con separadores de miles y decimales.
    
    Args:
        number: Número a formatear
        decimals: Número de decimales (por defecto 2)
        thousands_sep: Separador de miles (por defecto ',')
        decimal_sep: Separador decimal (por defecto '.')
        
    Returns:
        str: Número formateado
    """
    try:
        locale.setlocale(locale.LC_ALL, 'es_MX.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'es_MX')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, '')
    
    return locale.format_string(f"%.{decimals}f", number, grouping=True)

def format_name(name: str, title_case: bool = True) -> str:
    """
    Formatea un nombre propio.
    
    Args:
        name: Nombre a formatear
        title_case: Si es True, convierte a título (por defecto True)
        
    Returns:
        str: Nombre formateado
    """
    name = name.strip()
    if title_case:
        # Convertir a título pero preservar apellidos compuestos
        words = name.split()
        formatted_words = []
        for word in words:
            if word.lower() in ['de', 'del', 'la', 'las', 'los', 'y', 'e', 'o', 'u']:
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.title())
        return ' '.join(formatted_words)
    return name 