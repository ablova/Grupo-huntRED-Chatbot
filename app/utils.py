import spacy
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
import math
from spacy.matcher import Matcher
from django.utils.timezone import now
import logging
from typing import Dict
from spacy.tokens import Doc

logger = logging.getLogger(__name__)

try:
    # Cargar el modelo en español de spaCy
    nlp = spacy.load("es_core_news_sm")
except Exception as e:
    logger.error(f"Error al cargar el modelo de spaCy: {e}")
    raise e  # Re-lanzar la excepción para que el programa pueda manejarlo adecuadamente

# Inicializar el Matcher de spaCy
matcher = Matcher(nlp.vocab)

# Definir patrones para identificar intenciones
patterns = [
    {"label": "reiniciar", "pattern": [{"LOWER": {"IN": ["reiniciar", "reinicio", "reset", "empezar de nuevo"]}}]},
    {"label": "menu", "pattern": [{"LOWER": {"IN": ["menu", "menú", "main menu", "menú principal"]}}]},
    {"label": "recapitulación", "pattern": [{"LOWER": {"IN": ["recap", "recapitulación", "mi perfil", "ver información"]}}]},
    # Otros patrones existentes
    {"label": "saludo", "pattern": [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "buenas noches", "qué tal"]}}]},
    {"label": "despedida", "pattern": [{"LOWER": {"IN": ["adiós", "hasta luego", "nos vemos", "chao", "ciao", "bye"]}}]},
    {"label": "ayuda", "pattern": [{"LOWER": {"IN": ["ayuda", "soporte", "asistencia"]}}]},
    {"label": "buscar_vacante", "pattern": [{"LEMMA": "buscar"}, {"LEMMA": "vacante"}]},
    {"label": "postular_vacante", "pattern": [{"LEMMA": "postular"}, {"LEMMA": "vacante"}]},
    {"label": "solicitar_ayuda_postulacion", "pattern": [{"LEMMA": "necesitar"}, {"LOWER": {"IN": ["ayuda", "asistencia"]}}, {"LEMMA": "postular"}]},
    {"label": "consultar_estatus", "pattern": [{"LEMMA": "consultar"}, {"LEMMA": "estatus"}, {"LEMMA": "aplicación"}]},
    # Añade más patrones según tus necesidades
]

# Añadir patrones al Matcher
for pattern in patterns:
    matcher.add(pattern["label"], [pattern["pattern"]])

# Descargar recursos de NLTK
nltk.download('punkt')
nltk.download('vader_lexicon')

# Inicializar Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

def analyze_text(text):
    """
    Analiza el texto del usuario y extrae intenciones, entidades y sentimientos.

    Args:
        text (str): Mensaje del usuario.

    Returns:
        dict: Diccionario con intenciones, entidades y sentimiento.
    """
    try:
        doc = nlp(text.lower())

        # Buscar patrones de intención
        matches = matcher(doc)
        intents = []
        for match_id, start, end in matches:
            intent = nlp.vocab.strings[match_id]
            intents.append(intent)

        # Extraer entidades nombradas
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Analizar sentimiento
        sentiment = sia.polarity_scores(text)

        # Registrar los logs para depuración
        logger.debug(f"Text analyzed: {text}")
        logger.debug(f"Detected intents: {intents}")
        logger.debug(f"Entities found: {entities}")
        logger.debug(f"Sentiment analysis: {sentiment}")

        # Retornar análisis
        return {
            "intents": intents,
            "entities": entities,
            "sentiment": sentiment,
        }
    except Exception as e:
        logger.error(f"Error al analizar el texto: {e}", exc_info=True)
        return {
            "intents": [],
            "entities": [],
            "sentiment": {},
        }

def clean_text(text):
    """
    Limpia texto eliminando caracteres especiales y espacios adicionales.

    Args:
        text (str): Texto a limpiar.

    Returns:
        str: Texto limpio.
    """
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)  # Sustituir múltiples espacios por uno solo
    text = re.sub(r'[^\w\s]', '', text)  # Eliminar caracteres especiales
    return text.strip()

def detect_intents(doc: Doc, matcher) -> Dict[str, list]:
    """
    Detecta intents usando patrones definidos en el Matcher.

    Args:
        doc (Doc): Objeto Doc procesado por spaCy.
        matcher (Matcher): Objeto Matcher de spaCy con patrones cargados.

    Returns:
        dict: Diccionario con la lista de intents detectados.
    """
    try:
        matches = matcher(doc)
        intents = [doc.vocab.strings[match_id] for match_id, start, end in matches]
        return {"intents": intents}
    except Exception as e:
        logger.error(f"Error detectando intents: {e}", exc_info=True)
        return {"intents": []}
    
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos usando la fórmula de Haversine.

    Args:
        lat1, lon1: Coordenadas del primer punto.
        lat2, lon2: Coordenadas del segundo punto.

    Returns:
        float: Distancia en kilómetros.
    """
    R = 6371  # Radio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distancia en km