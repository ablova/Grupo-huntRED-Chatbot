"""
Módulo centralizado de utilidades para Grupo huntRED®.
Este archivo registra todas las utilidades compartidas en el sistema,
siguiendo la estructura modular y las reglas globales.
"""

import logging
import warnings
from django.utils.deprecation import RemovedInNextVersionWarning

logger = logging.getLogger(__name__)

# Advertencia para el archivo utils.py obsoleto
warnings.warn(
    "El archivo app/utils.py está obsoleto. Usa los módulos específicos en app/utils/",
    RemovedInNextVersionWarning, stacklevel=2
)

# Importar utilidades comunes
from app.utils.common import (
    format_duration, truncate_text, get_business_unit, 
    sanitize_string, format_currency
)

# Importar utilidades de análisis
from app.utils.analysis import (
    calculate_similarity_score, extract_keywords, 
    analyze_text_sentiment
)

# Importar utilidades de HTTP/API
from app.utils.http import (
    fetch_data_async, post_data_async, 
    handle_api_response, retry_request
)

# Importar utilidades de fecha/tiempo
from app.utils.date import (
    get_local_now, format_date_for_locale,
    get_next_business_day, calculate_date_difference
)

# Definir qué se expone al importar desde app.utils
__all__ = [
    # Utilidades comunes
    'format_duration', 'truncate_text', 'get_business_unit',
    'sanitize_string', 'format_currency',
    
    # Utilidades de análisis
    'calculate_similarity_score', 'extract_keywords',
    'analyze_text_sentiment',
    
    # Utilidades HTTP/API
    'fetch_data_async', 'post_data_async',
    'handle_api_response', 'retry_request',
    
    # Utilidades de fecha/tiempo
    'get_local_now', 'format_date_for_locale',
    'get_next_business_day', 'calculate_date_difference'
]
