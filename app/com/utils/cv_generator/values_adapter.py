"""
Adaptador de Valores para Generación de CVs.

Este módulo proporciona la integración entre los valores fundamentales 
de apoyo, solidaridad y sinergia, y el sistema de generación de CVs.
"""

import logging
from typing import Dict, Any, List, Optional

from app.com.chatbot.core.values import ValuesPrinciples
from app.com.chatbot.core.values_integration import ValuesChatMiddleware
from app.models import BusinessUnit, Person

logger = logging.getLogger(__name__)

class CVValuesAdapter:
    """
    Adaptador para integrar los valores fundamentales en la generación de CVs.
    """
    
    def __init__(self):
        """Inicializa el adaptador."""
        self.values_principles = ValuesPrinciples()
    
    def get_personalized_cv_message(self, 
                                   candidate_data: Dict[str, Any], 
                                   business_unit: str, 
                                   audience_type: str = 'client') -> str:
        """
        Genera un mensaje personalizado para el CV basado en valores.
        
        Args:
            candidate_data: Datos del candidato
            business_unit: Unidad de negocio
            audience_type: Tipo de audiencia ('client', 'candidate', 'consultant')
            
        Returns:
            Mensaje personalizado
        """
        # Extraer información relevante para el contexto
        first_name = candidate_data.get('name', '').split()[0] if candidate_data.get('name') else 'Candidato'
        position = candidate_data.get('title', 'profesional')
        years_experience = self._extract_experience_years(candidate_data)
        
        # Contexto para el mensaje
        context = {
            'nombre': first_name,
            'apellido': candidate_data.get('name', '').split()[1] if len(candidate_data.get('name', '').split()) > 1 else '',
            'posicion': position,
            'experiencia_años': years_experience,
            'business_unit': business_unit
        }
        
        # Determinar tipo de mensaje según audiencia
        message_type = f"cv_{audience_type.lower()}"
        
        # Obtener mensaje
        message = self.values_principles.get_values_based_message(message_type, context)
        
        # Si no se encontró un mensaje específico, usar uno genérico
        if not message:
            if audience_type == 'client':
                message = f"Este CV presenta a {first_name}, un profesional con {years_experience} años de experiencia en el área de {position}. Nuestro riguroso proceso de selección garantiza candidatos que no solo cumplen con los requisitos técnicos, sino que también se alinean con los valores de su organización."
            elif audience_type == 'candidate':
                message = f"{first_name}, hemos preparado este CV destacando tus fortalezas y potencial profesional. Nuestro compromiso es apoyarte en tu crecimiento profesional y encontrar la oportunidad que mejor se adapte a tus aspiraciones."
            else:  # consultor
                message = f"CV preparado para {first_name}, candidato de {business_unit}. Este perfil ha sido analizado considerando tanto sus habilidades técnicas como su potencial de crecimiento y ajuste cultural."
        
        return message
    
    def enrich_cv_data(self, 
                      cv_data: Dict[str, Any], 
                      person_id: Optional[int] = None,
                      business_unit: Optional[str] = None) -> Dict[str, Any]:
        """
        Enriquece los datos del CV con elementos basados en valores.
        
        Args:
            cv_data: Datos del CV
            person_id: ID del candidato (opcional)
            business_unit: Unidad de negocio (opcional)
            
        Returns:
            Datos del CV enriquecidos
        """
        enriched_data = cv_data.copy()
        
        # Determinar el tipo de audiencia basado en los datos
        audience_type = self._determine_audience_type(enriched_data)
        
        # Añadir mensaje personalizado
        if business_unit:
            enriched_data['values_message'] = self.get_personalized_cv_message(
                enriched_data, 
                business_unit, 
                audience_type
            )
        
        # Añadir elementos de diseño basados en valores según BU
        if business_unit:
            enriched_data['values_design'] = self._get_values_design_elements(business_unit)
        
        # Añadir mensaje motivacional específico si tenemos ID de persona
        if person_id:
            try:
                from app.models import Person
                person = Person.objects.get(id=person_id)
                context = {
                    'nombre': person.nombre,
                    'apellido': person.apellido_paterno if hasattr(person, 'apellido_paterno') else ''
                }
                motivational_message = self.values_principles.get_values_based_message(
                    "motivacion_profesional", 
                    context
                )
                enriched_data['motivational_message'] = motivational_message
            except Exception as e:
                logger.warning(f"No se pudo obtener mensaje motivacional para persona ID {person_id}: {str(e)}")
        
        return enriched_data
    
    def _determine_audience_type(self, cv_data: Dict[str, Any]) -> str:
        """
        Determina el tipo de audiencia basado en los datos del CV.
        
        Args:
            cv_data: Datos del CV
            
        Returns:
            Tipo de audiencia ('client', 'candidate', 'consultant')
        """
        # Si el diccionario contiene una clave específica para el tipo de audiencia
        if 'audience_type' in cv_data:
            return cv_data['audience_type']
        
        # Si es un CV ciego, probablemente es para cliente
        if cv_data.get('blind', False) or 'blind_identifier' in cv_data:
            return 'client'
        
        # Si tiene plan de desarrollo, probablemente es para candidato
        if 'development_plan' in cv_data:
            return 'candidate'
        
        # Si tiene métricas internas, probablemente es para consultor
        if any(key in cv_data for key in ['internal_metrics', 'consultant_notes']):
            return 'consultant'
        
        # Por defecto, asumir cliente
        return 'client'
    
    def _extract_experience_years(self, cv_data: Dict[str, Any]) -> int:
        """
        Extrae los años de experiencia de los datos del CV.
        
        Args:
            cv_data: Datos del CV
            
        Returns:
            Años de experiencia
        """
        try:
            from datetime import datetime
            
            experience = cv_data.get('experience', [])
            total_months = 0
            
            for exp in experience:
                # Convertir fechas de string a datetime
                if isinstance(exp.get('start_date'), str):
                    try:
                        start_date = datetime.strptime(exp['start_date'], '%m/%Y')
                    except ValueError:
                        # Intentar con otro formato
                        start_date = datetime.strptime(exp['start_date'], '%Y-%m-%d')
                else:
                    start_date = exp.get('start_date', datetime.now())
                
                if exp.get('end_date'):
                    if isinstance(exp['end_date'], str):
                        if exp['end_date'].lower() in ['presente', 'present', 'actual']:
                            end_date = datetime.now()
                        else:
                            try:
                                end_date = datetime.strptime(exp['end_date'], '%m/%Y')
                            except ValueError:
                                # Intentar con otro formato
                                end_date = datetime.strptime(exp['end_date'], '%Y-%m-%d')
                    else:
                        end_date = exp['end_date']
                else:
                    end_date = datetime.now()
                
                # Calcular meses
                months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_months += max(0, months)  # Asegurar que no sea negativo
            
            return total_months // 12  # Convertir a años
        except Exception as e:
            logger.warning(f"Error calculando años de experiencia: {str(e)}")
            return 5  # Valor por defecto
    
    def _get_values_design_elements(self, business_unit: str) -> Dict[str, Any]:
        """
        Obtiene elementos de diseño basados en valores para la BU específica.
        
        Args:
            business_unit: Nombre de la unidad de negocio
            
        Returns:
            Diccionario con elementos de diseño
        """
        # Colores y estilos por BU
        bu_styles = {
            'huntRED': {
                'primary_color': '#1a73e8',
                'secondary_color': '#e8f0fe',
                'accent_color': '#4285f4',
                'message_style': 'professional',
                'font_family': 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif'
            },
            'huntU': {
                'primary_color': '#0f9d58',
                'secondary_color': '#e6f4ea',
                'accent_color': '#137333',
                'message_style': 'enthusiastic',
                'font_family': 'Inter, Roboto, Arial, sans-serif'
            },
            'SEXSI': {
                'primary_color': '#9c27b0',
                'secondary_color': '#f3e5f5',
                'accent_color': '#7b1fa2',
                'message_style': 'confidential',
                'font_family': 'Montserrat, Helvetica, Arial, sans-serif'
            },
            'Amigro': {
                'primary_color': '#ff6d00',
                'secondary_color': '#fff3e0',
                'accent_color': '#e65100',
                'message_style': 'supportive',
                'font_family': 'Open Sans, Arial, Helvetica, sans-serif'
            }
        }
        
        # Aplicar estilos predeterminados si la BU no está definida
        return bu_styles.get(business_unit, bu_styles['huntRED'])


# Instancia global para uso conveniente
cv_values_adapter = CVValuesAdapter()
