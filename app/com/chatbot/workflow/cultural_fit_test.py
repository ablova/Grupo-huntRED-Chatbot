# /home/pablo/app/com/chatbot/workflow/cultural_fit.py
import random
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)

# Intentamos importar los modelos necesarios con manejo de errores
try:
    from app.models import Person, PersonCulturalProfile
except ImportError:
    logger.warning("No se pudieron importar los modelos necesarios. Algunas funciones pueden no estar disponibles.")
    Person = None
    PersonCulturalProfile = None

# Estructura de preguntas para evaluación de ajuste cultural
CULTURAL_FIT_QUESTIONS = {
    'CulturalFit': {
        'general': {
            'values': [
                {
                    'text': '¿Valoras trabajar en un entorno donde la transparencia sea una prioridad?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Es importante para ti que la empresa fomente la innovación continua?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Priorizas la colaboración y el trabajo en equipo en tu entorno laboral?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'motivators': [
                {
                    'text': '¿Te motiva tener autonomía para tomar decisiones en tu trabajo?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Es importante para ti recibir reconocimiento por tus logros?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Te impulsa contribuir a proyectos con un impacto social positivo?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'interests': [
                {
                    'text': '¿Disfrutas resolver problemas complejos en tu trabajo diario?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Te apasiona aprender continuamente sobre tu área profesional?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'work_style': [
                {
                    'text': '¿Prefieres un entorno laboral estructurado con procesos claros?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Te sientes cómodo trabajando de forma independiente?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'generational_values': [
                {
                    'text': '¿Prefieres comunicarte principalmente por medios digitales sobre reuniones presenciales?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Valoras la flexibilidad horaria sobre un horario fijo de trabajo?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Es importante para ti trabajar en una empresa con propósito social definido?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'social_impact': [
                {
                    'text': '¿Participas activamente en actividades de voluntariado o causas sociales?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Prefieres trabajar en empresas que tengan programas de responsabilidad social?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
                {
                    'text': '¿Te motiva que tu trabajo tenga un impacto positivo en la sociedad?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
        },
        'consumer': {
            'values': [
                {
                    'text': '¿Valoras un entorno de ventas donde la ética sea fundamental?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'motivators': [
                {
                    'text': '¿Te motiva superar metas de ventas mensuales?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'interests': [
                {
                    'text': '¿Te interesa construir relaciones a largo plazo con clientes?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'work_style': [
                {
                    'text': '¿Prefieres un entorno dinámico con interacción constante con clientes?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
        },
        'pharma': {
            'values': [
                {
                    'text': '¿Es importante para ti trabajar en una empresa que priorice la seguridad del paciente?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'motivators': [
                {
                    'text': '¿Te motiva influir en la adopción de nuevos tratamientos médicos?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'interests': [
                {
                    'text': '¿Te apasiona estar al día con los avances científicos en farmacéutica?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'work_style': [
                {
                    'text': '¿Prefieres un entorno laboral con protocolos estrictos y regulaciones claras?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
        },
        'service': {
            'values': [
                {
                    'text': '¿Valoras un entorno donde el servicio al cliente sea la prioridad principal?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'motivators': [
                {
                    'text': '¿Te motiva resolver problemas de los clientes de manera efectiva?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'interests': [
                {
                    'text': '¿Disfrutas interactuar con personas de diversos orígenes?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
            'work_style': [
                {
                    'text': '¿Te sientes cómodo manejando múltiples tareas al mismo tiempo?',
                    'options': ['1 - Nada', '2 - Poco', '3 - Neutral', '4 - Bastante', '5 - Mucho']
                },
            ],
        },
    }
}

def get_cultural_fit_questions(test_type: str = 'CulturalFit', domain: str = 'general', business_unit: Optional[str] = None) -> List[Dict]:
    """
    Devuelve preguntas para la evaluación de ajuste cultural según el tipo de prueba, dominio y unidad de negocio.
    
    Args:
        test_type (str): Tipo de prueba (default: 'CulturalFit').
        domain (str): Dominio de las preguntas (default: 'general').
        business_unit (Optional[str]): Unidad de negocio para preguntas específicas.
    
    Returns:
        List[Dict]: Lista de preguntas con texto y opciones.
    """
    cache_key = f"cultural_fit_questions_{test_type}_{domain}_{business_unit or 'none'}"
    questions = cache.get(cache_key)
    
    if questions is None:
        try:
            questions = CULTURAL_FIT_QUESTIONS.get(test_type, {}).get(domain, {})
            if business_unit and business_unit in CULTURAL_FIT_QUESTIONS.get(test_type, {}):
                questions = CULTURAL_FIT_QUESTIONS[test_type][business_unit]
            cache.set(cache_key, questions, timeout=3600)  # Caché por 1 hora
            logger.debug(f"Cached cultural fit questions for {cache_key}")
        except Exception as e:
            logger.error(f"Error retrieving cultural fit questions: {e}", exc_info=True)
            questions = {}
    
    return questions

def get_random_cultural_fit_questions(domain: str = 'general', business_unit: Optional[str] = None, num_questions: int = 10) -> Dict[str, List[Dict]]:
    """
    Selecciona preguntas aleatorias para la evaluación de ajuste cultural, equilibrando las dimensiones.
    
    Args:
        domain (str): Dominio de las preguntas (default: 'general').
        business_unit (Optional[str]): Unidad de negocio para preguntas específicas.
        num_questions (int): Número de preguntas a seleccionar (default: 10).
    
    Returns:
        Dict[str, List[Dict]]: Diccionario con preguntas por dimensión (values, motivators, interests, work_style).
    """
    selected_questions = {
        'values': [],
        'motivators': [],
        'interests': [],
        'work_style': []
    }
    
    try:
        all_questions = get_cultural_fit_questions('CulturalFit', domain, business_unit)
        
        # Distribuir preguntas equitativamente entre dimensiones
        questions_per_dimension = max(1, num_questions // len(selected_questions))
        
        for dimension in selected_questions:
            dimension_questions = all_questions.get(dimension, [])
            if dimension_questions:
                selected_questions[dimension] = random.sample(
                    dimension_questions,
                    min(questions_per_dimension, len(dimension_questions))
                )
        
        # Ajustar si no se alcanza el número total de preguntas
        total_selected = sum(len(q) for q in selected_questions.values())
        if total_selected < num_questions:
            remaining = num_questions - total_selected
            all_available = [
                q for dim in all_questions.values() for q in dim
                if q not in sum(selected_questions.values(), [])
            ]
            if all_available:
                selected_questions['values'].extend(
                    random.sample(all_available, min(remaining, len(all_available)))
                )
        
        logger.debug(f"Selected {total_selected} cultural fit questions for {business_unit or 'general'}")
    except Exception as e:
        logger.error(f"Error selecting random cultural fit questions: {e}", exc_info=True)
    
    return selected_questions

def analyze_cultural_fit_responses(responses: Dict[str, List[int]], business_unit: Optional[str] = None) -> Dict:
    """
    Analiza las respuestas del candidato y devuelve un perfil de ajuste cultural.
    
    Args:
        responses (Dict[str, List[int]]): Respuestas por dimensión (values, motivators, interests, work_style).
        business_unit (Optional[str]): Unidad de negocio para interpretación específica.
    
    Returns:
        Dict: Perfil con puntajes, fortalezas, áreas de mejora, recomendaciones y compatibilidad.
    """
    analysis = {
        'scores': {
            'values': 0.0,
            'motivators': 0.0,
            'interests': 0.0,
            'work_style': 0.0
        },
        'strengths': [],
        'improvement_areas': [],
        'recommendations': [],
        'compatibility': {}
    }
    
    try:
        # Calcular puntajes promedio por dimensión
        for dimension, response_list in responses.items():
            if response_list:
                analysis['scores'][dimension] = sum(response_list) / len(response_list)
        
        # Identificar fortalezas y áreas de mejora
        for dimension, score in analysis['scores'].items():
            if score >= 4:
                analysis['strengths'].append(f"Fuerte alineación en {dimension}")
            elif score < 3:
                analysis['improvement_areas'].append(f"Potencial mejora en {dimension}")
        
        # Añadir interpretación específica por unidad de negocio
        if business_unit:
            analysis.update(_add_business_unit_interpretation(analysis['scores'], business_unit))
        
        # Generar recomendaciones generales
        analysis['recommendations'].extend(_generate_general_recommendations(analysis['scores']))
        
        # Calcular compatibilidad con la unidad de negocio
        analysis['compatibility'] = _calculate_compatibility(analysis['scores'], business_unit)
        
        logger.info(f"Cultural fit analysis completed for business unit: {business_unit or 'general'}")
    except Exception as e:
        logger.error(f"Error analyzing cultural fit responses: {e}", exc_info=True)
    
    return analysis

def _add_business_unit_interpretation(scores: Dict[str, float], business_unit: Optional[str]) -> Dict:
    """
    Añade interpretación específica por unidad de negocio a los puntajes.
    
    Args:
        scores (Dict[str, float]): Puntajes por dimensión.
        business_unit (Optional[str]): Unidad de negocio.
    
    Returns:
        Dict: Actualizaciones al análisis (recomendaciones, compatibilidad).
    """
    updates = {'recommendations': [], 'compatibility': {}}
    
    if business_unit == 'consumer':
        if scores['motivators'] >= 4:
            updates['recommendations'].append('Entrenamiento en técnicas de persuasión para maximizar ventas.')
        if scores['work_style'] < 3:
            updates['recommendations'].append('Desarrollo de habilidades para entornos dinámicos de retail.')
        updates['compatibility']['consumer'] = scores['motivators'] * 0.4 + scores['work_style'] * 0.3 + scores['values'] * 0.2 + scores['interests'] * 0.1
    elif business_unit == 'pharma':
        if scores['values'] >= 4:
            updates['recommendations'].append('Capacitación en normativas farmacéuticas para reforzar ética.')
        if scores['interests'] < 3:
            updates['recommendations'].append('Fomentar interés en avances científicos mediante formación continua.')
        updates['compatibility']['pharma'] = scores['values'] * 0.4 + scores['interests'] * 0.3 + scores['motivators'] * 0.2 + scores['work_style'] * 0.1
    elif business_unit == 'service':
        if scores['work_style'] >= 4:
            updates['recommendations'].append('Aprovechar habilidades multitarea en roles de atención al cliente.')
        if scores['motivators'] < 3:
            updates['recommendations'].append('Motivar mediante programas de reconocimiento al cliente.')
        updates['compatibility']['service'] = scores['work_style'] * 0.4 + scores['motivators'] * 0.3 + scores['values'] * 0.2 + scores['interests'] * 0.1
    
    return updates

def _generate_general_recommendations(scores: Dict[str, float]) -> List[str]:
    """
    Genera recomendaciones generales basadas en los puntajes.
    
    Args:
        scores (Dict[str, float]): Puntajes por dimensión.
    
    Returns:
        List[str]: Lista de recomendaciones.
    """
    recommendations = []
    
    if scores['values'] >= 4:
        recommendations.append('Fomentar la alineación con los valores organizacionales mediante talleres.')
    if scores['motivators'] < 3:
        recommendations.append('Identificar motivadores personales a través de sesiones de coaching.')
    if scores['interests'] >= 4:
        recommendations.append('Asignar proyectos que aprovechen los intereses del candidato.')
    if scores['work_style'] < 3:
        recommendations.append('Ofrecer capacitación en gestión del tiempo y adaptabilidad.')
    
    return recommendations

def _calculate_compatibility(scores: Dict[str, float], business_unit: Optional[str]) -> Dict:
    """
    Calcula la compatibilidad cultural con la unidad de negocio.
    
    Args:
        scores (Dict[str, float]): Puntajes por dimensión.
        business_unit (Optional[str]): Unidad de negocio.
    
    Returns:
        Dict: Compatibilidad por unidad de negocio (puntaje entre 0 y 100).
    """
    compatibility = {}
    
    # Pesos por dimensión para cada unidad de negocio
    weights = {
        'consumer': {'values': 0.15, 'motivators': 0.35, 'interests': 0.1, 'work_style': 0.25, 'social_impact': 0.05, 'generational_values': 0.1},
        'pharma': {'values': 0.35, 'motivators': 0.15, 'interests': 0.25, 'work_style': 0.1, 'social_impact': 0.1, 'generational_values': 0.05},
        'service': {'values': 0.15, 'motivators': 0.25, 'interests': 0.1, 'work_style': 0.35, 'social_impact': 0.1, 'generational_values': 0.05},
        'general': {'values': 0.2, 'motivators': 0.2, 'interests': 0.15, 'work_style': 0.15, 'social_impact': 0.15, 'generational_values': 0.15}
    }
    
    unit = business_unit if business_unit in weights else 'general'
    try:
        compatibility_score = sum(
            scores[dimension] * weight
            for dimension, weight in weights[unit].items()
        ) * 20  # Escalar a 0-100
        compatibility[unit] = min(max(compatibility_score, 0), 100)
    except Exception as e:
        logger.error(f"Error calculating compatibility: {e}", exc_info=True)
        compatibility[unit] = 0.0
    
    return compatibility

async def save_cultural_profile(person_id: int, profile_data: Dict[str, Any]) -> bool:
    """
    Guarda el perfil cultural en la base de datos asociado a la persona.
    
    Args:
        person_id (int): ID de la persona.
        profile_data (Dict[str, Any]): Datos del perfil cultural.
    
    Returns:
        bool: True si se guardó correctamente, False en caso contrario.
    """
    if Person is None or PersonCulturalProfile is None:
        logger.error("No se pueden guardar perfiles culturales porque los modelos no están disponibles.")
        return False
        
    try:
        # Intentamos obtener la persona
        person = await sync_to_async(Person.objects.get)(id=person_id)
        
        # Extrae los puntajes de cada dimensión
        scores = profile_data.get('scores', {})
        
        # Creamos o actualizamos el perfil cultural
        cultural_profile, created = await sync_to_async(PersonCulturalProfile.objects.update_or_create)(
            person=person,
            defaults={
                'values_score': scores.get('values', 0),
                'motivators_score': scores.get('motivators', 0),
                'interests_score': scores.get('interests', 0),
                'work_style_score': scores.get('work_style', 0),
                'social_impact_score': scores.get('social_impact', 0),
                'generational_values_score': scores.get('generational_values', 0),
                'compatibility_data': profile_data.get('compatibility', {}),
                'strengths': profile_data.get('strengths', []),
                'areas_for_improvement': profile_data.get('areas_for_improvement', []),
                'recommendations': profile_data.get('recommendations', []),
                'full_profile_data': profile_data,
                'updated_at': timezone.now()
            }
        )
        
        logger.info(f"Cultural profile {'created' if created else 'updated'} for person {person_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving cultural profile for person {person_id}: {e}", exc_info=True)
        return False