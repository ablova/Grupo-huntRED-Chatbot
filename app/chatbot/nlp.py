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
import tensorflow as tf
import tensorflow_hub as hub
from sklearn.metrics.pairwise import cosine_similarity
from functools import lru_cache
import os
import pickle
import gc
from filelock import FileLock
import sys

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pablo/logs/nlp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constantes
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
}
EMBEDDINGS_CACHE = "/home/pablo/skills_data/embeddings_cache.pkl"
LOCK_FILE = "/home/pablo/skills_data/nlp_init.lock"
MODEL_CONFIG = {
    'SIMILARITY_THRESHOLD': 0.75,
    'CACHE_VERSION': 'v1.1'  # Actualizar versión para forzar regeneración si es necesario
}

# Variables globales
SKILL_EMBEDDINGS = {}
USE_MODEL = None

# Verificación para saltar carga pesada durante migraciones
SKIP_HEAVY_INIT = 'makemigrations' in sys.argv or 'migrate' in sys.argv

def ensure_directory_permissions(path: str, mode: int = 0o770) -> None:
    """Asegura permisos correctos para un directorio y sus archivos."""
    try:
        if not os.path.exists(path):
            os.makedirs(path, mode=mode)
        os.chmod(path, mode)
        os.chown(path, os.getuid(), 1004)  # GID de ai_huntred
        for root, dirs, files in os.walk(path):
            for d in dirs:
                os.chmod(os.path.join(root, d), mode)
                try:
                    os.chown(os.path.join(root, d), os.getuid(), 1004)
                except Exception:
                    pass
            for f in files:
                os.chmod(os.path.join(root, f), 0o660)
                try:
                    os.chown(os.path.join(root, f), os.getuid(), 1004)
                except Exception:
                    pass
        logger.debug(f"Permisos asegurados para {path}")
    except Exception as e:
        logger.warning(f"No se pudo configurar permisos para {path}: {str(e)}")

def load_use_model(model_url: str = "https://tfhub.dev/google/universal-sentence-encoder/4",
                  cache_dir: str = "/home/pablo/tfhub_cache") -> None:
    """Carga el modelo Universal Sentence Encoder con manejo robusto."""
    global USE_MODEL
    if SKIP_HEAVY_INIT:
        logger.info("Saltando carga del modelo durante migración")
        return
    if USE_MODEL is not None:
        logger.info("Modelo ya cargado, reutilizando instancia")
        return

    ensure_directory_permissions(os.path.dirname(LOCK_FILE))
    ensure_directory_permissions(cache_dir)
    with FileLock(LOCK_FILE):
        if USE_MODEL is not None:
            return

        try:
            # Configuración optimizada para CPU
            os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Deshabilitar GPU
            tf.config.threading.set_intra_op_parallelism_threads(1)
            tf.config.threading.set_inter_op_parallelism_threads(1)
            tf.config.set_soft_device_placement(True)
            tf.config.optimizer.set_jit(True)  # Habilitar XLA

            os.environ["TFHUB_CACHE_DIR"] = cache_dir
            logger.info(f"Cargando modelo desde {model_url} con caché en {cache_dir}")
            USE_MODEL = hub.KerasLayer(model_url, input_shape=[], dtype=tf.string, trainable=False)

            # Validar modelo
            test_input = tf.constant(["test"])
            test_embedding = USE_MODEL(test_input).numpy()
            logger.info(f"Modelo cargado y validado: dimensión {test_embedding.shape}")

            del test_input, test_embedding
            tf.keras.backend.clear_session()
            gc.collect()
        except Exception as e:
            logger.error(f"Error crítico al cargar el modelo: {str(e)}")
            raise RuntimeError(f"No se pudo cargar el modelo de TF Hub: {str(e)}")

def initialize_skill_embeddings(catalog: str = "relax_skills", batch_size: int = 20) -> None:
    """Carga embeddings desde caché o genera en lotes pequeños."""
    global SKILL_EMBEDDINGS
    if SKIP_HEAVY_INIT:
        logger.info("Saltando inicialización de embeddings durante migración")
        return
    if USE_MODEL is None:
        load_use_model()

    ensure_directory_permissions(os.path.dirname(EMBEDDINGS_CACHE))
    with FileLock(LOCK_FILE):
        # Verificar caché
        if os.path.exists(EMBEDDINGS_CACHE):
            try:
                with open(EMBEDDINGS_CACHE, "rb") as f:
                    cached_data = pickle.load(f)
                if cached_data.get("version") == MODEL_CONFIG['CACHE_VERSION']:
                    SKILL_EMBEDDINGS.update(cached_data["embeddings"])
                    logger.info(f"Embeddings cargados desde caché: {len(SKILL_EMBEDDINGS)} habilidades")
                    return
                else:
                    logger.warning("Versión de caché incompatible, regenerando...")
            except Exception as e:
                logger.warning(f"Fallo al cargar embeddings desde caché: {str(e)}, regenerando...")

        start_time = time.time()
        try:
            with open(FILE_PATHS[catalog], "r", encoding="utf-8") as f:
                skills_data = json.load(f)

            skill_names = [skill_info.get("skill_name") for skill_info in skills_data.values() if skill_info.get("skill_name")]
            logger.info(f"Cargando {len(skill_names)} habilidades desde {catalog}")

            for i in range(0, len(skill_names), batch_size):
                batch = skill_names[i:i + batch_size]
                translated_batch = [translate_text(name) for name in batch]
                batch_tensor = tf.constant(translated_batch)
                embeddings = USE_MODEL(batch_tensor).numpy()
                SKILL_EMBEDDINGS.update({translated.lower(): emb for translated, emb in zip(translated_batch, embeddings)})

                del batch, translated_batch, batch_tensor, embeddings
                tf.keras.backend.clear_session()
                gc.collect()

            logger.info(f"Embeddings de {catalog} cargados en {time.time() - start_time:.2f}s, total: {len(SKILL_EMBEDDINGS)}")

            # Guardar en caché con versión
            with open(EMBEDDINGS_CACHE, "wb") as f:
                pickle.dump({"version": MODEL_CONFIG['CACHE_VERSION'], "embeddings": SKILL_EMBEDDINGS}, f)
            os.chmod(EMBEDDINGS_CACHE, 0o660)
            os.chown(EMBEDDINGS_CACHE, os.getuid(), 1004)

            del skill_names, skills_data
            gc.collect()
        except Exception as e:
            logger.error(f"Error al inicializar embeddings de {catalog}: {str(e)}")
            raise

@lru_cache(maxsize=1000)
def translate_text(text: str) -> str:
    """Traducción con caché."""
    if SKIP_HEAVY_INIT:
        return text
    try:
        translator = GoogleTranslator(source='auto', target='en')
        return translator.translate(text)
    except Exception as e:
        logger.error(f"Error en traducción: {str(e)}")
        return text

class NLPProcessor:
    def __init__(self, mode: str = "candidate", language: str = "es", analysis_depth: str = "quick"):
        self.mode = mode
        self.language = language
        self.analysis_depth = analysis_depth
        logger.info(f"NLPProcessor inicializado: modo={mode}, idioma={language}, profundidad={analysis_depth}")

    async def preprocess(self, text: str) -> Dict[str, str]:
        if SKIP_HEAVY_INIT:
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}
        start_time = time.time()
        try:
            lang = await sync_to_async(detect)(text)
            translated = translate_text(text) if lang != "en" else text
            logger.info(f"Texto preprocesado en {time.time() - start_time:.2f}s")
            return {"original": text.lower(), "translated": translated.lower(), "lang": lang}
        except Exception as e:
            logger.error(f"Error en preprocesamiento: {str(e)}")
            return {"original": text.lower(), "translated": text.lower(), "lang": "unknown"}

    def get_text_embedding(self, text: str) -> np.ndarray:
        if SKIP_HEAVY_INIT:
            return np.zeros(512)
        if USE_MODEL is None:
            load_use_model()
        try:
            embedding = USE_MODEL([text]).numpy()[0]
            tf.keras.backend.clear_session()
            gc.collect()
            return embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {str(e)}")
            return np.zeros(512)

    async def extract_skills(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        if SKIP_HEAVY_INIT:
            return {"technical": [], "soft": [], "tools": [], "certifications": []}
        if USE_MODEL is None:
            load_use_model()
        if not SKILL_EMBEDDINGS:
            initialize_skill_embeddings()
        start_time = time.time()
        try:
            preprocessed = await self.preprocess(text)
            text_emb = self.get_text_embedding(preprocessed["translated"])
            skills = {"technical": [], "soft": [], "tools": [], "certifications": []}

            # Ajustar umbral dinámicamente
            threshold = {
                "quick": 0.7,
                "deep": 0.8,
                "intense": 0.9
            }.get(self.analysis_depth, MODEL_CONFIG['SIMILARITY_THRESHOLD'])

            for skill, emb in SKILL_EMBEDDINGS.items():
                similarity = cosine_similarity([text_emb], [emb])[0][0]
                if similarity > threshold:
                    skill_dict = {"original": skill, "translated": skill, "lang": "en", "embedding": emb.tolist()}
                    self._classify_skill(skill_dict, skills)

            logger.info(f"Habilidades extraídas en {time.time() - start_time:.2f}s (profundidad: {self.analysis_depth})")
            del text_emb
            gc.collect()
            return skills
        except Exception as e:
            logger.error(f"Error extrayendo habilidades: {str(e)}")
            return {"technical": [], "soft": [], "tools": [], "certifications": []}

    def _classify_skill(self, skill_dict: Dict, skills: Dict) -> None:
        skill_name = skill_dict["original"].lower()
        if "cert" in skill_name:
            skills["certifications"].append(skill_dict)
        elif any(t in skill_name for t in ["python", "sql", "java"]):
            skills["technical"].append(skill_dict)
        elif any(s in skill_name for s in ["comunicación", "liderazgo"]):
            skills["soft"].append(skill_dict)
        else:
            skills["tools"].append(skill_dict)

    def analyze_sentiment(self, text: str) -> str:
        if SKIP_HEAVY_INIT:
            return "neutral"
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            return "positive" if polarity > 0.05 else "negative" if polarity < -0.05 else "neutral"
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            return "neutral"

    async def analyze(self, text: str) -> Dict:
        if SKIP_HEAVY_INIT:
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "execution_time": 0.0,
                    "original_text": text.lower(),
                    "translated_text": text.lower(),
                    "detected_language": "unknown"
                }
            }
        start_time = time.time()
        try:
            preprocessed = await self.preprocess(text)
            skills = await self.extract_skills(text)
            sentiment = self.analyze_sentiment(preprocessed["translated"])

            if self.mode == "candidate":
                pass  # Lógica futura para candidatos
            elif self.mode == "opportunity":
                pass  # Lógica futura para oportunidades

            execution_time = time.time() - start_time
            logger.info(f"Análisis completado en {execution_time:.2f}s (modo: {self.mode})")
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
        except Exception as e:
            logger.error(f"Error en análisis: {str(e)}")
            return {
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "original_text": text.lower(),
                    "translated_text": text.lower(),
                    "detected_language": "unknown"
                }
            }

    async def analyze_batch(self, texts: List[str]) -> List[Dict]:
        if SKIP_HEAVY_INIT:
            return [{
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "execution_time": 0.0,
                    "original_text": text.lower(),
                    "translated_text": text.lower(),
                    "detected_language": "unknown"
                }
            } for text in texts]
        start_time = time.time()
        try:
            tasks = [self.analyze(text) for text in texts]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Procesamiento en lote completado en {time.time() - start_time:.2f}s")
            return results
        except Exception as e:
            logger.error(f"Error en procesamiento en lote: {str(e)}")
            return [{
                "skills": {"technical": [], "soft": [], "tools": [], "certifications": []},
                "sentiment": "neutral",
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "original_text": text.lower(),
                    "translated_text": text.lower(),
                    "detected_language": "unknown"
                }
            } for text in texts]

async def load_esco_skills() -> None:
    """Carga habilidades de ESCO en segundo plano."""
    if SKIP_HEAVY_INIT:
        logger.info("Saltando carga de habilidades ESCO durante migración")
        return
    with FileLock(LOCK_FILE):
        logger.info("Cargando habilidades de ESCO en segundo plano...")
        try:
            initialize_skill_embeddings("esco_skills", batch_size=5)
            logger.info("Carga de ESCO completada")
            tf.keras.backend.clear_session()
            gc.collect()
        except Exception as e:
            logger.error(f"Error cargando habilidades ESCO: {str(e)}")

def initialize_nlp() -> None:
    if not SKIP_HEAVY_INIT:
        load_use_model()
        initialize_skill_embeddings()

if __name__ == "__main__":
    nlp = NLPProcessor()
    text = "Tengo experiencia en Python y liderazgo, busco trabajo remoto."
    result = asyncio.run(nlp.analyze(text))
    print(result)
    asyncio.run(load_esco_skills())