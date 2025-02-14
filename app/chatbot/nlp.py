# Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import logging
import nltk
import spacy
import json
import re
import unidecode
from spacy.matcher import Matcher, PhraseMatcher
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor
from app.models import BusinessUnit
from app.chatbot.utils import get_all_skills_for_unit, get_positions_by_skills, prioritize_interests

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# ✅ Descargar recursos de NLTK
nltk.download('vader_lexicon', quiet=True)

# ✅ Diccionario de modelos NLP disponibles
MODEL_LANGUAGES = {
    "es": "es_core_news_md",
    "en": "en_core_web_md",
    "fr": "fr_core_news_md",
    "it": "it_core_news_md",
    "de": "de_core_news_md",
    "ru": "ru_core_news_md",
    "pt": "pt_core_news_md"
}

# ✅ Cargar modelos dinámicamente
loaded_models = {}

def load_nlp_model(language: str):
    """Carga el modelo de NLP para el idioma especificado, con fallback a español."""
    model_name = MODEL_LANGUAGES.get(language, "es_core_news_md")
    
    if model_name in loaded_models:
        return loaded_models[model_name]

    try:
        loaded_models[model_name] = spacy.load(model_name)
        logger.info(f"✅ Modelo SpaCy '{model_name}' cargado correctamente.")
        return loaded_models[model_name]
    except Exception as e:
        logger.error(f"❌ Error cargando modelo SpaCy para {language} ({model_name}): {e}")
        return loaded_models.get("es_core_news_md", None)  # Fallback a español

# ✅ Función para detectar idioma y cargar modelo correcto
def detect_and_load_nlp(text: str):
    """Detecta el idioma y carga el modelo NLP correspondiente."""
    try:
        detected_lang = detect(text)
        language = detected_lang if detected_lang in MODEL_LANGUAGES else "es"
        logger.info(f"🌍 Idioma detectado: {detected_lang} (Usando modelo {MODEL_LANGUAGES[language]})")
        return load_nlp_model(language)
    except Exception as e:
        logger.error(f"❌ Error detectando idioma: {e}")
        return load_nlp_model("es")  # Fallback a español

# ✅ Creación de PhraseMatcher dinámico
def phrase_matcher_factory(nlp_model):
    """Crea una instancia de PhraseMatcher según el modelo NLP disponible."""
    return PhraseMatcher(nlp_model.vocab, attr="LOWER") if nlp_model else None

# ✅ Inicialización de SkillExtractor con idioma dinámico
try:
    skill_db_path = "/home/pablo/skill_db_relax_20.json"
    with open(skill_db_path, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)

    nlp_default = load_nlp_model("es")  # Usamos español por defecto
    phrase_matcher = phrase_matcher_factory(nlp_default)

    if nlp_default and phrase_matcher:
        sn = SkillExtractor(nlp=nlp_default, skills_db=skills_db, phraseMatcher=phrase_matcher)
        logger.info("✅ SkillExtractor inicializado con modelo en español.")
    else:
        sn = None
        logger.warning("⚠ No se pudo inicializar SkillExtractor correctamente.")

except Exception as e:
    logger.error(f"❌ Error inicializando SkillExtractor: {e}", exc_info=True)
    sn = None

class NLPProcessor:
    """ Procesador de NLP para análisis de texto, intenciones, sentimiento e intereses. """

    def __init__(self):
        self.matcher = Matcher(nlp.vocab) if nlp else None
        self.define_intent_patterns()
        self.sia = SentimentIntensityAnalyzer() if nltk else None

    def define_intent_patterns(self) -> None:
        """ Define patrones de intenciones con Matcher. """
        if not self.matcher:
            return
        patterns = [[{"LOWER": {"IN": ["hola", "buenos días", "buenas tardes", "qué tal"]}}]]
        self.matcher.add("saludo", patterns)
        logger.debug("Patrones de saludo definidos en Matcher.")

    def analyze(self, text: str) -> dict:
        from app.chatbot.utils import clean_text, validate_term_in_catalog, get_all_divisions

        if not nlp:
            logger.error("No se ha cargado el modelo spaCy, devolviendo análisis vacío.")
            return {"intents": [], "entities": [], "sentiment": {}, "detected_divisions": []}

        cleaned_text = clean_text(text)
        doc = nlp(cleaned_text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        intents = []
        if self.matcher:
            matches = self.matcher(doc)
            intents = [nlp.vocab.strings[match_id] for match_id, _, _ in matches]
        sentiment = self.sia.polarity_scores(cleaned_text) if self.sia else {}
        all_divisions = get_all_divisions()
        detected_divisions = [term for term in entities if validate_term_in_catalog(term[0], all_divisions)]

        logger.debug(f"Análisis: Intenciones={intents}, Entidades={entities}, Sentimiento={sentiment}")
        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment,
            "detected_divisions": detected_divisions
        }
    
    def extract_skills(self, text: str, business_unit: str = "huntRED®") -> dict:
        """ Extrae habilidades, prioriza intereses y sugiere posiciones. """
        from app.chatbot.utils import get_all_skills_for_unit, get_positions_by_skills, prioritize_interests

        text_normalized = unidecode.unidecode(text.lower())
        skills = set()  # Evita duplicados
        
        # 1️⃣ Cargar habilidades desde catálogos y vacantes
        try:
            all_skills = get_all_skills_for_unit(business_unit)
            logger.info(f"📌 Habilidades cargadas para {business_unit}: {all_skills}")  
        except Exception as e:
            logger.error(f"Error obteniendo habilidades para {business_unit}: {e}")
            all_skills = []

        # 2️⃣ Coincidencias manuales con regex optimizado
        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills.add(skill)
                logger.info(f"✅ Coincidencia manual encontrada: {skill}")

        # 3️⃣ Extraer habilidades con SkillExtractor
        if sn and nlp and nlp.vocab.vectors_length > 0:
            try:
                results = sn.annotate(text)
                logger.info(f"🧠 SkillExtractor resultados: {results}")
                if isinstance(results, dict) and "results" in results:
                    extracted_skills = {item["skill"] for item in results["results"] if isinstance(item, dict)}
                    skills.update(extracted_skills)
                    logger.info(f"🧠 Habilidades extraídas por SkillExtractor: {extracted_skills}")
            except Exception as e:
                logger.error(f"❌ Error en SkillExtractor: {e}", exc_info=True)

        # 4️⃣ Priorizar intereses detectados
        prioritized_interests = prioritize_interests(list(skills))
        
        # 5️⃣ Buscar posiciones adecuadas con las habilidades encontradas
        suggested_positions = []
        if skills:
            try:
                suggested_positions = get_positions_by_skills(list(skills))
                logger.info(f"💼 Posiciones sugeridas: {suggested_positions}")
            except Exception as e:
                logger.error(f"Error obteniendo posiciones sugeridas: {e}", exc_info=True)

        # 6️⃣ Retornar en formato estructurado
        result = {
            "skills": list(skills),
            "prioritized_interests": prioritized_interests,
            "suggested_positions": suggested_positions
        }

        logger.info(f"🔎 Análisis final: {result}")
        return result
    def extract_interests_and_skills(self, text: str) -> dict:
        """
        Extrae intereses explícitos, habilidades y sugiere roles priorizando lo mencionado por el usuario.
        """
        text_normalized = unidecode.unidecode(text.lower())
        skills = set()
        priorities = {}

        # Cargar habilidades desde catálogos
        try:
            all_skills = get_all_skills_for_unit()
            logger.info(f"📌 Habilidades cargadas: {all_skills}")  
        except Exception as e:
            logger.error(f"Error obteniendo habilidades: {e}")
            all_skills = []

        # Coincidencias manuales
        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills.add(skill)
                priorities[skill] = 2  # Mayor peso a lo mencionado directamente

        # Extraer habilidades con SkillExtractor
        if sn and nlp and nlp.vocab.vectors_length > 0:
            try:
                results = sn.annotate(text)
                if isinstance(results, dict) and "results" in results:
                    extracted_skills = {item["skill"] for item in results["results"] if isinstance(item, dict)}
                    skills.update(extracted_skills)
                    for skill in extracted_skills:
                        priorities[skill] = priorities.get(skill, 1)  # Menor peso a lo detectado automáticamente
                    logger.info(f"🧠 Habilidades extraídas por SkillExtractor: {extracted_skills}")
            except Exception as e:
                logger.error(f"❌ Error en SkillExtractor: {e}", exc_info=True)

        # Aplicar ponderación a intereses
        prioritized_interests = prioritize_interests(list(skills))  # Se pasa solo la lista de skills
        
        return {
            "skills": list(skills),
            "prioritized_skills": prioritized_interests
        }
    def infer_gender(self, name: str) -> str:
        """ Infiera género basado en heurísticas simples. """
        GENDER_DICT = {"jose": "M", "maria": "F", "andrea": "F", "juan": "M"}
        parts = name.lower().split()
        m_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "M")
        f_count = sum(1 for p in parts if p in GENDER_DICT and GENDER_DICT[p] == "F")
        return "M" if m_count > f_count else "F" if f_count > m_count else "O"

    def extract_skills_and_roles(self, text: str, business_unit: str = "huntRED®") -> dict:
        """
        Extrae habilidades, identifica intereses explícitos y sugiere roles con prioridad en lo que el usuario menciona directamente.
        """
        text_normalized = unidecode.unidecode(text.lower())
        skills = set()
        priorities = {}  # Diccionario para ponderar lo que menciona el usuario

        # 1️⃣ Cargar habilidades desde catálogos
        try:
            all_skills = get_all_skills_for_unit(business_unit)
            logger.info(f"📌 Habilidades cargadas para {business_unit}: {all_skills}")  
        except Exception as e:
            logger.error(f"Error obteniendo habilidades para {business_unit}: {e}")
            all_skills = []

        # 2️⃣ Coincidencias manuales con prioridad
        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills.add(skill)
                priorities[skill] = 2  # Mayor peso a lo mencionado directamente

        # 3️⃣ Extraer habilidades con SkillExtractor
        if sn and nlp and nlp.vocab.vectors_length > 0:
            try:
                results = sn.annotate(text)
                if isinstance(results, dict) and "results" in results:
                    extracted_skills = {item["skill"] for item in results["results"] if isinstance(item, dict)}
                    skills.update(extracted_skills)
                    for skill in extracted_skills:
                        priorities[skill] = priorities.get(skill, 1)  # Menor peso a lo detectado automáticamente
                    logger.info(f"🧠 Habilidades extraídas por SkillExtractor: {extracted_skills}")
            except Exception as e:
                logger.error(f"❌ Error en SkillExtractor: {e}", exc_info=True)

        # 4️⃣ Ponderar y asociar a roles
        skills, skill_weights = prioritize_skills(skills, priorities)
        suggested_roles = get_positions_by_skills(skills, skill_weights) if skills else []

        return {
            "skills": skills,
            "suggested_roles": suggested_roles
        }


# Instancia global del procesador
nlp_processor = NLPProcessor()