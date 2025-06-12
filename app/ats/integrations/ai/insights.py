from typing import List, Dict
import openai
from app.models import Vacante
import logging

logger = logging.getLogger(__name__)

def get_profile_skills(profile_info: Dict) -> List[str]:
    """
    Extrae las habilidades más relevantes del perfil.
    
    Args:
        profile_info: Información del perfil de LinkedIn
        
    Returns:
        Lista de habilidades más relevantes
    """
    try:
        # Obtener ofertas activas para comparar habilidades
        active_jobs = Vacante.objects.filter(is_active=True)
        required_skills = set()
        for job in active_jobs:
            required_skills.update(job.required_skills.split(','))
            
        # Analizar el perfil con GPT
        prompt = f"""
        Analiza el siguiente perfil de LinkedIn y extrae las 3 habilidades más relevantes
        que coincidan con las habilidades requeridas en las ofertas activas.
        
        Perfil:
        - Nombre: {profile_info['name']}
        - Título: {profile_info['headline']}
        - Ubicación: {profile_info['location']}
        
        Habilidades requeridas en ofertas activas: {', '.join(required_skills)}
        
        Devuelve solo las 3 habilidades más relevantes, separadas por comas.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en análisis de perfiles profesionales."},
                {"role": "user", "content": prompt}
            ]
        )
        
        skills = response.choices[0].message.content.strip().split(',')
        return [skill.strip() for skill in skills[:3]]
        
    except Exception as e:
        logger.error(f"Error al obtener habilidades del perfil: {str(e)}")
        return []

def analyze_profile(profile_info: Dict) -> str:
    """
    Genera un insight personalizado sobre el perfil.
    
    Args:
        profile_info: Información del perfil de LinkedIn
        
    Returns:
        Insight personalizado
    """
    try:
        # Obtener ofertas activas
        active_jobs = Vacante.objects.filter(is_active=True)
        job_titles = [job.title for job in active_jobs]
        
        prompt = f"""
        Analiza el siguiente perfil de LinkedIn y genera un insight personalizado
        que destaque por qué sería un buen candidato para las ofertas activas.
        
        Perfil:
        - Nombre: {profile_info['name']}
        - Título: {profile_info['headline']}
        - Ubicación: {profile_info['location']}
        
        Ofertas activas: {', '.join(job_titles)}
        
        Genera un insight conciso (máximo 2 oraciones) que:
        1. Destaque una fortaleza específica del candidato
        2. Mencione cómo podría encajar en las ofertas activas
        3. Sea persuasivo pero profesional
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en reclutamiento y análisis de perfiles."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error al analizar perfil: {str(e)}")
        return ""

def generate_personalized_message(profile_info: Dict, template: str) -> str:
    """
    Genera un mensaje personalizado basado en el perfil y el template.
    
    Args:
        profile_info: Información del perfil de LinkedIn
        template: Template base del mensaje
        
    Returns:
        Mensaje personalizado
    """
    try:
        skills = get_profile_skills(profile_info)
        insight = analyze_profile(profile_info)
        
        # Obtener ofertas relevantes
        active_jobs = Vacante.objects.filter(is_active=True)
        relevant_jobs = []
        for job in active_jobs:
            job_skills = set(job.required_skills.split(','))
            if any(skill in job_skills for skill in skills):
                relevant_jobs.append(job)
                
        # Generar mensaje con GPT
        prompt = f"""
        Genera un mensaje personalizado para LinkedIn basado en el siguiente template
        y la información del perfil.
        
        Template: {template}
        
        Información del perfil:
        - Nombre: {profile_info['name']}
        - Título: {profile_info['headline']}
        - Ubicación: {profile_info['location']}
        - Habilidades relevantes: {', '.join(skills)}
        - Insight: {insight}
        
        Ofertas relevantes:
        {chr(10).join(f'- {job.title} en {job.company}' for job in relevant_jobs[:2])}
        
        El mensaje debe:
        1. Ser conciso (máximo 3 párrafos)
        2. Incluir un insight personalizado
        3. Mencionar ofertas específicas relevantes
        4. Incluir un llamado a la acción claro
        5. Mantener un tono profesional pero cercano
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en reclutamiento y comunicación profesional."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error al generar mensaje personalizado: {str(e)}")
        return template 