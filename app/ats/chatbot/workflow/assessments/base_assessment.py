from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.models import User


class BaseAssessment(ABC):
    """
    Clase base abstracta que define la interfaz para todas las evaluaciones.
    """
    # Identificador único para la evaluación (debe ser sobrescrito)
    assessment_id = None
    
    # Nombre para mostrar en la interfaz
    display_name = ""
    
    # Descripción de la evaluación
    description = ""
    
    # Orden de aparición en las interfaces
    order = 0
    
    @classmethod
    @abstractmethod
    def get_assessment_form(cls, request: HttpRequest, *args, **kwargs) -> Dict[str, Any]:
        """
        Devuelve el formulario para realizar la evaluación.
        Puede ser un formulario HTML o una estructura JSON para formularios dinámicos.
        """
        pass
    
    @classmethod
    @abstractmethod
    def process_assessment(cls, request: HttpRequest, *args, **kwargs) -> Dict[str, Any]:
        """
        Procesa los resultados de la evaluación.
        Devuelve un diccionario con los resultados.
        """
        pass
    
    @classmethod
    def get_assessment_results(cls, assessment_id: str, user: User) -> Optional[Dict[str, Any]]:
        """
        Obtiene los resultados de una evaluación específica para un usuario.
        """
        # Implementación por defecto que puede ser sobrescrita
        from .models import AssessmentResult
        try:
            result = AssessmentResult.objects.get(
                assessment_id=assessment_id,
                user=user,
                is_active=True
            )
            return result.results
        except AssessmentResult.DoesNotExist:
            return None
    
    @classmethod
    def get_available_assessments(cls, user: User) -> List[Dict[str, Any]]:
        """
        Devuelve la lista de evaluaciones disponibles para un usuario.
        """
        from .registry import AssessmentRegistry
        
        available = []
        for assessment_id, assessment_class in AssessmentRegistry.get_all_assessments().items():
            if assessment_class.is_available_for_user(user):
                available.append({
                    'id': assessment_id,
                    'name': assessment_class.display_name,
                    'description': assessment_class.description,
                    'completed': assessment_class.is_completed(user),
                    'order': assessment_class.order
                })
        
        # Ordenar por el campo 'order'
        return sorted(available, key=lambda x: x['order'])
