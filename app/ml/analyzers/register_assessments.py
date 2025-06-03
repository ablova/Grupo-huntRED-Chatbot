"""
Registro de assessments y modelos de ML para Grupo huntRED®

Este módulo registra todos los assessments y modelos de ML disponibles
al inicio de la aplicación.
"""
import logging
from pathlib import Path
import sys

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.ml.analyzers.assessment_registry import (
    AssessmentType,
    AssessmentMetadata,
    assessment_registry
)
from app.ml.models.cultural_fit_model import CulturalFitModel
from app.ml.models.personality_model import PersonalityModel
from app.ml.models.professional_model import ProfessionalModel
from app.ml.models.integrated_model import IntegratedModel

from app.ats.chatbot.workflow.assessments.personality.personality_workflow import PersonalityAssessment
from app.ats.chatbot.workflow.assessments.cultural.cultural_fit_workflow import CulturalFitWorkflow
from app.ats.chatbot.workflow.assessments.professional_dna.core import ProfessionalDNAWorkflow
from app.ats.chatbot.workflow.assessments.talent.talent_analysis_workflow import TalentAnalysisWorkflow

logger = logging.getLogger(__name__)

def register_assessments():
    """Registra todos los assessments disponibles."""
    
    # Registrar assessment de personalidad
    assessment_registry.register_assessment(
        AssessmentType.PERSONALITY,
        PersonalityAssessment,
        AssessmentMetadata(
            type=AssessmentType.PERSONALITY,
            name="Evaluación de Personalidad TIPI",
            description="Evaluación de rasgos de personalidad basada en el modelo TIPI",
            version="1.0.0",
            required_fields=["responses", "context"],
            output_fields=["traits", "insights", "recommendations"],
            ml_model="personality_model",
            dependencies=[]
        )
    )
    
    # Registrar assessment cultural
    assessment_registry.register_assessment(
        AssessmentType.CULTURAL,
        CulturalFitWorkflow,
        AssessmentMetadata(
            type=AssessmentType.CULTURAL,
            name="Evaluación de Compatibilidad Cultural",
            description="Evaluación de alineación con la cultura organizacional",
            version="1.0.0",
            required_fields=["responses", "business_unit"],
            output_fields=["dimensions", "compatibility", "insights"],
            ml_model="cultural_fit_model",
            dependencies=[]
        )
    )
    
    # Registrar assessment profesional
    assessment_registry.register_assessment(
        AssessmentType.PROFESSIONAL,
        ProfessionalDNAWorkflow,
        AssessmentMetadata(
            type=AssessmentType.PROFESSIONAL,
            name="Evaluación de ADN Profesional",
            description="Evaluación de competencias y habilidades profesionales",
            version="1.0.0",
            required_fields=["responses", "role"],
            output_fields=["competencies", "strengths", "development_areas"],
            ml_model="professional_model",
            dependencies=[]
        )
    )
    
    # Registrar assessment de talento
    assessment_registry.register_assessment(
        AssessmentType.TALENT,
        TalentAnalysisWorkflow,
        AssessmentMetadata(
            type=AssessmentType.TALENT,
            name="Análisis de Talento",
            description="Evaluación integral de potencial y desarrollo",
            version="1.0.0",
            required_fields=["responses", "career_goals"],
            output_fields=["potential", "development_plan", "recommendations"],
            ml_model="talent_model",
            dependencies=["personality", "cultural", "professional"]
        )
    )
    
    logger.info("Assessments registrados exitosamente")

def register_ml_models():
    """Registra todos los modelos de ML disponibles."""
    
    # Registrar modelo de compatibilidad cultural
    cultural_model = CulturalFitModel()
    assessment_registry.register_ml_model("cultural_fit_model", cultural_model)
    
    # Registrar modelo de personalidad
    personality_model = PersonalityModel()
    assessment_registry.register_ml_model("personality_model", personality_model)
    
    # Registrar modelo profesional
    professional_model = ProfessionalModel()
    assessment_registry.register_ml_model("professional_model", professional_model)
    
    # Registrar modelo integrado
    integrated_model = IntegratedModel()
    assessment_registry.register_ml_model("integrated_analysis", integrated_model)
    
    logger.info("Modelos ML registrados exitosamente")

def initialize_assessment_system():
    """Inicializa el sistema de assessments."""
    try:
        register_assessments()
        register_ml_models()
        logger.info("Sistema de assessments inicializado exitosamente")
    except Exception as e:
        logger.error(f"Error inicializando sistema de assessments: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_assessment_system() 