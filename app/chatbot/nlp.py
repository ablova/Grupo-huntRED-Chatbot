# /home/pablollh/app/chatbot/nlp.py
# /home/pablollh/app/chatbot/nlp.py

import logging
import nltk
import spacy
import json
from spacy.matcher import Matcher, PhraseMatcher
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor
from app.chatbot.utils import validate_term_in_catalog, get_division_skills, clean_text

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Descarga de recursos NLTK
nltk.download('vader_lexicon', quiet=True)

try:
    nlp = spacy.load("es_core_news_md")
    logger.info("Modelo de spaCy 'es_core_news_md' cargado correctamente.")
except Exception as e:
    logger.error(f"Error cargando modelo spaCy: {e}", exc_info=True)
    nlp = None

try:
    # Inicializar PhraseMatcher y SkillExtractor
    phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER") if nlp else None

    # Ruta al JSON con la base de datos de skills
    skill_db_path = "/home/pablollh/app/skill_db_relax_20.json"
    with open(skill_db_path, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)

    sn = SkillExtractor(
        nlp=nlp,
        skills_db=skills_db,
        phraseMatcher=phrase_matcher
    ) if nlp else None

    logger.info("SkillExtractor inicializado correctamente con skill_db_path.")
except Exception as e:
    logger.error(f"Error inicializando SkillExtractor: {e}", exc_info=True)
    sn = None

class NLPProcessor:
    def __init__(self):
        self.matcher = Matcher(nlp.vocab) if nlp else None
        self.define_intent_patterns()
        self.sia = SentimentIntensityAnalyzer() if nltk else None

    def define_intent_patterns(self):
        if not self.matcher:
            return
        saludo_patterns = [
            [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes"]}}]
        ]
        self.matcher.add("saludo", saludo_patterns)

    def analyze(self, text: str) -> dict:
        if not nlp:
            return {"intents": [], "entities": [], "sentiment": {}}

        cleaned_text = clean_text(text)
        doc = nlp(cleaned_text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        intents = []
        if self.matcher:
            matches = self.matcher(doc)
            intents = [nlp.vocab.strings[match_id] for match_id, _, _ in matches]

        sentiment = self.sia.polarity_scores(cleaned_text) if self.sia else {}

        detected_divisions = [term for term in entities if validate_term_in_catalog(term[0], get_division_skills.keys())]

        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment,
            "detected_divisions": detected_divisions
        }

    def extract_skills(self, text: str) -> list:
        """
        Extrae habilidades combinando DIVISION_SKILLS y skill_db_path.
        """
        skills = []
        detected_divisions = [division for division in get_division_skills.keys() if division.lower() in text.lower()]

        # Agregar habilidades desde DIVISION_SKILLS
        for division in detected_divisions:
            division_skills = get_division_skills(division)
            skills.extend(division_skills.get("Habilidades Técnicas", []))
            skills.extend(division_skills.get("Habilidades Blandas", []))

        # Agregar habilidades desde SkillExtractor
        if sn:
            try:
                results = sn.annotate(text)
                extracted_skills = [item['skill'] for item in results.get("results", [])]
                skills.extend(extracted_skills)
            except Exception as e:
                logger.error(f"Error extrayendo habilidades con SkillExtractor: {e}", exc_info=True)

        # Eliminar duplicados
        skills = list(set(skills))

        return skills
    
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