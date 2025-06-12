# /home/pablo/app/com/chatbot/generate_embeddings.py
import logging
import os
import time
import json
import gc
import numpy as np
import tensorflow as tf
import tensorflow_text as text  # Required for SentencepieceOp
import pickle
import sys
from tenacity import retry, stop_after_attempt, wait_exponential
try:
    from deep_translator import GoogleTranslator
    from langdetect import detect
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

# Set project root and PYTHONPATH
project_root = "/home/pablo"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Django setup
os.environ['DJANGO_SETTINGS_MODULE'] = 'ai_huntred.settings'
try:
    import django
    django.setup()
except ImportError as e:
    logging.error(f"Error setting up Django: {str(e)}")
    sys.exit(1)

from app.ats.chatbot.nlp.nlp import load_use_model, FILE_PATHS, EMBEDDINGS_CACHE

# Configuración de logging
log_dir = "/home/pablo/logs"
log_file = os.path.join(log_dir, "generate_embeddings.log")

def ensure_directory_permissions(directory):
    try:
        os.makedirs(directory, exist_ok=True)
        os.chmod(directory, 0o775)
        try:
            os.chown(directory, os.getuid(), os.getgid())  # Use current group
        except PermissionError as e:
            logger.warning(f"No se pudo cambiar propietario de {directory}: {str(e)}")
    except Exception as e:
        logger.warning(f"No se pudo configurar permisos para {directory}: {str(e)}")

try:
    ensure_directory_permissions(log_dir)
except Exception as e:
    logging.warning(f"Advertencia: No se pudo configurar permisos para {log_dir}: {str(e)}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('nlp')

# Configuración del modelo
MODEL_CONFIG = {'CACHE_VERSION': '1.0'}
SKILL_EMBEDDINGS = {}
USE_MODEL = None
BATCH_SIZE = 50

def track_progress(catalog: str, batch_size: int, total_skills: int, current_batch: int, start_time: float) -> None:
    """Muestra el progreso de la generación de embeddings."""
    batches_total = (total_skills + batch_size - 1) // batch_size
    progress = (current_batch + 1) / batches_total * 100
    elapsed = time.time() - start_time
    eta = (elapsed / (current_batch + 1)) * (batches_total - current_batch - 1) if current_batch > 0 else 0
    logger.info(f"Procesando {catalog}: Lote {current_batch + 1}/{batches_total} ({progress:.1f}%), ETA: {eta:.0f}s")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def translate_text(text: str) -> str:
    """Traduce texto a inglés si es necesario."""
    if not TRANSLATOR_AVAILABLE or not text:
        return text
    try:
        lang = detect(text)
        if lang != "en":
            translator = GoogleTranslator(source='auto', target='en')
            return translator.translate(text)
        return text
    except Exception as e:
        logger.warning(f"Error traduciendo texto '{text}': {str(e)}")
        return text

def initialize_with_progress(catalog: str, batch_size: int, embeddings_cache: str) -> bool:
    """Genera embeddings con seguimiento de progreso y manejo de memoria optimizado."""
    global SKILL_EMBEDDINGS, USE_MODEL
    cache_key = f"{catalog}_partial"

    # Verificar si ya está completo
    cached_data = None
    if os.path.exists(embeddings_cache):
        try:
            with open(embeddings_cache, "rb") as f:
                cached_data = pickle.load(f)
            if cached_data.get("version") == MODEL_CONFIG['CACHE_VERSION'] and catalog in cached_data.get("catalogs", []):
                logger.info(f"Embeddings ya generados para {catalog}, omitiendo")
                SKILL_EMBEDDINGS.update(cached_data.get("embeddings", {}))
                return True
        except Exception as e:
            logger.warning(f"Fallo al leer caché para {catalog}: {str(e)}, regenerando...")

    # Cargar datos
    try:
        with open(FILE_PATHS[catalog], "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"No se pudo leer {FILE_PATHS[catalog]}: {str(e)}")
        return False

    # Ajustar según el catálogo
    skill_names = []
    if catalog == "candidate_quick":
        skill_names = [skill_info.get("skill_cleaned", skill_info.get("skill_name", "")) for skill_info in data.values() if skill_info.get("skill_name")]
    elif catalog == "candidate_deep":
        for occ_key, occ_data in data.items():
            for skill_field in ["hasEssentialSkill", "hasOptionalSkill"]:
                skills = occ_data.get(skill_field, [])
                for skill in skills:
                    skill_name = skill.get("preferredLabel", {}).get("en", "") or skill.get("title", "")
                    if skill_name:
                        skill_names.append(skill_name.lower())
    else:
        logger.error(f"Catálogo no reconocido: {catalog}")
        return False

    total_skills = len(skill_names)
    logger.info(f"Total de habilidades en {catalog}: {total_skills}")

    # Cargar progreso parcial si existe
    start_index = 0
    partial_cache = f"{embeddings_cache}.{catalog}.partial"
    if os.path.exists(partial_cache):
        try:
            with open(partial_cache, "rb") as f:
                partial_data = pickle.load(f)
            SKILL_EMBEDDINGS.update(partial_data.get("embeddings", {}))
            start_index = partial_data.get("last_index", 0)
            logger.info(f"Retomando desde índice {start_index} para {catalog}")
        except Exception as e:
            logger.warning(f"Fallo al cargar caché parcial para {catalog}: {str(e)}, iniciando desde cero")

    # Generar embeddings
    batch_start_time = time.time()
    try:
        USE_MODEL = load_use_model()
        if USE_MODEL is None:
            logger.error(f"No se pudo cargar el modelo para {catalog}")
            return False

        for i in range(start_index, total_skills, batch_size):
            batch = skill_names[i:i + batch_size]
            translated_batch = [translate_text(name) for name in batch]
            batch_tensor = tf.constant(translated_batch)
            embeddings = USE_MODEL(batch_tensor).numpy().astype(np.float32)
            SKILL_EMBEDDINGS.update({translated.lower(): emb for translated, emb in zip(translated_batch, embeddings)})

            track_progress(catalog, batch_size, total_skills, i // batch_size, batch_start_time)
            
            # Guardar progreso parcial
            with open(partial_cache, "wb") as f:
                pickle.dump({"embeddings": SKILL_EMBEDDINGS, "last_index": i + batch_size}, f)
            os.chmod(partial_cache, 0o660)
            try:
                os.chown(partial_cache, os.getuid(), os.getgid())
            except PermissionError as e:
                logger.warning(f"No se pudo cambiar propietario de {partial_cache}: {str(e)}")

            # Liberar memoria
            del batch, translated_batch, batch_tensor, embeddings
            tf.keras.backend.clear_session()
            gc.collect()

        # Guardar caché final
        with open(embeddings_cache, "wb") as f:
            cached_data = {
                "version": MODEL_CONFIG['CACHE_VERSION'],
                "catalogs": cached_data.get("catalogs", []) + [catalog] if cached_data else [catalog],
                "embeddings": SKILL_EMBEDDINGS
            }
            pickle.dump(cached_data, f)
        os.chmod(embeddings_cache, 0o660)
        try:
            os.chown(embeddings_cache, os.getuid(), os.getgid())
        except PermissionError as e:
            logger.warning(f"No se pudo cambiar propietario de {embeddings_cache}: {str(e)}")

        # Eliminar caché parcial
        if os.path.exists(partial_cache):
            os.remove(partial_cache)

        logger.info(f"Embeddings generados para {catalog}")
        return True
    except Exception as e:
        logger.error(f"Error procesando {catalog}: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    from app.ats.integrations.services import send_message_async
    import asyncio
    try:
        logger.info("Iniciando generación de embeddings")
        ensure_directory_permissions("/home/pablo/skills_data")
        ensure_directory_permissions("/home/pablo/tfhub_cache")
        
        # Procesar catálogos
        success = True
        for catalog in ["candidate_quick"]:  # Temporarily skip candidate_deep
            logger.info(f"Generando embeddings para {catalog} con batch_size={BATCH_SIZE}")
            start_time = time.time()
            if not initialize_with_progress(catalog, BATCH_SIZE, EMBEDDINGS_CACHE):
                logger.error(f"Fallo al generar embeddings para {catalog}")
                success = False
            else:
                logger.info(f"Embeddings para {catalog} generados en {time.time() - start_time:.2f}s")

        # Lista de business units para notificaciones
        business_units = ["huntRED", "amigro"]
        
        if success:
            logger.info("Embeddings pre-generados y guardados en caché")
            # Enviar notificación de éxito
            asyncio.run(asyncio.gather(*[
                send_message_async(
                    platform="telegram",
                    user_id="871198362",
                    message="✅ Generación de embeddings completada exitosamente.",
                    business_unit_name=bu
                ) for bu in business_units
            ]))
        else:
            logger.error("Generación de embeddings incompleta")
            # Enviar notificación de fallo
            asyncio.run(asyncio.gather(*[
                send_message_async(
                    platform="telegram",
                    user_id="871198362",
                    message="❌ Generación de embeddings fallida. Revisa los logs.",
                    business_unit_name=bu
                ) for bu in business_units
            ]))
    except Exception as e:
        logger.error(f"Error crítico generando embeddings: {str(e)}", exc_info=True)
        # Enviar notificación de error
        asyncio.run(asyncio.gather(*[
            send_message_async(
                platform="telegram",
                user_id="871198362",
                message=f"❌ Error crítico en generate_embeddings.py: {str(e)}",
                business_unit_name=bu
            ) for bu in business_units
        ]))
        raise