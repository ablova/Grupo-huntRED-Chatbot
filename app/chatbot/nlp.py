# Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import logging
import nltk
import spacy
import json
from spacy.matcher import Matcher, PhraseMatcher
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Descarga de recursos NLTK (se ejecuta solo si no están ya descargados)
nltk.download('vader_lexicon', quiet=True)
try:
    nlp = spacy.load("es_core_news_md")
    logger.info("Modelo de spaCy 'es_core_news_md' cargado correctamente.")
except Exception as e:
    logger.error(f"Error cargando modelo spaCy: {e}", exc_info=True)
    nlp = None

try:
    # Inicializar un callable para PhraseMatcher que ignore los argumentos recibidos,
    # de modo que siempre se cree una instancia usando nlp.vocab y attr="LOWER"
    phrase_matcher_callable = (lambda *args, **kwargs: PhraseMatcher(nlp.vocab, attr="LOWER")) if nlp else None

    # Ruta al JSON con la base de datos de skills
    skill_db_path = "/home/pablo/skill_db_relax_20.json"
    with open(skill_db_path, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)

    sn = SkillExtractor(
        nlp=nlp,
        skills_db=skills_db,
        phraseMatcher=phrase_matcher_callable
    ) if nlp else None

    logger.info("SkillExtractor inicializado correctamente con skill_db_relax_20.json.")
except Exception as e:
    logger.error(f"Error inicializando SkillExtractor: {e}", exc_info=True)
    sn = None

class NLPProcessor:
    """
    Procesador de lenguaje natural para analizar textos, extraer intenciones, entidades, 
    sentimiento y habilidades.
    """
    def __init__(self):
        self.matcher = Matcher(nlp.vocab) if nlp else None
        self.define_intent_patterns()
        self.sia = SentimentIntensityAnalyzer() if nltk else None

    def define_intent_patterns(self) -> None:
        """
        Define patrones de intenciones (por ejemplo, saludo) usando Matcher.
        """
        if not self.matcher:
            return
        saludo_patterns = [
            [{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "qué tal"]}}]
        ]
        self.matcher.add("saludo", saludo_patterns)
        logger.debug("Patrones de saludo definidos en Matcher.")

    def analyze(self, text: str) -> dict:
        """ 
        Analiza el texto para extraer intenciones, entidades, sentimiento y divisiones detectadas.
        """
        from app.chatbot.utils import clean_text, validate_term_in_catalog, get_all_divisions

        if not nlp:
            logger.error("No se ha cargado el modelo spaCy, devolviendo análisis vacío.")
            return {"intents": [], "entities": [], "sentiment": {}, "detected_divisions": []}

        cleaned_text = clean_text(text)
        doc = nlp(cleaned_text)

        # Detectar entidades mejoradas
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        # Matcher personalizado para reconocer habilidades y términos clave
        phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        keywords = ["Python", "Django", "SQL", "Machine Learning", "Tableau", "gestión de riesgos"]
        patterns = [nlp(keyword) for keyword in keywords]
        phrase_matcher.add("TECH_SKILLS", patterns)

        matches = phrase_matcher(doc)
        matched_terms = [doc[start:end].text for match_id, start, end in matches]
        for term in matched_terms:
            entities.append((term, "SKILL"))

        # Extraer intenciones
        intents = []
        if self.matcher:
            matches = self.matcher(doc)
            intents = [nlp.vocab.strings[match_id] for match_id, _, _ in matches]

        # Analizar sentimiento
        sentiment = self.sia.polarity_scores(cleaned_text) if self.sia else {}

        # Detectar divisiones
        all_divisions = get_all_divisions()
        detected_divisions = [term for term in entities if validate_term_in_catalog(term[0], all_divisions)]

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
        Se verifica que el resultado de sn.annotate tenga el formato esperado.
        """
        from app.utilidades.catalogs import get_divisiones, get_skills_for_unit
        import json
        skills = []
        from app.chatbot.utils import get_all_divisions  # Asegurar que esta función existe en utils.py
        all_divisions = get_all_divisions()

        detected_divisions = [division for division in get_divisiones() if division.lower() in text.lower()]

        for division in detected_divisions:
            division_skills = get_skills_for_unit(division)
            skills.extend(division_skills.get("Habilidades Técnicas", []))
            skills.extend(division_skills.get("Habilidades Blandas", []))

        if sn:
            try:
                results = sn.annotate(text)
                # Si el resultado es una cadena, intentar convertirlo a dict
                if isinstance(results, str):
                    results = json.loads(results)
                extracted_skills = []
                # Verificar que results sea un diccionario y contenga la clave "results"
                if isinstance(results, dict) and "results" in results:
                    # Asegurarse de que cada item sea un diccionario con la clave 'skill'
                    extracted_skills = [
                        item['skill'] for item in results.get("results", [])
                        if isinstance(item, dict) and 'skill' in item
                    ]
                else:
                    logger.warning("El resultado de SkillExtractor no tiene el formato esperado.")
                skills.extend(extracted_skills)
            except Exception as e:
                logger.error(f"Error extrayendo habilidades con SkillExtractor: {e}", exc_info=True)
        else:
            logger.warning("SkillExtractor no está inicializado; se omiten habilidades extra.")

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

def load_catalog() -> dict:
    """
    Carga el catálogo desde '/home/pablo/app/utilidades/catalogs/catalogs.json'.
    Si ocurre algún error (archivo vacío o JSON mal formado), se devuelve un diccionario vacío.
    """
    catalog_path = "/home/pablo/app/utilidades/catalogs/catalogs.json"
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            logger.warning(f"El archivo {catalog_path} está vacío. Se utilizará un catálogo vacío.")
            return {}
        return data
    except Exception as e:
        logger.error(f"Error al cargar el catálogo desde {catalog_path}: {e}", exc_info=True)
        return {}
