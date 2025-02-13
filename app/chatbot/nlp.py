# /home/pablo/app/chatbot/nlp.py

# Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import logging
import nltk
import spacy
import json
from spacy.matcher import Matcher, PhraseMatcher
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor

# Configuración básica del logger (opcionalmente, se puede configurar en un módulo central)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Descarga de recursos NLTK (verifica si ya están instalados)
nltk.download('vader_lexicon', quiet=True)

try:
    nlp = spacy.load("es_core_news_md")
    logger.info("Modelo de spaCy 'es_core_news_md' cargado correctamente.")
except Exception as e:
    logger.error(f"Error cargando modelo spaCy: {e}", exc_info=True)
    nlp = None

try:
    # Inicializar PhraseMatcher para mejorar la detección de patrones (además del Matcher)
    phrase_matcher_callable = (lambda doc: PhraseMatcher(nlp.vocab, attr="LOWER")(doc)) if nlp else None

    # Ruta al JSON con la base de datos de skills (usar variable de entorno en producción)
    skill_db_path = "/home/pablo/skill_db_relax_20.json"
    with open(skill_db_path, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)

    sn = SkillExtractor(
        nlp=nlp,
        skills_db=skills_db,
        phraseMatcher=phrase_matcher_callable
    ) if nlp else None

    logger.info("SkillExtractor inicializado correctamente con skill_db_path.")
except Exception as e:
    logger.error(f"Error inicializando SkillExtractor: {e}", exc_info=True)
    sn = None

class NLPProcessor:
    """
    Procesador de lenguaje natural para analizar textos, extraer intenciones, entidades, 
    sentimiento y habilidades.
    """
    def __init__(self):
        # Usamos Matcher para patrones simples; se puede combinar con PhraseMatcher si se desea
        self.matcher = Matcher(nlp.vocab) if nlp else None
        self.define_intent_patterns()
        self.sia = SentimentIntensityAnalyzer() if nltk else None

    def define_intent_patterns(self) -> None:
        """
        Define patrones de intenciones (por ejemplo, saludo) usando Matcher.
        """
        if not self.matcher:
            return
        # Se pueden agregar más patrones según sea necesario
        saludo_patterns = [
            [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "qué tal"]}}]
        ]
        self.matcher.add("saludo", saludo_patterns)
        logger.debug("Patrones de saludo definidos en Matcher.")

    def analyze(self, text: str) -> dict:
        """
        Analiza el texto para extraer intenciones, entidades, sentimiento y divisiones detectadas.
        """
        # Importar funciones necesarias desde utils (asegúrese de que estén definidas)
        from app.chatbot.utils import clean_text, validate_term_in_catalog, get_division_skills

        if not nlp:
            logger.error("No se ha cargado el modelo spaCy, devolviendo análisis vacío.")
            return {"intents": [], "entities": [], "sentiment": {}}

        cleaned_text = clean_text(text)
        doc = nlp(cleaned_text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Extraer intenciones usando Matcher
        intents = []
        if self.matcher:
            matches = self.matcher(doc)
            intents = [nlp.vocab.strings[match_id] for match_id, _, _ in matches]

        # Analizar sentimiento
        sentiment = self.sia.polarity_scores(cleaned_text) if self.sia else {}

        # Detectar divisiones basadas en catalogo
        detected_divisions = [term for term in entities if validate_term_in_catalog(term[0], get_division_skills().keys())]

        logger.debug(f"Análisis: Intenciones={intents}, Entidades={entities}, Sentimiento={sentiment}")
        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment,
            "detected_divisions": detected_divisions
        }

    def extract_skills(self, text: str) -> list:
        """
        Extrae habilidades del texto combinando información de un catálogo y SkillExtractor.
        """
        from app.chatbot.utils import get_division_skills
        skills = []
        # Detectar divisiones usando el catálogo de habilidades
        detected_divisions = [division for division in get_division_skills().keys() if division.lower() in text.lower()]

        for division in detected_divisions:
            division_skills = get_division_skills(division)
            skills.extend(division_skills.get("Habilidades Técnicas", []))
            skills.extend(division_skills.get("Habilidades Blandas", []))

        # Si SkillExtractor (sn) está inicializado, extraer habilidades adicionales
        if sn:
            try:
                results = sn.annotate(text)
                extracted_skills = [item['skill'] for item in results.get("results", [])]
                skills.extend(extracted_skills)
            except Exception as e:
                logger.error(f"Error extrayendo habilidades con SkillExtractor: {e}", exc_info=True)
        else:
            logger.warning("SkillExtractor no está inicializado; se omiten habilidades extra.")

        # Eliminar duplicados
        skills = list(set(skills))
        logger.debug(f"Habilidades extraídas: {skills}")
        return skills
    
    def infer_gender(self, name: str) -> str:
        """
        Infiera el género basado en heurísticas simples utilizando un diccionario.
        """
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "F", "juan": "M"}
        parts = name.lower().split()
        if not parts:
            return "O"
        m_count, f_count = 0, 0
        for p in parts:
            if p in GENDER_DICT:
                if GENDER_DICT[p] == "M":
                    m_count += 1
                elif GENDER_DICT[p] == "F":
                    f_count += 1
        if m_count > f_count:
            return "M"
        elif f_count > m_count:
            return "F"
        else:
            return "O"

# Instancia global del procesador
nlp_processor = NLPProcessor()
