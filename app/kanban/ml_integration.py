# /home/pablo/app/kanban/ml_integration.py
"""
Integración entre el sistema Kanban y los modelos de Machine Learning.
Este módulo proporciona funcionalidades para enriquecer la experiencia
Kanban con recomendaciones basadas en ML.
"""

import logging
import json
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from typing import List, Dict, Any, Tuple, Optional
from asgiref.sync import sync_to_async

# Importaciones directas siguiendo reglas de Grupo huntRED®
from app.ml.ml_model import MatchmakingLearningSystem
from app.models import (
    Person, Vacante, Application, BusinessUnit
)

# Definiciones mock para modelos culturales
class CulturalDimension:
    id = 0
    name = "Dimensión Mock"

class CulturalValue:
    id = 0
    name = "Valor Mock"
    dimension = CulturalDimension()

class CulturalProfile:  # En realidad puede ser PersonCulturalProfile en el modelo real
    id = 0
    person_id = 0
# Importamos las clases mock directamente desde el módulo kanban
from app.kanban import (
    KanbanBoard, KanbanColumn, KanbanCard, KanbanCardHistory
)

# Obtener el logger específico para este módulo
logger = logging.getLogger('kanban.ml_integration')

class KanbanMLIntegration:
    """Clase que integra funcionalidades ML en el sistema Kanban."""
    
    CACHE_TTL = 3600  # Cache de 1 hora para predicciones
    
    def __init__(self, business_unit=None):
        """
        Inicializa la integración de ML para Kanban.
        
        Args:
            business_unit: Opcional, unidad de negocio específica para contextualizar recomendaciones
        """
        self.ml_system = MatchmakingLearningSystem(business_unit=business_unit)
        self.business_unit = business_unit
    
    def get_recommended_candidates_for_column(self, column: KanbanColumn, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene candidatos recomendados para una columna específica basado en ML.
        
        Args:
            column: Columna Kanban para la que se buscan recomendaciones
            limit: Número máximo de recomendaciones a devolver
            
        Returns:
            Lista de diccionarios con información de candidatos recomendados
        """
        cache_key = f"kanban_ml_recommendations_column_{column.id}_{limit}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            logger.info(f"Usando recomendaciones en caché para columna {column.name}")
            return cached_results
        
        try:
            # Identificar columna equivalente en flujo de trabajo
            workflow_stage = column.workflow_stage
            
            # Obtener aplicaciones activas que no estén ya en alguna tarjeta del tablero
            existing_application_ids = KanbanCard.objects.filter(
                column__board=column.board
            ).values_list('application_id', flat=True)
            
            # Filtrar aplicaciones por unidad de negocio si es necesario
            if self.business_unit:
                potential_applications = Application.objects.filter(
                    vacancy__business_unit=self.business_unit,
                    status='applied'
                ).exclude(id__in=existing_application_ids)
            else:
                potential_applications = Application.objects.filter(
                    status='applied'
                ).exclude(id__in=existing_application_ids)
            
            # Si no hay candidatos potenciales, retornar lista vacía
            if not potential_applications.exists():
                logger.info("No hay candidatos potenciales para recomendar")
                return []
            
            # Calcular predicciones para cada aplicación
            recommendations = []
            for app in potential_applications[:25]:  # Limitar a 25 para optimizar rendimiento
                try:
                    # Calcular score de predicción
                    score = self.ml_system.predict_candidate_success(app.user, app.vacancy)
                    
                    # Añadir a lista de recomendaciones
                    recommendations.append({
                        'application_id': app.id,
                        'person': {
                            'id': app.user.id,
                            'name': f"{app.user.nombre} {app.user.apellido_paterno}",
                            'email': app.user.email,
                        },
                        'vacancy': {
                            'id': app.vacancy.id,
                            'title': app.vacancy.title,
                            'company': app.vacancy.empresa.nombre if hasattr(app.vacancy, 'empresa') else None,
                        },
                        'score': score,
                        'applied_at': app.applied_at.strftime('%Y-%m-%d %H:%M') if app.applied_at else None,
                    })
                except Exception as e:
                    logger.error(f"Error calculando predicción para aplicación {app.id}: {str(e)}")
            
            # Ordenar por score y limitar al número solicitado
            recommendations = sorted(recommendations, key=lambda x: x['score'], reverse=True)[:limit]
            
            # Guardar en caché para futuras solicitudes
            cache.set(cache_key, recommendations, self.CACHE_TTL)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error obteniendo recomendaciones para columna {column.name}: {str(e)}")
            return []
    
    def predict_best_column_for_card(self, card: KanbanCard) -> Tuple[Optional[KanbanColumn], float]:
        """
        Predice la mejor columna para una tarjeta basado en el histórico y ML.
        
        Args:
            card: Tarjeta Kanban para la que se quiere predecir mejor columna
            
        Returns:
            Tupla con la columna recomendada y confianza de la predicción
        """
        cache_key = f"kanban_ml_best_column_card_{card.id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            column_id, confidence = cached_result
            try:
                column = KanbanColumn.objects.get(id=column_id)
                return column, confidence
            except KanbanColumn.DoesNotExist:
                pass  # Si la columna ya no existe, recalcular
        
        try:
            # Obtener todas las columnas del tablero
            columns = KanbanColumn.objects.filter(board=card.column.board)
            
            # Si solo hay una columna, no hay predicción que hacer
            if columns.count() <= 1:
                return None, 0.0
            
            # Generar vectores de características para el modelo de ML
            # Usamos datos históricos y características del candidato/vacante
            best_column = None
            highest_confidence = 0.0
            
            # Por ahora, implementación simplificada basada en el stage actual
            # En el futuro, podríamos implementar un modelo de ML específico para esto
            current_stage_position = card.column.workflow_stage.position if card.column.workflow_stage else 0
            
            # Recomendar avanzar al siguiente workflow stage con mayor confianza si la vacante tiene match alto
            for column in columns:
                # Saltar la columna actual
                if column.id == card.column.id:
                    continue
                
                # Obtener posición en el flujo de trabajo
                column_stage_position = column.workflow_stage.position if column.workflow_stage else 0
                
                # Calcular distancia (preferimos avances graduales, no saltos múltiples)
                position_diff = column_stage_position - current_stage_position
                
                # Calcula una confianza simple basada en la distancia
                if position_diff == 1:  # Avance de una posición (ideal)
                    base_confidence = 0.85
                elif position_diff > 1:  # Avance de múltiples posiciones (menos recomendado)
                    base_confidence = 0.40 / position_diff
                elif position_diff == -1:  # Retroceso de una posición
                    base_confidence = 0.25
                else:  # Retroceso mayor (raro, solo si hay problemas)
                    base_confidence = 0.10
                
                # Ajustar confianza según el score de ML
                try:
                    ml_score = self.ml_system.predict_candidate_success(
                        card.application.user, 
                        card.application.vacancy
                    )
                    
                    # Ajustar confianza según el score de ML
                    confidence = base_confidence * (0.5 + 0.5 * ml_score)
                    
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_column = column
                except Exception as e:
                    logger.error(f"Error calculando ML score para card {card.id}: {str(e)}")
                    confidence = base_confidence
                    if confidence > highest_confidence:
                        highest_confidence = confidence
                        best_column = column
            
            # Guardar en caché para futuras solicitudes
            if best_column:
                cache.set(cache_key, (best_column.id, highest_confidence), self.CACHE_TTL)
            
            return best_column, highest_confidence
            
        except Exception as e:
            logger.error(f"Error prediciendo mejor columna para tarjeta {card.id}: {str(e)}")
            return None, 0.0
    
    def get_similar_cards(self, card: KanbanCard, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Encuentra tarjetas similares a la dada usando ML.
        
        Args:
            card: Tarjeta Kanban para la que se buscan similares
            limit: Número máximo de tarjetas similares a devolver
            
        Returns:
            Lista de tarjetas similares con scores
        """
        cache_key = f"kanban_ml_similar_cards_{card.id}_{limit}"
        cached_results = cache.get(cache_key)
        
        if cached_results:
            return cached_results
        
        try:
            # Obtener todas las tarjetas excepto la actual
            other_cards = KanbanCard.objects.exclude(id=card.id)
            
            # Si no hay otras tarjetas, retornar lista vacía
            if not other_cards.exists():
                return []
            
            # Calcular similitud
            similar_cards = []
            for other_card in other_cards[:50]:  # Limitar para optimizar rendimiento
                try:
                    # Simplificado: usar similitud de habilidades entre vacantes como base
                    from app.ml.ml_model import calculate_match_percentage
                    
                    # Usando habilidades requeridas de las vacantes como base de similitud
                    vacancy1_skills = card.application.vacancy.required_skills or []
                    vacancy2_skills = other_card.application.vacancy.required_skills or []
                    
                    skills_similarity = calculate_match_percentage(vacancy1_skills, vacancy2_skills)
                    
                    # Solo considerar si la similitud es suficientemente alta
                    if skills_similarity > 40:
                        similar_cards.append({
                            'card': {
                                'id': other_card.id,
                                'column_name': other_card.column.name,
                                'person_name': f"{other_card.application.user.nombre} {other_card.application.user.apellido_paterno}",
                                'vacancy_title': other_card.application.vacancy.title,
                            },
                            'similarity_score': skills_similarity / 100.0  # Normalizar a escala 0-1
                        })
                except Exception as e:
                    logger.error(f"Error calculando similitud para tarjeta {other_card.id}: {str(e)}")
            
            # Ordenar por similitud y limitar
            similar_cards = sorted(similar_cards, key=lambda x: x['similarity_score'], reverse=True)[:limit]
            
            # Guardar en caché
            cache.set(cache_key, similar_cards, self.CACHE_TTL)
            
            return similar_cards
            
        except Exception as e:
            logger.error(f"Error encontrando tarjetas similares para {card.id}: {str(e)}")
            return []
    
    def prioritize_cards_in_column(self, column: KanbanColumn) -> List[Dict[str, Any]]:
        """
        Recomienda prioridad para tarjetas en una columna basándose en ML.
        
        Args:
            column: Columna Kanban para la que se quiere priorizar tarjetas
            
        Returns:
            Lista de tarjetas con prioridad sugerida
        """
        try:
            # Obtener todas las tarjetas en la columna
            cards = KanbanCard.objects.filter(column=column)
            
            # Si no hay tarjetas, retornar lista vacía
            if not cards.exists():
                return []
            
            # Calcular prioridad para cada tarjeta
            prioritized_cards = []
            for card in cards:
                try:
                    # Obtener score de ML para el candidato
                    ml_score = self.ml_system.predict_candidate_success(
                        card.application.user, 
                        card.application.vacancy
                    )
                    
                    # Convertir score a prioridad (1-4, donde 4 es la más alta)
                    if ml_score > 0.85:
                        suggested_priority = 4  # Urgente
                    elif ml_score > 0.70:
                        suggested_priority = 3  # Alta
                    elif ml_score > 0.50:
                        suggested_priority = 2  # Normal
                    else:
                        suggested_priority = 1  # Baja
                    
                    prioritized_cards.append({
                        'card_id': card.id,
                        'current_priority': card.priority,
                        'suggested_priority': suggested_priority,
                        'ml_score': ml_score,
                        'should_change': card.priority != suggested_priority
                    })
                except Exception as e:
                    logger.error(f"Error calculando prioridad para tarjeta {card.id}: {str(e)}")
            
            # Ordenar por ml_score (los mejores primero)
            return sorted(prioritized_cards, key=lambda x: x['ml_score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error priorizando tarjetas en columna {column.id}: {str(e)}")
            return []


# Funciones de utilidad para usar en las vistas

def analyze_skill_gaps(person, vacancy=None, target_role=None):
    """
    Analiza las brechas de habilidades para un candidato basado en una vacante o rol objetivo.
    
    Args:
        person: Objeto Person del candidato
        vacancy: Vacante objetivo opcional
        target_role: Rol objetivo opcional si no se proporciona vacante
        
    Returns:
        Diccionario con análisis de brechas de habilidades
    """
    # Verificar que tengamos skills del candidato
    candidate_skills = []
    if hasattr(person, 'skills') and person.skills:
        if isinstance(person.skills, str):
            try:
                candidate_skills = json.loads(person.skills)
            except:
                candidate_skills = []
        elif isinstance(person.skills, list):
            candidate_skills = person.skills
    
    # Determinar habilidades objetivo
    target_skills = []
    if vacancy:
        if hasattr(vacancy, 'skills_required') and vacancy.skills_required:
            if isinstance(vacancy.skills_required, str):
                try:
                    target_skills = json.loads(vacancy.skills_required)
                except:
                    target_skills = []
            elif isinstance(vacancy.skills_required, list):
                target_skills = vacancy.skills_required
    elif target_role:
        # Aquí podríamos obtener habilidades típicas para un rol específico
        # desde una base de conocimiento o modelo ML
        target_skills = _get_skills_for_role(target_role)
    
    # Calcular brechas
    missing_skills = [skill for skill in target_skills if skill not in candidate_skills]
    extra_skills = [skill for skill in candidate_skills if skill not in target_skills]
    common_skills = [skill for skill in candidate_skills if skill in target_skills]
    
    # Calcular porcentajes
    if target_skills:
        match_percentage = (len(common_skills) / len(target_skills)) * 100
    else:
        match_percentage = 0
    
    # Calcular potencial de desarrollo
    # Un algoritmo más complejo mediría la dificultad de aprender las habilidades faltantes
    development_potential = 0.85  # Valor predeterminado optimista
    if missing_skills:
        # Aquí podríamos usar ML para determinar el potencial real
        # Por ahora usamos un proxy simple
        development_potential -= (len(missing_skills) * 0.05)  # Reducir 5% por cada habilidad faltante
    
    return {
        'candidate_skills': candidate_skills,
        'target_skills': target_skills,
        'missing_skills': missing_skills,
        'extra_skills': extra_skills,
        'common_skills': common_skills,
        'match_percentage': match_percentage,
        'development_potential': max(0.2, min(1.0, development_potential)),
        'development_time_months': len(missing_skills) * 2  # Estimación simple: 2 meses por habilidad
    }

def get_vacancy_recommendations(person, limit=5):
    """
    Obtiene recomendaciones de vacantes para un candidato basado en su perfil.
    
    Args:
        person: Objeto Person del candidato
        limit: Número máximo de recomendaciones
        
    Returns:
        Lista de vacantes recomendadas con scores
    """
    cache_key = f"vacancy_recommendations_{person.id}_{limit}"
    cached_results = cache.get(cache_key)
    
    if cached_results:
        logger.info(f"Usando recomendaciones de vacantes en caché para candidato {person.id}")
        return cached_results
    
    try:
        # Obtener sistema ML
        ml_system = MatchmakingLearningSystem()
        
        # Obtener vacantes activas
        vacantes = Vacante.objects.filter(estado='activa')
        
        # Calcular scores para cada vacante
        recommendations = []
        for vacancy in vacantes[:20]:  # Limitar para optimizar rendimiento
            try:
                score = ml_system.predict_candidate_success(person, vacancy)
                
                # Solo incluir vacantes con match mayor al 50%
                if score > 0.5:
                    recommendations.append({
                        'vacancy_id': vacancy.id,
                        'title': vacancy.titulo,
                        'company': vacancy.empresa,
                        'score': score,
                        'match_percentage': int(score * 100)
                    })
            except Exception as e:
                logger.error(f"Error calculando score para vacante {vacancy.id}: {str(e)}")
        
        # Ordenar por score y limitar
        recommendations = sorted(recommendations, key=lambda x: x['score'], reverse=True)[:limit]
        
        # Guardar en caché
        cache.set(cache_key, recommendations, KanbanMLIntegration.CACHE_TTL)
        
        return recommendations
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones de vacantes para candidato {person.id}: {str(e)}")
        return []

def get_candidate_growth_data(person, audience_type='consultant'):
    """
    Genera un plan de desarrollo profesional para un candidato,
    adaptando el contenido según la audiencia objetivo.
    
    Args:
        person: Objeto Person del candidato
        audience_type: A quién va dirigido el plan: 'consultant', 'candidate' o 'client'
        
    Returns:
        Diccionario con datos del plan de crecimiento adaptados a la audiencia
    """
    # Generar roles objetivo potenciales basados en el rol actual
    current_role = getattr(person, 'puesto_actual', '') or 'Profesional'
    career_path = _generate_career_path(current_role)
    
    # Determinar habilidades objetivo basadas en el siguiente rol
    next_role = career_path[0]['title'] if career_path else 'Senior ' + current_role
    target_skills = _get_skills_for_role(next_role)
    
    # Analizar brechas de habilidades
    skill_gaps = analyze_skill_gaps(person, target_role=next_role)
    
    # Generar recursos recomendados basados en habilidades faltantes
    resources = _generate_learning_resources(skill_gaps['missing_skills'])
    
    # Obtener vacantes recomendadas
    recommended_vacancies = get_vacancy_recommendations(person, limit=3)
    
    # Generar recomendaciones personalizadas
    personal_recommendations = _generate_personal_recommendations(person, skill_gaps)
    
    # Generar ruta de desarrollo
    development_path = _generate_development_path(skill_gaps)
    
    # Definimos datos base comunes para todas las audiencias
    base_data = {
        'id': person.id,
        'name': f"{person.nombre} {person.apellido}",
        'current_role': current_role,
        'current_company': getattr(person, 'empresa_actual', '') or 'Empresa',
        'last_updated': timezone.now().strftime('%Y-%m-%d'),
        'experience_years': getattr(person, 'years_experience', 3) or 3,
        'current_skills': skill_gaps['candidate_skills'],
        'target_skills': skill_gaps['target_skills'],
        'skill_gaps': skill_gaps['missing_skills'],
    }
    
    # Configuramos datos específicos según audiencia
    if audience_type == 'consultant':
        # Para consultores: datos completos con métricas internas y análisis detallado
        return {
            **base_data,
            'current_match': skill_gaps['match_percentage'],
            'growth_potential': int(skill_gaps['development_potential'] * 100),
            'development_time_months': skill_gaps['development_time_months'],
            'development_path': development_path,
            'recommended_resources': resources,
            'career_path': career_path,
            'recommended_vacancies': recommended_vacancies,
            'personalized_recommendations': personal_recommendations,
            'extra_skills': skill_gaps.get('extra_skills', []),
            'analytics': {
                'development_complexity': _calculate_development_complexity(skill_gaps),
                'market_demand': _calculate_market_demand(skill_gaps),
                'salary_impact': _calculate_salary_impact(skill_gaps),
                'time_investment_roi': _calculate_time_investment_roi(skill_gaps)
            }
        }
    elif audience_type == 'client':
        # Para clientes: enfoque en potencial y valor, sin métricas detalladas
        adjusted_career_path = career_path.copy() if career_path else []
        # Eliminamos la probabilidad exacta para clientes
        for path in adjusted_career_path:
            path['match'] = _categorize_match_for_client(path.get('match', 0))
        
        return {
            **base_data,
            'current_match': _categorize_match_for_client(skill_gaps['match_percentage']),
            'growth_potential': _categorize_potential_for_client(skill_gaps['development_potential']),
            'development_path': [path for path in development_path if path.get('status') != 'future'],
            'key_strengths': _extract_key_strengths(skill_gaps),
            'development_areas': _extract_development_areas(skill_gaps),
            'career_path': adjusted_career_path[:2],  # Limitamos a 2 pasos próximos
            'organizational_fit': _calculate_organizational_fit(person),
            'time_to_proficiency': _categorize_time_to_proficiency(skill_gaps)
        }
    else:  # 'candidate'
        # Para candidatos: enfoque en desarrollo personal, aprendizaje y crecimiento
        return {
            **base_data,
            'development_path': development_path,
            'recommended_resources': resources,
            'career_path': career_path[:2],  # Limitamos a 2 pasos próximos
            'personalized_recommendations': personal_recommendations,
            'strengths': _extract_key_strengths(skill_gaps),
            'growth_areas': _extract_development_areas(skill_gaps),
            'estimated_timeline': skill_gaps['development_time_months'],
            'learning_path': _generate_learning_path(skill_gaps)
        }

# Funciones auxiliares internas para análisis de brechas

# Funciones auxiliares para categorización por audiencia
def _categorize_match_for_client(match_percentage):
    """Categoriza el porcentaje de match para clientes de forma cualitativa."""
    if match_percentage >= 85:
        return "Alto"
    elif match_percentage >= 70:
        return "Medio-Alto"
    elif match_percentage >= 50:
        return "Medio"
    else:
        return "En desarrollo"

def _categorize_potential_for_client(potential):
    """Categoriza el potencial para clientes de forma cualitativa."""
    potential_percentage = int(potential * 100)
    if potential_percentage >= 80:
        return "Excepcional"
    elif potential_percentage >= 65:
        return "Alto"
    elif potential_percentage >= 50:
        return "Medio"
    else:
        return "Moderado"

def _extract_key_strengths(skill_gaps):
    """Extrae fortalezas clave basadas en habilidades actuales y coincidentes."""
    common_skills = skill_gaps.get('common_skills', [])
    candidate_skills = skill_gaps.get('candidate_skills', [])
    
    # Priorizamos habilidades coincidentes y completamos con otras si es necesario
    if common_skills:
        strengths = common_skills[:3]  # Top 3 habilidades coincidentes
    else:
        strengths = []
    
    # Si necesitamos más fortalezas, añadimos del resto de habilidades del candidato
    if len(strengths) < 3 and candidate_skills:
        additional = [s for s in candidate_skills if s not in strengths][:3-len(strengths)]
        strengths.extend(additional)
    
    return strengths

def _extract_development_areas(skill_gaps):
    """Extrae áreas de desarrollo basadas en habilidades faltantes."""
    missing_skills = skill_gaps.get('missing_skills', [])
    return missing_skills[:3]  # Top 3 habilidades a desarrollar

def _calculate_organizational_fit(person):
    """Calcula el ajuste organizacional (dummy para demostración)."""
    # En producción, esto analizaría factores como cultura, valores, experiencia previa
    return "Alto"

def _categorize_time_to_proficiency(skill_gaps):
    """Categoriza el tiempo estimado para alcanzar competencia."""
    months = skill_gaps.get('development_time_months', 6)
    if months <= 2:
        return "Corto (1-2 meses)"
    elif months <= 6:
        return "Medio (3-6 meses)"
    else:
        return "Largo (6+ meses)"

def _calculate_development_complexity(skill_gaps):
    """Calcula la complejidad de desarrollo basada en habilidades faltantes."""
    missing_skills = skill_gaps.get('missing_skills', [])
    
    # Habilidades consideradas complejas (en producción vendría de una base de conocimiento)
    complex_skills = ["Machine Learning", "AWS", "Kubernetes", "Arquitectura de Software", "Data Science"]
    
    # Contar cuántas habilidades complejas faltan
    complex_count = sum(1 for skill in missing_skills if skill in complex_skills)
    
    if complex_count == 0:
        return "Baja"
    elif complex_count <= 2:
        return "Media"
    else:
        return "Alta"

def _calculate_market_demand(skill_gaps):
    """Calcula la demanda del mercado para las habilidades objetivo."""
    target_skills = skill_gaps.get('target_skills', [])
    
    # Habilidades con alta demanda (en producción vendría de análisis del mercado)
    high_demand_skills = ["Python", "JavaScript", "AWS", "React", "Docker", "Kubernetes", "Machine Learning"]
    
    # Contar cuántas habilidades de alta demanda hay en las objetivo
    demand_count = sum(1 for skill in target_skills if skill in high_demand_skills)
    demand_percentage = (demand_count / len(target_skills)) * 100 if target_skills else 0
    
    if demand_percentage >= 70:
        return "Alta"
    elif demand_percentage >= 40:
        return "Media"
    else:
        return "Baja"

def _calculate_salary_impact(skill_gaps):
    """Estima el impacto salarial de adquirir las habilidades faltantes."""
    missing_skills = skill_gaps.get('missing_skills', [])
    
    # Habilidades con alto impacto salarial (en producción vendría de datos del mercado)
    high_impact_skills = ["Machine Learning", "AWS", "Kubernetes", "Data Science", "React Native"]
    
    # Contar cuántas habilidades de alto impacto faltan
    impact_count = sum(1 for skill in missing_skills if skill in high_impact_skills)
    
    if impact_count >= 2:
        return "Alto (+20%)"
    elif impact_count >= 1:
        return "Medio (+10-15%)"
    else:
        return "Bajo (+5-10%)"

def _calculate_time_investment_roi(skill_gaps):
    """Calcula el retorno de inversión del tiempo de desarrollo."""
    # Simplificación para demo - en producción usaríamos múltiples factores
    development_time = skill_gaps.get('development_time_months', 6)
    salary_impact = _calculate_salary_impact(skill_gaps)
    
    if development_time <= 3 and salary_impact == "Alto (+20%)":
        return "Excelente"
    elif development_time <= 6 and salary_impact in ["Alto (+20%)", "Medio (+10-15%)"]:
        return "Bueno"
    else:
        return "Moderado"

def _generate_learning_path(skill_gaps):
    """Genera una ruta de aprendizaje estructurada para el candidato."""
    missing_skills = skill_gaps.get('missing_skills', [])
    development_time = skill_gaps.get('development_time_months', 6)
    
    if not missing_skills:
        return [
            {
                "phase": "Actualización continua",
                "duration": "Permanente",
                "focus": "Mantenerse al día en tecnologías actuales",
                "activities": ["Blogs", "Podcasts", "Conferencias", "Networking"]
            }
        ]
    
    # Dividir el tiempo total en fases
    phase1_time = max(1, int(development_time * 0.3))  # 30% del tiempo
    phase2_time = max(1, int(development_time * 0.4))  # 40% del tiempo
    phase3_time = development_time - phase1_time - phase2_time  # Resto
    
    # Dividir habilidades por fases (prioridades)
    third = max(1, len(missing_skills) // 3)
    skills_phase1 = missing_skills[:third]
    skills_phase2 = missing_skills[third:2*third]
    skills_phase3 = missing_skills[2*third:]
    
    learning_path = [
        {
            "phase": "Fundamentos",
            "duration": f"{phase1_time} {'mes' if phase1_time == 1 else 'meses'}",
            "focus": "Adquirir conocimientos básicos y fundamentos",
            "skills": skills_phase1,
            "activities": ["Cursos en línea", "Tutoriales", "Libros introductorios"]
        },
        {
            "phase": "Práctica aplicada",
            "duration": f"{phase2_time} {'mes' if phase2_time == 1 else 'meses'}",
            "focus": "Aplicar conocimientos en proyectos prácticos",
            "skills": skills_phase2,
            "activities": ["Proyectos personales", "Ejercicios prácticos", "Contribución a proyectos open source"]
        }
    ]
    
    # Solo agregar fase 3 si hay habilidades para ella
    if skills_phase3:
        learning_path.append({
            "phase": "Especialización",
            "duration": f"{phase3_time} {'mes' if phase3_time == 1 else 'meses'}",
            "focus": "Profundizar conocimientos y desarrollar especialización",
            "skills": skills_phase3,
            "activities": ["Proyectos avanzados", "Mentoría", "Certificaciones", "Networking"]
        })
    
    return learning_path

# Funciones auxiliares internas

def _get_skills_for_role(role_name):
    """
    Obtiene habilidades típicas para un rol específico.
    En producción, esta información vendría de una base de conocimiento o modelo ML.
    
    Args:
        role_name: Nombre del rol
        
    Returns:
        Lista de habilidades típicas para ese rol
    """
    # Diccionario de ejemplo con habilidades por rol
    role_skills = {
        'Desarrollador': ['Python', 'JavaScript', 'Git', 'SQL'],
        'Senior Desarrollador': ['Python', 'JavaScript', 'Git', 'SQL', 'Docker', 'CI/CD', 'Arquitectura de Software'],
        'Tech Lead': ['Arquitectura de Software', 'Gestión de Proyectos', 'CI/CD', 'AWS', 'System Design', 'Mentoring'],
        'Engineering Manager': ['Liderazgo', 'Gestión de Proyectos', 'Scrum', 'Planificación Estratégica', 'Presupuestos'],
        'Product Manager': ['Análisis de Producto', 'UX', 'Estrategia', 'Priorización', 'Roadmapping'],
        'Data Scientist': ['Python', 'R', 'Machine Learning', 'SQL', 'Estadística', 'Visualización de Datos'],
        'DevOps Engineer': ['Docker', 'Kubernetes', 'CI/CD', 'Cloud', 'Linux', 'Scripting'],
        'QA Engineer': ['Selenium', 'Testing', 'SQL', 'Automatización', 'Gestión de Bugs'],
        'UI/UX Designer': ['Figma', 'UX Research', 'Wireframing', 'Usabilidad', 'Diseño Responsivo']
    }
    
    # Buscar el rol exacto o un rol similar
    for key in role_skills.keys():
        if key.lower() in role_name.lower() or role_name.lower() in key.lower():
            return role_skills[key]
    
    # Si no se encuentra, devolver habilidades generales
    return ['Comunicación', 'Resolución de Problemas', 'Trabajo en Equipo', 'Adaptabilidad', 'Organización']

def _generate_career_path(current_role):
    """
    Genera una trayectoria profesional basada en el rol actual.
    
    Args:
        current_role: Rol actual del candidato
        
    Returns:
        Lista de diccionarios con roles futuros
    """
    # Posibles trayectorias (en producción, esto vendría de un modelo más complejo)
    career_tracks = {
        'Desarrollador': [
            {'title': 'Senior Desarrollador', 'timeframe': '1-2 años', 'match': 85, 'badge_class': 'success'},
            {'title': 'Tech Lead', 'timeframe': '2-4 años', 'match': 70, 'badge_class': 'primary'},
            {'title': 'Engineering Manager', 'timeframe': '4-6 años', 'match': 55, 'badge_class': 'info'}
        ],
        'Diseñador': [
            {'title': 'Senior Diseñador', 'timeframe': '1-2 años', 'match': 85, 'badge_class': 'success'},
            {'title': 'Lead Designer', 'timeframe': '2-4 años', 'match': 75, 'badge_class': 'primary'},
            {'title': 'UX Director', 'timeframe': '4-6 años', 'match': 60, 'badge_class': 'info'}
        ],
        'Analista': [
            {'title': 'Senior Analista', 'timeframe': '1-2 años', 'match': 85, 'badge_class': 'success'},
            {'title': 'Data Scientist', 'timeframe': '2-3 años', 'match': 70, 'badge_class': 'primary'},
            {'title': 'Head of Analytics', 'timeframe': '4-5 años', 'match': 60, 'badge_class': 'info'}
        ]
    }
    
    # Buscar la trayectoria adecuada basada en el rol actual
    for key in career_tracks.keys():
        if key.lower() in current_role.lower():
            return career_tracks[key]
    
    # Trayectoria predeterminada si no se encuentra una específica
    return [
        {'title': 'Senior ' + current_role, 'timeframe': '1-2 años', 'match': 85, 'badge_class': 'success'},
        {'title': 'Lead ' + current_role, 'timeframe': '2-4 años', 'match': 70, 'badge_class': 'primary'},
        {'title': 'Director de ' + current_role, 'timeframe': '4-6 años', 'match': 55, 'badge_class': 'info'}
    ]

def _generate_learning_resources(missing_skills):
    """
    Genera recursos de aprendizaje recomendados para las habilidades faltantes.
    
    Args:
        missing_skills: Lista de habilidades faltantes
        
    Returns:
        Lista de recursos recomendados
    """
    # Ejemplo de recursos por habilidad (en producción esto vendría de una API o base de datos)
    skill_resources = {
        'Python': {
            'type': 'course',
            'title': 'Python para Ciencia de Datos y Machine Learning',
            'provider': 'Udemy',
            'description': 'Curso completo que cubre Python desde lo básico hasta aplicaciones avanzadas en ML.',
            'duration': '40 horas',
            'rating': 4.7,
            'reviews': 1243,
            'url': 'https://www.udemy.com/course/python-data-science-machine-learning/'
        },
        'AWS': {
            'type': 'certification',
            'title': 'AWS Certified Solutions Architect',
            'provider': 'Amazon Web Services',
            'description': 'Certificación que valida tu capacidad para diseñar sistemas en AWS.',
            'duration': '3 meses',
            'rating': 4.9,
            'reviews': 856,
            'url': 'https://aws.amazon.com/certification/solutions-architect-associate/'
        },
        'JavaScript': {
            'type': 'book',
            'title': 'Eloquent JavaScript',
            'provider': 'No Starch Press',
            'description': 'Una introducción moderna a la programación JavaScript.',
            'duration': 'N/A',
            'rating': 4.8,
            'reviews': 567,
            'url': 'https://eloquentjavascript.net/'
        },
        'Machine Learning': {
            'type': 'course',
            'title': 'Machine Learning de Stanford',
            'provider': 'Coursera',
            'description': 'El curso de ML más popular del mundo, impartido por Andrew Ng.',
            'duration': '60 horas',
            'rating': 4.9,
            'reviews': 12500,
            'url': 'https://www.coursera.org/learn/machine-learning'
        },
        'Docker': {
            'type': 'course',
            'title': 'Docker Mastery',
            'provider': 'Udemy',
            'description': 'Domina Docker desde cero con este curso práctico.',
            'duration': '18 horas',
            'rating': 4.7,
            'reviews': 3450,
            'url': 'https://www.udemy.com/course/docker-mastery/'
        }
    }
    
    resources = []
    for skill in missing_skills[:3]:  # Limitamos a 3 recursos
        if skill in skill_resources:
            resource = skill_resources[skill].copy()
            resource['skills'] = [skill]
            resources.append(resource)
    
    # Si no encontramos recursos específicos, agregamos uno genérico
    if not resources:
        resources.append({
            'type': 'course',
            'title': 'Desarrollo Profesional Continuo',
            'provider': 'LinkedIn Learning',
            'description': 'Curso general para mejorar habilidades profesionales y técnicas.',
            'duration': '15 horas',
            'rating': 4.5,
            'reviews': 867,
            'skills': missing_skills[:2] if missing_skills else ['Desarrollo Profesional'],
            'url': 'https://www.linkedin.com/learning/'
        })
    
    return resources

def _generate_personal_recommendations(person, skill_gaps):
    """
    Genera recomendaciones personalizadas basadas en el análisis del candidato.
    
    Args:
        person: Objeto Person del candidato
        skill_gaps: Análisis de brechas de habilidades
        
    Returns:
        Lista de recomendaciones personalizadas
    """
    # Lista de posibles recomendaciones
    recommendations = []
    
    # Recomendación basada en habilidades faltantes
    if skill_gaps['missing_skills']:
        top_skills = skill_gaps['missing_skills'][:3]
        recommendations.append({
            'title': 'Enfoque en Habilidades Clave',
            'description': f"Para mejorar tu empleabilidad, prioriza desarrollar: {', '.join(top_skills)}"
        })
    
    # Recomendación basada en el potencial de crecimiento
    if skill_gaps['development_potential'] > 0.7:
        recommendations.append({
            'title': 'Alto Potencial Detectado',
            'description': 'Tienes un excelente potencial para crecer profesionalmente. Considera roles más desafiantes.'
        })
    elif skill_gaps['development_potential'] > 0.4:
        recommendations.append({
            'title': 'Desarrollo Continuo',
            'description': 'Mantén un enfoque en aprendizaje continuo para mejorar tu perfil profesional.'
        })
    
    # Recomendación sobre certificaciones
    if any(skill in ['AWS', 'Azure', 'GCP', 'Kubernetes', 'Scrum', 'PMP'] for skill in skill_gaps['missing_skills']):
        recommendations.append({
            'title': 'Certificaciones Recomendadas',
            'description': 'Considera obtener certificaciones relevantes para validar tus conocimientos.'
        })
    
    # Recomendación sobre networking profesional
    recommendations.append({
        'title': 'Redes Profesionales',
        'description': 'Amplía tu red profesional participando en eventos y comunidades relacionadas con tu campo.'
    })
    
    return recommendations[:3]  # Limitar a 3 recomendaciones

def _generate_development_path(skill_gaps):
    """
    Genera una ruta de desarrollo basada en las brechas de habilidades.
    
    Args:
        skill_gaps: Análisis de brechas de habilidades
        
    Returns:
        Lista de etapas de desarrollo
    """
    missing_skills = skill_gaps['missing_skills']
    
    # Si no hay habilidades faltantes, crear un plan genérico
    if not missing_skills:
        return [
            {
                'title': 'Consolidación de Conocimientos',
                'timeframe': '1-3 meses',
                'description': 'Refuerza y profundiza en las habilidades que ya posees.',
                'skills': skill_gaps['candidate_skills'][:3],
                'status': 'current'
            },
            {
                'title': 'Exploración de Nuevas Tecnologías',
                'timeframe': '3-6 meses',
                'description': 'Explora tecnologías emergentes para mantenerte actualizado.',
                'skills': [],
                'status': 'future'
            }
        ]
    
    # Dividir las habilidades faltantes en grupos para crear etapas
    third = max(1, len(missing_skills) // 3)
    first_group = missing_skills[:third]
    second_group = missing_skills[third:2*third]
    third_group = missing_skills[2*third:]
    
    return [
        {
            'title': 'Adquisición de Habilidades Fundamentales',
            'timeframe': '1-3 meses',
            'description': 'Enfoque en adquirir conocimientos básicos en las tecnologías principales requeridas.',
            'skills': first_group,
            'status': 'completed' if not first_group else 'current'
        },
        {
            'title': 'Desarrollo de Competencias Avanzadas',
            'timeframe': '3-6 meses',
            'description': 'Profundizar en habilidades específicas y aplicarlas en contextos prácticos.',
            'skills': second_group,
            'status': 'future' if first_group else 'current'
        },
        {
            'title': 'Especialización y Aplicación Práctica',
            'timeframe': '6-12 meses',
            'description': 'Consolidar conocimientos y desarrollar un área de especialización.',
            'skills': third_group,
            'status': 'future'
        }
    ]

def get_ml_recommendations(request, board_id=None, column_id=None, card_id=None):
    """
    Función de utilidad para obtener diversas recomendaciones ML para mostrar en la UI Kanban.
    Puede ser llamada desde las vistas para enriquecer los contextos de plantilla.
    
    Args:
        request: Objeto request de Django
        board_id: ID opcional del tablero
        column_id: ID opcional de la columna 
        card_id: ID opcional de la tarjeta
        
    Returns:
        Diccionario con diversas recomendaciones según el contexto
    """
    results = {
        'recommended_candidates': [],
        'column_recommendation': None,
        'similar_cards': [],
        'priority_suggestions': []
    }
    
    # Determinar unidad de negocio basada en el usuario actual
    business_unit = None
    if hasattr(request.user, 'business_unit'):
        business_unit = request.user.business_unit
    
    # Inicializar integración ML
    ml_integration = KanbanMLIntegration(business_unit=business_unit)
    
    # Si tenemos una tarjeta, obtener recomendaciones específicas
    if card_id:
        try:
            card = KanbanCard.objects.get(id=card_id)
            
            # Obtener columna recomendada y similares
            best_column, confidence = ml_integration.predict_best_column_for_card(card)
            if best_column and confidence > 0.5:
                results['column_recommendation'] = {
                    'column_id': best_column.id,
                    'column_name': best_column.name,
                    'confidence': confidence,
                    'message': f"Recomendamos mover esta tarjeta a la columna '{best_column.name}'"
                }
            
            # Obtener tarjetas similares
            results['similar_cards'] = ml_integration.get_similar_cards(card)
        except KanbanCard.DoesNotExist:
            pass
    
    # Si tenemos una columna, obtener candidatos recomendados y prioridades
    if column_id:
        try:
            column = KanbanColumn.objects.get(id=column_id)
            results['recommended_candidates'] = ml_integration.get_recommended_candidates_for_column(column)
            results['priority_suggestions'] = ml_integration.prioritize_cards_in_column(column)
        except KanbanColumn.DoesNotExist:
            pass
    
    return results
