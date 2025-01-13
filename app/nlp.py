# /home/pablollh/app/nlp.py

import logging
import nltk
import spacy
from spacy.matcher import Matcher, PhraseMatcher
from spacy.lang.es import Spanish
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor
from app.catalogs import DIVISION_SKILLS

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Descarga de recursos NLTK
nltk.download('vader_lexicon', quiet=True)

try:
    nlp = spacy.load("es_core_news_md")  # Ajusta el modelo de spaCy que uses
    logger.info("Modelo de spaCy 'es_core_news_md' cargado correctamente.")
except Exception as e:
    logger.error(f"Error cargando modelo spaCy: {e}", exc_info=True)
    nlp = None

USE_SKILL_EXTRACTOR = True  # O False si deseas desactivarlo globalmente

phrase_matcher = None
sn = None

try:
    if nlp is not None:
        phrase_matcher = PhraseMatcher(nlp.vocab)
        # Ajusta la ruta al JSON con la base de datos de skills
        skill_db_path = "/home/pablollh/app/skill_db_relax_20.json"
        
        sn = SkillExtractor(
            nlp=nlp,
            skills_db=skill_db_path,
            phrase_matcher=phrase_matcher,
            keywords_collection=True,
        )
        logger.info("SkillExtractor 'sn' inicializado correctamente.")
    else:
        logger.warning("No se pudo inicializar SkillExtractor porque nlp es None.")

except Exception as e:
    logger.error(f"Error inicializando SkillExtractor: {e}", exc_info=True)
    sn = None

class NLPProcessor:
    def __init__(self):
        # Cargar el matcher de spaCy
        if nlp is not None:
            self.matcher = Matcher(nlp.vocab)
        else:
            self.matcher = None
        self.define_intent_patterns()

        # Iniciar Sentiment Analyzer
        try:
            self.sia = SentimentIntensityAnalyzer()
            logger.info("SentimentIntensityAnalyzer inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error inicializando SentimentIntensityAnalyzer: {e}", exc_info=True)
            self.sia = None

    def define_intent_patterns(self):
        if not self.matcher:
            return
        saludo_patterns = [
            [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "buenas noches"]}}],
        ]
        self.matcher.add("saludo", saludo_patterns)

    def analyze(self, text: str) -> dict:
        """
        Procesa el texto: detecta intenciones, entidades y sentimiento.
        """
        if not nlp:
            return {"intents": [], "entities": [], "sentiment": {}}

        doc = nlp(text.lower())
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        intents = []
        if self.matcher:
            matches = self.matcher(doc)
            intents = [nlp.vocab.strings[match_id] for match_id, start, end in matches]

        sentiment = self.sia.polarity_scores(text) if self.sia else {}

        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment
        }

    def extract_skills(self, text: str) -> list:
        """
        Usa SkillExtractor para extraer habilidades del texto.
        """
        if not USE_SKILL_EXTRACTOR or sn is None:
            logger.warning("SkillExtractor está deshabilitado o no se ha inicializado (sn=None).")
            return []
        try:
            results = sn.annotate(text)
            # `results.get("results", [])` según la estructura que retorne skillNer
            raw_skills = results.get("results", [])
            # Podrías mapear raw_skills a un simpler array de strings
            extracted = [item['skill'] for item in raw_skills]
            return extracted
        except Exception as e:
            logger.error(f"Error extrayendo habilidades con skillNer: {e}", exc_info=True)
            return []

    def infer_gender(self, name: str) -> str:
        """
        Infiera el género basado en el nombre (heurística de ejemplo).
        """
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "F", "juan": "M"}
        # ...
        parts = name.lower().split()
        if not parts:
            return "O"
        # contemos M, F
        m_count, f_count = 0, 0
        for p in parts:
            if p in GENDER_DICT and GENDER_DICT[p] == "M":
                m_count += 1
            elif p in GENDER_DICT and GENDER_DICT[p] == "F":
                f_count += 1
        if m_count > f_count:
            return "M"
        elif f_count > m_count:
            return "F"
        else:
            return "O"


# Instancia global
nlp_processor = NLPProcessor()