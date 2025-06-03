from typing import List, Dict, Any
import spacy
from transformers import pipeline

from app.ats.utils.skills.base.base_models import Skill, Competency, SkillCategory, CompetencyLevel
from app.ats.utils.skills.prediction import create_skill_predictor

def create_skill_processor(language: str = 'es') -> Dict[str, Any]:
    """
    Crea un procesador de habilidades.
    
    Args:
        language: Idioma del procesamiento
        
    Returns:
        Diccionario con el procesador configurado
    """
    # Cargar modelos
    nlp = spacy.load(f"{language}_core_news_lg")
    classifier = pipeline("text-classification", model="nlptown/bert-base-multilingual-uncased-sentiment")
    
    # Configurar predictor
    predictor = create_skill_predictor(
        model=None,  # Aquí se cargaría el modelo entrenado
        feature_names=[]  # Aquí se cargarían los nombres de características
    )
    
    return {
        'nlp': nlp,
        'classifier': classifier,
        'predictor': predictor,
        'process_text': lambda text: _process_text(text, nlp, classifier, predictor)
    }

def _process_text(text: str, nlp, classifier, predictor) -> List[Skill]:
    """
    Procesa un texto para extraer habilidades.
    
    Args:
        text: Texto a procesar
        nlp: Modelo de spaCy
        classifier: Clasificador de texto
        predictor: Predictor de habilidades
        
    Returns:
        Lista de habilidades extraídas
    """
    # Procesar con spaCy
    doc = nlp(text)
    
    # Extraer entidades y frases relevantes
    skills = []
    for ent in doc.ents:
        if ent.label_ in ['SKILL', 'TECH']:
            skill = Skill(
                name=ent.text,
                category=SkillCategory.TECHNICAL,
                confidence=ent._.confidence if hasattr(ent._, 'confidence') else 1.0
            )
            skills.append(skill)
    
    return skills 