# app/ats/chatbot/workflow/assessments/professional_dna/questions.py
"""
Módulo de preguntas para la evaluación de personalidad avanzada.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------
# NOTA IMPORTANTE SOBRE BusinessUnit:
# ---------------------------------------------
# Este archivo NO define BusinessUnit.
# Para lógica de negocio y análisis, usa el Enum BusinessUnit
# definido en: app/ats/chatbot/integrations/matchmaking/factors.py
# Para operaciones de base de datos, usa el modelo BusinessUnit
# definido en: app/models.py
#
# Ejemplo de importación del Enum:
# from app.ats.chatbot.integrations.matchmaking.factors import BusinessUnit
# ---------------------------------------------

class QuestionType(Enum):
    RATING = "rating"
    MULTIPLE_CHOICE = "multiple_choice"
    BOOLEAN = "boolean"
    TEXT = "text"

class QuestionCategory(Enum):
    """Categorías de preguntas para el análisis Professional DNA."""
    LEADERSHIP = "leadership"
    INNOVATION = "innovation"
    COMMUNICATION = "communication"
    RESILIENCE = "resilience"
    RESULTS = "results"
    PERSONALITY = "personality"
    DERAILERS = "derailers"
    VALUES = "values"

@dataclass
class Question:
    id: str
    text: str
    type: QuestionType
    weight: float
    options: Optional[List[Any]] = None  # Puede ser List[Dict[str, Any]] o List[str]
    max_selections: Optional[int] = None
    category: Optional[QuestionCategory] = None
    weights: Optional[Dict[str, float]] = None
    difficulty_level: Optional[str] = None
    dimensions: Optional[List[str]] = None

class PersonalityQuestions:
    """Clase para gestionar las preguntas de personalidad."""
    
    def __init__(self):
        self.questions = {
            'adjustment': [
                Question(
                    id='stress_management',
                    text='¿Cómo manejas situaciones de alta presión?',
                    type=QuestionType.RATING,
                    weight=1.0,
                    options=[
                        {'value': 1, 'label': '⭐ Muy difícil'},
                        {'value': 2, 'label': '⭐⭐ Difícil'},
                        {'value': 3, 'label': '⭐⭐⭐ Neutral'},
                        {'value': 4, 'label': '⭐⭐⭐⭐ Bien'},
                        {'value': 5, 'label': '⭐⭐⭐⭐⭐ Excelente'}
                    ]
                ),
                Question(
                    id='emotional_stability',
                    text='¿Cómo describirías tu estabilidad emocional?',
                    type=QuestionType.MULTIPLE_CHOICE,
                    weight=0.9,
                    options=[
                        '😌 Muy estable',
                        '😊 Generalmente estable',
                        '😐 Variable',
                        '😔 Inestable',
                        '😢 Muy inestable'
                    ],
                    max_selections=2
                )
            ],
            'ambition': [
                Question(
                    id='career_goals',
                    text='¿Qué tan ambicioso/a eres con tus metas profesionales?',
                    type=QuestionType.RATING,
                    weight=1.0,
                    options=[
                        {'value': 1, 'label': '⭐ No ambicioso'},
                        {'value': 2, 'label': '⭐⭐ Poco ambicioso'},
                        {'value': 3, 'label': '⭐⭐⭐ Moderadamente ambicioso'},
                        {'value': 4, 'label': '⭐⭐⭐⭐ Muy ambicioso'},
                        {'value': 5, 'label': '⭐⭐⭐⭐⭐ Extremadamente ambicioso'}
                    ]
                ),
                Question(
                    id='achievement_orientation',
                    text='¿Qué te motiva más en tu carrera?',
                    type=QuestionType.MULTIPLE_CHOICE,
                    weight=0.9,
                    options=[
                        '🎯 Logro de objetivos',
                        '💼 Progreso profesional',
                        '💰 Compensación económica',
                        '🌟 Reconocimiento',
                        '🤝 Impacto en otros'
                    ],
                    max_selections=3
                )
            ],
            'sociability': [
                Question(
                    id='social_interaction',
                    text='¿Cómo te sientes en situaciones sociales?',
                    type=QuestionType.RATING,
                    weight=1.0,
                    options=[
                        {'value': 1, 'label': '⭐ Muy incómodo'},
                        {'value': 2, 'label': '⭐⭐ Incómodo'},
                        {'value': 3, 'label': '⭐⭐⭐ Neutral'},
                        {'value': 4, 'label': '⭐⭐⭐⭐ Cómodo'},
                        {'value': 5, 'label': '⭐⭐⭐⭐⭐ Muy cómodo'}
                    ]
                ),
                Question(
                    id='team_preference',
                    text='¿Cómo prefieres trabajar?',
                    type=QuestionType.MULTIPLE_CHOICE,
                    weight=0.9,
                    options=[
                        '👥 En equipo',
                        '👤 Individualmente',
                        '🤝 Colaborativamente',
                        '🎯 Por objetivos',
                        '🔄 Rotando roles'
                    ],
                    max_selections=2
                )
            ]
        }
    
    def get_questions(self, dimension: str) -> List[Question]:
        """Obtiene las preguntas para una dimensión específica."""
        return self.questions.get(dimension, [])

class DerailerQuestions:
    """Clase para gestionar las preguntas sobre derailers."""
    
    def __init__(self):
        self.questions = {
            'excitable': [
                Question(
                    id='emotional_reaction',
                    text='¿Cómo reaccionas ante situaciones estresantes?',
                    type=QuestionType.RATING,
                    weight=1.0,
                    options=[
                        {'value': 1, 'label': '⭐ Muy calmado'},
                        {'value': 2, 'label': '⭐⭐ Calmado'},
                        {'value': 3, 'label': '⭐⭐⭐ Neutral'},
                        {'value': 4, 'label': '⭐⭐⭐⭐ Reactivo'},
                        {'value': 5, 'label': '⭐⭐⭐⭐⭐ Muy reactivo'}
                    ]
                ),
                Question(
                    id='stress_coping',
                    text='¿Qué haces cuando te sientes estresado/a?',
                    type=QuestionType.MULTIPLE_CHOICE,
                    weight=0.9,
                    options=[
                        '🧘‍♂️ Meditar',
                        '🏃‍♂️ Ejercicio',
                        '😤 Expresar frustración',
                        '🤐 Aislarme',
                        '💭 Analizar la situación'
                    ],
                    max_selections=3
                )
            ],
            'skeptical': [
                Question(
                    id='trust_level',
                    text='¿Qué tan confiado/a eres en general?',
                    type=QuestionType.RATING,
                    weight=1.0,
                    options=[
                        {'value': 1, 'label': '⭐ Muy confiado'},
                        {'value': 2, 'label': '⭐⭐ Confiado'},
                        {'value': 3, 'label': '⭐⭐⭐ Neutral'},
                        {'value': 4, 'label': '⭐⭐⭐⭐ Escéptico'},
                        {'value': 5, 'label': '⭐⭐⭐⭐⭐ Muy escéptico'}
                    ]
                ),
                Question(
                    id='decision_making',
                    text='¿Cómo tomas decisiones importantes?',
                    type=QuestionType.MULTIPLE_CHOICE,
                    weight=0.9,
                    options=[
                        '🔍 Analizando datos',
                        '👥 Consultando a otros',
                        '❓ Cuestionando todo',
                        '⚡ Instintivamente',
                        '📊 Evaluando riesgos'
                    ],
                    max_selections=3
                )
            ]
        }
    
    def get_questions(self, dimension: str) -> List[Question]:
        """Obtiene las preguntas para una dimensión específica."""
        return self.questions.get(dimension, [])

class ValueQuestions:
    """Clase para gestionar las preguntas sobre valores."""
    
    def __init__(self):
        self.questions = {
            'recognition': [
                Question(
                    id='recognition_importance',
                    text='¿Qué tan importante es el reconocimiento para ti?',
                    type=QuestionType.RATING,
                    weight=1.0,
                    options=[
                        {'value': 1, 'label': '⭐ No importante'},
                        {'value': 2, 'label': '⭐⭐ Poco importante'},
                        {'value': 3, 'label': '⭐⭐⭐ Moderadamente importante'},
                        {'value': 4, 'label': '⭐⭐⭐⭐ Muy importante'},
                        {'value': 5, 'label': '⭐⭐⭐⭐⭐ Extremadamente importante'}
                    ]
                ),
                Question(
                    id='recognition_type',
                    text='¿Qué tipo de reconocimiento valoras más?',
                    type=QuestionType.MULTIPLE_CHOICE,
                    weight=0.9,
                    options=[
                        '🏆 Premios formales',
                        '👏 Reconocimiento público',
                        '💬 Feedback positivo',
                        '💰 Incentivos económicos',
                        '🌟 Logros personales'
                    ],
                    max_selections=3
                )
            ],
            'power': [
                Question(
                    id='influence_importance',
                    text='¿Qué tan importante es tener influencia para ti?',
                    type=QuestionType.RATING,
                    weight=1.0,
                    options=[
                        {'value': 1, 'label': '⭐ No importante'},
                        {'value': 2, 'label': '⭐⭐ Poco importante'},
                        {'value': 3, 'label': '⭐⭐⭐ Moderadamente importante'},
                        {'value': 4, 'label': '⭐⭐⭐⭐ Muy importante'},
                        {'value': 5, 'label': '⭐⭐⭐⭐⭐ Extremadamente importante'}
                    ]
                ),
                Question(
                    id='leadership_style',
                    text='¿Cómo te gustaría ejercer el liderazgo?',
                    type=QuestionType.MULTIPLE_CHOICE,
                    weight=0.9,
                    options=[
                        '👑 Autoritario',
                        '🤝 Democrático',
                        '🎯 Orientado a resultados',
                        '💡 Innovador',
                        '👥 Colaborativo'
                    ],
                    max_selections=3
                )
            ]
        }
    
    def get_questions(self, dimension: str) -> List[Question]:
        """Obtiene las preguntas para una dimensión específica."""
        return self.questions.get(dimension, [])

class AdvancedAssessmentQuestions:
    """Clase principal para gestionar todas las preguntas de la evaluación."""
    
    def __init__(self):
        self.personality = PersonalityQuestions()
        self.derailers = DerailerQuestions()
        self.values = ValueQuestions()
    
    def get_all_questions(self) -> Dict[str, Any]:
        """Obtiene todas las preguntas organizadas por categoría."""
        return {
            'personality': {
                dimension: self.personality.get_questions(dimension)
                for dimension in self.personality.questions.keys()
            },
            'derailers': {
                dimension: self.derailers.get_questions(dimension)
                for dimension in self.derailers.questions.keys()
            },
            'values': {
                dimension: self.values.get_questions(dimension)
                for dimension in self.values.questions.keys()
            }
        }
    
    def get_questions_by_dimension(self, dimension: str) -> List[Question]:
        """Obtiene todas las preguntas para una dimensión específica."""
        questions = []
        
        # Buscar en personalidad
        if dimension in self.personality.questions:
            questions.extend(self.personality.get_questions(dimension))
        
        # Buscar en derailers
        if dimension in self.derailers.questions:
            questions.extend(self.derailers.get_questions(dimension))
        
        # Buscar en valores
        if dimension in self.values.questions:
            questions.extend(self.values.get_questions(dimension))
        
        return questions 