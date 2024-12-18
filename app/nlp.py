# /home/pablollh/app/nlp.py

import logging
import nltk
import spacy
from spacy.matcher import Matcher
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor
from app.catalogs import DIVISION_SKILLS

logger = logging.getLogger(__name__)

# Configuración básica de logging (si aún no está configurada en otro lugar)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Descargar datos necesarios para NLTK
nltk.download('vader_lexicon', quiet=True)

# Cargar el modelo de spaCy una sola vez
try:
    nlp = spacy.load("es_core_news_md")
    logger.info("Modelo de spaCy 'es_core_news_md' cargado correctamente.")
except Exception as e:
    logger.error(f"Error cargando modelo spaCy: {e}")
    raise e

# Ruta al archivo de base de datos de habilidades
skills_db_path = "/home/pablollh/app/skill_db_relax_20.json"

# Crear el objeto SkillExtractor
try:
    sn = SkillExtractor(
        nlp=nlp,
        skills_db=skills_db_path,
    )
    logger.info("SkillExtractor 'sn' inicializado correctamente.")
except Exception as e:
    logger.error(f"Error inicializando SkillExtractor: {e}")
    sn = None

# Variable para habilitar o deshabilitar SkillExtractor temporalmente
USE_SKILL_EXTRACTOR = False  # Cambia a True si deseas habilitarlo

if USE_SKILL_EXTRACTOR and sn:
    try:
        # Añadir habilidades personalizadas desde DIVISION_SKILLS
        for division, skills in DIVISION_SKILLS.items():
            for skill in skills:
                try:
                    sn.add_skill(skill, division=division)
                    logger.debug(f"Habilidad '{skill}' añadida a la división '{division}'.")
                except Exception as e:
                    logger.warning(f"Error añadiendo habilidad '{skill}': {e}")
    except Exception as e:
        logger.error(f"Error al añadir habilidades personalizadas: {e}")

class NLPProcessor:
    def __init__(self):
        # Inicializar el Matcher de spaCy
        self.matcher = Matcher(nlp.vocab)
        self.define_intent_patterns()

        # Inicializar el analizador de sentimiento
        try:
            self.sia = SentimentIntensityAnalyzer()
            logger.info("SentimentIntensityAnalyzer inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error inicializando SentimentIntensityAnalyzer: {e}")
            self.sia = None

    def define_intent_patterns(self):
        """
        Define patrones de intenciones usando el Matcher de spaCy.
        """
        saludo_patterns = [
            [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "buenas noches"]}}]
        ]
        self.matcher.add("saludo", saludo_patterns)
        logger.debug("Patrones de intenciones definidos en NLPProcessor.")

    def analyze(self, text: str) -> dict:
        """
        Procesa el texto: detecta intenciones, entidades y sentimiento.
        """
        doc = nlp(text.lower())
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Detectar intenciones
        matches = self.matcher(doc)
        intents = [nlp.vocab.strings[match_id] for match_id, start, end in matches]

        # Analizar sentimiento
        sentiment = self.sia.polarity_scores(text) if self.sia else {}

        logger.debug(f"Análisis completado para el texto: {text}")
        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment
        }

    def extract_skills(self, text: str) -> list:
        """
        Usa SkillExtractor para extraer habilidades del texto.
        """
        if USE_SKILL_EXTRACTOR and sn:
            try:
                skills = sn.annotate(text)
                logger.debug(f"Habilidades extraídas: {skills.get('results', [])}")
                return skills.get("results", [])
            except Exception as e:
                logger.error(f"Error extrayendo habilidades: {e}")
                return []
        else:
            logger.warning("SkillExtractor está deshabilitado o no se ha inicializado.")
            return []

    def infer_gender(self, name: str) -> str:
        """
        Infiera el género basado en el nombre.
        """
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "O"}  # Ejemplo
        gender_count = {"M": 0, "F": 0, "O": 0}
        for part in name.lower().split():
            gender = GENDER_DICT.get(part, "O")
            gender_count[gender] += 1
        inferred_gender = "M" if gender_count["M"] > gender_count["F"] else \
                          "F" if gender_count["F"] > gender_count["M"] else "O"
        logger.debug(f"Género inferido para '{name}': {inferred_gender}")
        return inferred_gender

# Crear una instancia singleton de NLPProcessor para uso global
nlp_processor = NLPProcessor()