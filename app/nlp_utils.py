# /home/amigro/app/nlp_utils.py

import spacy
from spacy.matcher import Matcher
import logging

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
    {"label": "reiniciar", "pattern": [{"LOWER": {"IN": ["reiniciar", "reinicio", "comenzar de nuevo el chat", "inicio pllh", "reset", "empezar de nuevo"]}}]},
    {"label": "menu", "pattern": [{"LOWER": {"IN": ["menu", "menú", "main menu", "menú principal", "menú_iterativo"]}}]},
    {"label": "recapitulación", "pattern": [{"LOWER": {"IN": ["recap", "recapitulación", "mi perfil", "ver información"]}}]},
    # Otros patrones existentes
    {"label": "saludo", "pattern": [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "buenas noches"]}}]},
    {"label": "despedida", "pattern": [{"LOWER": {"IN": ["adiós", "hasta luego", "nos vemos", "chao", "ciao"]}}]},
    {"label": "buscar_vacante", "pattern": [{"LEMMA": "buscar"}, {"LEMMA": "vacante"}]},
    {"label": "postular_vacante", "pattern": [{"LEMMA": "postular"}, {"LEMMA": "vacante"}]},
    
    # Añade más patrones según tus necesidades
]

# Añadir patrones al Matcher
for pattern in patterns:
    matcher.add(pattern["label"], [pattern["pattern"]])

def analyze_text(text):
    """
    Analiza el texto del usuario y extrae intenciones y entidades.

    Args:
        text (str): Mensaje del usuario.

    Returns:
        dict: Diccionario con intenciones y entidades extraídas.
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

        # Retornar análisis
        return {
            "intents": intents,
            "entities": entities,
        }
    except Exception as e:
        logger.error(f"Error al analizar el texto: {e}", exc_info=True)
        return {
            "intents": [],
            "entities": [],
        }
