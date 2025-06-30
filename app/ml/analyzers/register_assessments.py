# /home/pablo/app/ml/analyzers/register_assessments.py
"""
Registro y gestión de evaluaciones.

Este módulo maneja el registro y la gestión de las diferentes evaluaciones
que se realizan en el sistema.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
import sys

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.ats.integrations.services.assessment import Assessment

from app.ml.core.models.assessments.cultural_fit_model import CulturalFitModel
from app.ml.core.models.assessments.personality_model import PersonalityModel
from app.ml.core.models.assessments.professional_model import ProfessionalModel
from app.ml.core.models.assessments.integrated_model import IntegratedModel

from app.ml.analyzers.assessment_registry import (
    AssessmentType,
    AssessmentMetadata,
    assessment_registry
)
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
    
    # Registrar assessment de movilidad (Amigro)
    assessment_registry.register_assessment(
        AssessmentType.MOBILITY,
        None,  # TODO: Implementar MobilityAssessment
        AssessmentMetadata(
            type=AssessmentType.MOBILITY,
            name="Análisis de Movilidad",
            description="Evalúa disposición y capacidad para la movilidad laboral",
            version="1.0.0",
            required_fields=["responses", "mobility_preferences"],
            output_fields=["mobility_score", "preferences", "recommendations"],
            ml_model="mobility_model",
            dependencies=[]
        )
    )
    
    # Registrar assessment generacional (Amigro)
    assessment_registry.register_assessment(
        AssessmentType.GENERATIONAL,
        None,  # TODO: Implementar GenerationalAssessment
        AssessmentMetadata(
            type=AssessmentType.GENERATIONAL,
            name="Análisis Generacional",
            description="Descubre cómo tu generación influye en tu perfil laboral",
            version="1.0.0",
            required_fields=["responses", "generation"],
            output_fields=["generational_traits", "work_style", "insights"],
            ml_model="generational_model",
            dependencies=[]
        )
    )
    
    # Registrar assessment de liderazgo (huntRED Executive)
    assessment_registry.register_assessment(
        AssessmentType.LEADERSHIP,
        None,  # TODO: Implementar LeadershipAssessment
        AssessmentMetadata(
            type=AssessmentType.LEADERSHIP,
            name="Estilo de Liderazgo",
            description="Descubre tu estilo de liderazgo natural y potencial",
            version="1.0.0",
            required_fields=["responses", "leadership_experience"],
            output_fields=["leadership_style", "strengths", "development_areas"],
            ml_model="leadership_model",
            dependencies=["personality", "professional"]
        )
    )
    
    # Registrar assessment motivacional
    assessment_registry.register_assessment(
        AssessmentType.MOTIVATIONAL,
        None,  # TODO: Implementar MotivationalAssessment
        AssessmentMetadata(
            type=AssessmentType.MOTIVATIONAL,
            name="Análisis Motivacional",
            description="Identifica tus motivadores principales en el trabajo",
            version="1.0.0",
            required_fields=["responses", "work_preferences"],
            output_fields=["motivators", "drivers", "recommendations"],
            ml_model="motivational_model",
            dependencies=[]
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
    
    # Registrar modelo de talento
    talent_model = TalentModel()
    assessment_registry.register_ml_model("talent_model", talent_model)
    
    # Registrar modelos específicos por Business Unit
    try:
        from app.ml.core.models.assessments.mobility_model import MobilityModel
        mobility_model = MobilityModel()
        assessment_registry.register_ml_model("mobility_model", mobility_model)
    except ImportError:
        logger.warning("MobilityModel no disponible")
    
    try:
        from app.ml.core.models.assessments.generational_model import GenerationalModel
        generational_model = GenerationalModel()
        assessment_registry.register_ml_model("generational_model", generational_model)
    except ImportError:
        logger.warning("GenerationalModel no disponible")
    
    try:
        from app.ml.core.models.assessments.leadership_model import LeadershipModel
        leadership_model = LeadershipModel()
        assessment_registry.register_ml_model("leadership_model", leadership_model)
    except ImportError:
        logger.warning("LeadershipModel no disponible")
    
    try:
        from app.ml.core.models.assessments.motivational_model import MotivationalModel
        motivational_model = MotivationalModel()
        assessment_registry.register_ml_model("motivational_model", motivational_model)
    except ImportError:
        logger.warning("MotivationalModel no disponible")
    
    logger.info("Modelos ML registrados exitosamente")

def initialize_assessment_system():
    """Inicializa todo el sistema de assessments."""
    try:
        # Registrar assessments
        register_assessments()
        
        # Registrar modelos ML
        register_ml_models()
        
        # Verificar integridad del sistema
        verify_system_integrity()
        
        logger.info("Sistema de assessments inicializado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando sistema de assessments: {str(e)}")
        return False

def verify_system_integrity():
    """Verifica la integridad del sistema de assessments."""
    try:
        # Verificar que todos los assessments tengan sus modelos ML correspondientes
        for assessment_type in AssessmentType:
            metadata = assessment_registry.get_assessment_metadata(assessment_type)
            if metadata and metadata.ml_model:
                model = assessment_registry.get_ml_model(metadata.ml_model)
                if not model:
                    logger.warning(f"Assessment {assessment_type.value} requiere modelo ML '{metadata.ml_model}' no registrado")
        
        # Verificar dependencias
        for assessment_type in AssessmentType:
            metadata = assessment_registry.get_assessment_metadata(assessment_type)
            if metadata and metadata.dependencies:
                for dep in metadata.dependencies:
                    dep_metadata = assessment_registry.get_assessment_metadata(AssessmentType(dep))
                    if not dep_metadata:
                        logger.warning(f"Assessment {assessment_type.value} depende de '{dep}' no registrado")
        
        logger.info("Verificación de integridad del sistema completada")
        
    except Exception as e:
        logger.error(f"Error en verificación de integridad: {str(e)}")

if __name__ == "__main__":
    initialize_assessment_system() 