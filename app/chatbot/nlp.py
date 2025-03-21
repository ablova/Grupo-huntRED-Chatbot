import os
import json
import time
import logging
import spacy
import nltk
import pandas as pd
from functools import lru_cache
from langdetect import detect
import numpy as np
import tensorflow as tf
from transformers import pipeline, TFAutoModel, AutoTokenizer
from sklearn.metrics.pairwise import cosine_similarity
from diskcache import Cache
from typing import Dict, List, Optional
import requests
from app.ml.ml_opt import configure_tensorflow_based_on_load
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from app.chatbot.intents_handler import INTENTS  # Importar INTENTS directamente

# Configurar TensorFlow según la carga del sistema
configure_tensorflow_based_on_load()

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nltk.download('vader_lexicon', quiet=True)

# Rutas de archivos (ajustadas según tu estructura, sin "intents")
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
    "tabiya_skills": "/home/pablo/skills_data/tabiya/tabiya-esco-v1.1.1/csv/skills.csv",
    "opportunity_catalog": "/home/pablo/app/utilidades/catalogs/skills.json"
}

class NLPProcessor:
    def __init__(self, mode: str = "candidate", analysis_depth: str = "quick", language: str = "es"):
        """
        Inicializa el procesador NLP con modelos y catálogos.
        Modo: 'candidate' o 'opportunity'.
        Análisis: 'quick' (rápido) o 'deep' (profundo).
        """
        self.mode = mode
        self.depth = analysis_depth
        self.language = language
        self.last_used = time.time()

        # Modelos ligeros para quick
        self.nlp_spacy = spacy.load("es_core_news_sm" if language == "es" else "en_core_web_sm")

        # Modelos multilenguajes (inicializados como None para lazy loading)
        self._encoder = None
        self._encoder_tokenizer = None
        self._ner = None
        self._translator = None
        self._sentiment_analyzer = None
        self._intent_classifier = None
        self.api_key = os.getenv("GROK_API_KEY")

        # Catálogos
        self.candidate_catalog = self._load_catalog("candidate")
        self.opportunity_catalog = self._load_opportunity_catalog()
        self.intents = self._load_intents()  # Esto ahora usará INTENTS de intents_handler.py

        # Cacheo para embeddings
        self._cache_embeddings = {}

    def _check_and_free_models(self, timeout=600):  # 10 minutos
        if time.time() - self.last_used > timeout:
            self._encoder = None
            self._ner = None
            self._translator = None
            self._sentiment_analyzer = None
            self._intent_classifier = None
            logger.info("Modelos liberados por inactividad")
        self.last_used = time.time()

    def _load_encoder(self):
        if self._encoder is None:
            self._encoder = TFAutoModel.from_pretrained("distilbert-base-multilingual-cased")
            self._encoder_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")
        return self._encoder, self._encoder_tokenizer

    def _load_ner(self):
        if self._ner is None:
            self._ner = pipeline("ner", model="dslim/bert-base-NER", framework="tf", aggregation_strategy="simple")
        return self._ner

    def _load_translator(self):
        if self._translator is None:
            self._translator = pipeline("translation", model="Helsinki-NLP/opus-mt-es-en", framework="tf")
        return self._translator

    def _load_sentiment_analyzer(self):
        if self._sentiment_analyzer is None:
            self._sentiment_analyzer = SentimentIntensityAnalyzer()
        return self._sentiment_analyzer

    def _load_intent_classifier(self):
        if self._intent_classifier is None:
            self._intent_classifier = pipeline("text-classification", model="distilbert-base-multilingual-cased", framework="tf")
        return self._intent_classifier

    @lru_cache(maxsize=1)
    def _load_catalog(self, catalog_type: str) -> Dict[str, List[Dict[str, str]]]:
        """Carga y combina los catálogos de habilidades según el tipo."""
        catalog = {"technical": [], "soft": [], "tools": [], "certifications": []}
        for path_key, path in FILE_PATHS.items():
            if path_key == "opportunity_catalog":  # Ignorar opportunity_catalog aquí
                continue
            if not os.path.exists(path):
                logger.warning(f"Archivo no encontrado: {path}")
                continue
            try:
                if path.endswith(".json"):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if path_key == "relax_skills":
                        for category in catalog:
                            for skill in data.get(category, []):
                                lang = detect(skill)
                                translated = self._translate_to_english(skill) if lang != "en" else skill
                                catalog[category].append({"original": skill, "translated": translated.lower(), "lang": lang})
                    elif path_key == "esco_skills" and isinstance(data, list):
                        for entry in data:
                            if isinstance(entry, dict) and "skill" in entry:
                                skill = entry["skill"]
                                lang = detect(skill)
                                translated = self._translate_to_english(skill) if lang != "en" else skill
                                self._classify_skill({"original": skill, "translated": translated.lower(), "lang": lang}, catalog)
                elif path.endswith(".csv"):
                    df = pd.read_csv(path)
                    for _, row in df.iterrows():
                        skill = row.get("preferredLabel_en")
                        if skill:
                            self._classify_skill({"original": skill, "translated": skill.lower(), "lang": "en"}, catalog)
                logger.info(f"Cargado {path} con éxito")
            except Exception as e:
                logger.warning(f"Error al cargar {path}: {e}")
        
        for category in catalog:
            seen = set()
            catalog[category] = [s for s in catalog[category] if not (s["translated"] in seen or seen.add(s["translated"]))]
        
        logger.info(f"Catálogo de {catalog_type} cargado: {len(catalog['technical'])} technical, {len(catalog['soft'])} soft")
        return catalog

    @lru_cache(maxsize=1)
    def _load_opportunity_catalog(self) -> List[Dict]:
        opp_path = FILE_PATHS["opportunity_catalog"]
        if not os.path.exists(opp_path):
            logger.warning(f"Archivo no encontrado: {opp_path}. Usando catálogo vacío.")
            return []
        try:
            with open(opp_path, "r", encoding="utf-8") as f:
                content = f.read().strip()  # Leer como string y eliminar espacios
                opp_data = json.loads(content)  # Convertir a objeto JSON
            opportunities = []
            for opp in opp_data:
                skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
                for category in skills:
                    for skill in opp.get(category, []):
                        lang = detect(skill)
                        translated = self._translate_to_english(skill) if lang != "en" else skill
                        skills[category].append({"original": skill, "translated": translated.lower(), "lang": lang})
                opportunities.append({"title": opp["title"], "required_skills": skills})
            logger.info(f"Catálogo de oportunidades cargado con {len(opportunities)} oportunidades")
            return opportunities
        except Exception as e:
            logger.warning(f"Error al cargar {opp_path}: {e}. Usando catálogo vacío.")
            return []

    @lru_cache(maxsize=1)
    def _load_intents(self) -> Dict[str, List[str]]:
        """Carga el catálogo de intents desde intents_handler.py."""
        logger.info("Intents cargados desde intents_handler.py")
        return {intent: data["patterns"] for intent, data in INTENTS.items()}

    def _translate_to_english(self, text: str) -> str:
        """Traduce texto a inglés si es necesario."""
        translator = self._load_translator()
        try:
            return translator(text)[0]["translation_text"]
        except Exception as e:
            logger.warning(f"Error en traducción: {e}. Usando texto original.")
            return text

    def preprocess(self, text: str) -> Dict[str, str]:
        """Preprocesa el texto, detecta el idioma y traduce si es necesario."""
        if not text or len(text.strip()) < 3:
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        lang = detect(text)
        translated = self._translate_to_english(text) if lang != "en" else text
        return {"original": text.lower(), "translated": translated.lower(), "lang": lang}

    def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """Extrae habilidades del texto según el modo y profundidad."""
        self._check_and_free_models()
        preprocessed = self.preprocess(text)
        translated = preprocessed["translated"]
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}
        catalog = self.candidate_catalog if self.mode == "candidate" else self.opportunity_catalog

        if self.depth == "quick":
            # Modo rápido: búsqueda simple en catálogo
            for category, skill_list in catalog.items():
                for skill_dict in skill_list:
                    if skill_dict["translated"] in translated or skill_dict["original"] in preprocessed["original"]:
                        skills[category].append(skill_dict)
        else:  # Modo deep
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
        
        # Eliminar duplicados
        for category in skills:
            seen = set()
            skills[category] = [s for s in skills[category] if not (s["translated"] in seen or seen.add(s["translated"]))]
        
        return skills

    def _classify_entity(self, entity_group: str) -> str:
        """Clasifica entidades NER en categorías de habilidades."""
        if entity_group in ["SKILL", "TECH"]: return "technical"
        if entity_group == "TOOL": return "tools"
        if entity_group == "CERT": return "certifications"
        return "soft"

    def _classify_skill(self, skill_dict: Dict[str, str], catalog: Dict[str, List], from_catalog: bool = False):
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

    @lru_cache(maxsize=128)
    def get_text_embedding(self, text: str) -> np.ndarray:
        """Genera el embedding del texto."""
        encoder, tokenizer = self._load_encoder()
        inputs = tokenizer(text, return_tensors="tf", padding=True, truncation=True, max_length=128)
        outputs = encoder(inputs["input_ids"], attention_mask=inputs["attention_mask"])
        return tf.reduce_mean(outputs.last_hidden_state, axis=1).numpy()[0]

    def get_skill_embedding(self, skill: str) -> np.ndarray:
        """Genera el embedding de una habilidad con cacheo."""
        if skill not in self._cache_embeddings:
            self._cache_embeddings[skill] = self.get_text_embedding(skill)
        return self._cache_embeddings[skill]

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

    def analyze(self, text: str, mode: str = None) -> Dict:
        """Analiza el texto según el modo y profundidad."""
        start_time = time.time()
        preprocessed = self.preprocess(text)
        analysis_mode = mode if mode is not None else self.mode
        skills = self.extract_skills(text)
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

        if analysis_mode == "candidate":
            result["opportunities"] = self.match_opportunities(skills)
        elif analysis_mode == "opportunity":
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
        result = nlp.analyze(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))