# /home/pablo/app/com/chatbot/workflow/assessments/integrated_assessment_manager.py
"""
Módulo para gestión integrada de assessments en Grupo huntRED®

Este módulo proporciona una interfaz unificada para gestionar todos los tipos
de assessments disponibles, permitiendo ejecutarlos individualmente o como
conjunto integrado.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from asgiref.sync import sync_to_async

from app.ml.analyzers.assessment_registry import (
    AssessmentType,
    AssessmentMetadata,
    assessment_registry
)

logger = logging.getLogger(__name__)

class IntegratedAssessmentManager:
    """
    Gestor integrado de assessments que coordina la ejecución y análisis
    de diferentes tipos de evaluaciones.
    """
    
    def __init__(self):
        self.active_assessments: Dict[str, Any] = {}
        self.completed_assessments: set = set()
        self.assessment_results: Dict[str, Dict] = {}
        
    async def start_assessment(self, assessment_type: Union[str, AssessmentType]) -> str:
        """
        Inicia un nuevo assessment del tipo especificado.
        
        Args:
            assessment_type: Tipo de assessment a iniciar
            
        Returns:
            Mensaje inicial del assessment
        """
        if isinstance(assessment_type, str):
            try:
                assessment_type = AssessmentType(assessment_type)
            except ValueError:
                return "Tipo de assessment inválido"
        
        # Verificar si ya hay un assessment activo del mismo tipo
        if assessment_type.value in self.active_assessments:
            return "Ya existe un assessment activo de este tipo"
        
        # Obtener la clase del assessment del registro
        assessment_class = assessment_registry.get_assessment_class(assessment_type)
        if not assessment_class:
            return "No se encontró el assessment solicitado"
        
        # Crear instancia del assessment
        assessment_instance = assessment_class()
        
        # Iniciar el assessment
        self.active_assessments[assessment_type.value] = assessment_instance
        return await assessment_instance.initialize({})
    
    async def process_assessment_message(self, 
                                       assessment_type: Union[str, AssessmentType], 
                                       message: str,
                                       message_type: str = 'text') -> str:
        """
        Procesa un mensaje dentro de un flujo de assessment específico.
        
        Args:
            assessment_type: Tipo de assessment
            message: Mensaje del usuario
            message_type: Tipo de mensaje (texto, imagen, etc.)
            
        Returns:
            Respuesta del sistema al mensaje
        """
        if isinstance(assessment_type, str):
            try:
                assessment_type = AssessmentType(assessment_type)
            except ValueError:
                logger.error(f"Tipo de assessment inválido: {assessment_type}")
                return "Tipo de assessment inválido"
        
        # Obtener el assessment activo
        assessment_instance = self.active_assessments.get(assessment_type.value)
        if not assessment_instance:
            return "No se encontró un assessment activo del tipo solicitado"
        
        # Procesar el mensaje
        response = await assessment_instance.process_message(message)
        
        # Si el assessment ha finalizado, guardar resultados y actualizar análisis
        if assessment_instance.is_completed():
            self.completed_assessments.add(assessment_type.value)
            self.assessment_results[assessment_type.value] = assessment_instance.get_results()
            
            # Actualizar análisis integrado si hay suficientes assessments completados
            if len(self.completed_assessments) >= 2:
                await self._update_integrated_analysis()
        
        return response
    
    async def _update_integrated_analysis(self) -> None:
        """Actualiza el análisis integrado con los resultados de los assessments completados."""
        try:
            # Obtener resultados de todos los assessments completados
            results = {
                assessment_type: self.assessment_results[assessment_type]
                for assessment_type in self.completed_assessments
            }
            
            # Obtener el modelo de ML para análisis integrado
            integrated_model = assessment_registry.get_ml_model('integrated_analysis')
            if not integrated_model:
                logger.error("No se encontró el modelo de análisis integrado")
                return
                
            # Generar análisis integrado
            integrated_analysis = await sync_to_async(integrated_model.analyze)(results)
            
            # Actualizar resultados integrados
            self.assessment_results[AssessmentType.INTEGRATED.value] = integrated_analysis
            
            logger.info("Análisis integrado actualizado exitosamente")
        except Exception as e:
            logger.error(f"Error al actualizar análisis integrado: {str(e)}")
    
    async def get_assessment_results(self, assessment_type: Optional[Union[str, AssessmentType]] = None) -> Dict:
        """
        Obtiene los resultados de un assessment específico o todos los resultados.
        
        Args:
            assessment_type: Tipo de assessment (opcional)
            
        Returns:
            Diccionario con los resultados
        """
        if assessment_type:
            if isinstance(assessment_type, str):
                try:
                    assessment_type = AssessmentType(assessment_type)
                except ValueError:
                    return {"error": "Tipo de assessment inválido"}
            
            return self.assessment_results.get(assessment_type.value, {})
        
        return self.assessment_results
    
    def is_assessment_active(self, assessment_type: Union[str, AssessmentType]) -> bool:
        """Verifica si hay un assessment activo del tipo especificado."""
        if isinstance(assessment_type, str):
            try:
                assessment_type = AssessmentType(assessment_type)
            except ValueError:
                return False
        
        return assessment_type.value in self.active_assessments
    
    def get_active_assessments(self) -> List[str]:
        """Obtiene la lista de tipos de assessments activos."""
        return list(self.active_assessments.keys())
    
    def get_completed_assessments(self) -> List[str]:
        """Obtiene la lista de tipos de assessments completados."""
        return list(self.completed_assessments)
        
    def get_available_assessments(self) -> List[Dict[str, Any]]:
        """
        Obtiene información sobre todos los assessments disponibles.
        
        Returns:
            Lista de diccionarios con información de cada assessment
        """
        available = []
        for assessment_type in assessment_registry.get_available_assessments():
            metadata = assessment_registry.get_assessment_metadata(assessment_type)
            if metadata:
                available.append({
                    'type': assessment_type.value,
                    'name': metadata.name,
                    'description': metadata.description,
                    'version': metadata.version,
                    'is_active': assessment_type.value in self.active_assessments,
                    'is_completed': assessment_type.value in self.completed_assessments
                })
        return available
