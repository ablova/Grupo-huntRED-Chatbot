# Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import logging
import nltk
import spacy
import json
from spacy.matcher import Matcher, PhraseMatcher
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor
from app.models import BusinessUnit

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

    def extract_skills(self, text: str, user_id: str = None) -> list:
        """
        Extrae habilidades del texto combinando información de un catálogo y SkillExtractor.

        Args:
            text (str): Texto a analizar.
            user_id (str, opcional): ID del usuario (WhatsApp phone ID, Telegram bot ID, etc.).

        Returns:
            list: Lista de habilidades detectadas.
        """
        from app.chatbot.utils import get_all_skills_for_unit

        # Obtener la unidad de negocio desde ChatState
        business_unit = "huntRED®"  # Valor por defecto
        if user_id:
            try:
                from app.models import ChatState
                chat_state = ChatState.objects.get(user_id=user_id)
                business_unit = chat_state.business_unit.name
            except ChatState.DoesNotExist:
                logger.error(f"No se encontró ChatState para user_id: {user_id}, usando '{business_unit}'.")
            except Exception as e:
                logger.error(f"Error obteniendo BusinessUnit desde user_id ({user_id}): {e}")

        # Obtener todas las habilidades de la unidad de negocio correspondiente
        skills = []
        all_skills = get_all_skills_for_unit(business_unit)

        # Buscar coincidencias manualmente con palabras clave del catálogo
        for skill in all_skills:
            if skill.lower() in text.lower():
                skills.append(skill)

        # Si SkillExtractor está disponible, extraer habilidades adicionales
        if sn:
            try:
                results = sn.annotate(text)
                if isinstance(results, dict) and "results" in results:
                    extracted_skills = [item["skill"] for item in results["results"] if isinstance(item, dict)]
                    skills.extend(extracted_skills)
                else:
                    logger.error(f"Formato inesperado en resultados de SkillExtractor: {results}")
            except Exception as e:
                logger.error(f"Error extrayendo habilidades con SkillExtractor: {e}", exc_info=True)

        # Eliminar duplicados
        skills = list(set(skills))
        logger.debug(f"Habilidades extraídas para {business_unit}: {skills}")
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
