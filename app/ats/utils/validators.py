# /home/pablo/app/ats/utils/validators.py
import re
from typing import Optional
from datetime import datetime

def validate_email(email: str) -> bool:
    """
    Valida un email usando una expresión regular.
    
    Args:
        email: Email a validar
        
    Returns:
        bool: True si el email es válido, False en caso contrario
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """
    Valida un número de teléfono.
    
    Args:
        phone: Número de teléfono a validar
        
    Returns:
        bool: True si el número es válido, False en caso contrario
    """
    # Eliminar espacios, guiones y paréntesis
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Validar formato internacional
    if phone.startswith('+'):
        return bool(re.match(r'^\+\d{10,15}$', phone))
    
    # Validar formato nacional
    return bool(re.match(r'^\d{10}$', phone))

def validate_rfc(rfc: str) -> bool:
    """
    Valida un RFC mexicano.
    
    Args:
        rfc: RFC a validar
        
    Returns:
        bool: True si el RFC es válido, False en caso contrario
    """
    # Patrón para RFC de persona física
    pattern_fisica = r'^[A-Z]{4}\d{6}[A-Z0-9]{3}$'
    # Patrón para RFC de persona moral
    pattern_moral = r'^[A-Z]{3}\d{6}[A-Z0-9]{3}$'
    
    rfc = rfc.upper()
    return bool(re.match(pattern_fisica, rfc) or re.match(pattern_moral, rfc))

def validate_cp(cp: str) -> bool:
    """
    Valida un código postal mexicano.
    
    Args:
        cp: Código postal a validar
        
    Returns:
        bool: True si el código postal es válido, False en caso contrario
    """
    return bool(re.match(r'^\d{5}$', cp))

def validate_url(url: str) -> bool:
    """
    Valida una URL.
    
    Args:
        url: URL a validar
        
    Returns:
        bool: True si la URL es válida, False en caso contrario
    """
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(pattern, url))

def validate_linkedin_url(url: str) -> bool:
    """
    Valida una URL de LinkedIn.
    
    Args:
        url: URL de LinkedIn a validar
        
    Returns:
        bool: True si la URL es válida, False en caso contrario
    """
    pattern = r'^https?:\/\/(www\.)?linkedin\.com\/(in|company)\/[\w\-]+\/?$'
    return bool(re.match(pattern, url))

def validate_age(birth_date: str, min_age: int = 18, max_age: int = 100) -> bool:
    """
    Valida si una persona está dentro de un rango de edad.
    
    Args:
        birth_date: Fecha de nacimiento en formato YYYY-MM-DD
        min_age: Edad mínima permitida
        max_age: Edad máxima permitida
        
    Returns:
        bool: True si la edad está dentro del rango, False en caso contrario
    """
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return min_age <= age <= max_age
    except ValueError:
        return False

def validate_salary(salary: str) -> bool:
    """
    Valida un formato de salario.
    
    Args:
        salary: Salario a validar (puede incluir símbolos de moneda y separadores)
        
    Returns:
        bool: True si el formato es válido, False en caso contrario
    """
    # Eliminar símbolos de moneda y espacios
    salary = re.sub(r'[^\d.,]', '', salary)
    # Validar formato numérico
    return bool(re.match(r'^\d{1,3}(,\d{3})*(\.\d{2})?$', salary))

def validate_gender(gender: str) -> bool:
    """
    Valida un género.
    
    Args:
        gender: Género a validar
        
    Returns:
        bool: True si el género es válido, False en caso contrario
    """
    valid_genders = ['masculino', 'femenino', 'otro', 'prefiero no decirlo']
    return gender.lower() in valid_genders 