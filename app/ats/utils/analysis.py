"""
Utilidades de análisis para Grupo huntRED®.
Funciones compartidas para análisis de texto, similitud y procesamiento de datos.
"""

import logging
import re
from typing import List, Dict, Any, Set, Tuple, Optional
from django.conf import settings
import numpy as np

logger = logging.getLogger(__name__)

def calculate_similarity_score(text1: str, text2: str) -> float:
    """
    Calcula la puntuación de similitud entre dos textos usando
    medidas básicas de similitud léxica.
    
    Args:
        text1: Primer texto para comparar
        text2: Segundo texto para comparar
        
    Returns:
        float: Puntuación de similitud (0-1)
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalizar textos
    text1 = text1.lower()
    text2 = text2.lower()
    
    # Eliminar signos de puntuación y caracterres especiales
    text1 = re.sub(r'[^\w\s]', '', text1)
    text2 = re.sub(r'[^\w\s]', '', text2)
    
    # Tokenizar
    tokens1 = set(text1.split())
    tokens2 = set(text2.split())
    
    # Calcular similitud de Jaccard
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def extract_keywords(text: str, stop_words: Set[str] = None, min_length: int = 3) -> List[str]:
    """
    Extrae palabras clave de un texto, eliminando palabras comunes (stop words).
    
    Args:
        text: Texto del cual extraer palabras clave
        stop_words: Conjunto de palabras a ignorar
        min_length: Longitud mínima de palabras a considerar
        
    Returns:
        List[str]: Lista de palabras clave extraídas
    """
    if not text:
        return []
    
    # Normalizar texto
    text = text.lower()
    
    # Eliminar signos de puntuación y caracteres especiales
    text = re.sub(r'[^\w\s]', '', text)
    
    # Si no se proporcionan stop words, usar un conjunto básico
    if stop_words is None:
        stop_words = {
            'a', 'al', 'algo', 'algunas', 'algunos', 'ante', 'antes', 'como', 'con',
            'contra', 'cual', 'cuando', 'de', 'del', 'desde', 'donde', 'durante',
            'e', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 'erais',
            'éramos', 'eran', 'eras', 'eres', 'es', 'esa', 'esas', 'ese', 'eso',
            'esos', 'esta', 'estaba', 'estabais', 'estábamos', 'estaban', 'estabas',
            'estad', 'estada', 'estadas', 'estado', 'estados', 'estáis', 'estamos',
            'están', 'estar', 'estará', 'estarán', 'estarás', 'estaré', 'estaréis',
            'estaremos', 'estás', 'este', 'esto', 'estos', 'estoy', 'etc', 'ha',
            'hace', 'haces', 'hacéis', 'hacemos', 'hacen', 'hacer', 'hacia', 'hago',
            'hasta', 'he', 'hecho', 'hay', 'la', 'las', 'le', 'les', 'lo', 'los', 'me',
            'mi', 'mis', 'mucho', 'muchos', 'muy', 'ni', 'no', 'nos', 'nosotras',
            'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'os', 'otra',
            'otras', 'otro', 'otros', 'para', 'pero', 'por', 'porque', 'que', 'qué',
            'quien', 'quienes', 'quién', 'quiénes', 'se', 'sea', 'seáis', 'seamos',
            'sean', 'seas', 'ser', 'será', 'serán', 'serás', 'seré', 'seréis', 'seremos',
            'si', 'sí', 'sido', 'siendo', 'sin', 'sobre', 'sois', 'somos', 'son', 'soy',
            'su', 'sus', 'suya', 'suyas', 'suyo', 'suyos', 'también', 'tanto', 'te',
            'tenéis', 'tenemos', 'tener', 'tengo', 'ti', 'tiene', 'tienen', 'tienes',
            'todo', 'todos', 'tu', 'tú', 'tus', 'tuve', 'tuvieron', 'tuvimos', 'tuviste',
            'tuvisteis', 'tuvo', 'un', 'una', 'uno', 'unos', 'vosotras', 'vosotros',
            'vuestra', 'vuestras', 'vuestro', 'vuestros', 'y', 'ya', 'yo'
        }
    
    # Tokenizar
    tokens = text.split()
    
    # Filtrar stop words y palabras cortas
    keywords = [word for word in tokens if word not in stop_words and len(word) >= min_length]
    
    # Obtener frecuencias
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Ordenar por frecuencia
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, freq in sorted_keywords]


def analyze_text_sentiment(text: str) -> Dict[str, Any]:
    """
    Analiza el sentimiento de un texto usando reglas básicas.
    Para análisis avanzado, debería integrarse con un servicio NLP.
    
    Args:
        text: Texto a analizar
        
    Returns:
        Dict: Resultados del análisis con claves 'sentiment' y 'score'
    """
    if not text:
        return {"sentiment": "neutral", "score": 0.0}
    
    # Palabras positivas y negativas básicas en español
    positive_words = {
        'bueno', 'excelente', 'genial', 'fantástico', 'increíble', 'positivo',
        'bien', 'mejor', 'perfecto', 'maravilloso', 'agradable', 'satisfecho',
        'contento', 'feliz', 'alegre', 'encantado', 'eficiente', 'rápido',
        'eficaz', 'útil', 'recomendable', 'satisfactorio', 'espectacular',
        'extraordinario', 'óptimo', 'favorable', 'beneficioso', 'ventajoso',
        'ganancia', 'progreso', 'mejora', 'avance', 'éxito'
    }
    
    negative_words = {
        'malo', 'terrible', 'horrible', 'pésimo', 'negativo', 'mal', 'peor',
        'deficiente', 'desagradable', 'insatisfecho', 'disgustado', 'infeliz',
        'triste', 'decepcionado', 'ineficiente', 'lento', 'inútil',
        'desaconsejable', 'insatisfactorio', 'nefasto', 'desfavorable',
        'perjudicial', 'desventajoso', 'pérdida', 'retroceso', 'deterioro',
        'fracaso', 'error', 'fallo', 'problema', 'queja', 'reclamación'
    }
    
    # Normalizar y tokenizar texto
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    
    # Contar palabras positivas y negativas
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    # Calcular puntuación
    total_words = len(words)
    if total_words == 0:
        return {"sentiment": "neutral", "score": 0.0}
    
    # Calcular porcentajes
    positive_percent = positive_count / total_words
    negative_percent = negative_count / total_words
    
    # Calcular puntuación de sentimiento (entre -1 y 1)
    sentiment_score = (positive_percent - negative_percent) * 5  # Amplificar para mayor claridad
    sentiment_score = max(min(sentiment_score, 1.0), -1.0)  # Limitar entre -1 y 1
    
    # Determinar sentimiento general
    if sentiment_score > 0.1:
        sentiment = "positive"
    elif sentiment_score < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "score": sentiment_score,
        "positive_words": positive_count,
        "negative_words": negative_count
    }


def calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> Dict[str, float]:
    """
    Calcula el intervalo de confianza para un conjunto de datos numéricos.
    Optimizado para rendimiento con conjuntos pequeños y medianos.
    
    Args:
        data: Lista de valores numéricos
        confidence: Nivel de confianza (por defecto 0.95 o 95%)
        
    Returns:
        Dict: Resultados con 'mean', 'lower_bound', 'upper_bound' y 'confidence_level'
    """
    if not data:
        return {
            "mean": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 0.0,
            "confidence_level": confidence
        }
    
    # Convertir a numpy array para cálculos más eficientes
    arr = np.array(data)
    n = len(arr)
    mean = np.mean(arr)
    std_dev = np.std(arr, ddof=1)  # Usar n-1 para muestra
    
    # Para muestras pequeñas usar distribución t-student
    if n < 30:
        # Aproximación con t-student, usando z-score para muestras grandes
        from scipy import stats
        t_value = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin_error = t_value * (std_dev / np.sqrt(n))
    else:
        # Para muestras grandes, usar distribución normal
        z_score = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }.get(confidence, 1.96)  # Valor Z para nivel de confianza
        
        margin_error = z_score * (std_dev / np.sqrt(n))
    
    return {
        "mean": float(mean),
        "lower_bound": float(mean - margin_error),
        "upper_bound": float(mean + margin_error),
        "confidence_level": confidence
    }


def detect_outliers(data: List[float], method: str = 'iqr', threshold: float = 1.5) -> List[float]:
    """
    Detecta valores atípicos (outliers) en un conjunto de datos.
    
    Args:
        data: Lista de valores numéricos
        method: Método de detección ('iqr' o 'zscore')
        threshold: Umbral para considerar un valor como atípico
        
    Returns:
        List[float]: Lista de valores considerados atípicos
    """
    if not data or len(data) < 4:  # Necesitamos al menos unos pocos puntos
        return []
    
    # Convertir a numpy array
    arr = np.array(data)
    
    if method == 'iqr':
        # Método de rango intercuartil (IQR)
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - (threshold * iqr)
        upper_bound = q3 + (threshold * iqr)
        
        # Identificar outliers
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        
    elif method == 'zscore':
        # Método de Z-Score
        mean = np.mean(arr)
        std = np.std(arr)
        
        if std == 0:  # Evitar división por cero
            return []
            
        # Calcular z-scores
        z_scores = [(x - mean) / std for x in data]
        
        # Identificar outliers
        outliers = [data[i] for i, z in enumerate(z_scores) if abs(z) > threshold]
        
    else:
        # Método por defecto si no se reconoce
        logger.warning(f"Método de detección de outliers '{method}' no reconocido, usando 'iqr'")
        return detect_outliers(data, 'iqr', threshold)
    
    return outliers


def calculate_cultural_compatibility(person_values: Dict[str, float], 
                                     org_values: Dict[str, float],
                                     weights: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Calcula la compatibilidad cultural entre una persona y una organización.
    
    Args:
        person_values: Diccionario con valores de dimensiones culturales de la persona
        org_values: Diccionario con valores de dimensiones culturales de la organización
        weights: Pesos para cada dimensión (opcional)
        
    Returns:
        Dict: Resultados de compatibilidad
    """
    # Verificar que tenemos datos
    if not person_values or not org_values:
        return {
            "compatibility_score": 0.0,
            "compatibility_level": "Sin datos suficientes",
            "dimensions": {}
        }
    
    # Inicializar resultado
    result = {
        "dimensions": {},
        "overall_values": {},
        "compatibility_dimensions": {}
    }
    
    # Si no se proporcionan pesos, usar 1.0 para todas las dimensiones
    if not weights:
        weights = {dim: 1.0 for dim in set(list(person_values.keys()) + list(org_values.keys()))}
    
    # Normalizar pesos para que sumen 1
    total_weight = sum(weights.values())
    if total_weight > 0:
        normalized_weights = {k: v / total_weight for k, v in weights.items()}
    else:
        normalized_weights = weights
    
    # Calcular compatibilidad por dimensión
    dimension_scores = []
    dimension_compatibility = {}
    
    for dim in set(list(person_values.keys()) + list(org_values.keys())):
        person_value = person_values.get(dim, 0)
        org_value = org_values.get(dim, 0)
        
        # Si alguno de los valores no está disponible, omitir
        if person_value == 0 or org_value == 0:
            continue
        
        # Calcular diferencia y convertir a puntuación (5 - diferencia absoluta)
        # Esto da 5 para match perfecto, y menos para valores divergentes
        difference = abs(person_value - org_value)
        dim_score = max(0, 5 - difference)
        
        # Normalizar a 0-100%
        compatibility = (dim_score / 5) * 100
        
        dimension_compatibility[dim] = compatibility
        dimension_scores.append(compatibility * normalized_weights.get(dim, 1.0))
    
    # Calcular puntuación global
    if dimension_scores:
        overall_compatibility = sum(dimension_scores)
    else:
        overall_compatibility = 0.0
    
    # Determinar nivel de compatibilidad
    if overall_compatibility >= 85:
        level = "Excelente"
    elif overall_compatibility >= 70:
        level = "Muy bueno"
    elif overall_compatibility >= 50:
        level = "Bueno"
    elif overall_compatibility >= 30:
        level = "Regular"
    else:
        level = "Bajo"
    
    result["compatibility_score"] = overall_compatibility
    result["compatibility_level"] = level
    result["dimensions"] = dimension_compatibility
    
    return result
