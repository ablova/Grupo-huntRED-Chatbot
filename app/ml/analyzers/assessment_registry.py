"""
Registro centralizado de assessments para Grupo huntRED®

Este módulo proporciona un registro dinámico de todos los tipos de assessments
disponibles, permitiendo su integración con el chatbot y el sistema de ML.
"""
import logging
from typing import Dict, List, Any, Optional, Type
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AssessmentType(Enum):
    """Tipos de assessments disponibles"""
    PERSONALITY = "personality"
    CULTURAL = "cultural"
    PROFESSIONAL = "professional"
    TALENT = "talent"
    MOBILITY = "mobility"
    GENERATIONAL = "generational"
    LEADERSHIP = "leadership"
    MOTIVATIONAL = "motivational"
    INTEGRATED = "integrated"

@dataclass
class AssessmentMetadata:
    """Metadatos de un assessment"""
    type: AssessmentType
    name: str
    description: str
    version: str
    required_fields: List[str]
    output_fields: List[str]
    ml_model: Optional[str] = None
    dependencies: List[str] = None

class BaseAssessment(ABC):
    """Clase base para todos los assessments"""
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> str:
        """Inicializa el assessment con el contexto proporcionado"""
        pass
        
    @abstractmethod
    def process_message(self, message: str) -> str:
        """Procesa un mensaje del usuario durante el assessment"""
        pass
        
    @abstractmethod
    def get_results(self) -> Dict[str, Any]:
        """Obtiene los resultados del assessment"""
        pass
        
    @abstractmethod
    def is_completed(self) -> bool:
        """Verifica si el assessment está completado"""
        pass

class AssessmentRegistry:
    """
    Registro centralizado de assessments.
    
    Permite registrar y acceder a diferentes tipos de assessments
    de manera dinámica.
    """
    
    def __init__(self):
        self._assessments: Dict[AssessmentType, Type[BaseAssessment]] = {}
        self._metadata: Dict[AssessmentType, AssessmentMetadata] = {}
        self._ml_models: Dict[str, Any] = {}
        
    def register_assessment(self, 
                          assessment_type: AssessmentType,
                          assessment_class: Type[BaseAssessment],
                          metadata: AssessmentMetadata) -> None:
        """
        Registra un nuevo tipo de assessment.
        
        Args:
            assessment_type: Tipo de assessment
            assessment_class: Clase que implementa el assessment
            metadata: Metadatos del assessment
        """
        self._assessments[assessment_type] = assessment_class
        self._metadata[assessment_type] = metadata
        logger.info(f"Assessment registrado: {assessment_type.value}")
        
    def get_assessment_class(self, assessment_type: AssessmentType) -> Optional[Type[BaseAssessment]]:
        """Obtiene la clase de un assessment por su tipo"""
        return self._assessments.get(assessment_type)
        
    def get_assessment_metadata(self, assessment_type: AssessmentType) -> Optional[AssessmentMetadata]:
        """Obtiene los metadatos de un assessment por su tipo"""
        return self._metadata.get(assessment_type)
        
    def register_ml_model(self, model_name: str, model: Any) -> None:
        """Registra un modelo de ML para su uso en assessments"""
        self._ml_models[model_name] = model
        logger.info(f"Modelo ML registrado: {model_name}")
        
    def get_ml_model(self, model_name: str) -> Optional[Any]:
        """Obtiene un modelo de ML por su nombre"""
        return self._ml_models.get(model_name)
        
    def get_available_assessments(self) -> List[AssessmentType]:
        """Obtiene la lista de assessments disponibles"""
        return list(self._assessments.keys())
        
    def get_assessment_dependencies(self, assessment_type: AssessmentType) -> List[str]:
        """Obtiene las dependencias de un assessment"""
        metadata = self._metadata.get(assessment_type)
        return metadata.dependencies if metadata else []
        
    def validate_assessment_data(self, 
                               assessment_type: AssessmentType,
                               data: Dict[str, Any]) -> bool:
        """
        Valida que los datos cumplan con los requisitos del assessment.
        
        Args:
            assessment_type: Tipo de assessment
            data: Datos a validar
            
        Returns:
            True si los datos son válidos, False en caso contrario
        """
        metadata = self._metadata.get(assessment_type)
        if not metadata:
            return False
            
        # Verificar campos requeridos
        for field in metadata.required_fields:
            if field not in data:
                logger.error(f"Campo requerido faltante: {field}")
                return False
                
        return True
        
    def get_assessment_output_schema(self, assessment_type: AssessmentType) -> List[str]:
        """Obtiene el esquema de salida de un assessment"""
        metadata = self._metadata.get(assessment_type)
        return metadata.output_fields if metadata else []
        
    def get_assessment_version(self, assessment_type: AssessmentType) -> Optional[str]:
        """Obtiene la versión de un assessment"""
        metadata = self._metadata.get(assessment_type)
        return metadata.version if metadata else None
        
    def get_assessment_description(self, assessment_type: AssessmentType) -> Optional[str]:
        """Obtiene la descripción de un assessment"""
        metadata = self._metadata.get(assessment_type)
        return metadata.description if metadata else None

# Instancia global del registro
assessment_registry = AssessmentRegistry() 