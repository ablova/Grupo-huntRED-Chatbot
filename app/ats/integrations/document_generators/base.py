from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.template.loader import render_to_string
from django.conf import settings
import os
import json
import logging

logger = logging.getLogger(__name__)

class BaseDocumentGenerator(ABC):
    """Clase base para todos los generadores de documentos"""
    
    def __init__(self, business_unit: Optional[Any] = None):
        self.business_unit = business_unit
        self.template_dir = self._get_template_dir()
        self.output_dir = self._get_output_dir()
    
    def _get_template_dir(self) -> str:
        """Obtiene el directorio de plantillas"""
        return os.path.join(settings.BASE_DIR, 'app/ats/templates/documents')
    
    def _get_output_dir(self) -> str:
        """Obtiene el directorio de salida"""
        return os.path.join(settings.MEDIA_ROOT, 'documents')
    
    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> str:
        """Genera el documento"""
        pass
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Renderiza una plantilla con el contexto dado"""
        try:
            return render_to_string(
                f'documents/{template_name}',
                context
            )
        except Exception as e:
            logger.error(f"Error al renderizar plantilla {template_name}: {str(e)}")
            raise
    
    def save_document(self, content: str, filename: str) -> str:
        """Guarda el documento generado"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return filepath
        except Exception as e:
            logger.error(f"Error al guardar documento {filename}: {str(e)}")
            raise
    
    def get_business_unit_config(self) -> Dict[str, Any]:
        """Obtiene la configuración específica de la Business Unit"""
        if not self.business_unit:
            return {}
        
        try:
            return {
                'name': self.business_unit.name,
                'logo': self.business_unit.logo.url if self.business_unit.logo else None,
                'contact_info': {
                    'phone': self.business_unit.admin_phone,
                    'email': self.business_unit.admin_email
                },
                'branding': {
                    'primary_color': self.business_unit.primary_color,
                    'secondary_color': self.business_unit.secondary_color,
                    'font_family': self.business_unit.font_family
                }
            }
        except Exception as e:
            logger.error(f"Error al obtener configuración de BU: {str(e)}")
            return {}
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Valida los datos de entrada"""
        required_fields = self.get_required_fields()
        return all(field in data for field in required_fields)
    
    @abstractmethod
    def get_required_fields(self) -> list:
        """Retorna los campos requeridos para la generación"""
        pass
    
    def get_template_variables(self) -> Dict[str, Any]:
        """Retorna las variables disponibles en las plantillas"""
        return {
            'business_unit': self.get_business_unit_config(),
            'generator': {
                'name': self.__class__.__name__,
                'version': '1.0.0'
            }
        }
    
    def format_document(self, content: str) -> str:
        """Formatea el documento según las reglas de la Business Unit"""
        if not self.business_unit:
            return content
        
        # Aplicar formato según la configuración de la BU
        config = self.get_business_unit_config()
        if config.get('branding'):
            # Aplicar estilos de marca
            pass
        
        return content
    
    def log_generation(self, document_type: str, metadata: Dict[str, Any]) -> None:
        """Registra la generación del documento"""
        logger.info(
            f"Documento generado: {document_type}",
            extra={
                'business_unit': self.business_unit.name if self.business_unit else None,
                'metadata': json.dumps(metadata)
            }
        ) 