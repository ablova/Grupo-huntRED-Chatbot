from django.utils import timezone
from datetime import timedelta
from app.models import (
    Person, Application, Vacante, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState, WorkflowStage,
    GamificationAchievement, GamificationBadge, GamificationEvent
)
import logging
from typing import Dict, List, Optional, Any, Tuple
from django.db.models import Q, Count, Avg
from collections import defaultdict
import math

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
        # Optimizar consulta usando subqueries y evitar múltiples consultas
        now = timezone.now()
        
        # Calcular puntuación de coincidencia para cada vacante
        vacancies = Vacante.objects.filter(
            status='active'
        ).annotate(
            skill_match=Count('required_skills', filter=Q(required_skills__in=user.skills)),
            experience_match=Avg('experience_years', filter=Q(experience_years__lte=user.experience_years)),
            salary_match=Avg('salary_range', filter=Q(salary_range__gte=user.expected_salary)),
            location_match=Count('location', filter=Q(location=user.location))
        ).annotate(
            total_score=(F('skill_match') * 0.4) + 
                      (F('experience_match') * 0.3) + 
                      (F('salary_match') * 0.2) + 
                      (F('location_match') * 0.1)
        ).filter(
            total_score__gte=0.5  # Solo mostrar vacantes con puntuación mínima
        ).select_related('business_unit').prefetch_related('required_skills')
        
        # Ordenar por puntuación total y fecha de publicación
        return vacancies.order_by('-total_score', '-created_at')[:5]

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
