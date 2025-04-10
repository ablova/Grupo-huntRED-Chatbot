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

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
FILE_PATHS = {
    "relax_skills": "/home/pablo/skills_data/skill_db_relax_20.json",
    "esco_skills": "/home/pablo/skills_data/ESCO_occup_skills.json",
}
MODEL_CONFIG = {'SIMILARITY_THRESHOLD': 0.8}

# Caché global de embeddings
SKILL_EMBEDDINGS = {}

# Variable global para el modelo
USE_MODEL = None

def load_use_model(model_url="https://tfhub.dev/google/universal-sentence-encoder/4", cache_dir="/home/pablo/tfhub_cache"):
    """Carga el modelo Universal Sentence Encoder con manejo robusto de caché y permisos."""
    global USE_MODEL
    try:
        # Configuración ligera para CPU
        tf.config.optimizer.set_jit(True)
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.config.set_soft_device_placement(True)
        
        # Manejo del directorio de caché
        import os
        import shutil
        import time
        
        # Limpiar completamente el caché para evitar conflictos
        if os.path.exists(cache_dir):
            logger.info(f"Limpiando caché existente en {cache_dir}")
            for _ in range(3):  # Intentar 3 veces
                try:
                    shutil.rmtree(cache_dir)  # Eliminar todo el directorio
                    break
                except PermissionError:
                    logger.warning("Esperando permisos para limpiar caché, reintentando...")
                    time.sleep(1)
            else:
                raise RuntimeError("No se pudo limpiar el caché tras reintentos")
        
        # Crear directorio fresco con permisos correctos
        os.makedirs(cache_dir, mode=0o700)
        os.environ["TFHUB_CACHE_DIR"] = cache_dir
        logger.info(f"Cargando modelo desde {model_url} con caché fresco en {cache_dir}")
        
        USE_MODEL = hub.KerasLayer(model_url, input_shape=[], dtype=tf.string, trainable=False)
        
        # Validación
        test_input = tf.constant(["test"])
        test_embedding = USE_MODEL(test_input).numpy()
        logger.info(f"Modelo cargado y validado: dimensión {test_embedding.shape}")
        
        # Limpieza
        del test_input, test_embedding
        tf.keras.backend.clear_session()
    except Exception as e:
        logger.error(f"Error crítico al cargar el modelo: {str(e)}")
        raise RuntimeError(f"No se pudo cargar el modelo de TF Hub: {str(e)}")

@lru_cache(maxsize=1000)
def translate_text(text: str) -> str:
    """Traducción con caché"""
    try:
        translator = GoogleTranslator(source='auto', target='en')
        return translator.translate(text)
    except Exception as e:
        logger.error(f"Error en traducción: {e}")
        return text

def initialize_skill_embeddings(catalog: str = "relax_skills", batch_size=10):
    """Carga embeddings en lotes pequeños para minimizar uso de memoria."""
    global SKILL_EMBEDDINGS
    if USE_MODEL is None:
        raise RuntimeError("Modelo USE no está cargado. Inicializa el modelo primero.")
    
    start_time = time.time()
    try:
        with open(FILE_PATHS[catalog], "r", encoding="utf-8") as f:
            skills_data = json.load(f)
        
        skill_names = [skill_info.get("skill_name") for skill_info in skills_data.values() if skill_info.get("skill_name")]
        logger.info(f"Cargando {len(skill_names)} habilidades desde {catalog}")
        
        # Procesar en lotes muy pequeños para evitar OOM
        for i in range(0, len(skill_names), batch_size):
            batch = skill_names[i:i + batch_size]
            translated_batch = [translate_text(name) for name in batch]
            batch_tensor = tf.constant(translated_batch)
            embeddings = USE_MODEL(batch_tensor).numpy()
            SKILL_EMBEDDINGS.update({translated.lower(): emb for translated, emb in zip(translated_batch, embeddings)})
            
            # Limpieza inmediata por lote
            del batch, translated_batch, batch_tensor, embeddings
            tf.keras.backend.clear_session()
        
        logger.info(f"Embeddings de {catalog} cargados en {time.time() - start_time:.2f}s, total: {len(SKILL_EMBEDDINGS)}")
        
        # Liberación final
        del skill_names, skills_data
    except Exception as e:
        logger.error(f"Error al inicializar embeddings de {catalog}: {str(e)}")
        raise

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
        if USE_MODEL is None:
            raise RuntimeError("Modelo USE no está cargado.")
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
        """Clasifica habilidades en categorías"""
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

async def load_esco_skills():
    """Carga habilidades de ESCO en segundo plano con reintentos y limpieza."""
    max_retries = 3
    retry_delay = 5  # segundos
    
    for attempt in range(max_retries):
        try:
            logger.info("Cargando habilidades de ESCO en segundo plano...")
            initialize_skill_embeddings("esco_skills", batch_size=5)  # Lote aún más pequeño
            logger.info("Carga de ESCO completada")
            break
        except Exception as e:
            logger.warning(f"Intento {attempt + 1}/{max_retries} fallido: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Fallo definitivo al cargar habilidades de ESCO")
                raise
        finally:
            tf.keras.backend.clear_session()

# Inicialización del modelo y habilidades
try:
    load_use_model()  # Cargar modelo con fallback
    initialize_skill_embeddings()  # Inicializar embeddings
except RuntimeError as e:
    logger.critical(f"Fallo crítico al inicializar el modelo o embeddings: {str(e)}")
    raise

if __name__ == "__main__":
    # Ejemplo de uso
    nlp = NLPProcessor()
    text = "Tengo experiencia en Python y liderazgo, busco trabajo remoto."
    result = asyncio.run(nlp.analyze(text))
    print(result)

    # Cargar ESCO en segundo plano
    asyncio.run(load_esco_skills())