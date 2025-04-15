# /home/pablo/app/chatbot/generate_embeddings.py

import logging
import os
import time
import json
from app.chatbot.nlp import load_use_model, initialize_skill_embeddings

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
    eta = (elapsed / (current_batch + 1)) * (batches_total - current_batch - 1) if current_batch > 0 else 0
    logger.info(f"Procesando {catalog}: Lote {current_batch + 1}/{batches_total} ({progress:.1f}%), ETA: {eta:.0f}s")

if __name__ == "__main__":
    try:
        logger.info("Iniciando generación de embeddings")
        
        # Cargar el modelo
        start_time = time.time()
        load_use_model()
        logger.info(f"Modelo cargado en {time.time() - start_time:.2f}s")

        # Generar embeddings para relax_skills con progreso
        catalog = "relax_skills"
        batch_size = 20
        start_time = time.time()
        logger.info(f"Generando embeddings para {catalog} con batch_size={batch_size}")
        with open('/home/pablo/skills_data/skill_db_relax_20.json', 'r', encoding='utf-8') as f:
            skills_data = json.load(f)
        total_skills = len([s for s in skills_data.values() if s.get("skill_name")])
        logger.info(f"Total de habilidades en {catalog}: {total_skills}")
        
        initialize_skill_embeddings(catalog=catalog, batch_size=batch_size)
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
        
        initialize_skill_embeddings(catalog=catalog, batch_size=batch_size)
        logger.info(f"Embeddings para esco_skills generados en {time.time() - start_time:.2f}s")

        logger.info("Embeddings pre-generados y guardados en caché")
    except Exception as e:
        logger.error(f"Error generando embeddings: {str(e)}", exc_info=True)
        raise