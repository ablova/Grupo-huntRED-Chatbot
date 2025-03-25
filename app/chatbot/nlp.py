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

# Rutas de archivos (ajustadas según tu estructura)
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "tabiya_skills": "/home/pablo/skills_data/tabiya/tabiya-esco-v1.1.1/csv/skills.csv",
    "opportunity_catalog": "/home/pablo/app/utilidades/catalogs/skills.json",
    "intents": "/home/pablo/chatbot_data/intents.json"  # Este archivo ya no se usa
}

# Catálogos globales para evitar recarga
CANDIDATE_CATALOG = None
OPPORTUNITY_CATALOG = None
INTENTS_CATALOG = None

class NLPProcessor:
    def __init__(self, mode: str = "candidate", analysis_depth: str = "quick", language: str = "es"):
        """
        Inicializa el procesador NLP con modelos y catálogos.
        Modo: 'candidate' o 'opportunity'.
        Análisis: 'quick' (rápido), 'deep' (profundo), 'intense' (intenso).
        """
        self.mode = mode
        self.depth = analysis_depth
        self.language = language
        self.last_used = time.time()

        # Modelos ligeros para quick
        try:
            self.nlp_spacy = spacy.load("es_core_news_sm" if language == "es" else "en_core_web_sm")
        except Exception as e:
            logger.error(f"Error al cargar modelo spaCy: {e}")
            self.nlp_spacy = None

        # Modelos multilenguajes (inicializados como None para lazy loading)
        self._encoder = None
        self._encoder_tokenizer = None
        self._ner = None
        self._translator = None
        self._translator_fallback = None  # Para el modelo local como respaldo
        self._sentiment_analyzer = None
        self._intent_classifier = None
        self.api_key = os.getenv("GROK_API_KEY")

        # Cargar catálogos globales (solo una vez)
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

    def _check_and_free_models(self, timeout=600):  # 10 minutos
        """Libera modelos si han estado inactivos por más del tiempo especificado."""
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
        """Carga el modelo encoder y tokenizer bajo demanda."""
        if self._encoder is None:
            try:
                self._encoder = TFAutoModel.from_pretrained("distilbert-base-multilingual-cased")
                self._encoder_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")
                logger.info("Modelo encoder y tokenizer cargados con éxito")
            except Exception as e:
                logger.error(f"Error al cargar el encoder: {e}")
                raise
        return self._encoder, self._encoder_tokenizer

    def _load_ner(self):
        """Carga el modelo NER bajo demanda."""
        if self._ner is None:
            try:
                self._ner = pipeline("ner", model="dslim/bert-base-NER", framework="tf", aggregation_strategy="simple")
                logger.info("Modelo NER cargado con éxito")
            except Exception as e:
                logger.error(f"Error al cargar el modelo NER: {e}")
                raise
        return self._ner

    def _load_translator(self):
        """Carga el traductor de Google Translate bajo demanda."""
        if self._translator is None:
            try:
                self._translator = Translator()
                logger.info("Traductor Google Translate cargado con éxito")
            except Exception as e:
                logger.error(f"Error al cargar el traductor de Google Translate: {e}")
                raise
        return self._translator

    def _load_translator_fallback(self):
        """Carga el modelo de traducción local como respaldo."""
        if self._translator_fallback is None:
            try:
                self._translator_fallback = pipeline("translation", model="facebook/m2m100_418M", framework="tf", src_lang="es", tgt_lang="en")
                logger.info("Modelo de traducción local cargado con éxito: facebook/m2m100_418M")
            except Exception as e:
                logger.error(f"Error al cargar el modelo de traducción local: {e}")
                raise
        return self._translator_fallback

    def _load_sentiment_analyzer(self):
        """Carga el analizador de sentimientos bajo demanda."""
        if self._sentiment_analyzer is None:
            try:
                self._sentiment_analyzer = SentimentIntensityAnalyzer()
                logger.info("Analizador de sentimientos cargado con éxito")
            except Exception as e:
                logger.error(f"Error al cargar el analizador de sentimientos: {e}")
                raise
        return self._sentiment_analyzer

    def _load_intent_classifier(self):
        """Carga el clasificador de intenciones bajo demanda."""
        if self._intent_classifier is None:
            try:
                self._intent_classifier = pipeline("text-classification", model="distilbert-base-multilingual-cased", framework="tf")
                logger.info("Clasificador de intenciones cargado con éxito")
            except Exception as e:
                logger.error(f"Error al cargar el clasificador de intenciones: {e}")
                raise
        return self._intent_classifier

    def _load_catalog(self, catalog_type: str) -> Dict[str, List[Dict[str, str]]]:
        """Carga y combina los catálogos de habilidades según el tipo."""
        cache_key = f"catalog_{catalog_type}"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info(f"Catálogo de {catalog_type} cargado desde caché")
            return cached_catalog

        catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}

        # Diccionario de archivos esperados y cómo procesarlos
        CATALOG_FILES = {
            "relax_skills": {
                "path": FILE_PATHS["relax_skills"],
                "type": "json",
                "process": lambda data: self._process_relax_skills(data, catalog)
            },
            "esco_skills": {
                "path": FILE_PATHS["esco_skills"],
                "type": "json",
                "process": lambda data: self._process_esco_skills(data, catalog)
            },
            "tabiya_skills": {
                "path": FILE_PATHS["tabiya_skills"],
                "type": "csv",
                "process": lambda data: self._process_csv_skills(data, catalog)
            },
            "skills": {
                "path": "/home/pablo/skills_data/skills.json",
                "type": "json",
                "process": lambda data: self._process_json_skills(data, catalog, categories=["technical", "soft", "tools", "certifications"])
            },
            "occupations_es": {
                "path": "/home/pablo/skills_data/occupations_es.json",
                "type": "json",
                "process": lambda data: self._process_occupations(data, catalog)
            },
            "skills_relax": {
                "path": "/home/pablo/skills_data/skills_relax.json",
                "type": "json",
                "process": lambda data: self._process_json_skills(data, catalog, categories=["technical", "soft", "tools", "certifications"])
            },
            "skills_opportunities": {
                "path": "/home/pablo/skills_data/skills_opportunities.json",
                "type": "json",
                "process": lambda data: self._process_opportunities(data, catalog)
            }
        }

        for file_key, file_info in CATALOG_FILES.items():
            path = file_info["path"]
            if path in [FILE_PATHS["opportunity_catalog"], FILE_PATHS["intents"]]:
                continue
            if not os.path.exists(path):
                logger.warning(f"Archivo no encontrado: {path}. Omitiendo.")
                continue
            try:
                if file_info["type"] == "json":
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    logger.debug(f"Contenido de {path}: {json.dumps(data, indent=2)[:500]}...")  # Mostrar primeros 500 caracteres
                elif file_info["type"] == "csv":
                    data = pd.read_csv(path)
                    logger.debug(f"Columnas de {path}: {list(data.columns)}")
                    logger.debug(f"Primeras filas de {path}:\n{data.head().to_string()}")
                skills_before = {category: len(catalog[category]) for category in catalog}
                file_info["process"](data)
                skills_added = {category: len(catalog[category]) - skills_before[category] for category in catalog}
                logger.info(f"Cargado {path} con éxito. Habilidades añadidas: {skills_added}")
            except Exception as e:
                logger.error(f"Error al cargar {path}: {e}")
                continue
        
        for category in catalog:
            seen = set()
            catalog[category] = [s for s in catalog[category] if not (s["translated"] in seen or seen.add(s["translated"]))]
        
        logger.info(f"Catálogo de {catalog_type} cargado: {len(catalog['technical'])} technical, {len(catalog['soft'])} soft")
        cache.set(cache_key, catalog, timeout=None)  # Almacenar sin expiración
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

    def _load_opportunity_catalog(self) -> List[Dict]:
        """Carga el catálogo de oportunidades."""
        cache_key = "opportunity_catalog"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info("Catálogo de oportunidades cargado desde caché")
            return cached_catalog

        opp_path = FILE_PATHS["opportunity_catalog"]
        if not os.path.exists(opp_path):
            logger.error(f"Archivo no encontrado: {opp_path}. Usando catálogo vacío.")
            return []
        try:
            with open(opp_path, "r", encoding="utf-8") as f:
                opp_data = json.load(f)
            if not isinstance(opp_data, list):
                logger.error(f"El contenido de {opp_path} no es una lista válida. Usando catálogo vacío.")
                return []
            opportunities = []
            for opp in opp_data:
                if not isinstance(opp, dict) or "title" not in opp:
                    logger.warning(f"Entrada inválida en {opp_path}: {opp}. Saltando.")
                    continue
                skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
                for category in skills:
                    category_skills = opp.get(category, [])
                    if category_skills:
                        translated_skills = asyncio.run(self._translate_to_english_batch(category_skills))
                        for skill, translated in zip(category_skills, translated_skills):
                            lang = detect(skill)
                            skills[category].append({"original": skill, "translated": translated.lower(), "lang": lang})
                opportunities.append({"title": opp["title"], "required_skills": skills})
            logger.info(f"Catálogo de oportunidades cargado con {len(opportunities)} oportunidades")
            cache.set(cache_key, opportunities, timeout=None)  # Almacenar sin expiración
            return opportunities
        except Exception as e:
            logger.error(f"Error al cargar {opp_path}: {e}. Usando catálogo vacío.")
            return []

    def _load_intents(self) -> Dict[str, List[str]]:
        """Carga el catálogo de intents desde intents_handler.py."""
        cache_key = "intents_catalog"
        cached_catalog = cache.get(cache_key)
        if cached_catalog is not None:
            logger.info("Catálogo de intents cargado desde caché")
            return cached_catalog

        try:
            from app.chatbot.intents_handler import INTENTS
            intents_data = {}
            for intent, data in INTENTS.items():
                intents_data[intent] = data.get("patterns", [])
            logger.info("Intents cargados con éxito desde intents_handler.py")
            cache.set(cache_key, intents_data, timeout=None)  # Almacenar sin expiración
            return intents_data
        except Exception as e:
            logger.error(f"Error al cargar intents desde intents_handler.py: {e}. Usando intents vacíos.")
            return {}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    async def _translate_with_google_async(self, text: str) -> str:
        """Traduce un texto usando Google Translate de manera asíncrona."""
        cache_key = f"translation_{text}_es_en"
        cached_translation = cache.get(cache_key)
        if cached_translation is not None:
            return cached_translation
        
        translator = self._load_translator()
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: translator.translate(text, src="es", dest="en", timeout=5)
            )
            cache.set(cache_key, result.text, timeout=3600)  # Expirar después de 1 hora
            return result.text
        except Exception as e:
            raise Exception(f"Error en traducción con Google Translate: {e}")

    async def _translate_batch_with_google(self, texts: List[str]) -> List[str]:
        """Traduce múltiples textos en paralelo usando Google Translate."""
        tasks = [self._translate_with_google_async(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [result if isinstance(result, str) else text for result, text in zip(results, texts)]

    def _translate_to_english(self, text: str) -> str:
        """Traduce texto a inglés si es necesario, usando Google Translate como primera opción y m2m100 como respaldo."""
        try:
            return asyncio.run(self._translate_with_google_async(text))
        except Exception as e:
            logger.warning(f"Error en traducción con Google Translate: {e}. Intentando con modelo local.")

        translator_fallback = self._load_translator_fallback()
        try:
            result = translator_fallback(text, max_length=512)
            return result[0]["translation_text"]
        except Exception as e:
            logger.warning(f"Error en traducción con modelo local: {e}. Usando texto original.")
            return text

    async def _translate_to_english_batch(self, texts: List[str]) -> List[str]:
        """Traduce múltiples textos a inglés en paralelo."""
        try:
            return await self._translate_batch_with_google(texts)
        except Exception as e:
            logger.warning(f"Error en traducción por lote con Google Translate: {e}. Usando modelo local.")
            translator_fallback = self._load_translator_fallback()
            try:
                results = [translator_fallback(text, max_length=512)[0]["translation_text"] for text in texts]
                return results
            except Exception as e:
                logger.warning(f"Error en traducción por lote con modelo local: {e}. Usando textos originales.")
                return texts

    def preprocess(self, text: str) -> Dict[str, str]:
        """Preprocesa el texto, detecta el idioma y traduce si es necesario."""
        if not text or len(text.strip()) < 3:
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        try:
            lang = detect(text)
        except Exception as e:
            logger.warning(f"Error al detectar idioma: {e}. Asumiendo idioma desconocido.")
            lang = "unknown"
        translated = self._translate_to_english(text) if lang != "en" else text
        return {"original": text.lower(), "translated": translated.lower(), "lang": lang}

    async def preprocess_batch(self, texts: List[str]) -> List[Dict[str, str]]:
        """Preprocesa múltiples textos en paralelo."""
        try:
            langs = [detect(text) if text and len(text.strip()) >= 3 else "unknown" for text in texts]
        except Exception as e:
            logger.warning(f"Error al detectar idiomas: {e}. Asumiendo idioma desconocido.")
            langs = ["unknown"] * len(texts)

        to_translate = [text for text, lang in zip(texts, langs) if lang != "en"]
        translated_texts = await self._translate_to_english_batch(to_translate)
        translated_iter = iter(translated_texts)

        results = []
        for text, lang in zip(texts, langs):
            if not text or len(text.strip()) < 3:
                results.append({"original": text.lower(), "translated": text.lower(), "lang": "unknown"})
            else:
                translated = next(translated_iter) if lang != "en" else text
                results.append({"original": text.lower(), "translated": translated.lower(), "lang": lang})
        return results

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """Extrae habilidades del texto según el modo y profundidad."""
        self._check_and_free_models()
        preprocessed = self.preprocess(text)
        translated = preprocessed["translated"]
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        catalog = self.candidate_catalog if self.mode == "candidate" else self.opportunity_catalog

        if self.depth == "quick":
            # Modo rápido: búsqueda simple en catálogo
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
            # Modo profundo: NER + embeddings
            ner = self._load_ner()
            ner_results = ner(translated)
            for res in ner_results:
                if res["score"] > 0.7:  # Umbral de confianza
                    category = self._classify_entity(res["entity_group"])
                    skills[category].append({"original": res["word"], "translated": res["word"].lower(), "lang": preprocessed["lang"]})
            
            text_emb = self.get_text_embedding(translated)
            for category, skill_list in catalog.items():
                for skill_dict in skill_list:
                    skill_emb = self.get_skill_embedding(skill_dict["translated"])
                    similarity = cosine_similarity([text_emb], [skill_emb])[0][0]
                    if similarity > 0.8:  # Umbral de similitud
                        skills[category].append(skill_dict)
        elif self.depth == "intense":
            # Modo intenso: usar API externa (Grok)
            if not self.api_key:
                logger.error("API key para Grok no encontrada. Asegúrate de configurar GROK_API_KEY.")
                return skills
            try:
                response = requests.post(
                    "https://api.xai.com/grok",  # Ajustar URL según la API real
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
        
        # Eliminar duplicados
        for category in skills:
            seen = set()
            skills[category] = [s for s in skills[category] if not (s["translated"] in seen or seen.add(s["translated"]))]
        
        return skills

    def _classify_entity(self, entity_group: str) -> str:
        """Clasifica entidades NER en categorías de habilidades."""
        if entity_group in ["SKILL", "TECH"]:
            return "technical"
        if entity_group == "TOOL":
            return "tools"
        if entity_group == "CERT":
            return "certifications"
        return "soft"

    def _classify_skill(self, skill_dict: Dict[str, str], catalog: Dict[str, List]) -> None:
        """Clasifica una habilidad en una categoría."""
        skill = skill_dict["translated"]
        if any(keyword in skill for keyword in ["certified", "certification", "license"]):
            catalog["certifications"].append(skill_dict)
        elif any(keyword in skill for keyword in ["python", "java", "sql", "aws", "machine learning"]):
            catalog["technical"].append(skill_dict)
        elif any(keyword in skill for keyword in ["tool", "software", "excel", "git"]):
            catalog["tools"].append(skill_dict)
        else:
            catalog["soft"].append(skill_dict)

    def get_text_embedding(self, text: str) -> np.ndarray:
        """Genera el embedding del texto."""
        cache_key = f"embedding_{text}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        encoder, tokenizer = self._load_encoder()
        inputs = tokenizer(text, return_tensors="tf", padding=True, truncation=True, max_length=128)
        outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
        embedding = tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]
        cache.set(cache_key, embedding, timeout=3600)  # Expirar después de 1 hora
        return embedding

    def get_skill_embedding(self, skill: str) -> np.ndarray:
        """Genera el embedding de una habilidad con cacheo."""
        cache_key = f"skill_embedding_{skill}"
        cached_embedding = cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding

        embedding = self.get_text_embedding(skill)
        cache.set(cache_key, embedding, timeout=3600)  # Expirar después de 1 hora
        return embedding

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analiza el sentimiento del texto."""
        sentiment_analyzer = self._load_sentiment_analyzer()
        sentiment = sentiment_analyzer.polarity_scores(text)
        return {
            "compound": sentiment["compound"],
            "label": "positive" if sentiment["compound"] > 0.05 else "negative" if sentiment["compound"] < -0.05 else "neutral"
        }

    def classify_intent(self, text: str) -> Dict[str, float]:
        """Clasifica la intención del usuario en una conversación de chatbot."""
        intent_classifier = self._load_intent_classifier()
        preprocessed = self.preprocess(text)
        translated = preprocessed["translated"]
        intent_result = intent_classifier(translated)[0]
        return {"intent": intent_result["label"], "confidence": intent_result["score"]}

    def match_opportunities(self, candidate_skills: Dict[str, List[Dict[str, str]]]) -> List[Dict]:
        """Relaciona las habilidades del candidato con oportunidades laborales."""
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
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)[:5]  # Top 5

    async def analyze(self, text: str) -> Dict:
        """Analiza el texto según el modo y profundidad."""
        start_time = time.time()
        preprocessed = self.preprocess(text)
        skills = await self.extract_skills(text)
        sentiment = self.analyze_sentiment(preprocessed["translated"])
        result = {
            "skills": skills,
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
            result["opportunities"] = self.match_opportunities(skills)
        elif self.mode == "opportunity":
            result["required_skills"] = skills

        if self.depth == "quick":
            result["intents"] = self.classify_intent(text)
        
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