# Ubicación: /home/pablo/app/chatbot/nlp.py

import os
import json
import time
import logging
import spacy
import nltk
import pandas as pd
import asyncio
from langdetect import detect
import numpy as np
import tensorflow as tf
from transformers import pipeline, TFAutoModel, AutoTokenizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional
import requests
from app.ml.ml_opt import configure_tensorflow_based_on_load
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from googletrans import Translator
from django.core.cache import cache
from tenacity import retry, stop_after_attempt, wait_exponential

# Configurar TensorFlow según la carga del sistema
configure_tensorflow_based_on_load()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nltk.download('vader_lexicon', quiet=True)

# Rutas de archivos
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "tabiya_skills": "/home/pablo/skills_data/tabiya/tabiya-esco-v1.1.1/csv/skills.csv",
    "opportunity_catalog": "/home/pablo/app/utilidades/catalogs/skills.json",
    "intents": "/home/pablo/chatbot_data/intents.json"  # Este archivo ya no se usa directamente
}

# Definición de CATALOG_FILES
CATALOG_FILES = {
    "relax_skills": {
        "path": FILE_PATHS["relax_skills"],
        "type": "json",
        "process": lambda data, catalog: NLPProcessor._process_relax_skills(None, data, catalog)
    },
    "esco_skills": {
        "path": FILE_PATHS["esco_skills"],
        "type": "json",
        "process": lambda data, catalog: NLPProcessor._process_esco_skills(None, data, catalog)
    },
    "tabiya_skills": {
        "path": FILE_PATHS["tabiya_skills"],
        "type": "csv",
        "process": lambda data, catalog: NLPProcessor._process_csv_skills(None, data, catalog)
    }
}

# Catálogos globales
CANDIDATE_CATALOG = None
OPPORTUNITY_CATALOG = None
INTENTS_CATALOG = None

class NLPProcessor:
    def __init__(self, mode: str = "candidate", analysis_depth: str = "quick", language: str = "es"):
        self.mode = mode
        self.depth = analysis_depth
        self.language = language
        self.last_used = time.time()

        try:
            self.nlp_spacy = spacy.load("es_core_news_sm" if language == "es" else "en_core_web_sm")
        except Exception as e:
            logger.error(f"Error al cargar modelo spaCy: {e}")
            self.nlp_spacy = None

        self._encoder = None
        self._encoder_tokenizer = None
        self._ner = None
        self._translator = None
        self._translator_fallback = None
        self._sentiment_analyzer = None
        self._intent_classifier = None
        self.api_key = os.getenv("GROK_API_KEY")

        global CANDIDATE_CATALOG, OPPORTUNITY_CATALOG, INTENTS_CATALOG
        if CANDIDATE_CATALOG is None:
            CANDIDATE_CATALOG = self._load_catalog("candidate")
        if OPPORTUNITY_CATALOG is None:
            OPPORTUNITY_CATALOG = self._load_opportunity_catalog()
        if INTENTS_CATALOG is None:
            INTENTS_CATALOG = self._load_intents()

        self.candidate_catalog = CANDIDATE_CATALOG
        self.opportunity_catalog = OPPORTUNITY_CATALOG
        self.intents = INTENTS_CATALOG

        # Cacheo para embeddings (usamos django.core.cache)
        self._cache_embeddings = {}

    def _check_and_free_models(self, timeout=600):
        if time.time() - self.last_used > timeout:
            self._encoder = None
            self._ner = None
            self._translator = None
            self._translator_fallback = None
            self._sentiment_analyzer = None
            self._intent_classifier = None
            logger.info("Modelos liberados por inactividad")
        self.last_used = time.time()

    def _load_encoder(self):
        if self._encoder is None:
            self._encoder = TFAutoModel.from_pretrained("distilbert-base-multilingual-cased", from_pt=True)
            self._encoder_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")
            logger.info("Modelo encoder y tokenizer cargados con from_pt=True")
        return self._encoder, self._encoder_tokenizer

    def _load_ner(self):
        if self._ner is None:
            self._ner = pipeline("ner", model="dslim/bert-base-NER", framework="tf", aggregation_strategy="simple")
            logger.info("Modelo NER cargado")
        return self._ner

    def _load_translator(self):
        if self._translator is None:
            self._translator = Translator()
            logger.info("Traductor Google Translate cargado")
        return self._translator

    def _load_translator_fallback(self):
        if self._translator_fallback is None:
            self._translator_fallback = pipeline("translation", model="facebook/m2m100_418M", framework="tf", src_lang="es", tgt_lang="en")
            logger.info("Modelo de traducción local cargado: facebook/m2m100_418M")
        return self._translator_fallback

    def _load_sentiment_analyzer(self):
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = SentimentIntensityAnalyzer()
            logger.info("Analizador de sentimientos cargado")
        return self._sentiment_analyzer

    def _load_intent_classifier(self):
        if self._intent_classifier is None:
            self._intent_classifier = pipeline("text-classification", model="distilbert-base-multilingual-cased", framework="tf")
            logger.info("Clasificador de intenciones cargado")
        return self._intent_classifier

    def _load_catalog(self, catalog_type: str) -> Dict[str, List[Dict[str, str]]]:
        """Carga catálogos desde archivos con manejo robusto y logs."""
        cache_key = f"catalog_{catalog_type}"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info(f"Catálogo de {catalog_type} cargado desde caché")
            return cached_catalog

        catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}
        
        for file_key, file_info in CATALOG_FILES.items():
            path = file_info["path"]
            # Excluir archivos específicos
            if path in [FILE_PATHS["opportunity_catalog"], FILE_PATHS["intents"]]:
                logger.debug(f"Omitiendo archivo excluido: {path}")
                continue
            
            # Verificar existencia del archivo
            if not os.path.exists(path):
                logger.warning(f"Archivo no encontrado: {path}. Omitiendo.")
                continue
            
            try:
                if file_info["type"] == "json":
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                elif file_info["type"] == "csv":
                    data = pd.read_csv(path)
                else:
                    logger.error(f"Tipo de archivo no soportado para {path}: {file_info['type']}")
                    continue
                
                file_info["process"](data, catalog)  # Asumiendo que process actualiza el catálogo
                logger.info(f"Catálogo cargado exitosamente desde {path}")
            
            except Exception as e:
                logger.error(f"Error al cargar {path}: {e}", exc_info=True)
                continue
        
        cache.set(cache_key, catalog, timeout=CACHE_TIMEOUT)
        return catalog

    def _process_json_skills(self, data: Dict, catalog: Dict, categories: List[str]) -> None:
        """Procesa archivos JSON con habilidades organizadas por categorías."""
        for category in categories:
            skills = data.get(category, [])
            if not skills:
                logger.debug(f"No se encontraron habilidades en la categoría {category} del archivo.")
                continue
            translated_skills = asyncio.run(self._translate_to_english_batch(skills))
            for skill, translated in zip(skills, translated_skills):
                lang = detect(skill)
                catalog[category].append({"original": skill, "translated": translated.lower(), "lang": lang})

    def _process_relax_skills(self, data: Dict, catalog: Dict) -> None:
        """Procesa el archivo skill_db_relax_20.json."""
        for skill_id, skill_info in data.items():
            skill_name = skill_info.get("skill_name")
            skill_type = skill_info.get("skill_type")
            if not skill_name or not skill_type:
                logger.debug(f"Entrada inválida en skill_db_relax_20.json: {skill_info}")
                continue
            lang = detect(skill_name)
            translated = self._translate_to_english(skill_name) if lang != "en" else skill_name
            skill_dict = {"original": skill_name, "translated": translated.lower(), "lang": lang}
            if skill_type == "Certification":
                catalog["certifications"].append(skill_dict)
            elif skill_type == "Hard Skill":
                catalog["technical"].append(skill_dict)
            elif skill_type == "Soft Skill":
                catalog["soft"].append(skill_dict)
            else:
                catalog["tools"].append(skill_dict)

    def _process_esco_skills(self, data: Dict, catalog: Dict) -> None:
        """Procesa el archivo ESCO_occup_skills.json."""
        for occupation, info in data.items():
            description = info.get("description", "")
            if not description:
                logger.debug(f"No se encontró descripción para la ocupación {occupation} en ESCO_occup_skills.json")
                continue
            # Podríamos extraer habilidades de la descripción, pero por ahora lo omitimos
            logger.debug(f"Omitiendo ocupación {occupation} en ESCO_occup_skills.json: no se encontraron habilidades directas")

    def _process_csv_skills(self, data: pd.DataFrame, catalog: Dict) -> None:
        """Procesa archivos CSV con habilidades."""
        for _, row in data.iterrows():
            skill = row.get("PREFERREDLABEL")  # Ajustado a la columna real
            if skill:
                self._classify_skill({"original": skill, "translated": skill.lower(), "lang": "en"}, catalog)
            else:
                logger.debug(f"Fila sin PREFERREDLABEL en skills.csv: {row.to_dict()}")

    def _process_occupations(self, data: List[Dict], catalog: Dict) -> None:
        """Procesa el archivo occupations_es.json."""
        for entry in data:
            if isinstance(entry, dict) and "occupation" in entry:
                skills = entry.get("skills", [])
                if skills:
                    translated_skills = asyncio.run(self._translate_to_english_batch(skills))
                    for skill, translated in zip(skills, translated_skills):
                        lang = detect(skill)
                        self._classify_skill({"original": skill, "translated": translated.lower(), "lang": lang}, catalog)
            else:
                logger.debug(f"Entrada inválida en occupations_es.json: {entry}")

    def _process_opportunities(self, data: List[Dict], catalog: Dict) -> None:
        """Procesa el archivo skills_opportunities.json."""
        for entry in data:
            if isinstance(entry, dict) and "title" in entry:
                for category, skills in entry.get("skills", {}).items():
                    if skills:
                        translated_skills = asyncio.run(self._translate_to_english_batch(skills))
                        for skill, translated in zip(skills, translated_skills):
                            lang = detect(skill)
                            catalog[category].append({"original": skill, "translated": translated.lower(), "lang": lang})
            else:
                logger.debug(f"Entrada inválida en skills_opportunities.json: {entry}")

    async def _load_opportunity_catalog(self) -> List[Dict]:
        cache_key = "opportunity_catalog"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info(f"✅ Catálogo de oportunidades cargado desde caché")
            return cached_catalog

        logger.debug(f"[nlp] Cargando opportunity_catalog desde {FILE_PATHS['opportunity_catalog']}")
        opp_path = FILE_PATHS["opportunity_catalog"]
        if not os.path.exists(opp_path):
            logger.error(f"Archivo no encontrado: {opp_path}. Usando catálogo vacío.")
            return []

        try:
            with open(opp_path, "r", encoding="utf-8") as f:
                opp_data = json.load(f)

            # Si es un diccionario anidado, convertir a lista
            opportunities = []
            if isinstance(opp_data, dict):
                for business_unit, roles in opp_data.items():
                    for role, skills in roles.items():
                        skill_dict = {
                            "technical": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Habilidades Técnicas", [])],
                            "soft": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Habilidades Blandas", [])],
                            "certifications": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Certificaciones", [])],
                            "tools": [{"original": s, "translated": s.lower(), "lang": "es"} for s in skills.get("Herramientas", [])]
                        }
                        opportunities.append({
                            "title": f"{role} en {business_unit}",
                            "required_skills": skill_dict
                        })
            elif isinstance(opp_data, list):
                opportunities = opp_data  # Si ya es una lista, usarla directamente
            else:
                logger.error(f"Formato no soportado en {opp_path}. Usando catálogo vacío.")
                return []

            # Traducir habilidades a inglés
            for opp in opportunities:
                for category in opp["required_skills"]:
                    skills = opp["required_skills"][category]
                    if skills:
                        translated = await self._translate_to_english_batch([s["original"] for s in skills])
                        for skill, trans in zip(skills, translated):
                            skill["translated"] = trans.lower()

            logger.info(f"Catálogo de oportunidades cargado con {len(opportunities)} oportunidades")
            cache.set(cache_key, opportunities, timeout=None)
            logger.info(f"✅ Catálogo de oportunidades cargado con {len(opportunities)} oportunidades")
            return opportunities
        except Exception as e:
            logger.error(f"Error al cargar {opp_path}: {e}. Usando catálogo vacío.")
            return []

    def _load_intents(self) -> Dict[str, List[str]]:
        cache_key = "intents_catalog"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info("Catálogo de intents cargado desde caché")
            return cached_catalog

        try:
            from app.chatbot.intents_handler import INTENTS
            intents_data = {intent: data["patterns"] for intent, data in INTENTS.items()}
            logger.info("Intents cargados desde intents_handler.py")
            cache.set(cache_key, intents_data, timeout=None)
            return intents_data
        except Exception as e:
            logger.error(f"Error al cargar intents: {e}. Usando intents vacíos.")
            return {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def _translate_to_english(self, text: str) -> str:
        """Traducción asíncrona a inglés."""
        cache_key = f"translation_{text}_es_en"
        cached_translation = cache.get(cache_key)
        if cached_translation is not None:
            return cached_translation

        translator = self._load_translator()
        try:
            # Ejecutar la traducción en un executor para evitar bloqueos
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: translator.translate(text, src="es", dest="en").text
            )
            cache.set(cache_key, result, timeout=3600)
            return result
        except Exception as e:
            logger.warning(f"Error en traducción: {e}")
            return text  # Fallback al texto original

    async def _translate_to_english_batch(self, texts: List[str]) -> List[str]:
        """Traduce múltiples textos en paralelo."""
        tasks = [self._translate_to_english(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, str) else t for r, t in zip(results, texts)]

    async def preprocess(self, text: str) -> Dict[str, str]:
        """Preprocesamiento asíncrono del texto."""
        if not text or len(text.strip()) < 3:
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        lang = detect(text)
        translated = await self._translate_to_english(text) if lang != "en" else text
        return {"original": text.lower(), "translated": translated.lower(), "lang": lang}

    async def preprocess_batch(self, texts: List[str]) -> List[Dict[str, str]]:
        langs = [detect(text) if text and len(text.strip()) >= 3 else "unknown" for text in texts]
        to_translate = [text for text, lang in zip(texts, langs) if lang != "en"]
        translated_texts = await self._translate_to_english_batch(to_translate)
        translated_iter = iter(translated_texts)
        return [
            {"original": text.lower(), "translated": next(translated_iter) if lang != "en" else text.lower(), "lang": lang}
            if text and len(text.strip()) >= 3 else {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
            for text, lang in zip(texts, langs)
        ]

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        self._check_and_free_models()
        preprocessed = await self.preprocess(text)  # Must have await
        translated = preprocessed["translated"]
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        catalog = self.candidate_catalog if self.mode == "candidate" else self.opportunity_catalog

        if self.depth == "quick":
            if self.nlp_spacy:
                doc = self.nlp_spacy(preprocessed["original"])
                for ent in doc.ents:
                    category = self._classify_entity(ent.label_)
                    skills[category].append({"original": ent.text, "translated": ent.text.lower(), "lang": preprocessed["lang"]})
            for category, skill_list in catalog.items():
                for skill_dict in skill_list:
                    if skill_dict["translated"] in translated or skill_dict["original"] in preprocessed["original"]:
                        skills[category].append(skill_dict)
        elif self.depth == "deep":
            ner = self._load_ner()
            ner_results = ner(translated)
            for res in ner_results:
                if res["score"] > 0.7:
                    category = self._classify_entity(res["entity_group"])
                    skills[category].append({"original": res["word"], "translated": res["word"].lower(), "lang": preprocessed["lang"]})
            text_emb = self.get_text_embedding(translated)
            for category, skill_list in catalog.items():
                for skill_dict in skill_list:
                    skill_emb = self.get_skill_embedding(skill_dict["translated"])
                    similarity = cosine_similarity([text_emb], [skill_emb])[0][0]
                    if similarity > 0.8:
                        skills[category].append(skill_dict)
            self._ner = None  # Liberar modelo después de uso
        elif self.depth == "intense":
            if not self.api_key:
                logger.error("API key para Grok no encontrada.")
                return skills
            try:
                response = requests.post(
                    "https://api.xai.com/grok",  # Ajustar URL según API real
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"text": preprocessed["original"], "task": "extract_skills"}
                )
                response.raise_for_status()
                api_skills = response.json().get("skills", {})
                for category, skill_list in api_skills.items():
                    for skill in skill_list:
                        skills[category].append({"original": skill, "translated": skill.lower(), "lang": preprocessed["lang"]})
            except Exception as e:
                logger.error(f"Error al usar la API de Grok: {e}")

        for category in skills:
            seen = set()
            skills[category] = [s for s in skills[category] if not (s["translated"] in seen or seen.add(s["translated"]))]

        return {"skills": skills}

    def _classify_entity(self, entity_group: str) -> str:
        if entity_group in ["SKILL", "TECH"]:
            return "technical"
        if entity_group == "TOOL":
            return "tools"
        if entity_group == "CERT":
            return "certifications"
        return "soft"

    def get_text_embedding(self, text: str) -> np.ndarray:
        cache_key = f"embedding_{text}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        encoder, tokenizer = self._load_encoder()
        inputs = tokenizer(text, return_tensors="tf", padding=True, truncation=True, max_length=128)
        outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
        embedding = tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]
        cache.set(cache_key, embedding, timeout=3600)
        return embedding

    def get_skill_embedding(self, skill: str) -> np.ndarray:
        cache_key = f"skill_embedding_{skill}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        embedding = self.get_text_embedding(skill)
        cache.set(cache_key, embedding, timeout=3600)
        return embedding

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        sentiment_analyzer = self._load_sentiment_analyzer()
        sentiment = sentiment_analyzer.polarity_scores(text)
        return {
            "compound": sentiment["compound"],
            "label": "positive" if sentiment["compound"] > 0.05 else "negative" if sentiment["compound"] < -0.05 else "neutral"
        }

    def classify_intent(self, text: str) -> Dict[str, float]:
        intent_classifier = self._load_intent_classifier()
        preprocessed = self.preprocess(text)
        intent_result = intent_classifier(preprocessed["translated"])[0]
        return {"intent": intent_result["label"], "confidence": intent_result["score"]}

    def match_opportunities(self, candidate_skills: Dict[str, List[Dict[str, str]]]) -> List[Dict]:
        if self.mode != "candidate":
            logger.warning("match_opportunities solo está disponible en modo 'candidate'")
            return []
        matches = []
        candidate_emb = np.mean([self.get_skill_embedding(s["translated"]) for s in sum(candidate_skills.values(), [])] or [np.zeros(768)], axis=0)
        for opp in self.opportunity_catalog:
            opp_skills = sum(opp["required_skills"].values(), [])
            opp_emb = np.mean([self.get_skill_embedding(s["translated"]) for s in opp_skills] or [np.zeros(768)], axis=0)
            score = cosine_similarity([candidate_emb], [opp_emb])[0][0]
            matches.append({"opportunity": opp["title"], "match_score": score})
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)[:5]


    def get_suggested_skills(self, business_unit: str, category: str = "general") -> List[str]:
        """Devuelve habilidades sugeridas para una unidad de negocio."""
        if not self.opportunity_catalog:
            logger.warning("Catálogo de oportunidades vacío. No se pueden sugerir habilidades.")
            return []

        # Buscar oportunidades relacionadas con la unidad de negocio
        relevant_opps = [opp for opp in self.opportunity_catalog if business_unit.lower() in opp["title"].lower()]
        if not relevant_opps:
            logger.warning(f"No se encontraron oportunidades para {business_unit}. Usando catálogo general.")
            relevant_opps = self.opportunity_catalog

        # Extraer habilidades de las oportunidades relevantes
        suggested = set()
        for opp in relevant_opps:
            if category == "general":
                for cat_skills in opp["required_skills"].values():
                    for skill in cat_skills:
                        suggested.add(skill["original"])
            else:
                for skill in opp["required_skills"].get(category, []):
                    suggested.add(skill["original"])
        
        return list(suggested)

    async def analyze(self, text: str) -> Dict:
        start_time = time.time()
        preprocessed = await self.preprocess(text)
        skills = await self.extract_skills(text)
        sentiment = self.analyze_sentiment(preprocessed["translated"])
        result = {
            "skills": skills["skills"],  # Extract inner dict
            "sentiment": sentiment["label"],
            "sentiment_score": abs(sentiment["compound"]),
            "metadata": {
                "execution_time": time.time() - start_time,
                "original_text": preprocessed["original"],
                "translated_text": preprocessed["translated"],
                "detected_language": preprocessed["lang"]
            }
        }
        if self.mode == "candidate":
            result["opportunities"] = self.match_opportunities(skills["skills"])
        elif self.mode == "opportunity":
            result["required_skills"] = skills

        if self.depth == "quick":
            result["intent"] = self.classify_intent(text)

        return result

if __name__ == "__main__":
    nlp = NLPProcessor(mode="candidate", analysis_depth="quick")
    examples = {
        "candidate_quick": "Tengo experiencia en Python y trabajo en equipo.",
        "candidate_deep": "Soy un desarrollador con certificación AWS y habilidades en Java.",
        "opportunity_quick": "Buscamos un ingeniero con experiencia en SQL y comunicación."
    }
    for mode, text in examples.items():
        print(f"\nAnalizando en modo '{mode}':")
        nlp.depth = "quick" if "quick" in mode else "deep"
        result = asyncio.run(nlp.analyze(text))
        print(json.dumps(result, indent=2, ensure_ascii=False))