from pathlib import Path
import importlib.util
import logging
from typing import Dict, Type, Optional

logger = logging.getLogger(__name__)


class AssessmentRegistry:
    """
    Registro dinámico de evaluaciones disponibles en el sistema.
    """
    _assessments: Dict[str, Type['BaseAssessment']] = {}

    @classmethod
    def register(cls, assessment_class: Type['BaseAssessment']):
        """Registra una nueva evaluación en el sistema."""
        assessment_id = assessment_class.assessment_id
        if assessment_id in cls._assessments:
            logger.warning(f"Assessment '{assessment_id}' ya está registrado. Sobrescribiendo.")
        cls._assessments[assessment_id] = assessment_class
        return assessment_class

    @classmethod
    def get_assessment(cls, assessment_id: str) -> Optional[Type['BaseAssessment']]:
        """Obtiene una clase de evaluación por su ID."""
        return cls._assessments.get(assessment_id)

    @classmethod
    def get_all_assessments(cls) -> Dict[str, Type['BaseAssessment']]:
        """Obtiene todas las evaluaciones registradas."""
        return dict(cls._assessments)

    @classmethod
    def discover_assessments(cls, base_path: str):
        """
        Descubre automáticamente evaluaciones en subdirectorios.
        Cada evaluación debe tener un archivo __init__.py que exponga la clase de la evaluación.
        """
        base_dir = Path(base_path)
        for item in base_dir.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                try:
                    init_file = item / '__init__.py'
                    if init_file.exists():
                        module_name = f"app.ats.chatbot.workflow.assessments.{item.name}"
                        spec = importlib.util.spec_from_file_location(module_name, init_file)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        logger.info(f"Módulo de evaluación cargado: {module_name}")
                except Exception as e:
                    logger.error(f"Error cargando evaluación {item.name}: {str(e)}", exc_info=True)


# Alias para facilitar el registro
def register_assessment(assessment_class):
    """Decorador para registrar una evaluación."""
    return AssessmentRegistry.register(assessment_class)


# Cargar evaluaciones al importar el módulo
AssessmentRegistry.discover_assessments(Path(__file__).parent)
