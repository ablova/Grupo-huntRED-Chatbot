"""
Módulo de preguntas para la evaluación de planes de sucesión.

Este módulo define las preguntas y cuestionarios utilizados para evaluar
la preparación de los candidatos en los planes de sucesión.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

class QuestionCategory(str, Enum):
    """Categorías de preguntas para la evaluación de sucesión."""
    LEADERSHIP = "liderazgo"
    TECHNICAL_SKILLS = "habilidades_tecnicas"
    STRATEGIC_THINKING = "pensamiento_estrategico"
    BUSINESS_ACUMEN = "conocimiento_negocio"
    CHANGE_MANAGEMENT = "gestion_cambio"
    TEAM_DEVELOPMENT = "desarrollo_equipo"
    COMMUNICATION = "comunicacion"
    RESULTS_ORIENTATION = "orientacion_resultados"


@dataclass
class AssessmentQuestion:
    """Clase que representa una pregunta de evaluación."""
    id: str
    category: QuestionCategory
    question_text: str
    description: Optional[str] = None
    weight: float = 1.0
    options: List[Dict[str, Any]] = field(default_factory=list)
    required: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la pregunta a un diccionario."""
        return {
            'id': self.id,
            'category': self.category.value,
            'question_text': self.question_text,
            'description': self.description,
            'weight': self.weight,
            'options': self.options,
            'required': self.required
        }


class SuccessionQuestionnaire:
    """Cuestionario para evaluar la preparación para la sucesión."""
    
    def __init__(self, position_level: str = "manager"):
        """
        Inicializa el cuestionario.
        
        Args:
            position_level: Nivel del puesto ('entry', 'manager', 'director', 'c_level')
        """
        self.position_level = position_level
        self.questions: List[AssessmentQuestion] = []
        self._initialize_questions()
    
    def _initialize_questions(self) -> None:
        """Inicializa las preguntas según el nivel del puesto."""
        # Preguntas base para todos los niveles
        base_questions = [
            AssessmentQuestion(
                id="leadership_vision",
                category=QuestionCategory.LEADERSHIP,
                question_text="¿Con qué frecuencia inspira y motiva a su equipo para alcanzar objetivos desafiantes?",
                description="Evalúa la capacidad de inspirar y motivar al equipo.",
                weight=1.2,
                options=[
                    {"value": 1, "text": "Rara vez o nunca"},
                    {"value": 2, "text": "Algunas veces"},
                    {"value": 3, "text": "Frecuentemente"},
                    {"value": 4, "text": "Casi siempre"},
                    {"value": 5, "text": "Siempre"}
                ]
            ),
            AssessmentQuestion(
                id="strategic_thinking",
                category=QuestionCategory.STRATEGIC_THINKING,
                question_text="¿Con qué frecuencia anticipa tendencias futuras y desarrolla estrategias efectivas?",
                weight=1.1
            ),
            AssessmentQuestion(
                id="business_acumen",
                category=QuestionCategory.BUSINESS_ACUMEN,
                question_text="¿Cómo calificaría su comprensión del modelo de negocio y la industria?",
                weight=1.0
            )
        ]
        
        # Preguntas específicas por nivel
        level_specific = []
        
        if self.position_level in ["manager", "director", "c_level"]:
            level_specific.extend([
                AssessmentQuestion(
                    id="team_development",
                    category=QuestionCategory.TEAM_DEVELOPMENT,
                    question_text="¿Con qué frecuencia identifica y desarrolla el talento en su equipo?",
                    weight=1.3 if self.position_level == "manager" else 1.1
                ),
                AssessmentQuestion(
                    id="change_management",
                    category=QuestionCategory.CHANGE_MANAGEMENT,
                    question_text="¿Cómo maneja los procesos de cambio organizacional?",
                    weight=1.2
                )
            ])
            
        if self.position_level in ["director", "c_level"]:
            level_specific.extend([
                AssessmentQuestion(
                    id="organizational_strategy",
                    category=QuestionCategory.STRATEGIC_THINKING,
                    question_text="¿Cómo contribuye a la definición de la estrategia organizacional?",
                    weight=1.4
                ),
                AssessmentQuestion(
                    id="stakeholder_management",
                    category=QuestionCategory.COMMUNICATION,
                    question_text="¿Cómo maneja las relaciones con los grupos de interés clave?",
                    weight=1.3
                )
            ])
            
        if self.position_level == "c_level":
            level_specific.extend([
                AssessmentQuestion(
                    id="corporate_vision",
                    category=QuestionCategory.LEADERSHIP,
                    question_text="¿Cómo define y comunica la visión corporativa?",
                    weight=1.5
                ),
                AssessmentQuestion(
                    id="shareholder_value",
                    category=QuestionCategory.BUSINESS_ACUMEN,
                    question_text="¿Cómo contribuye a la creación de valor para los accionistas?",
                    weight=1.4
                )
            ])
        
        self.questions = base_questions + level_specific
    
    def get_questions(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las preguntas del cuestionario.
        
        Returns:
            Lista de diccionarios con las preguntas
        """
        return [q.to_dict() for q in self.questions]
    
    def get_questions_by_category(self, category: QuestionCategory) -> List[Dict[str, Any]]:
        """
        Obtiene las preguntas de una categoría específica.
        
        Args:
            category: Categoría de las preguntas a obtener
            
        Returns:
            Lista de diccionarios con las preguntas de la categoría
        """
        return [
            q.to_dict() 
            for q in self.questions 
            if q.category == category
        ]
    
    def calculate_scores(self, answers: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcula las puntuaciones por categoría basadas en las respuestas.
        
        Args:
            answers: Diccionario con las respuestas (pregunta_id: valor)
            
        Returns:
            Diccionario con las puntuaciones por categoría
        """
        category_scores = {cat.value: {"total": 0, "weight": 0, "count": 0} 
                          for cat in QuestionCategory}
        
        for question in self.questions:
            if question.id in answers:
                cat = question.category.value
                answer_value = answers[question.id]
                weight = question.weight
                
                # Actualizar totales por categoría
                category_scores[cat]["total"] += answer_value * weight
                category_scores[cat]["weight"] += weight
                category_scores[cat]["count"] += 1
        
        # Calcular promedios ponderados
        result = {}
        for cat, scores in category_scores.items():
            if scores["count"] > 0:
                result[cat] = {
                    "score": scores["total"] / scores["weight"],
                    "question_count": scores["count"]
                }
        
        return result
    
    def generate_development_recommendations(
        self, 
        category_scores: Dict[str, Dict[str, float]]
    ) -> Dict[str, List[str]]:
        """
        Genera recomendaciones de desarrollo basadas en las puntuaciones.
        
        Args:
            category_scores: Puntuaciones por categoría
            
        Returns:
            Diccionario con recomendaciones por categoría
        """
        recommendations = {}
        
        for cat, scores in category_scores.items():
            score = scores["score"]
            cat_recommendations = []
            
            if score < 2.5:  # Área de mejora significativa
                cat_recommendations.extend(self._get_recommendations(cat, "low"))
            elif score < 3.5:  # Área de mejora moderada
                cat_recommendations.extend(self._get_recommendations(cat, "medium"))
            else:  # Área de fortaleza
                cat_recommendations.extend(self._get_recommendations(cat, "high"))
            
            if cat_recommendations:
                recommendations[cat] = cat_recommendations
        
        return recommendations
    
    def _get_recommendations(self, category: str, level: str) -> List[str]:
        """
        Obtiene recomendaciones específicas para una categoría y nivel de puntuación.
        
        Args:
            category: Categoría de la competencia
            level: Nivel de puntuación ('low', 'medium', 'high')
            
        Returns:
            Lista de recomendaciones
        """
        # Este es un ejemplo básico - en una implementación real, esto podría
        # provenir de una base de conocimiento o ser más detallado
        
        recommendations = {
            "liderazgo": {
                "low": [
                    "Tomar un curso de liderazgo básico",
                    "Buscar un mentor con experiencia en liderazgo",
                    "Leer libros sobre estilos de liderazgo"
                ],
                "medium": [
                    "Participar en proyectos que requieran liderazgo de equipos",
                    "Recibir retroalimentación 360° sobre habilidades de liderazgo"
                ],
                "high": [
                    "Mentorar a otros en desarrollo de liderazgo",
                    "Liderar iniciativas estratégicas"
                ]
            },
            "habilidades_tecnicas": {
                "low": [
                    "Tomar cursos de actualización técnica",
                    "Buscar certificaciones relevantes"
                ],
                "medium": [
                    "Participar en proyectos que requieran habilidades técnicas avanzadas",
                    "Enseñar a otros para reforzar el conocimiento"
                ],
                "high": [
                    "Mentorar a otros en habilidades técnicas",
                    "Participar en grupos de expertos"
                ]
            },
            # Agregar más categorías según sea necesario
        }
        
        return recommendations.get(category, {}).get(level, [])
