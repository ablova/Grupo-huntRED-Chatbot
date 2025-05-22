# /home/pablo/app/com/chatbot/workflow/assessments/cultural/cultural_fit_test.py
"""
Módulo de funciones para el test de compatibilidad cultural.
Proporciona funciones para obtener preguntas, analizar respuestas y guardar perfiles culturales.
"""

import logging
from typing import Dict, List, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)

async def get_cultural_fit_questions(
    test_type: str = 'CulturalFit',
    domain: str = 'general',
    business_unit: Optional[Any] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Obtiene las preguntas para el test de compatibilidad cultural.
    
    Args:
        test_type: Tipo de test (por defecto 'CulturalFit')
        domain: Dominio del test (por defecto 'general')
        business_unit: Unidad de negocio específica
        
    Returns:
        Dict con preguntas organizadas por dimensión
    """
    # Preguntas base para cada dimensión
    questions = {
        "values": [
            {
                "id": "v1",
                "text": "¿Qué valor consideras más importante en un entorno laboral?",
                "options": ["Apoyo mutuo", "Competitividad", "Innovación", "Tradición"],
                "type": "single_choice"
            },
            {
                "id": "v2",
                "text": "¿Cómo te sientes respecto al trabajo en equipo?",
                "options": ["Muy importante", "Importante", "Neutral", "Prefiero trabajar solo"],
                "type": "single_choice"
            }
        ],
        "motivators": [
            {
                "id": "m1",
                "text": "¿Qué te motiva más en tu trabajo?",
                "options": ["Reconocimiento", "Desarrollo personal", "Estabilidad", "Desafíos"],
                "type": "single_choice"
            }
        ],
        "work_style": [
            {
                "id": "ws1",
                "text": "¿Prefieres trabajar con horarios fijos o flexibles?",
                "options": ["Horarios fijos", "Flexibles", "Mixto", "No me importa"],
                "type": "single_choice"
            }
        ]
    }
    
    # Ajustar preguntas según la unidad de negocio
    if business_unit:
        # Aquí se pueden agregar preguntas específicas por BU
        pass
        
    return questions

async def analyze_cultural_fit_responses(
    responses: Dict[str, List[Any]],
    business_unit: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Analiza las respuestas del test cultural.
    
    Args:
        responses: Diccionario con respuestas por dimensión
        business_unit: Unidad de negocio específica
        
    Returns:
        Dict con resultados del análisis
    """
    analysis = {
        "values": {
            "score": 0,
            "insights": []
        },
        "motivators": {
            "score": 0,
            "insights": []
        },
        "work_style": {
            "score": 0,
            "insights": []
        }
    }
    
    # Analizar respuestas por dimensión
    for dimension, answers in responses.items():
        if dimension in analysis:
            # Calcular score y generar insights
            score = sum(1 for ans in answers if ans in ["Apoyo mutuo", "Muy importante", "Desarrollo personal", "Flexibles"])
            analysis[dimension]["score"] = (score / len(answers)) * 100 if answers else 0
            
            # Generar insights basados en las respuestas
            if dimension == "values":
                if "Apoyo mutuo" in answers:
                    analysis[dimension]["insights"].append("Valoras el trabajo colaborativo")
            elif dimension == "motivators":
                if "Desarrollo personal" in answers:
                    analysis[dimension]["insights"].append("Te enfocas en el crecimiento profesional")
    
    return analysis

async def save_cultural_profile(
    person_id: str,
    analysis_result: Dict[str, Any],
    business_unit: Optional[Any] = None
) -> bool:
    """
    Guarda el perfil cultural del usuario.
    
    Args:
        person_id: ID de la persona
        analysis_result: Resultados del análisis
        business_unit: Unidad de negocio específica
        
    Returns:
        bool: True si se guardó correctamente
    """
    try:
        # Aquí iría la lógica para guardar en la base de datos
        logger.info(f"Perfil cultural guardado para persona {person_id}")
        return True
    except Exception as e:
        logger.error(f"Error guardando perfil cultural: {str(e)}")
        return False 