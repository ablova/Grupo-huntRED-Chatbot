"""
Utilidades de fecha y hora para Grupo huntRED®.
Funciones para manipulación de fechas, cálculos de tiempo y formateo.
"""

import logging
import pytz
from typing import Optional, Union, Dict, List
from datetime import datetime, date, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

def get_local_now(tz_name: str = "America/Mexico_City") -> datetime:
    """
    Obtiene la fecha y hora actual en la zona horaria especificada.
    
    Args:
        tz_name: Nombre de la zona horaria (por defecto: Ciudad de México)
        
    Returns:
        datetime: Fecha y hora actual en la zona horaria especificada
    """
    try:
        # Obtener fecha y hora UTC actual
        utc_now = datetime.now(pytz.UTC)
        
        # Convertir a la zona horaria especificada
        local_tz = pytz.timezone(tz_name)
        return utc_now.astimezone(local_tz)
    except Exception as e:
        logger.error(f"Error obteniendo hora local: {str(e)}")
        # Fallback a la hora de Django
        return timezone.now()


def format_date_for_locale(
    dt: Union[datetime, date],
    locale: str = "es_MX",
    format_type: str = "full",
    tz_name: str = None
) -> str:
    """
    Formatea una fecha según la configuración regional.
    
    Args:
        dt: Fecha a formatear
        locale: Configuración regional (es_MX, en_US, etc.)
        format_type: Tipo de formato (full, short, time_only)
        tz_name: Nombre opcional de zona horaria
        
    Returns:
        str: Fecha formateada
    """
    if not dt:
        return ""
    
    # Convertir a datetime si es una fecha
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())
    
    # Agregar zona horaria si no tiene
    if tz_name and dt.tzinfo is None:
        local_tz = pytz.timezone(tz_name)
        dt = local_tz.localize(dt)
    
    # Formatear según locale y tipo
    if locale.startswith("es"):
        # Formatos para español
        if format_type == "full":
            # lunes, 19 de mayo de 2025
            month_names = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
                          "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            weekday = day_names[dt.weekday()]
            return f"{weekday}, {dt.day} de {month_names[dt.month-1]} de {dt.year}"
        elif format_type == "short":
            # 19/05/2025
            return f"{dt.day:02d}/{dt.month:02d}/{dt.year}"
        elif format_type == "time_only":
            # 10:30
            return f"{dt.hour:02d}:{dt.minute:02d}"
        elif format_type == "datetime":
            # 19/05/2025 10:30
            return f"{dt.day:02d}/{dt.month:02d}/{dt.year} {dt.hour:02d}:{dt.minute:02d}"
    else:
        # Formatos para inglés y otros
        if format_type == "full":
            # Monday, May 19, 2025
            return dt.strftime("%A, %B %d, %Y")
        elif format_type == "short":
            # 05/19/2025
            return dt.strftime("%m/%d/%Y")
        elif format_type == "time_only":
            # 10:30 AM
            return dt.strftime("%I:%M %p")
        elif format_type == "datetime":
            # 05/19/2025 10:30 AM
            return dt.strftime("%m/%d/%Y %I:%M %p")
    
    # Formato por defecto
    return dt.isoformat()


def get_next_business_day(
    from_date: Optional[Union[datetime, date]] = None,
    skip_days: int = 1,
    holidays: List[date] = None
) -> date:
    """
    Calcula el siguiente día hábil, saltando fines de semana y feriados.
    
    Args:
        from_date: Fecha de inicio (por defecto: hoy)
        skip_days: Número de días hábiles a saltar
        holidays: Lista de fechas feriadas a excluir
        
    Returns:
        date: Siguiente día hábil
    """
    if from_date is None:
        from_date = timezone.now().date()
    elif isinstance(from_date, datetime):
        from_date = from_date.date()
    
    if holidays is None:
        holidays = []
    
    business_days = 0
    current_date = from_date
    
    while business_days < skip_days:
        current_date += timedelta(days=1)
        
        # Verificar si es fin de semana (5=sábado, 6=domingo)
        if current_date.weekday() >= 5:
            continue
        
        # Verificar si es feriado
        if current_date in holidays:
            continue
        
        # Es día hábil
        business_days += 1
    
    return current_date


def calculate_date_difference(
    start_date: Union[datetime, date],
    end_date: Union[datetime, date] = None,
    unit: str = "days"
) -> int:
    """
    Calcula la diferencia entre dos fechas en la unidad especificada.
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin (por defecto: ahora)
        unit: Unidad de tiempo (days, hours, minutes, seconds)
        
    Returns:
        int: Diferencia en la unidad especificada
    """
    if end_date is None:
        end_date = timezone.now()
    
    # Convertir a datetime si es una fecha
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.min.time())
    
    # Asegurar que ambos tienen zona horaria
    if start_date.tzinfo is None:
        start_date = pytz.UTC.localize(start_date)
    if end_date.tzinfo is None:
        end_date = pytz.UTC.localize(end_date)
    
    # Calcular diferencia
    diff = end_date - start_date
    
    # Convertir a la unidad solicitada
    if unit == "days":
        return diff.days
    elif unit == "hours":
        return int(diff.total_seconds() / 3600)
    elif unit == "minutes":
        return int(diff.total_seconds() / 60)
    elif unit == "seconds":
        return int(diff.total_seconds())
    else:
        # Unidad no reconocida, devolver días por defecto
        return diff.days
