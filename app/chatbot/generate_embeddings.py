# 📌 Ubicación en servidor: /home/pablo/app/chatbot/generate_embeddings.py
import logging
import os
from nlp import load_use_model, initialize_skill_embeddings, ensure_directory_permissions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    ensure_directory_permissions("/home/pablo/skills_data")
    ensure_directory_permissions("/home/pablo/tfhub_cache")
    load_use_model()
    initialize_skill_embeddings("relax_skills", batch_size=20)
    initialize_skill_embeddings("esco_skills", batch_size=5)
    logger.info("Embeddings pre-generados y guardados en caché")