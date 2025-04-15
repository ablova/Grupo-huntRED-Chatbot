# 📌 Ubicación en servidor: /home/pablo/app/chatbot/generate_embeddings.py
import logging
import os
import time
from app.chatbot.nlp import load_use_model, initialize_skill_embeddings, ensure_directory_permissions

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/pablo/logs/generate_embeddings.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def track_progress(catalog: str, batch_size: int, total_skills: int, current_batch: int, start_time: float) -> None:
    """Muestra el progreso de la generación de embeddings."""
    batches_total = (total_skills + batch_size - 1) // batch_size
    progress = (current_batch + 1) / batches_total * 100
    elapsed = time.time() - start_time
    if current_batch > 0:
        eta = (elapsed / (current_batch + 1)) * (batches_total - current_batch - 1)
    else:
        eta = 0
    logger.info(f"Procesando {catalog}: Lote {current_batch + 1}/{batches_total} ({progress:.1f}%), ETA: {eta:.0f}s")

if __name__ == "__main__":
    try:
        logger.info("Iniciando generación de embeddings")
        ensure_directory_permissions("/home/pablo/skills_data")
        ensure_directory_permissions("/home/pablo/tfhub_cache")
        
        # Cargar el modelo
        start_time = time.time()
        load_use_model()
        logger.info(f"Modelo cargado en {time.time() - start_time:.2f}s")

        # Generar embeddings para relax_skills con progreso
        catalog = "relax_skills"
        batch_size = 20
        start_time = time.time()
        logger.info(f"Generando embeddings para {catalog} con batch_size={batch_size}")
        # Simular conteo de habilidades para mostrar progreso
        with open('/home/pablo/skills_data/skill_db_relax_20.json', 'r', encoding='utf-8') as f:
            skills_data = json.load(f)
        total_skills = len([s for s in skills_data.values() if s.get("skill_name")])
        logger.info(f"Total de habilidades en {catalog}: {total_skills}")

        # Modificar initialize_skill_embeddings para soportar callbacks de progreso
        def initialize_with_progress(catalog: str, batch_size: int):
            from app.chatbot.nlp import SKILL_EMBEDDINGS, USE_MODEL
            if SKILL_EMBEDDINGS:
                logger.info(f"Embeddings ya cargados para {catalog}, omitiendo")
                return
            with open(FILE_PATHS[catalog], "r", encoding="utf-8") as f:
                skills_data = json.load(f)
            skill_names = [skill_info.get("skill_name") for skill_info in skills_data.values() if skill_info.get("skill_name")]
            batch_start_time = time.time()
            for i in range(0, len(skill_names), batch_size):
                batch = skill_names[i:i + batch_size]
                translated_batch = [translate_text(name) for name in batch]
                batch_tensor = tf.constant(translated_batch)
                embeddings = USE_MODEL(batch_tensor).numpy().astype(np.float32)
                SKILL_EMBEDDINGS.update({translated.lower(): emb for translated, emb in zip(translated_batch, embeddings)})
                track_progress(catalog, batch_size, total_skills, i // batch_size, batch_start_time)
                del batch, translated_batch, batch_tensor, embeddings
                tf.keras.backend.clear_session()
                gc.collect()
            with open(EMBEDDINGS_CACHE, "wb") as f:
                pickle.dump({"version": MODEL_CONFIG['CACHE_VERSION'], "embeddings": SKILL_EMBEDDINGS}, f)
            os.chmod(EMBEDDINGS_CACHE, 0o660)
            os.chown(EMBEDDINGS_CACHE, os.getuid(), 1004)

        # Generar embeddings para relax_skills
        initialize_with_progress("relax_skills", batch_size=20)
        logger.info(f"Embeddings para relax_skills generados en {time.time() - start_time:.2f}s")

        # Generar embeddings para esco_skills
        catalog = "esco_skills"
        batch_size = 5
        start_time = time.time()
        logger.info(f"Generando embeddings para {catalog} con batch_size={batch_size}")
        with open('/home/pablo/skills_data/ESCO_occup_skills.json', 'r', encoding='utf-8') as f:
            skills_data = json.load(f)
        total_skills = len([s for s in skills_data.values() if s.get("skill_name")])
        logger.info(f"Total de habilidades en {catalog}: {total_skills}")
        initialize_with_progress("esco_skills", batch_size=5)
        logger.info(f"Embeddings para esco_skills generados en {time.time() - start_time:.2f}s")

        logger.info("Embeddings pre-generados y guardados en caché")
    except Exception as e:
        logger.error(f"Error generando embeddings: {str(e)}", exc_info=True)
        raise