# /home/pablo/app/com/chatbot/utils/nlp_utils.py
"""
Utilidades para procesamiento de lenguaje natural.
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
import spacy
from transformers import pipeline

logger = logging.getLogger(__name__)

class NLPUtils:
    """Utilidades para procesamiento de lenguaje natural."""

    # Caché para modelos NLP
    _nlp_model = None
    _sentiment_analyzer = None
    _entity_recognizer = None

    @classmethod
    def get_nlp_model(cls):
        """Obtiene o inicializa el modelo de spaCy."""
        if cls._nlp_model is None:
            try:
                cls._nlp_model = spacy.load(settings.NLP_MODEL_PATH)
            except Exception as e:
                logger.error(f"Error al cargar modelo NLP: {str(e)}")
                cls._nlp_model = spacy.blank('es')
        return cls._nlp_model

    @classmethod
    def get_sentiment_analyzer(cls):
        """Obtiene o inicializa el analizador de sentimientos."""
        if cls._sentiment_analyzer is None:
            try:
                cls._sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model=settings.SENTIMENT_MODEL_PATH
                )
            except Exception as e:
                logger.error(f"Error al cargar analizador de sentimientos: {str(e)}")
                cls._sentiment_analyzer = None
        return cls._sentiment_analyzer

    @classmethod
    def get_entity_recognizer(cls):
        """Obtiene o inicializa el reconocedor de entidades."""
        if cls._entity_recognizer is None:
            try:
                cls._entity_recognizer = pipeline(
                    "ner",
                    model=settings.NER_MODEL_PATH
                )
            except Exception as e:
                logger.error(f"Error al cargar reconocedor de entidades: {str(e)}")
                cls._entity_recognizer = None
        return cls._entity_recognizer

    @staticmethod
    def analyze_text(text: str) -> Dict:
        """Analiza un texto y retorna información sobre su contenido."""
        if not text:
            return {}

        nlp = NLPUtils.get_nlp_model()
        doc = nlp(text)

        # Análisis básico
        analysis = {
            'tokens': [token.text for token in doc],
            'lemmas': [token.lemma_ for token in doc],
            'pos_tags': [(token.text, token.pos_) for token in doc],
            'entities': [(ent.text, ent.label_) for ent in doc.ents],
            'sentences': [sent.text for sent in doc.sents]
        }

        # Análisis de sentimiento si está disponible
        sentiment_analyzer = NLPUtils.get_sentiment_analyzer()
        if sentiment_analyzer:
            try:
                sentiment = sentiment_analyzer(text)[0]
                analysis['sentiment'] = {
                    'label': sentiment['label'],
                    'score': sentiment['score']
                }
            except Exception as e:
                logger.error(f"Error en análisis de sentimiento: {str(e)}")

        return analysis

    @staticmethod
    def extract_entities(text: str) -> List[Tuple[str, str]]:
        """Extrae entidades nombradas del texto."""
        if not text:
            return []

        nlp = NLPUtils.get_nlp_model()
        doc = nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents]

    @staticmethod
    def get_sentiment(text: str) -> Optional[Dict]:
        """Analiza el sentimiento del texto."""
        if not text:
            return None

        sentiment_analyzer = NLPUtils.get_sentiment_analyzer()
        if not sentiment_analyzer:
            return None

        try:
            result = sentiment_analyzer(text)[0]
            return {
                'label': result['label'],
                'score': result['score']
            }
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            return None

    @staticmethod
    def is_question(text: str) -> bool:
        """Determina si un texto es una pregunta."""
        if not text:
            return False

        question_patterns = [
            r'\?$',  # Termina con signo de interrogación
            r'^(qué|qué|quien|quién|cómo|cuándo|dónde|por qué|para qué|cuál|cuáles)',
            r'^(puedes|podrías|sabes|conoces|tienes|hay)',
        ]

        text = text.lower().strip()
        return any(re.search(pattern, text) for pattern in question_patterns)

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
        """Extrae palabras clave del texto."""
        if not text:
            return []

        nlp = NLPUtils.get_nlp_model()
        doc = nlp(text)

        # Filtrar por relevancia (sustantivos, verbos, adjetivos)
        keywords = [
            token.lemma_ for token in doc
            if token.pos_ in ['NOUN', 'VERB', 'ADJ']
            and not token.is_stop
            and len(token.text) > 2
        ]

        # Contar frecuencia
        keyword_freq = {}
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

        # Ordenar por frecuencia y retornar los más relevantes
        sorted_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [keyword for keyword, _ in sorted_keywords[:max_keywords]] 