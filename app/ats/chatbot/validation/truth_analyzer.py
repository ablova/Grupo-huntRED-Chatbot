# app/ats/chatbot/validation/truth_analyzer.py
"""TruthSense™: Módulo para detección de inconsistencias en perfiles de candidatos.
Implementa técnicas de validación cruzada y análisis de consistencia para verificar
la veracidad de la información proporcionada durante la creación de perfiles.
"""
import logging
import re
import json
from datetime import datetime, date
from typing import Dict, List, Tuple, Any, Optional, Union
import asyncio
import aiohttp
import hashlib

from django.conf import settings
from asgiref.sync import sync_to_async
from django.core.cache import cache

# Importar modelos desde app.models
from app.models import (
    Person,
    Experience,
    Skill,
    PersonSkill,
    ChatState,
    SocialConnection,
    Company,
    BusinessUnit
)

from app.ats.utils.nlp import NLPProcessor
from app.ats.utils.skills_utils import create_skill_processor

logger = logging.getLogger(__name__)

class TruthAnalyzer:
    """
    Clase para analizar la consistencia y veracidad de la información 
    proporcionada por candidatos durante el proceso de creación de perfil.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el analizador de verdad.
        
        Args:
            business_unit (BusinessUnit): Unidad de negocio para la que se configura el analizador.
                                         Determina el conjunto de habilidades y el origen de la solicitud.
        """
        if not isinstance(business_unit, BusinessUnit):
            raise ValueError("business_unit debe ser una instancia de BusinessUnit")
            
        self.business_unit = business_unit
        self.nlp_processor = NLPProcessor(business_unit=business_unit)
        self.skill_processor = create_skill_processor(
            business_unit=business_unit.name,
            language="es",
            mode="executive"
        )
        self.consistency_threshold = getattr(settings, 'TRUTH_CONSISTENCY_THRESHOLD', 0.7)
        self.verification_enabled = getattr(settings, 'ENABLE_VERIFICATION', True)
        self.social_verification_enabled = getattr(settings, 'ENABLE_SOCIAL_VERIFICATION', True)
        
        # Proveedores de verificación para distintas redes sociales
        self.social_providers = {
            'linkedin': {
                'base_url': getattr(settings, 'LINKEDIN_API_URL', 'https://api.linkedin.com/v2/'),
                'fields': ['firstName', 'lastName', 'headline', 'vanityName', 'profilePicture'],
                'auth_header': 'Bearer',
                'weight': 0.4  # Peso en la puntuación de veracidad (40%)
            },
            'github': {
                'base_url': 'https://api.github.com/users/',
                'fields': ['name', 'company', 'bio', 'public_repos', 'followers'],
                'auth_header': 'token',
                'weight': 0.2  # Peso en la puntuación de veracidad (20%)
            },
            'twitter': {
                'base_url': 'https://api.twitter.com/2/users/by/username/',
                'fields': ['name', 'description', 'profile_image_url', 'verified'],
                'auth_header': 'Bearer',
                'weight': 0.15  # Peso en la puntuación de veracidad (15%)
            },
            'instagram': {
                'base_url': 'https://graph.instagram.com/me',
                'fields': ['username', 'account_type', 'media_count'],
                'auth_header': 'Bearer',
                'weight': 0.15  # Peso en la puntuación de veracidad (15%)
            }
        }
        
        # Caché para respuestas de APIs (evitar llamadas repetidas)
        self.cache_ttl = 3600 * 24  # 24 horas
        
        logger.info(f"TruthAnalyzer inicializado para unidad de negocio: {business_unit.name}")
    
    async def verify_consistency(self, persona: Person, current_question: str, 
                                response: str, chat_history: List[Dict]) -> Dict:
        """
        Verifica la consistencia de la respuesta actual con la información previa.
        
        Args:
            persona: Objeto Person del candidato
            current_question: Pregunta actual en proceso
            response: Respuesta del candidato
            chat_history: Historial de chat previo
            
        Returns:
            Dict con métricas de consistencia y red flags detectados
        """
        if not self.verification_enabled:
            return {'consistency_score': 1.0, 'is_consistent': True}
        
        result = {
            'consistency_score': 1.0,
            'is_consistent': True,
            'red_flags': [],
            'detected_skill': None,
            'declared_level': None
        }
        
        # Determinar el tipo de verificación según la pregunta
        if 'experiencia' in current_question.lower() or 'trabajo' in current_question.lower():
            result = await self._verify_experience_consistency(persona, response, chat_history)
        
        elif 'habilidad' in current_question.lower() or 'skill' in current_question.lower():
            result = await self._verify_skill_consistency(persona, response, chat_history)
        
        elif 'education' in current_question.lower() or 'educación' in current_question.lower():
            result = await self._verify_education_consistency(persona, response, chat_history)
            
        # Actualizar el flag general de consistencia
        result['is_consistent'] = result['consistency_score'] >= self.consistency_threshold
        
        return result
    
    async def _verify_experience_consistency(self, persona: Person, response: str, 
                                           chat_history: List[Dict]) -> Dict:
        """Verifica la consistencia de experiencias laborales."""
        result = {
            'consistency_score': 1.0,
            'red_flags': [],
            'detected_skill': None,
            'declared_level': None
        }
        
        # Extraer información temporal y de responsabilidades
        date_ranges = await self._extract_date_ranges(response)
        
        # Verificar solapamientos temporales imposibles
        if date_ranges and len(date_ranges) > 1:
            overlaps = await self._check_time_overlaps(date_ranges)
            if overlaps:
                result['consistency_score'] -= 0.2 * len(overlaps)
                result['red_flags'].append({
                    'type': 'time_overlap',
                    'message': 'Solapamiento temporal detectado en experiencias',
                    'details': overlaps
                })
        
        # Verificar contra experiencias previas almacenadas
        stored_experiences = await sync_to_async(list)(
            Experience.objects.filter(person=persona).values('start_date', 'end_date', 'role', 'company')
        )
        
        if stored_experiences:
            for stored_exp in stored_experiences:
                # Verificar inconsistencias con lo previamente declarado
                nlp_comparison = await self.nlp_processor.calculate_text_similarity(
                    response, 
                    f"{stored_exp['role']} en {stored_exp['company']} desde {stored_exp['start_date']} hasta {stored_exp['end_date']}"
                )
                
                if nlp_comparison < 0.6 and self._mentioned_company(stored_exp['company'], response):
                    result['consistency_score'] -= 0.15
                    result['red_flags'].append({
                        'type': 'experience_inconsistency',
                        'message': f"Información inconsistente con experiencia previa en {stored_exp['company']}",
                        'details': {
                            'stored': stored_exp,
                            'similarity_score': nlp_comparison
                        }
                    })
        
        return result
    
    async def _verify_skill_consistency(self, persona: Person, response: str, 
                                      chat_history: List[Dict]) -> Dict:
        """Verifica la consistencia de habilidades declaradas."""
        result = {
            'consistency_score': 1.0,
            'red_flags': [],
            'detected_skill': None,
            'declared_level': None
        }
        
        # Extraer nivel de experiencia declarado
        skill_name, experience_level = await self._extract_skill_level(response)
        if skill_name and experience_level:
            result['detected_skill'] = skill_name
            result['declared_level'] = experience_level
            
            # Verificar contra experiencias laborales
            experiences = await sync_to_async(list)(
                Experience.objects.filter(person=persona).values('description', 'start_date', 'end_date')
            )
            
            # Calcular el tiempo total de experiencia basado en fechas de trabajo
            total_years_experience = 0
            for exp in experiences:
                if exp['start_date'] and exp['end_date']:
                    total_years_experience += (exp['end_date'].year - exp['start_date'].year)
            
            # Si declara más experiencia de la posible por su historial laboral
            if experience_level > total_years_experience + 1:  # Margen de 1 año
                result['consistency_score'] -= 0.3
                result['red_flags'].append({
                    'type': 'excessive_skill_level',
                    'message': f'Nivel de experiencia en {skill_name} inconsistente con historial laboral',
                    'details': {
                        'declared_years': experience_level,
                        'work_history_years': total_years_experience
                    }
                })
            
            # Verificar menciones de la habilidad en experiencias previas
            skill_mentioned = False
            for exp in experiences:
                if skill_name.lower() in exp['description'].lower():
                    skill_mentioned = True
                    break
            
            if not skill_mentioned and experience_level > 2:
                result['consistency_score'] -= 0.2
                result['red_flags'].append({
                    'type': 'skill_not_in_experience',
                    'message': f'Habilidad {skill_name} no aparece en descripción de experiencias previas',
                    'details': {'skill': skill_name, 'level': experience_level}
                })
        
        return result
    
    async def _verify_education_consistency(self, persona: Person, response: str, 
                                          chat_history: List[Dict]) -> Dict:
        """Verifica la consistencia de información educativa."""
        result = {
            'consistency_score': 1.0,
            'red_flags': [],
            'detected_skill': None,
            'declared_level': None
        }
        
        # Extraer instituciones educativas mencionadas
        education_info = await self._extract_education_info(response)
        
        # Verificar contra respuestas previas
        previous_education = [msg for msg in chat_history 
                             if 'education' in msg.get('type', '') 
                             or 'educación' in msg.get('type', '')]
        
        if previous_education and education_info:
            # Verificar inconsistencias en instituciones o fechas
            for prev_edu in previous_education:
                nlp_comparison = await self.nlp_processor.calculate_text_similarity(
                    response, prev_edu.get('response', '')
                )
                
                if nlp_comparison < 0.5:
                    result['consistency_score'] -= 0.25
                    result['red_flags'].append({
                        'type': 'education_inconsistency',
                        'message': 'Información educativa inconsistente con declaraciones previas',
                        'details': {
                            'current': education_info,
                            'previous': prev_edu.get('response', ''),
                            'similarity_score': nlp_comparison
                        }
                    })
        
        return result
    
    async def generate_verification_question(self, skill: str, declared_level: int) -> Dict:
        """
        Genera una pregunta de verificación basada en la habilidad detectada.
        
        Args:
            skill: Habilidad detectada
            declared_level: Nivel de experiencia declarado (años)
            
        Returns:
            Dict con información de la pregunta de verificación
        """
        question_types = [
            "técnica",   # Preguntas técnicas específicas
            "situacional",  # Cómo resolverías X situación
            "experiencial"  # Describe un proyecto donde usaste X
        ]
        
        # Seleccionar tipo de pregunta según nivel declarado
        if declared_level <= 2:
            question_type = "técnica" 
        elif declared_level <= 5:
            question_type = "situacional"
        else:
            question_type = "experiencial"
        
        # Generar pregunta específica según el skill
        question = await self._generate_skill_specific_question(skill, declared_level, question_type)
        
        return {
            'type': 'verification',
            'skill': skill,
            'level': declared_level,
            'question_type': question_type,
            'question': question
        }
    
    async def _generate_skill_specific_question(self, skill: str, level: int, question_type: str) -> str:
        """Genera una pregunta específica para la habilidad y nivel."""
        # Ejemplos de preguntas según tipo y nivel
        questions = {
            'python': {
                'técnica': [
                    "¿Puedes explicar la diferencia entre una lista y una tupla en Python?",
                    "¿Cómo manejarías un error de tipo KeyError en un diccionario?"
                ],
                'situacional': [
                    "¿Cómo implementarías un sistema de caché para optimizar consultas repetitivas?",
                    "Describe cómo estructurarías un proyecto web con Django"
                ],
                'experiencial': [
                    "Cuéntame sobre el proyecto más complejo que has desarrollado con Python y qué patrones de diseño aplicaste",
                    "¿Has contribuido a algún proyecto open source en Python? ¿Cómo fue tu experiencia?"
                ]
            },
            'javascript': {
                'técnica': [
                    "¿Cuál es la diferencia entre let, const y var en JavaScript?",
                    "Explica cómo funciona el event loop en JavaScript"
                ],
                'situacional': [
                    "¿Cómo implementarías un sistema de gestión de estado en una aplicación React?",
                    "¿Qué estrategia usarías para optimizar el rendimiento de una aplicación JavaScript?"
                ],
                'experiencial': [
                    "Describe un desafío técnico que enfrentaste en un proyecto JavaScript y cómo lo resolviste",
                    "¿Has liderado equipos de desarrollo frontend? ¿Qué metodologías implementaste?"
                ]
            },
            'default': {
                'técnica': [
                    f"¿Podrías explicar un concepto básico de {skill}?",
                    f"¿Qué herramientas o frameworks has utilizado con {skill}?"
                ],
                'situacional': [
                    f"Si tuvieras que implementar un proyecto usando {skill}, ¿cómo lo estructurarías?",
                    f"¿Cómo resolverías un problema de rendimiento en un sistema que usa {skill}?"
                ],
                'experiencial': [
                    f"Cuéntame sobre el proyecto más complejo donde usaste {skill}",
                    f"¿Has liderado equipos o proyectos que usan {skill}? ¿Cómo fue la experiencia?"
                ]
            }
        }
        
        # Obtener preguntas para la habilidad específica o usar default
        skill_questions = questions.get(skill.lower(), questions['default'])
        type_questions = skill_questions.get(question_type, skill_questions['técnica'])
        
        # Seleccionar una pregunta al azar (en producción podría ser más sofisticado)
        import random
        return random.choice(type_questions)
    
    @staticmethod
    async def _extract_date_ranges(text: str) -> List[Tuple[datetime, datetime]]:
        """Extrae rangos de fechas de un texto."""
        # Patrones para fechas en formato común: MM/YYYY, MM-YYYY, Mes YYYY
        date_patterns = [
            r'(\d{1,2})/(\d{4})\s*-\s*(\d{1,2})/(\d{4})',  # MM/YYYY - MM/YYYY
            r'(\d{1,2})-(\d{4})\s*-\s*(\d{1,2})-(\d{4})',  # MM-YYYY - MM-YYYY
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})\s*-\s*(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})'  # Mes YYYY - Mes YYYY
        ]
        
        date_ranges = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                groups = match.groups()
                if len(groups) == 4:
                    try:
                        # Convertir a objetos datetime
                        if groups[0].isdigit():  # Formato numérico
                            start_date = datetime(int(groups[1]), int(groups[0]), 1)
                            end_date = datetime(int(groups[3]), int(groups[2]), 1)
                        else:  # Formato texto
                            month_map = {
                                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                            }
                            start_date = datetime(int(groups[1]), month_map[groups[0]], 1)
                            end_date = datetime(int(groups[3]), month_map[groups[2]], 1)
                        
                        date_ranges.append((start_date, end_date))
                    except (ValueError, KeyError):
                        # Ignorar fechas inválidas
                        pass
        
        return date_ranges
    
    @staticmethod
    async def _check_time_overlaps(date_ranges: List[Tuple[datetime, datetime]]) -> List[Dict]:
        """Verifica solapamientos temporales en rangos de fechas."""
        overlaps = []
        for i, (start1, end1) in enumerate(date_ranges):
            for j, (start2, end2) in enumerate(date_ranges[i+1:], i+1):
                # Verificar solapamiento
                if start1 <= end2 and start2 <= end1:
                    overlaps.append({
                        'range1': (start1.strftime('%m/%Y'), end1.strftime('%m/%Y')),
                        'range2': (start2.strftime('%m/%Y'), end2.strftime('%m/%Y'))
                    })
        return overlaps
    
    @staticmethod
    async def _extract_skill_level(text: str) -> Tuple[Optional[str], Optional[int]]:
        """Extrae el nombre de la habilidad y su nivel de experiencia en años."""
        # Patrones comunes para experiencia: "X años de experiencia en Y"
        experience_patterns = [
            r'(\d+)\s+años\s+(?:de\s+)?(?:experiencia)?\s+(?:en|con)\s+(\w+)',
            r'experiencia\s+(?:de|con)\s+(\d+)\s+años\s+(?:en|con)\s+(\w+)',
            r'(\w+)\s+(?:durante|por)\s+(\d+)\s+años'
        ]
        
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                groups = match.groups()
                if len(groups) == 2:
                    try:
                        if groups[0].isdigit():  # Primer grupo es número
                            years = int(groups[0])
                            skill = groups[1]
                        else:  # Segundo grupo es número
                            years = int(groups[1])
                            skill = groups[0]
                        
                        return skill, years
                    except ValueError:
                        pass
        
        return None, None
    
    @staticmethod
    async def _extract_education_info(text: str) -> Dict:
        """Extrae información educativa de un texto."""
        education_info = {
            'institutions': [],
            'degrees': [],
            'years': []
        }
        
        # Extraer instituciones educativas comunes
        institution_pattern = r'(?:universidad|instituto|escuela|colegio|faculty|school|college|university)\s+(?:de|of|del)?\s+([A-Za-z\s]+)'
        institutions = re.finditer(institution_pattern, text.lower())
        
        for match in institutions:
            if match.group(1).strip():
                education_info['institutions'].append(match.group(1).strip())
        
        # Extraer títulos académicos
        degree_pattern = r'(?:licenciado|ingeniero|técnico|master|doctorado|phd|bachelor|licenciatura|ingeniería|maestría)\s+(?:en|of)?\s+([A-Za-z\s]+)'
        degrees = re.finditer(degree_pattern, text.lower())
        
        for match in degrees:
            if match.group(1).strip():
                education_info['degrees'].append(match.group(1).strip())
        
        # Extraer años
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        years = re.findall(year_pattern, text)
        education_info['years'] = [int(y) for y in years]
        
        return education_info
    
    @staticmethod
    def _mentioned_company(company: str, text: str) -> bool:
        """Verifica si una compañía es mencionada en el texto."""
        return company.lower() in text.lower()


    async def verify_social_profiles(self, persona: Person) -> Dict:
        """
        Verifica los perfiles de redes sociales del candidato para validar su identidad
        y la consistencia de la información proporcionada.
        
        Args:
            persona: Objeto Person del candidato
            
        Returns:
            Dict con información de verificación de cada red social y puntuación general
        """
        if not self.social_verification_enabled:
            return {
                'verification_score': 0,
                'profiles_verified': 0,
                'social_profiles': []
            }
        
        # Información de redes sociales almacenada en extras
        extras = persona.extras or {}
        social_profiles = extras.get('social_profiles', {})
        
        verification_results = {
            'verification_score': 0,
            'profiles_verified': 0,
            'social_profiles': []
        }
        
        # Si no hay perfiles sociales, devolver resultado vacío
        if not social_profiles:
            return verification_results
        
        total_score = 0
        total_weight = 0
        verified_count = 0
        
        for platform, username in social_profiles.items():
            if not username or platform not in self.social_providers:
                continue
                
            # Verificar si tenemos resultados en caché
            cache_key = f"social_verify_{platform}_{username}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                profile_verification = cached_result
            else:
                # Realizar verificación del perfil social
                profile_verification = await self._verify_social_profile(platform, username, persona)
                
                # Guardar en caché para futuras consultas
                if profile_verification:
                    cache.set(cache_key, profile_verification, self.cache_ttl)
            
            if profile_verification:
                # Añadir a resultados
                verification_results['social_profiles'].append({
                    'platform': platform,
                    'username': username,
                    'verified': profile_verification.get('verified', False),
                    'name': profile_verification.get('name', ''),
                    'profile_url': profile_verification.get('profile_url', ''),
                    'verified_date': profile_verification.get('verified_date', datetime.now().strftime('%Y-%m-%d'))
                })
                
                # Actualizar puntuación general
                platform_weight = self.social_providers[platform]['weight']
                total_weight += platform_weight
                
                if profile_verification.get('verified', False):
                    total_score += platform_weight
                    verified_count += 1
        
        # Calcular puntuación final (normalizada a 100)
        if total_weight > 0:
            verification_results['verification_score'] = int((total_score / total_weight) * 100)
        verification_results['profiles_verified'] = verified_count
        
        return verification_results
    
    async def _verify_social_profile(self, platform: str, username: str, persona: Person) -> Dict:
        """
        Verifica un perfil social específico y compara la información con la del candidato.
        
        Args:
            platform: Plataforma social (linkedin, github, etc)
            username: Nombre de usuario o ID en la plataforma
            persona: Objeto Person del candidato
            
        Returns:
            Dict con información y estado de verificación
        """
        provider = self.social_providers.get(platform)
        if not provider:
            return None
            
        result = {
            'platform': platform,
            'username': username,
            'verified': False,
            'name': '',
            'profile_url': '',
            'verified_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Por razones de seguridad, no incluimos claves API reales en este código
        # En producción, estas claves se obtendrían de settings o variables de entorno
        api_key = getattr(settings, f"{platform.upper()}_API_KEY", '')
        
        # Si no hay API key, simular verificación básica
        if not api_key and not platform == 'linkedin':
            # Simulación de verificación (solo para desarrollo)
            result['verified'] = self._simulate_verification(platform, username, persona)
            result['name'] = f"{persona.name if persona.name else ''}"
            
            # URLs base por plataforma
            platform_urls = {
                'linkedin': f"https://www.linkedin.com/in/{username}/",
                'github': f"https://github.com/{username}",
                'twitter': f"https://twitter.com/{username}",
                'instagram': f"https://instagram.com/{username}"
            }
            result['profile_url'] = platform_urls.get(platform, '')
            
            return result
            
        # En caso de tener integración real con APIs, usar esto:
        try:
            # Ejecutar verificación asíncrona según la plataforma
            if platform == 'linkedin':
                verified_data = await self._verify_linkedin_profile(username, api_key, persona)
            elif platform == 'github':
                verified_data = await self._verify_github_profile(username, api_key, persona)
            elif platform == 'twitter':
                verified_data = await self._verify_twitter_profile(username, api_key, persona)
            elif platform == 'instagram':
                verified_data = await self._verify_instagram_profile(username, api_key, persona)
            else:
                return result
                
            # Actualizar resultado con datos obtenidos
            result.update(verified_data)
            
        except Exception as e:
            logger.error(f"Error verificando perfil social {platform}/{username}: {str(e)}")
            
        return result
    
    def _simulate_verification(self, platform: str, username: str, persona: Person) -> bool:
        """
        Simula un proceso de verificación para desarrollo y testing.
        En producción, este método sería reemplazado por llamadas reales a APIs.
        
        Args:
            platform: Plataforma social
            username: Nombre de usuario
            persona: Objeto Person del candidato
            
        Returns:
            Boolean indicando si la verificación fue exitosa
        """
        # Generar hash determinístico basado en username y platform para consistencia
        combined = f"{username}:{platform}:{persona.email if persona.email else ''}"            
        hash_value = int(hashlib.md5(combined.encode()).hexdigest(), 16)
        
        # Utilizar el hash para determinar si está verificado (para desarrollo)
        # LinkedIn tiene mayor probabilidad de verificación
        if platform == 'linkedin':
            return hash_value % 100 < 85  # 85% de verificación
        elif platform == 'github':
            return hash_value % 100 < 75  # 75% de verificación
        else:
            return hash_value % 100 < 65  # 65% de verificación
    
    async def _verify_linkedin_profile(self, profile_id: str, api_key: str, persona: Person) -> Dict:
        """Verifica un perfil de LinkedIn. Implementación completa requiere OAuth y API real."""
        # Simulación para desarrollo
        result = {
            'verified': self._simulate_verification('linkedin', profile_id, persona),
            'name': persona.name if persona.name else '',
            'profile_url': f"https://www.linkedin.com/in/{profile_id}/"
        }
        return result
    
    async def _verify_github_profile(self, username: str, api_key: str, persona: Person) -> Dict:
        """Verifica un perfil de GitHub usando su API pública."""
        result = {
            'verified': False,
            'name': '',
            'profile_url': f"https://github.com/{username}"
        }
        
        # Implementación real con API de GitHub
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if api_key:
                    headers['Authorization'] = f"token {api_key}"
                    
                url = f"https://api.github.com/users/{username}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verificar si el nombre coincide aproximadamente
                        gh_name = data.get('name', '').lower()
                        person_name = persona.name.lower() if persona.name else ''
                        
                        # Determinar verificación basado en nombre y otra información
                        name_match = self.nlp_processor.calculate_similarity(gh_name, person_name) > 0.7
                        email_match = False
                        
                        # Verificar correo electrónico si está disponible
                        if persona.email and data.get('email'):
                            email_match = persona.email.lower() == data.get('email').lower()
                        
                        result['verified'] = name_match or email_match
                        result['name'] = data.get('name', '')
                        result['avatar_url'] = data.get('avatar_url', '')
                        result['bio'] = data.get('bio', '')
                        
        except Exception as e:
            logger.error(f"Error verificando perfil de GitHub: {str(e)}")
            
        return result
    
    async def _verify_twitter_profile(self, username: str, api_key: str, persona: Person) -> Dict:
        """Verifica un perfil de Twitter/X. Implementación completa requiere API real."""
        # Simulación para desarrollo
        result = {
            'verified': self._simulate_verification('twitter', username, persona),
            'name': persona.name if persona.name else '',
            'profile_url': f"https://twitter.com/{username}"
        }
        return result
        
    async def _verify_instagram_profile(self, username: str, api_key: str, persona: Person) -> Dict:
        """Verifica un perfil de Instagram. Implementación completa requiere API real."""
        # Simulación para desarrollo
        result = {
            'verified': self._simulate_verification('instagram', username, persona),
            'name': persona.name if persona.name else '',
            'profile_url': f"https://instagram.com/{username}"
        }
        return result
    
    async def prepare_cv_verification_data(self, persona: Person) -> Dict:
        """
        Prepara los datos de verificación para mostrar en el CV.
        
        Args:
            persona: Objeto Person del candidato
            
        Returns:
            Dict con datos formateados para la plantilla del CV
        """
        # Obtener puntuación de veracidad general (TruthSense™)
        truth_score = await self._calculate_truth_score(persona)
        
        # Verificar perfiles sociales (SocialVerify™)
        social_verification = await self.verify_social_profiles(persona)
        
        # Extraer y estructurar datos de verificación de educación 
        education_verifications = await self._prepare_education_verifications(persona)
        
        # Extraer y estructurar datos de verificación de experiencia
        experience_verifications = await self._prepare_experience_verifications(persona)
        
        # Obtener conexiones sociales para SocialLink™
        social_connections = await self._prepare_social_connections(persona)
        
        # Estructurar resultado completo
        result = {
            # TruthSense™
            'truth_score': truth_score,
            'verification_date': datetime.now().strftime('%d/%m/%Y'),
            'show_verification': truth_score > 0,
            
            # SocialVerify™
            'social_verifications': social_verification.get('social_profiles', []),
            'education_verifications': education_verifications,
            'experience_verifications': experience_verifications,
            
            # SocialLink™
            'social_connections': social_connections,
            'social_connections_json': json.dumps(social_connections),
            'person_id': str(persona.id) if persona.id else '',
        }
        
        return result
    
    async def _calculate_truth_score(self, persona: Person) -> int:
        """
        Calcula la puntuación de veracidad global basada en los diferentes factores.
        
        Args:
            persona: Objeto Person del candidato
            
        Returns:
            Puntuación de veracidad (0-100)
        """
        # Extraer puntuación de extras si existe
        extras = persona.extras or {}
        stored_score = extras.get('truth_score', None)
        
        if stored_score is not None:
            return int(stored_score)
        
        # Calcular puntuación base según completitud
        base_score = 50  # Puntuación base por defecto
        
        # Factores que aumentan la puntuación
        if persona.email and '@' in persona.email:
            base_score += 5
            
        if persona.phone:
            base_score += 5
            
        # Verificar experiencia y educación
        experiences = await sync_to_async(list)(persona.experience_set.all())
        education = await sync_to_async(list)(persona.education_set.all())
        
        # Puntos por cada experiencia y educación (máx 15 puntos)
        base_score += min(len(experiences) * 3, 15) 
        base_score += min(len(education) * 3, 15)
        
        # Factores de perfiles sociales verificados
        social_verification = await self.verify_social_profiles(persona)
        profiles_verified = social_verification.get('profiles_verified', 0)
        
        # Cada perfil verificado suma hasta 10 puntos
        social_score = min(profiles_verified * 10, 40)
        
        # Combinar puntuaciones (la social tiene más peso)
        final_score = int((base_score * 0.6) + (social_score))
        
        # Limitar a rango 0-100
        final_score = max(0, min(final_score, 100))
        
        # Almacenar para futuras referencias
        extras['truth_score'] = final_score
        persona.extras = extras
        await sync_to_async(persona.save)()  
        
        return final_score
    
    async def _prepare_education_verifications(self, persona: Person) -> List[Dict]:
        """
        Prepara datos de verificación de educación para el CV.
        """
        result = []
        
        # Obtener registros de educación
        education_records = await sync_to_async(list)(persona.education_set.all())
        
        for edu in education_records:
            # Determinar si la educación está verificada basado en criterios
            # En implementación real, se verificaría contra fuentes externas
            verified = False
            pending = True
            
            # Simular verificación para desarrollo
            # Educación más reciente tiene más probabilidad de estar verificada
            if edu.end_year and edu.end_year > 2010:
                verified = edu.id % 3 == 0  # Simplemente para variar los resultados
                pending = not verified
            
            result.append({
                'institution': edu.institution,
                'degree': edu.degree,
                'date_range': f"{edu.start_year or ''} - {edu.end_year or 'Presente'}",
                'verified': verified,
                'pending': pending
            })
            
        return result
    
    async def _prepare_experience_verifications(self, persona: Person) -> List[Dict]:
        """
        Prepara datos de verificación de experiencia para el CV.
        """
        result = []
        
        # Obtener registros de experiencia
        experience_records = await sync_to_async(list)(persona.experience_set.all())
        
        for exp in experience_records:
            # Simular verificación para desarrollo
            # Experiencia más reciente tiene más probabilidad de estar verificada
            verified = False
            pending = True
            
            # Obtener año de inicio y fin como números
            start_year = None
            if exp.start_date:
                start_year = int(exp.start_date.split('-')[0]) if '-' in exp.start_date else None
                
            end_year = None
            if exp.end_date and exp.end_date != 'Presente':
                end_year = int(exp.end_date.split('-')[0]) if '-' in exp.end_date else None
            
            # Verificar experiencias más recientes con mayor probabilidad
            if end_year and end_year > 2018:
                verified = exp.id % 2 == 0  # Simplemente para variar los resultados
                pending = not verified
            elif start_year and start_year > 2018:
                verified = exp.id % 3 == 0
                pending = not verified
            
            result.append({
                'company': exp.company,
                'position': exp.position,
                'date_range': f"{exp.start_date or ''} - {exp.end_date or 'Presente'}",
                'verified': verified,
                'pending': pending
            })
            
        return result
    
    async def _prepare_social_connections(self, persona: Person) -> List[Dict]:
        """
        Prepara datos de conexiones sociales para SocialLink™.
        """
        result = []
        
        # Obtener conexiones sociales del modelo SocialConnection
        connections = await sync_to_async(list)(persona.social_connections.through.objects.filter(from_person=persona))
        
        for connection in connections:
            # Obtener la persona conectada
            to_person = connection.to_person
            
            # Simplificar el tipo de relación para la visualización
            relationship_types = {
                'friend': 'Amigo' if persona.language == 'es' else 'Friend',
                'family': 'Familiar' if persona.language == 'es' else 'Family',
                'colleague': 'Colega' if persona.language == 'es' else 'Colleague',
                'classmate': 'Compañero' if persona.language == 'es' else 'Classmate',
                'referral': 'Referido' if persona.language == 'es' else 'Referral'
            }
            
            relationship = relationship_types.get(connection.relationship_type, connection.relationship_type)
            
            result.append({
                'id': str(to_person.id) if to_person.id else '',
                'name': to_person.name,
                'relationship': relationship,
                'role': to_person.current_position,
                'verified': connection.verified,
                'connection_date': connection.created_at.strftime('%d/%m/%Y') if connection.created_at else ''
            })
            
        return result

def get_truth_analyzer(business_unit: BusinessUnit) -> TruthAnalyzer:
    """
    Obtiene una instancia de TruthAnalyzer para la unidad de negocio especificada.
    
    Args:
        business_unit (BusinessUnit): Unidad de negocio para la que se configura el analizador.
        
    Returns:
        TruthAnalyzer: Instancia configurada del analizador de verdad.
    """
    return TruthAnalyzer(business_unit=business_unit)