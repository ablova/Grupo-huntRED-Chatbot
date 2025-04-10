# 📌 Ubicación en servidor: /home/pablo/app/chatbot/nlp.py
import asyncio
import logging
import time
import json
import numpy as np
from typing import Dict, List
from asgiref.sync import sync_to_async
from langdetect import detect
from deep_translator import GoogleTranslator
from textblob import TextBlob
import tensorflow_hub as hub
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar Universal Sentence Encoder
USE_MODEL = hub.load("https://tfhub.dev/google/universal-sentence-encoder-multilingual/3")

# Constantes
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
}
MODEL_CONFIG = {'SIMILARITY_THRESHOLD': 0.8}

# Caché global de embeddings
SKILL_EMBEDDINGS = {}

@lru_cache(maxsize=1000)
def translate_text(text: str) -> str:
    """Traducción con caché"""
    try:
        translator = GoogleTranslator(source='auto', target='en')
        return translator.translate(text)
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        return text

def initialize_skill_embeddings(catalog: str = "relax_skills"):
    """Carga embeddings de habilidades desde un catálogo"""
    global SKILL_EMBEDDINGS
    with open(FILE_PATHS[catalog], "r", encoding="utf-8") as f:
        skills_data = json.load(f)
    for skill_info in skills_data.values():
        skill_name = skill_info.get("skill_name")
        if skill_name:
            translated = translate_text(skill_name)
            SKILL_EMBEDDINGS[translated.lower()] = USE_MODEL([translated]).numpy()[0]

# Cargar relax_skills por defecto
initialize_skill_embeddings()

class NLPProcessor:
    def __init__(self, mode: str = "candidate", language: str = "es"):
        self.mode = mode
        self.language = language
        logger.info(f"NLPProcessor inicializado: modo={mode}, idioma={language}")

    async def preprocess(self, text: str) -> Dict[str, str]:
        """Preprocesa el texto y lo traduce a inglés"""
        start_time = time.time()
        lang = await sync_to_async(detect)(text)
        translated = translate_text(text) if lang != "en" else text
        logger.info(f"Texto preprocesado en {time.time() - start_time:.2f}s")
        return {"original": text.lower(), "translated": translated.lower(), "lang": lang}

    def get_text_embedding(self, text: str) -> np.ndarray:
        """Genera embeddings para un texto"""
        return USE_MODEL([text]).numpy()[0]

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """Extrae habilidades del texto"""
        start_time = time.time()
        preprocessed = await self.preprocess(text)
        text_emb = self.get_text_embedding(preprocessed["translated"])
        skills = {"technical": [], "soft": [], "tools": [], "certifications": []}

        for skill, emb in SKILL_EMBEDDINGS.items():
            similarity = cosine_similarity([text_emb], [emb])[0][0]
            if similarity > MODEL_CONFIG['SIMILARITY_THRESHOLD']:
                skill_dict = {"original": skill, "translated": skill, "lang": "en", "embedding": emb.tolist()}
                self._classify_skill(skill_dict, skills)
        
        logger.info(f"Habilidades extraídas en {time.time() - start_time:.2f}s")
        return skills

    def _classify_skill(self, skill_dict: Dict, skills: Dict):
        """Clasifica habilidades en categorías (personalizable según tus necesidades)"""
        skill_name = skill_dict["original"].lower()
        if "cert" in skill_name:
            skills["certifications"].append(skill_dict)
        elif any(t in skill_name for t in ["python", "sql", "java"]):  # Ejemplo
            skills["technical"].append(skill_dict)
        elif any(s in skill_name for s in ["comunicación", "liderazgo"]):  # Ejemplo
            skills["soft"].append(skill_dict)
        else:
            skills["tools"].append(skill_dict)

    def analyze_sentiment(self, text: str) -> str:
        """Analiza el sentimiento del texto"""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        return "positive" if polarity > 0.05 else "negative" if polarity < -0.05 else "neutral"

    async def analyze(self, text: str) -> Dict:
        """Analiza un texto individual"""
        start_time = time.time()
        preprocessed = await self.preprocess(text)
        skills = await self.extract_skills(text)
        sentiment = self.analyze_sentiment(preprocessed["translated"])
        execution_time = time.time() - start_time
        logger.info(f"Análisis completado en {execution_time:.2f}s")
        return {
            "skills": skills,
            "sentiment": sentiment,
            "metadata": {
                "execution_time": execution_time,
                "original_text": preprocessed["original"],
                "translated_text": preprocessed["translated"],
                "detected_language": preprocessed["lang"]
            }
        }

    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Procesa múltiples textos en lote"""
        start_time = time.time()
        tasks = [self.analyze(text) for text in texts]
        results = await asyncio.gather(*tasks)
        logger.info(f"Procesamiento en lote completado en {time.time() - start_time:.2f}s")
        return results

# Carga asíncrona de ESCO (ejecutar en segundo plano)
async def load_esco_skills():
    logger.info("Cargando habilidades de ESCO en segundo plano...")
    initialize_skill_embeddings("esco_skills")
    logger.info("Carga de ESCO completada")

if __name__ == "__main__":
    # Ejemplo de uso
    nlp = NLPProcessor()
    text = "Tengo experiencia en Python y liderazgo, busco trabajo remoto."
    result = asyncio.run(nlp.analyze(text))
    print(result)

    # Cargar ESCO en segundo plano
    asyncio.run(load_esco_skills())