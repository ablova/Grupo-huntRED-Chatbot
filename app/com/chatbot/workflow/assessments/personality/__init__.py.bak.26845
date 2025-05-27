# /home/pablo/app/com/chatbot/workflow/assessments/personality/__init__.py
"""
Módulo de evaluación de personalidad.
"""
# Importamos directamente la clase PersonalityAssessment
from app.com.chatbot.workflow.assessments.personality.personality_workflow import PersonalityAssessment

# Exponemos TEST_QUESTIONS para compatibilidad con código existente
TEST_QUESTIONS = PersonalityAssessment.TEST_QUESTIONS

# Definimos adaptadores para mantener compatibilidad con código existente
def get_questions_personality(test_type="huntBigFive", domain="general", business_unit=None):
    """Adaptador para PersonalityAssessment.get_questions"""
    assessment = PersonalityAssessment()
    return assessment.get_questions(test_type, domain, business_unit)

def get_random_tipi_questions(domain="general", business_unit=None):
    """Adaptador para PersonalityAssessment.get_random_tipi_questions"""
    assessment = PersonalityAssessment()
    return assessment.get_random_tipi_questions(domain, business_unit)

def analyze_personality_responses(responses, business_unit=None):
    """Adaptador para PersonalityAssessment.analyze_responses"""
    assessment = PersonalityAssessment()
    return assessment.analyze_responses(responses, business_unit)

# Re-exportamos la clase principal para mantener compatibilidad
__all__ = ['PersonalityAssessment', 'get_questions_personality', 'get_random_tipi_questions', 'analyze_personality_responses', 'TEST_QUESTIONS']
