# Ubicación en servidor: /home/pablollh/app/chatbot/utils.py
from django.utils import timezone
from datetime import timedelta
from app.models import (
    Person, Application, Vacante, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState, WorkflowStage,
    GamificationAchievement, GamificationBadge, GamificationEvent,
    GptApi, ConfiguracionBU
)
import logging
from typing import Dict, List, Optional, Any, Tuple, List, Dict, Tuple
from django.db.models import Q, Count, Avg
from collections import defaultdict
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import json
import re
import requests
import time
import asyncio
import pandas as pd
from datetime import datetime
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer
from typing import Dict, List, Any, Optional
from difflib import get_close_matches
from app.utilidades.catalogs import get_divisiones, map_skill_to_database
from app.chatbot.chatbot import nlp_processor as NLPProcessor
from app.chatbot.nlp import NLPProcessor as NLPProcessorClass

# Variable global para la instancia de NLPProcessor
logger = logging.getLogger(__name__)
_nlp_processor_instance: Optional[NLPProcessorClass] = None

logger = logging.getLogger(__name__)

class ChatbotUtils:
    """
    Clase utilitaria para el chatbot que proporciona métodos para manejar estados,
    recomendaciones y mensajes personalizados.
    
    Métodos:
        get_next_workflow_stage(): Obtiene siguiente etapa del flujo de trabajo
        update_chat_state(): Actualiza el estado del chat
        get_vacancy_recommendations(): Recomienda vacantes
        get_application_status(): Obtiene estado de aplicaciones
        get_gamification_progress(): Obtiene progreso de gamificación
        get_next_interview(): Obtiene próxima entrevista
        get_recent_interactions(): Obtiene interacciones recientes
        get_skill_match_score(): Calcula coincidencia de habilidades
        get_experience_match_score(): Calcula coincidencia de experiencia
        get_salary_match_score(): Calcula coincidencia de salario
        get_location_match_score(): Calcula coincidencia de ubicación
        calculate_match_score(): Calcula puntaje total de coincidencia
        get_recommendation_message(): Genera mensaje de recomendación
        get_gamification_message(): Genera mensaje de gamificación
    """

    @staticmethod
    def get_next_workflow_stage(current_stage: str) -> Optional[WorkflowStage]:
        """
        Obtiene la siguiente etapa del flujo de trabajo.
        
        Args:
            current_stage: Nombre de la etapa actual
            
        Returns:
            WorkflowStage: Siguiente etapa o None si no existe
        """
        try:
            current = WorkflowStage.objects.get(name=current_stage)
            next_stage = WorkflowStage.objects.filter(
                order__gt=current.order
            ).order_by('order').first()
            return next_stage
        except WorkflowStage.DoesNotExist:
            return None

    @staticmethod
    def update_chat_state(user: Person, state: str, message: str) -> ChatState:
        """
        Actualiza el estado del chat.
        
        Args:
            user: Usuario
            state: Nuevo estado
            message: Último mensaje
            
        Returns:
            ChatState: Estado actualizado
        """
        chat_state, _ = ChatState.objects.get_or_create(user=user)
        chat_state.current_state = state
        chat_state.last_message = message
        chat_state.last_interaction = timezone.now()
        chat_state.save()
        return chat_state

    @staticmethod
    def get_vacancy_recommendations(user: Person) -> List[Vacante]:
        """
        Recomienda vacantes basadas en el perfil del usuario.
        
        Args:
            user: Usuario para el cual se recomendarán vacantes
            
        Returns:
            List[Vacante]: Lista de vacantes recomendadas
        """
        # Obtener habilidades priorizadas basándose en intereses
        prioritized_skills, skill_weights = prioritize_interests(
            [skill.name for skill in user.skills.all()],
            [interest.name for interest in user.interests.all()]
        )
        
        # Obtener posiciones recomendadas basándose en habilidades
        positions = get_positions_by_skills(prioritized_skills)
        
        # Filtrar y ordenar vacantes activas
        now = timezone.now()
        vacancies = Vacante.objects.filter(
            status='active',
            created_at__lte=now
        ).select_related('business_unit').prefetch_related('required_skills')
        
        # Calcular puntaje de coincidencia para cada vacante
        scored_vacancies = []
        for vacancy in vacancies:
            score = ChatbotUtils.calculate_match_score(user, vacancy)
            scored_vacancies.append((vacancy, score))
        
        # Ordenar por puntaje y fecha de publicación
        scored_vacancies.sort(key=lambda x: (x[1], x[0].created_at), reverse=True)
        
        # Devolver las 5 mejores coincidencias
        return [v[0] for v in scored_vacancies[:5]]

    @staticmethod
    def get_nlp_processor() -> Optional[NLPProcessorClass]:
        """Obtiene la instancia singleton de NLPProcessor."""
        global _nlp_processor_instance
        if _nlp_processor_instance is None:
            try:
                _nlp_processor_instance = NLPProcessorClass(language="es", mode="candidate")
                logger.info("Instancia de NLPProcessor creada exitosamente")
            except Exception as e:
                logger.error(f"Error creando NLPProcessor: {e}", exc_info=True)
                _nlp_processor_instance = None
        return _nlp_processor_instance

    @staticmethod
    def load_catalog() -> dict:
        """Carga el catálogo de habilidades desde catalogs.json."""
        CATALOG_PATH = os.path.join(settings.BASE_DIR, 'app', 'utilidades', 'catalogs', 'catalogs.json')
        if not os.path.exists(CATALOG_PATH):
            logger.error(f"Archivo de catálogo no encontrado: {CATALOG_PATH}")
            return {}
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error al cargar catálogo desde {CATALOG_PATH}: {e}")
            return {}

    @staticmethod
    def get_all_skills_for_unit(unit_name: str = "huntRED®") -> List[str]:
        """Devuelve todas las habilidades de una unidad de negocio desde catalogs.json."""
        skills = []
        try:
            catalog = ChatbotUtils.load_catalog()
            unit_data = catalog.get(unit_name, {})
            for division, roles in unit_data.items():
                for role, attributes in roles.items():
                    skills.extend(attributes.get("Habilidades Técnicas", []))
                    skills.extend(attributes.get("Habilidades Blandas", []))
                    skills.extend(attributes.get("Herramientas", []))
            return list(set(skills))  # Eliminar duplicados
        except Exception as e:
            logger.error(f"Error obteniendo habilidades de {unit_name}: {e}")
            return []

    @staticmethod
    def clean_text(text: str) -> str:
        """Limpia texto eliminando caracteres especiales y espacios adicionales."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'[^\w\sáéíóúñüÁÉÍÓÚÑÜ]', '', text, flags=re.UNICODE)
        return text

    @staticmethod
    def analyze_text(text: str) -> Dict[str, any]:
        """Analiza el texto usando NLPProcessor."""
        nlp_processor = ChatbotUtils.get_nlp_processor()
        if nlp_processor is None:
            logger.warning("No se pudo obtener NLPProcessor, devolviendo resultado vacío")
            return {"entities": [], "sentiment": {}}
        
        try:
            cleaned_text = ChatbotUtils.clean_text(text)
            result = nlp_processor.analyze(cleaned_text)
            return result
        except Exception as e:
            logger.error(f"Error analizando texto '{text}': {e}", exc_info=True)
            return {"entities": [], "sentiment": {}}

    @staticmethod
    def validate_term_in_catalog(term: str, catalog: List[str]) -> bool:
        """ Valida si un término existe en un catálogo especificado. """
        return term.lower() in [item.lower() for item in catalog]

    @staticmethod
    def get_all_divisions() -> List[str]:
        """ Obtiene todas las divisiones disponibles en los catálogos. """
        return get_divisiones()

    @staticmethod
    def generate_verification_token(key: str) -> str:
        """ Genera un token seguro para verificación. """
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        return serializer.dumps(key, salt='verification-salt')

    @staticmethod
    def confirm_verification_token(token: str, expiration: int = 3600) -> Optional[str]:
        """ Valida un token de verificación con tiempo de expiración. """
        serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
        try:
            key = serializer.loads(token, salt='verification-salt', max_age=expiration)
            return key
        except Exception:
            return None

    @staticmethod
    def validate_request_data(data: Dict, required_fields: List[str]) -> None:
        """ Valida que los datos enviados cumplan con los campos requeridos. """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Faltan los campos requeridos: {', '.join(missing_fields)}")

    @staticmethod
    def format_template_response(template: str, **kwargs) -> str:
        """ Formatea una plantilla de texto con variables dinámicas. """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Error al formatear plantilla: {str(e)}")
            return template

    @staticmethod
    def validate_request_fields(required_fields: List[str], data: Dict) -> bool:
        """ Valida que todos los campos requeridos estén presentes en el payload. """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(f"Faltan campos requeridos: {missing_fields}")
            return False
        return True

    @staticmethod
    def log_with_correlation_id(message: str, correlation_id: str, level: str = "info"):
        """ Registra mensajes con un ID de correlación para rastrear flujos de forma únicos. """
        log_message = f"[CorrelationID: {correlation_id}] {message}"
        if level == "info":
            logger.info(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "error":
            logger.error(log_message)
        else:
            logger.debug(log_message)

    # Constantes para control de spam
    SPAM_DETECTION_WINDOW = 30  # 30 segundos
    MAX_MESSAGE_REPEATS = 3     # Cuántas veces puede repetir el mismo mensaje antes de ser SPAM
    MAX_MESSAGES_PER_MINUTE = 10  # Límite de mensajes por usuario por minuto

    @staticmethod
    def is_spam_message(user_id: str, text: str) -> bool:
        """
        Verifica si un mensaje es considerado SPAM basándose en su frecuencia y repetición.
        
        Args:
            user_id (str): ID del usuario.
            text (str): Texto del mensaje.

        Returns:
            bool: True si el mensaje es considerado SPAM, False en caso contrario.
        """
        if not text:
            return False

        text_cleaned = re.sub(r'\W+', '', text.lower().strip())  # Limpiar caracteres especiales
        cache_key = f"spam_check:{user_id}"
        user_messages = cache.get(cache_key, [])

        # Registrar el nuevo mensaje
        current_time = time.time()
        user_messages.append((text_cleaned, current_time))
        
        # Filtrar mensajes dentro de la ventana de tiempo
        user_messages = [(msg, ts) for msg, ts in user_messages if current_time - ts < ChatbotUtils.SPAM_DETECTION_WINDOW]

        # Contar repeticiones
        message_count = sum(1 for msg, _ in user_messages if msg == text_cleaned)
        if message_count >= ChatbotUtils.MAX_MESSAGE_REPEATS:
            return True  # SPAM detectado por mensajes repetidos

        # Guardar historial actualizado
        cache.set(cache_key, user_messages, timeout=ChatbotUtils.SPAM_DETECTION_WINDOW)
        return False

    @staticmethod
    def update_user_message_history(user_id: str):
        """
        Registra la cantidad de mensajes enviados por un usuario en un minuto.
        
        Args:
            user_id (str): ID del usuario.
        """
        cache_key = f"msg_count:{user_id}"
        timestamps = cache.get(cache_key, [])
        current_time = time.time()

        # Limpiar mensajes fuera del período de 1 minuto
        timestamps = [ts for ts in timestamps if current_time - ts < 60]
        
        # Agregar el nuevo mensaje
        timestamps.append(current_time)
        
        # Guardar en cache
        cache.set(cache_key, timestamps, timeout=60)

    @staticmethod
    def is_user_spamming(user_id: str) -> bool:
        """
        Verifica si un usuario ha enviado demasiados mensajes en un corto periodo.
        
        Args:
            user_id (str): ID del usuario.

        Returns:
            bool: True si el usuario está enviando demasiados mensajes, False en caso contrario.
        """
        cache_key = f"msg_count:{user_id}"
        timestamps = cache.get(cache_key, [])

        return len(timestamps) > ChatbotUtils.MAX_MESSAGES_PER_MINUTE

    # Constantes para asignación de unidades de negocio
    BUSINESS_UNITS_KEYWORDS = {
        'huntRED®': {
            'manager': 2, 'director': 3, 'leadership': 2, 'senior manager': 4, 'operations manager': 3,
            'project manager': 3, 'head of': 4, 'gerente': 2, 'director de': 3, 'jefe de': 4, 'subdirector': 3, 'dirección': 3, 'subdirección': 3
        },
        'huntRED® Executive': {
            'strategic': 3, 'board': 4, 'global': 3, 'vp': 4, 'president': 4, 'cfo': 5, 'ceo': 5, 'coo': 5, 'consejero': 4,
            'executive': 4, 'cto': 5, 'chief': 4, 'executive director': 5, 'senior vp': 5, 'vice president': 4,
            'estrategico': 3, 'global': 3, 'presidente': 4, 'chief': 4
        },
        'huntu': {
            'trainee': 3, 'junior': 3, 'entry-level': 4, 'intern': 3, 'graduate': 3, 'developer': 2, 'engineer': 2,
            'senior developer': 3, 'lead developer': 3, 'software engineer': 2, 'data analyst': 2, 'it specialist': 2,
            'technical lead': 3, 'architect': 3, 'analyst': 2, 'specialist': 2, 'consultant': 2, 'programador': 2,
            'ingeniero': 2, 'analista': 2, 'recién egresado': 2, 'practicante': 2, 'pasante': 2, 'becario': 2, 'líder': 2, 'coordinador': 2
        },
        'amigro': {
            'migration': 4, 'bilingual': 3, 'visa sponsorship': 4, 'temporary job': 3, 'worker': 2, 'operator': 2,
            'constructor': 2, 'laborer': 2, 'assistant': 2, 'technician': 2, 'support': 2, 'seasonal': 2,
            'entry-level': 2, 'no experience': 3, 'trabajador': 2, 'operador': 2, 'asistente': 2, 'migración': 4, 'ejecutivo': 2, 'auxiliar': 3, 'soporte': 3
        }
    }

    SENIORITY_KEYWORDS = {
        'junior': 1, 'entry-level': 1, 'mid-level': 2, 'senior': 3, 'lead': 3,
        'manager': 4, 'director': 5, 'vp': 5, 'executive': 5, 'chief': 5, 'jefe': 4
    }

    INDUSTRY_KEYWORDS = {
        'tech': {'developer', 'engineer', 'software', 'data', 'it', 'architect', 'programador', 'ingeniero'},
        'management': {'manager', 'director', 'executive', 'leadership', 'gerente', 'jefe'},
        'operations': {'operator', 'worker', 'constructor', 'technician', 'trabajador', 'operador'},
        'strategy': {'strategic', 'global', 'board', 'president', 'estrategico'}
    }

    @staticmethod
    async def assign_business_unit_async(job_title: str, job_description: str = None, 
                                      salary_range=None, required_experience=None, 
                                      location: str = None) -> Optional[int]:
        """
        Asigna la unidad de negocio más adecuada para una vacante basada en varios criterios.
        
        Args:
            job_title (str): Título del puesto.
            job_description (str, optional): Descripción del puesto.
            salary_range (tuple, optional): Rango de salario.
            required_experience (int, optional): Años de experiencia requeridos.
            location (str, optional): Ubicación del puesto.

        Returns:
            Optional[int]: ID de la unidad de negocio asignada, o None si no se puede asignar.
        """
        job_title_lower = job_title.lower()
        job_desc_lower = job_description.lower() if job_description else ""
        location_lower = location.lower() if location else ""

        bu_candidates = await sync_to_async(list)(BusinessUnit.objects.all())
        logger.debug(f"Unidades de negocio disponibles: {[bu.name for bu in bu_candidates]}")
        scores = {bu.name: 0 for bu in bu_candidates}

        seniority_score = 0
        for keyword, score in ChatbotUtils.SENIORITY_KEYWORDS.items():
            if keyword in job_title_lower:
                seniority_score = max(seniority_score, score)
        logger.debug(f"Puntuación de seniority: {seniority_score}")

        industry_scores = {ind: 0 for ind in ChatbotUtils.INDUSTRY_KEYWORDS}
        for ind, keywords in ChatbotUtils.INDUSTRY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in job_title_lower or keyword in job_desc_lower:
                    industry_scores[ind] += 1
        dominant_industry = max(industry_scores, key=industry_scores.get) if max(industry_scores.values()) > 0 else None
        logger.debug(f"Industria dominante: {dominant_industry}, puntajes: {industry_scores}")

        for bu in bu_candidates:
            try:
                config = await sync_to_async(ConfiguracionBU.objects.get)(business_unit=bu)
                weights = {
                    "ubicacion": config.weight_location or 10,
                    "hard_skills": config.weight_hard_skills or 45,
                    "soft_skills": config.weight_soft_skills or 35,
                    "tipo_contrato": config.weight_contract or 10,
                    "personalidad": getattr(config, 'weight_personality', 15),
                }
            except ConfiguracionBU.DoesNotExist:
                weights = {
                    "ubicacion": 5,
                    "hard_skills": 45,
                    "soft_skills": 35,
                    "tipo_contrato": 5,
                    "personalidad": 10,
                }
            logger.debug(f"Pesos para {bu.name}: {weights}")

            if seniority_score >= 5:
                weights["soft_skills"] = 45
                weights["hard_skills"] = 30
                weights["ubicacion"] = 10
                weights["personalidad"] = 25
            elif seniority_score >= 3:
                weights["soft_skills"] = 40
                weights["hard_skills"] = 40
                weights["ubicacion"] = 10
                weights["personalidad"] = 20
            else:
                weights["ubicacion"] = 15
                weights["hard_skills"] = 50
                weights["soft_skills"] = 25
                weights["personalidad"] = 10

            for keyword, weight in ChatbotUtils.BUSINESS_UNITS_KEYWORDS.get(bu.name, {}).items():
                if keyword in job_title_lower or (job_description and keyword in job_desc_lower):
                    scores[bu.name] += weight * weights["hard_skills"]

            if seniority_score >= 5:
                if bu.name == 'huntRED Executive':
                    scores[bu.name] += 4 * weights["personalidad"]
                elif bu.name == 'huntRED':
                    scores[bu.name] += 2 * weights["soft_skills"]
            elif seniority_score >= 3:
                if bu.name == 'huntRED':
                    scores[bu.name] += 3 * weights["soft_skills"]
                elif bu.name == 'huntu':
                    scores[bu.name] += 1 * weights["hard_skills"]
            elif seniority_score >= 1:
                if bu.name == 'huntu':
                    scores[bu.name] += 2 * weights["hard_skills"]
                elif bu.name == 'amigro':
                    scores[bu.name] += 1 * weights["ubicacion"]
            else:
                if bu.name == 'amigro':
                    scores[bu.name] += 3 * weights["ubicacion"]

            if dominant_industry:
                if dominant_industry == 'tech':
                    if bu.name == 'huntu':
                        scores[bu.name] += 3 * weights["hard_skills"] * industry_scores['tech']
                    elif bu.name == 'huntRED':
                        scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['tech']
                elif dominant_industry == 'management':
                    if bu.name == 'huntRED':
                        scores[bu.name] += 3 * weights["soft_skills"] * industry_scores['management']
                    elif bu.name == 'huntRED Executive':
                        scores[bu.name] += 2 * weights["personalidad"] * industry_scores['management']
                elif dominant_industry == 'operations':
                    if bu.name == 'amigro':
                        scores[bu.name] += 3 * weights["ubicacion"] * industry_scores['operations']
                elif dominant_industry == 'strategy':
                    if bu.name == 'huntRED Executive':
                        scores[bu.name] += 3 * weights["personalidad"] * industry_scores['strategy']
                    elif bu.name == 'huntRED':
                        scores[bu.name] += 1 * weights["soft_skills"] * industry_scores['strategy']

            if job_description:
                if any(term in job_desc_lower for term in ['migration', 'visa', 'bilingual', 'temporary', 'migración']):
                    if bu.name == 'amigro':
                        scores[bu.name] += 4 * weights["ubicacion"]
                if any(term in job_desc_lower for term in ['strategic', 'global', 'executive', 'board', 'estrategico']):
                    if bu.name == 'huntRED Executive':
                        scores[bu.name] += 3 * weights["personalidad"]
                if any(term in job_desc_lower for term in ['development', 'coding', 'software', 'data', 'programación']):
                    if bu.name == 'huntu':
                        scores[bu.name] += 3 * weights["hard_skills"]
                if any(term in job_desc_lower for term in ['operations', 'management', 'leadership', 'gerencia']):
                    if bu.name == 'huntRED':
                        scores[bu.name] += 3 * weights["soft_skills"]

            if location:
                if any(term in location_lower for term in ['usa', 'europe', 'asia', 'mexico', 'latam', 'frontera', 'migración']):
                    if bu.name == 'amigro':
                        scores[bu.name] += 3 * weights["ubicacion"]
                if any(term in location_lower for term in ['silicon valley', 'new york', 'london']):
                    if bu.name == 'huntRED Executive':
                        scores[bu.name] += 2 * weights["personalidad"]
                    elif bu.name == 'huntu':
                        scores[bu.name] += 1 * weights["hard_skills"]

        max_score = max(scores.values())
        candidates = [bu for bu, score in scores.items() if score == max_score]
        logger.debug(f"Puntuaciones finales: {scores}, candidatos: {candidates}")
        priority_order = ['huntRED Executive', 'huntRED', 'huntu', 'amigro']

        if candidates:
            if len(candidates) > 1 and dominant_industry:
                if dominant_industry == 'strategy' and 'huntRED Executive' in candidates:
                    chosen_bu = 'huntRED Executive'
                elif dominant_industry == 'management' and 'huntRED' in candidates:
                    chosen_bu = 'huntRED'
                elif dominant_industry == 'tech' and 'huntu' in candidates:
                    chosen_bu = 'huntu'
                elif dominant_industry == 'operations' and 'amigro' in candidates:
                    chosen_bu = 'amigro'
                else:
                    for bu in priority_order:
                        if bu in candidates:
                            chosen_bu = bu
                            break
            else:
                chosen_bu = candidates[0]
        else:
            chosen_bu = 'huntRED'

        try:
            bu_obj = await sync_to_async(BusinessUnit.objects.get)(name=chosen_bu)
            logger.info(f"✅ Unidad de negocio asignada: {chosen_bu} (ID: {bu_obj.id}) para '{job_title}'")
            return bu_obj.id
        except BusinessUnit.DoesNotExist:
            logger.warning(f"⚠️ Unidad de negocio '{chosen_bu}' no encontrada, usando huntRED por defecto")
            try:
                default_bu = await sync_to_async(BusinessUnit.objects.get)(id=1)
                logger.info(f"🔧 Asignada huntRED por defecto (ID: {default_bu.id}) para '{job_title}'")
                return default_bu.id
            except BusinessUnit.DoesNotExist:
                logger.error(f"❌ Unidad de negocio por defecto 'huntRED' no encontrada en BD")
                return None
        """
        Recomienda vacantes basadas en el perfil del usuario.
        
        Args:
            user: Usuario para el cual se recomendarán vacantes
            
        Returns:
            List[Vacante]: Lista de vacantes recomendadas
        """
        # Obtener habilidades priorizadas basándose en intereses
        prioritized_skills, skill_weights = prioritize_interests(
            [skill.name for skill in user.skills.all()],
            [interest.name for interest in user.interests.all()]
        )
        
        # Obtener posiciones recomendadas basándose en habilidades
        positions = get_positions_by_skills(prioritized_skills)
        
        # Filtrar y ordenar vacantes activas
        now = timezone.now()
        vacancies = Vacante.objects.filter(
            status='active',
            created_at__lte=now
        ).select_related('business_unit').prefetch_related('required_skills')
        
        # Calcular puntaje de coincidencia para cada vacante
        scored_vacancies = []
        for vacancy in vacancies:
            score = ChatbotUtils.calculate_match_score(user, vacancy)
            scored_vacancies.append((vacancy, score))
        
        # Ordenar por puntaje y fecha de publicación
        scored_vacancies.sort(key=lambda x: (x[1], x[0].created_at), reverse=True)
        
        # Devolver las 5 mejores coincidencias
        return [v[0] for v in scored_vacancies[:5]]

    @staticmethod
    def prioritize_interests(skills: List[str], interests: List[str]) -> Tuple[List[str], Dict[str, float]]:
        """
        Prioriza habilidades basándose en intereses del usuario.
        
        Args:
            skills: Lista de habilidades detectadas
            interests: Lista de intereses del usuario
            
        Returns:
            Tuple[List[str], Dict[str, float]]: Lista de habilidades priorizadas y sus pesos
        """
        if not interests:
            return skills, {skill: 1.0 for skill in skills}
        
        # Crear vectorizador TF-IDF
        vectorizer = TfidfVectorizer()
        
        # Combinar habilidades e intereses para el vectorizador
        all_texts = skills + interests
        
        # Obtener matriz TF-IDF
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Obtener vectores para habilidades e intereses
        skill_vectors = tfidf_matrix[:len(skills)]
        interest_vectors = tfidf_matrix[len(skills):]
        
        # Calcular similitud coseno entre habilidades e intereses
        similarities = cosine_similarity(skill_vectors, interest_vectors).mean(axis=1)
        
        # Ordenar habilidades por similitud
        sorted_indices = np.argsort(similarities)[::-1]
        prioritized_skills = [skills[i] for i in sorted_indices]
        
        # Calcular pesos basados en similitud
        weights = {prioritized_skills[i]: float(similarities[sorted_indices[i]]) for i in range(len(skills))}
        
        return prioritized_skills, weights

    @staticmethod
    def get_positions_by_skills(skills: List[str]) -> List[Dict[str, Any]]:
        """
        Obtiene posiciones recomendadas basándose en habilidades.
        
        Args:
            skills: Lista de habilidades priorizadas
            
        Returns:
            List[Dict[str, Any]]: Lista de posiciones recomendadas con información relevante
        """
        # Obtener todas las vacantes activas
        now = timezone.now()
        vacancies = Vacante.objects.filter(
            status='active',
            created_at__lte=now
        ).prefetch_related('required_skills')
        
        # Calcular puntaje para cada vacante
        scored_vacancies = []
        for vacancy in vacancies:
            # Obtener habilidades requeridas
            required_skills = set(skill.name for skill in vacancy.required_skills.all())
            candidate_skills = set(skills)
            
            # Calcular porcentaje de habilidades coincidentes
            score = len(required_skills.intersection(candidate_skills)) / len(required_skills)
            
            scored_vacancies.append({
                'title': vacancy.title,
                'required_skills': list(required_skills),
                'score': score,
                'vacancy': vacancy
            })
        
        # Ordenar por score
        scored_vacancies.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_vacancies

    @staticmethod
    def get_application_status(user: Person) -> Dict[str, int]:
        """
        Obtiene el estado de las aplicaciones del usuario.
        
        Args:
            user: Usuario
            
        Returns:
            Dict: Diccionario con estadísticas de aplicaciones
        """
        # Optimizar consulta usando annotate
        stats = user.application_set.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status__in=['applied', 'in_review'])),
            interview=Count('id', filter=Q(status='interview')),
            hired=Count('id', filter=Q(status='hired'))
        )
        return stats

    @staticmethod
    def get_gamification_progress(user: Person) -> Dict[str, int]:
        """
        Obtiene el progreso de gamificación del usuario.
        
        Args:
            user: Usuario
            
        Returns:
            Dict: Diccionario con progreso de gamificación
        """
        # Optimizar consulta usando select_related
        profile = user.gamification_profile.select_related('badges', 'achievements')
        
        # Calcular progreso hacia el siguiente nivel
        next_level_points = profile.level * 1000  # Puntos requeridos para el siguiente nivel
        current_progress = (profile.points / next_level_points) * 100 if next_level_points > 0 else 0
        
        return {
            'points': profile.points,
            'level': profile.level,
            'experience': profile.experience,
            'badges': profile.badges.count(),
            'achievements': profile.achievements.count(),
            'progress_to_next_level': round(current_progress, 2)
        }

    @staticmethod
    def get_next_interview(user: Person) -> Optional[Application]:
        """
        Obtiene la próxima entrevista del usuario.
        
        Args:
            user: Usuario
            
        Returns:
            Application: Próxima entrevista o None si no existe
        """
        return user.application_set.filter(
            status='interview',
            interview_date__gte=timezone.now()
        ).order_by('interview_date').first()

    @staticmethod
    def get_recent_interactions(user: Person) -> List[Dict]:
        """
        Obtiene las interacciones recientes del usuario.
        
        Args:
            user: Usuario
            
        Returns:
            List[Dict]: Lista de interacciones recientes
        """
        # Optimizar consulta usando values y order_by
        return user.application_set.values(
            'vacancy__title',
            'status',
            'updated_at',
            'interview_date'
        ).order_by('-updated_at')[:5]

    @staticmethod
    def get_skill_match_score(user: Person, vacancy: Vacante) -> float:
        """
        Calcula el puntaje de coincidencia de habilidades.
        
        Args:
            user: Usuario
            vacancy: Vacante
            
        Returns:
            float: Puntaje de coincidencia (0.0 - 1.0)
        """
        # Optimizar usando sets y operaciones vectorizadas
        if not vacancy.required_skills:
            return 1.0
            
        user_skills = set(user.skills or [])
        required_skills = set(vacancy.required_skills)
        
        # Calcular puntuación ponderada
        common_skills = user_skills.intersection(required_skills)
        total_skills = len(required_skills)
        
        # Ajustar puntuación según la importancia de las habilidades
        skill_importance = {
            'technical': 1.5,  # Habilidades técnicas son más importantes
            'soft': 1.2,      # Habilidades blandas son importantes
            'languages': 1.0,  # Idiomas son importantes
            'tools': 0.8      # Conocimiento de herramientas es menos importante
        }
        
        weighted_score = 0
        for skill in common_skills:
            category = skill.category if hasattr(skill, 'category') else 'technical'
            weighted_score += skill_importance.get(category, 1.0)
            
        return min(1.0, weighted_score / (total_skills * 1.5))

    @staticmethod
    def get_experience_match_score(user: Person, vacancy: Vacante) -> float:
        """
        Calcula el puntaje de coincidencia de experiencia.
        
        Args:
            user: Usuario
            vacancy: Vacante
            
        Returns:
            float: Puntaje de coincidencia (0.0 - 1.0)
        """
        # Optimizar cálculo de experiencia usando rangos
        if not vacancy.required_experience:
            return 1.0
            
        if user.experience_years is None:
            return 0.0
            
        # Definir rangos de experiencia
        experience_ranges = [
            (0, 1),    # Junior
            (2, 4),    # Intermedio
            (5, 8),    # Senior
            (9, float('inf'))  # Expert
        ]
        
        # Determinar rango de experiencia del usuario
        user_range = next((i for i, (low, high) in enumerate(experience_ranges) 
                         if low <= user.experience_years <= high), len(experience_ranges) - 1)
        
        # Determinar rango de experiencia requerido
        required_range = next((i for i, (low, high) in enumerate(experience_ranges) 
                             if low <= vacancy.required_experience <= high), len(experience_ranges) - 1)
        
        # Calcular puntuación basada en la diferencia de rangos
        range_diff = abs(user_range - required_range)
        return max(0.0, 1.0 - (range_diff * 0.25))

    @staticmethod
    def get_salary_match_score(user: Person, vacancy: Vacante) -> float:
        """
        Calcula el puntaje de coincidencia de salario.
        
        Args:
            user: Usuario
            vacancy: Vacante
            
        Returns:
            float: Puntaje de coincidencia (0.0 - 1.0)
        """
        # Optimizar cálculo de salario usando rangos y flexibilidad
        if not vacancy.salary_range:
            return 1.0
            
        min_salary, max_salary = vacancy.salary_range
        if user.expected_salary is None:
            return 0.0
            
        # Calcular flexibilidad salarial
        salary_flexibility = 0.1  # 10% de flexibilidad
        
        # Calcular rango de aceptación
        acceptable_range = max_salary * (1 + salary_flexibility)
        
        if user.expected_salary <= acceptable_range:
            return 1.0
            
        # Calcular puntuación basada en la diferencia
        diff = user.expected_salary - acceptable_range
        max_diff = acceptable_range * 0.5  # Máximo 50% por encima
        
        return max(0.0, 1.0 - (diff / max_diff))

    @staticmethod
    def get_location_match_score(user: Person, vacancy: Vacante) -> float:
        """
        Calcula el puntaje de coincidencia de ubicación.
        
        Args:
            user: Usuario
            vacancy: Vacante
            
        Returns:
            float: Puntaje de coincidencia (0.0 - 1.0)
        """
        # Optimizar cálculo de ubicación usando geolocalización
        if not vacancy.location:
            return 1.0
            
        # Obtener coordenadas de las ubicaciones
        try:
            user_coords = user.location.coordinates
            vacancy_coords = vacancy.location.coordinates
        except AttributeError:
            return 0.5  # Puntaje medio si no hay coordenadas
            
        # Calcular distancia usando la fórmula de Haversine
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Radio de la Tierra en km
        
        lat1, lon1 = radians(user_coords[0]), radians(user_coords[1])
        lat2, lon2 = radians(vacancy_coords[0]), radians(vacancy_coords[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        distance = R * c  # Distancia en km
        
        # Definir rangos de distancia
        if distance <= 10:  # Mismo área
            return 1.0
        elif distance <= 50:  # Mismo estado
            return 0.8
        elif distance <= 200:  # Mismo país
            return 0.6
        else:  # Distancia internacional
            return 0.4

    @staticmethod
    def calculate_match_score(user: Person, vacancy: Vacante) -> float:
        """
        Calcula el puntaje total de coincidencia.
        
        Args:
            user: Usuario
            vacancy: Vacante
            
        Returns:
            float: Puntaje total (0.0 - 1.0)
        """
        # Optimizar cálculo de puntuación usando ponderaciones dinámicas
        base_weights = {
            'skills': 0.4,
            'experience': 0.3,
            'salary': 0.2,
            'location': 0.1
        }
        
        # Ajustar pesos según el tipo de vacante
        if vacancy.category == 'technical':
            base_weights['skills'] = 0.5
            base_weights['experience'] = 0.3
            base_weights['salary'] = 0.15
            base_weights['location'] = 0.05
        elif vacancy.category == 'management':
            base_weights['skills'] = 0.3
            base_weights['experience'] = 0.4
            base_weights['salary'] = 0.2
            base_weights['location'] = 0.1
        
        # Normalizar pesos
        total_weight = sum(base_weights.values())
        weights = {k: v/total_weight for k, v in base_weights.items()}
        
        # Calcular puntuaciones
        scores = {
            'skills': ChatbotUtils.get_skill_match_score(user, vacancy),
            'experience': ChatbotUtils.get_experience_match_score(user, vacancy),
            'salary': ChatbotUtils.get_salary_match_score(user, vacancy),
            'location': ChatbotUtils.get_location_match_score(user, vacancy)
        }
        
        # Aplicar ponderación final
        final_score = sum(weights[k] * scores[k] for k in weights)
        
        # Ajustar puntuación según el nivel de urgencia de la vacante
        urgency_factor = 1.0
        if vacancy.urgency_level == 'high':
            urgency_factor = 1.2
        elif vacancy.urgency_level == 'low':
            urgency_factor = 0.8
            
        return min(1.0, final_score * urgency_factor)

    @staticmethod
    def get_recommendation_message(user: Person, vacancy: Vacante) -> str:
        """
        Genera un mensaje de recomendación personalizado.
        
        Args:
            user: Usuario
            vacancy: Vacante
            
        Returns:
            str: Mensaje de recomendación
        """
        score = ChatbotUtils.calculate_match_score(user, vacancy)
        
        # Determinar el nivel de coincidencia
        score_levels = {
            (0.8, 1.0): "¡Excelente coincidencia!",
            (0.6, 0.8): "Buena coincidencia",
            (0.4, 0.6): "Coincidencia moderada",
            (0.0, 0.4): "Coincidencia limitada"
        }
        
        score_level = next((level for (low, high), level in score_levels.items() 
                          if low <= score < high), "Coincidencia limitada")
        
        message = f"{score_level}\n\n"
        message += f"Puntaje: {score:.2f}/1.0\n\n"
        
        # Generar recomendaciones específicas
        recommendations = []
        
        # Análisis de habilidades
        skill_score = ChatbotUtils.get_skill_match_score(user, vacancy)
        if skill_score < 0.8:
            recommendations.append("Considera mejorar tus habilidades técnicas")
        
        # Análisis de experiencia
        exp_score = ChatbotUtils.get_experience_match_score(user, vacancy)
        if exp_score < 0.8:
            recommendations.append("Considera aumentar tu experiencia laboral")
        
        # Análisis de salario
        salary_score = ChatbotUtils.get_salary_match_score(user, vacancy)
        if salary_score < 0.8:
            recommendations.append("Revisa tus expectativas salariales")
        
        # Análisis de ubicación
        location_score = ChatbotUtils.get_location_match_score(user, vacancy)
        if location_score < 0.8:
            recommendations.append("Considera la ubicación de la vacante")
        
        if recommendations:
            message += "Áreas de mejora:\n"
            message += "\n".join(f"- {rec}" for rec in recommendations)
        else:
            message += "¡Excelente! Tu perfil se ajusta perfectamente a esta vacante."
        
        # Agregar detalles de la vacante
        message += f"\n\nDetalles de la vacante:\n"
        message += f"Puesto: {vacancy.title}\n"
        message += f"Ubicación: {vacancy.location}\n"
        message += f"Experiencia requerida: {vacancy.required_experience} años\n"
        message += f"Salario: ${vacancy.salary_range[0]} - ${vacancy.salary_range[1]}\n"
        
        return message

    @staticmethod
    def get_gamification_message(user: Person) -> str:
        """
        Genera un mensaje de gamificación personalizado.
        
        Args:
            user: Usuario
            
        Returns:
            str: Mensaje de gamificación
        """
        profile = user.gamification_profile
        
        # Calcular progreso hacia el siguiente nivel
        next_level_points = profile.level * 1000
        current_progress = (profile.points / next_level_points) * 100
        
        message = f"¡Hola {user.get_full_name()}!\n\n"
        message += f"Nivel: {profile.level}\n"
        message += f"Puntos: {profile.points}/{next_level_points}\n"
        message += f"Progreso: {current_progress:.1f}%\n\n"
        
        # Mostrar badges y logros
        badges = profile.badges.all()
        achievements = profile.achievements.all()
        
        if badges.exists():
            message += "Badges obtenidos:\n"
            message += "\n".join(f"- {badge.name}" for badge in badges)
            message += "\n\n"
        
        if achievements.exists():
            message += "Logros recientes:\n"
            message += "\n".join(f"- {ach.name}" for ach in achievements[:3])
            message += "\n\n"
        
        # Mostrar recomendaciones de acción
        message += "¡Sigue mejorando!\n"
        actions = []
        
        if profile.experience < 100:
            actions.append("Completa tu perfil")
        if not profile.cv_uploaded:
            actions.append("Sube tu CV")
        if not profile.photo:
            actions.append("Agrega una foto")
        if not profile.skills.exists():
            actions.append("Añade tus habilidades")
        
        if actions:
            message += "Acciones recomendadas:\n"
            message += "\n".join(f"- {action}" for action in actions)
        
        return message

@staticmethod
def get_onboarding_message(user: Person) -> str:
    """
    Genera un mensaje de bienvenida personalizado.
    
    Returns:
        str: Mensaje de bienvenida
    """
    # Verificar datos existentes del usuario
    existing_data = []
    missing_data = []
        
    if user.location:
        existing_data.append("Ubicación")
    else:
        missing_data.append("Tu ubicación actual")
            
    if user.skills.exists():
        existing_data.append("Habilidades")
    else:
        missing_data.append("Tus habilidades principales")
            
    if user.education:
        existing_data.append("Educación")
    else:
        missing_data.append("Tu nivel educativo")
            
    if user.experience_years is not None:
        existing_data.append("Experiencia")
    else:
        missing_data.append("Tu experiencia laboral")
            
    if user.expected_salary is not None:
        existing_data.append("Expectativas salariales")
    else:
        missing_data.append("Tus expectativas salariales")
            
    message = f"¡Hola {user.get_full_name()}!\n\n"
    message += "¡Bienvenido/a a nuestro sistema de reclutamiento!\n\n"
        
    if existing_data:
        message += "Datos completados:\n"
        message += "\n".join(f"- {data}" for data in existing_data)
        message += "\n\n"
        
    if missing_data:
        message += "Datos pendientes:\n"
        message += "\n".join(f"{i}. {data}" for i, data in enumerate(missing_data, 1))
        message += "\n\n"
        
    message += "¿Por dónde te gustaría comenzar?\n"
    message += "\n".join(f"{i}. {data}" for i, data in enumerate(missing_data, 1))
        
    return message

@staticmethod
def get_help_message() -> str:
    """
    Genera un mensaje de ayuda con opciones de interacción.
    
    Returns:
        str: Mensaje de ayuda
    """
    options = [
        "Ver mis aplicaciones",
        "Buscar nuevas oportunidades",
        "Ver mi perfil",
        "Ver mi progreso en gamificación",
        "Ver mis entrevistas programadas",
        "Actualizar mi perfil",
        "Ver estadísticas del sistema",
        "Ver recomendaciones personalizadas",
        "Ver logros y badges",
        "Ver preguntas frecuentes"
    ]
        
    message = "¡Hola! Aquí tienes algunas opciones:\n\n"
    message += "\n".join(f"{i}. {opt}" for i, opt in enumerate(options, 1))
    message += "\n\n¿Qué te gustaría hacer?\n"
    message += "\nEscribe el número correspondiente a la opción que deseas."
        
    return message
