import logging
import os
import time
import json
import gc
import numpy as np
import tensorflow as tf
import sys
import pickle

# Agregar la raíz del proyecto al PYTHONPATH
project_root = "/home/pablo"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.chatbot.nlp import load_use_model, ensure_directory_permissions, translate_text, FILE_PATHS, EMBEDDINGS_CACHE, MODEL_CONFIG
from filelock import FileLock

# Configuración de logging
log_dir = "/home/pablo/logs"
log_file = os.path.join(log_dir, "generate_embeddings.log")

# Asegurar permisos del directorio de logs
try:
    ensure_directory_permissions(log_dir)
except Exception as e:
    print(f"Advertencia: No se pudo configurar permisos para {log_dir}: {str(e)}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def track_progress(catalog: str, batch_size: int, total_skills: int, current_batch: int, start_time: float) -> None:
    """Muestra el progreso de la generación de embeddings."""
    batches_total = (total_skills + batch_size - 1) // batch_size
    progress = (current_batch + 1) / batches_total * 100
    elapsed = time.time() - start_time
    eta = (elapsed / (current_batch + 1)) * (batches_total - current_batch - 1) if current_batch > 0 else 0
    logger.info(f"Procesando {catalog}: Lote {current_batch + 1}/{batches_total} ({progress:.1f}%), ETA: {eta:.0f}s, Memoria usada: {os.popen('free -m').readlines()[1].split()[2]} MB")

def initialize_with_progress(catalog: str, batch_size: int, embeddings_cache: str) -> bool:
    """Genera embeddings con seguimiento de progreso y manejo de memoria optimizado."""
    global SKILL_EMBEDDINGS, USE_MODEL
    from app.chatbot.nlp import SKILL_EMBEDDINGS, USE_MODEL
    cache_key = f"{catalog}_partial"

    # Verificar si ya está completo
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
            skills_data = json.load(f)
    except Exception as e:
        logger.error(f"No se pudo leer {FILE_PATHS[catalog]}: {str(e)}")
        return False

    skill_names = [skill_info.get("skill_name") for skill_info in skills_data.values() if skill_info.get("skill_name")]
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
            os.chown(partial_cache, os.getuid(), 1004)

            # Liberar memoria
            del batch, translated_batch, batch_tensor, embeddings
            tf.keras.backend.clear_session()
            gc.collect()

        # Guardar caché final
        with open(embeddings_cache, "wb") as f:
            cached_data = {
                "version": MODEL_CONFIG['CACHE_VERSION'],
                "catalogs": cached_data.get("catalogs", []) + [catalog] if os.path.exists(embeddings_cache) else [catalog],
                "embeddings": SKILL_EMBEDDINGS
            }
            pickle.dump(cached_data, f)
        os.chmod(embeddings_cache, 0o660)
        os.chown(embeddings_cache, os.getuid(), 1004)

        # Eliminar caché parcial
        if os.path.exists(partial_cache):
            os.remove(partial_cache)

        logger.info(f"Embeddings generados para {catalog}")
        return True
    except Exception as e:
        logger.error(f"Error procesando {catalog}: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    try:
        logger.info("Iniciando generación de embeddings")
        ensure_directory_permissions("/home/pablo/skills_data")
        ensure_directory_permissions("/home/pablo/tfhub_cache")
        
        # Cargar el modelo
        start_time = time.time()
        load_use_model()
        logger.info(f"Modelo cargado en {time.time() - start_time:.2f}s")

        # Procesar catálogos con lotes pequeños
        success = True
        for catalog, batch_size in [("relax_skills", 5), ("esco_skills", 5)]:
            logger.info(f"Generando embeddings para {catalog} con batch_size={batch_size}")
            start_time = time.time()
            if not initialize_with_progress(catalog, batch_size, EMBEDDINGS_CACHE):
                logger.error(f"Fallo al generar embeddings para {catalog}")
                success = False
            else:
                logger.info(f"Embeddings para {catalog} generados en {time.time() - start_time:.2f}s")

        if success:
            logger.info("Embeddings pre-generados y guardados en caché")
        else:
            logger.error("Generación de embeddings incompleta")
    except Exception as e:
        logger.error(f"Error crítico generando embeddings: {str(e)}", exc_info=True)
        raise