# Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import logging
#import nltk
import spacy
import json
import re
import unidecode
from spacy.matcher import Matcher, PhraseMatcher
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from skillNer.skill_extractor_class import SkillExtractor
from app.models import BusinessUnit, GptApi
from app.chatbot.utils import get_all_skills_for_unit, get_positions_by_skills, prioritize_interests, map_skill_to_database
from app.chatbot.gpt import GPTHandler
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from tabiya_livelihoods_classifer import EntityLinker
from transformers import pipeline

logger = logging.getLogger("app.chatbot.nlp")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# ✅ Descargar recursos de NLTK
#nltk.download('vader_lexicon', quiet=True)

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
    """Carga modelos de NLP de forma optimizada."""
    model_name = MODEL_LANGUAGES.get(language, "es_core_news_md")
    if model_name in loaded_models:
        return loaded_models[model_name]
    try:
        loaded_models[model_name] = spacy.load(model_name)
        logger.info(f"✅ Modelo NLP '{model_name}' cargado correctamente.")
    except Exception as e:
        logger.error(f"❌ Error cargando modelo '{model_name}': {e}")
        return None
    return loaded_models[model_name]

# ✅ Función para detectar idioma y cargar modelo correcto
def detect_and_load_nlp(text: str):
    """Detecta idioma y carga el modelo NLP correspondiente."""
    try:
        detected_lang = detect(text)
        language = MODEL_LANGUAGES.get(detected_lang, "es")
        return load_nlp_model(language)
    except Exception as e:
        logger.error(f"❌ Error detectando idioma: {e}")
        return load_nlp_model("es")

# ✅ Se mueve la inicialización después de definir las funciones
nlp = load_nlp_model("es")  # Modelo por defecto en español

# ✅ Creación de PhraseMatcher dinámico
def phrase_matcher_factory(nlp_model):
    """Crea una instancia de PhraseMatcher según el modelo NLP disponible."""
    return PhraseMatcher(nlp_model.vocab) if nlp_model else None  #quitamos , attr="LOWER"

# ✅ Inicialización de SkillExtractor con idioma dinámico
try:
    skill_db_path = "/home/pablo/skill_db_relax_20.json"
    logger.info(f"📂 Cargando base de datos de habilidades desde: {skill_db_path}")

    with open(skill_db_path, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)
    
    logger.info(f"✅ Base de datos cargada con {len(skills_db)} registros")

    nlp_default = load_nlp_model("es")  
    phrase_matcher = phrase_matcher_factory(nlp_default)

    if nlp_default and phrase_matcher:
        try:
            sn = SkillExtractor(nlp=nlp_default, skills_db=skills_db, phraseMatcher=phrase_matcher)
            logger.info("✅ SkillExtractor inicializado correctamente.")
        except Exception as e:
            sn = None
            logger.error(f"❌ Error en SkillExtractor: {e}", exc_info=True)
    else:
        sn = None
        logger.warning("⚠ No se pudo inicializar SkillExtractor: `nlp_default` o `phrase_matcher` es None.")

except Exception as e:
    logger.error(f"❌ Error inicializando SkillExtractor: {e}", exc_info=True)
    sn = None

# ✅ Modificar NLPProcessor para manejar modelos dinámicos
class NLPProcessor:
    """Procesador de NLP para análisis de texto, intenciones, sentimiento e intereses."""

    def __init__(self, language: str = "es"):
        """Inicializa el procesador NLP con el idioma especificado."""
        self.language = language
        self.nlp = load_nlp_model(language)
        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        self.define_intent_patterns()
        self.gpt_handler = GPTHandler()
        self.sentiment_analyzer = RoBertASentimentAnalyzer()  # Inicializar RoBERTa aquí
        self.model_type = None
        self._load_model_config()
        self.stop_words = set(stopwords.words("spanish") + stopwords.words("english"))

    def _load_model_config(self):
        """Carga la configuración del modelo desde GptApi."""
        try:
            gpt_api = GptApi.objects.first()
            if gpt_api:
                self.model_type = gpt_api.model_type
                if not self.gpt_handler.client:
                    asyncio.run(self.gpt_handler.initialize())
                logger.info(f"Modelo configurado: {self.model_type}")
            else:
                self.model_type = "gpt-4"
                logger.warning("No se encontró configuración de GptApi, usando GPT-4 por defecto.")
        except Exception as e:
            logger.error(f"Error cargando configuración de modelo: {e}", exc_info=True)
            self.model_type = "gpt-4"

    def set_language(self, language: str):
        """Permite cambiar dinámicamente el idioma del modelo NLP."""
        self.language = language
        self.nlp = load_nlp_model(language)
        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        logger.info(f"🔄 Modelo NLP cambiado a: {language}")

    def define_intent_patterns(self) -> None:
        """Define patrones de intenciones con Matcher."""
        if not self.matcher:
            return
        # ... (patrones existentes sin cambios)
        logger.debug("Patrones de intenciones definidos: saludo, despedida, informacion_servicios, ayuda.")

    async def analyze(self, text: str) -> dict:
        """Análisis asíncrono de texto con RoBERTa para sentimiento."""
        from app.chatbot.utils import clean_text, validate_term_in_catalog, get_all_divisions

        if not self.nlp:
            logger.error("No se ha cargado el modelo spaCy, devolviendo análisis vacío.")
            return {"intents": [], "entities": [], "sentiment": "neutral", "detected_divisions": []}

        cleaned_text = clean_text(text)
        doc = await asyncio.to_thread(self.nlp, cleaned_text)  # Hacer SpaCy asíncrono
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        intents = []
        if self.matcher:
            matches = await asyncio.to_thread(self.matcher, doc)  # Hacer Matcher asíncrono
            intents = [self.nlp.vocab.strings[match_id] for match_id, _, _ in matches]
        
        # Usar RoBERTa para sentimiento en lugar de NLTK
        sentiment = await asyncio.to_thread(self.sentiment_analyzer.analyze_sentiment, cleaned_text)
        all_divisions = get_all_divisions()
        detected_divisions = [term for term in entities if validate_term_in_catalog(term[0], all_divisions)]

        logger.debug(f"Análisis: Intenciones={intents}, Entidades={entities}, Sentimiento={sentiment}")
        return {
            "entities": entities,
            "intents": intents,
            "sentiment": sentiment,  # Ahora solo RoBERTa
            "detected_divisions": detected_divisions
        }

    async def extract_skills(self, text: str, business_unit: str = "huntRED®") -> dict:
        """Extrae habilidades usando skillNer, TabiyaJobClassifier y GPTHandler, con análisis de sentimientos unificado."""
        from app.chatbot.utils import get_all_skills_for_unit, get_positions_by_skills, prioritize_interests, map_skill_to_database

        text_normalized = unidecode.unidecode(text.lower())
        skills_from_skillner = set()
        skills_from_tabiya = set()
        skills_from_gpt = set()
        all_skills = get_all_skills_for_unit(business_unit)

        # 1️⃣ Extracción con skillNer
        for skill in all_skills:
            skill_normalized = unidecode.unidecode(skill.lower())
            if re.search(r'\b' + re.escape(skill_normalized) + r'\b', text_normalized):
                skills_from_skillner.add(skill)
        if sn and self.nlp and self.nlp.vocab.vectors_length > 0:
            try:
                results = await asyncio.to_thread(sn.annotate, text)  # Hacer skillNer asíncrono
                if isinstance(results, dict) and "results" in results:
                    extracted_skills = {item["skill"] for item in results["results"] if isinstance(item, dict)}
                    skills_from_skillner.update(extracted_skills)
            except Exception as e:
                logger.error(f"Error en SkillExtractor: {e}", exc_info=True)

        # 2️⃣ Extracción con TabiyaJobClassifier
        tabiya_classifier = TabiyaJobClassifier()
        try:
            tabiya_results = await asyncio.to_thread(tabiya_classifier.classify, text)  # Hacer Tabiya asíncrono
            skills_from_tabiya = {item['skill'] for item in tabiya_results if 'skill' in item}
        except Exception as e:
            logger.error(f"Error con TabiyaJobClassifier: {e}", exc_info=True)

        # 3️⃣ Extracción con GPTHandler
        if not self.gpt_handler.client:
            await self.gpt_handler.initialize()
        prompt = (
            f"Extrae habilidades técnicas, blandas o herramientas del texto según el marco ESCO "
            f"y devuélvelas en un JSON usando nombres estándar y sin duplicados.\n\n"
            f"Texto: {text}\n\nSalida: "
        )
        response = await self.gpt_handler.generate_response(prompt, business_unit=None)
        try:
            gpt_output = json.loads(response.split("Salida: ")[-1].strip() if "Salida: " in response else response)
            skills_from_gpt = {map_skill_to_database(skill, all_skills) for skill in gpt_output.get("skills", []) if map_skill_to_database(skill, all_skills)}
        except json.JSONDecodeError:
            skills_from_gpt = set()
            logger.warning("Error al parsear respuesta de GPTHandler")

        # 4️⃣ Análisis de sentimiento con RoBERTa (ya calculado en analyze)
        analysis = await self.analyze(text)  # Reutilizar el análisis unificado
        sentiment = analysis["sentiment"]
        sentiment_score = 1.0 if sentiment == "positive" else 0.7 if sentiment == "neutral" else 0.5

        # 5️⃣ Combinación final
        all_skills_combined = skills_from_skillner.union(skills_from_tabiya).union(skills_from_gpt)

        # 6️⃣ Priorizar intereses y sugerir posiciones
        prioritized_interests = prioritize_interests(list(all_skills_combined))
        suggested_positions = get_positions_by_skills(list(all_skills_combined))

        result = {
            "skills": list(all_skills_combined),
            "prioritized_interests": prioritized_interests,
            "suggested_positions": suggested_positions,
            "sentiment": sentiment,
            "sentiment_score": sentiment_score
        }
        logger.info(f"Análisis final: {result}")
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

class TabiyaJobClassifier:
    def __init__(self):
        self.linker = EntityLinker()

    def classify(self, text):
        return self.linker.link_text(text)

class RoBertASentimentAnalyzer:
    def __init__(self, model_name="cardiffnlpsentiment-robertabassentiment"):
        self.tokenizer = AutoTokenizer.from_pretrain(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrain(model_name)

    def analyze_sentiment(self, text):
        inputs = self.tokenizer(text, return_tens=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            predicted_class = torch.arginmax(logits, dim=1).item()
        labels = ["negative", "neutral", "positive"]
        return labels[predicted_class]


# Instancia global del procesador
nlp_processor = NLPProcessor()