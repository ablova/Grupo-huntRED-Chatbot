"""
Módulo de evaluación de personalidad.
"""
from app.com.chatbot.workflow.assessments.personality.personality_workflow import (
    get_questions_personality,
    get_random_tipi_questions,
    analyze_personality_responses
)

class PersonalityAssessment:
    """Clase para manejar la evaluación de personalidad."""
    
    def __init__(self):
        self.test_questions = get_questions_personality
        self.tipi_questions = get_random_tipi_questions
        self.analyze = analyze_personality_responses

__all__ = ['PersonalityAssessment']
