"""
Integración con LinkedIn para publicación de oportunidades laborales.
"""
import logging
from typing import Dict, Any
import requests
from django.conf import settings
from app.models import Vacante, BusinessUnit
from app.ats.models.worker import Worker
from app.ats.publish.integrations.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

class LinkedInIntegration(BaseIntegration):
    """
    Integración con LinkedIn para publicación de oportunidades laborales.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa la integración con la configuración necesaria.
        
        Args:
            business_unit: Unidad de negocio a la que pertenece la publicación.
        """
        super().__init__(business_unit)
        self.api_config = self._get_api_config()
        
    def _get_api_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de API de LinkedIn para la unidad de negocio.
        
        Returns:
            Configuración de API de LinkedIn.
        """
        config = ApiConfig.get_config('linkedin', self.business_unit)
        if not config:
            raise ValueError(f"No se encontró configuración de LinkedIn para la unidad de negocio {self.business_unit}")
        return {
            'client_id': config.api_key,
            'client_secret': config.api_secret,
            'access_token': config.additional_settings.get('access_token'),
            'company_id': config.additional_settings.get('company_id')
        }
    
    def _format_job_post(self, vacancy: Vacante) -> Dict[str, Any]:
        """
        Formatea la oportunidad laboral para la API de LinkedIn.
        
        Args:
            vacancy: Oportunidad laboral a publicar.
            
        Returns:
            Diccionario con los datos formateados para la API de LinkedIn.
        """
        return {
            "title": vacancy.titulo,
            "description": vacancy.descripcion,
            "company": {
                "name": vacancy.empresa.company,
                "linkedin_id": self.api_config['company_id']
            },
            "location": vacancy.ubicacion,
            "salary": {
                "amount": float(vacancy.salario),
                "currency": "MXN"
            } if vacancy.salario else None,
            "employment_type": vacancy.modalidad,
            "skills": vacancy.skills_required,
            "benefits": vacancy.beneficios.split('\n') if vacancy.beneficios else [],
            "application_url": f"{settings.BASE_URL}/vacantes/{vacancy.id}/"
        }
    
    async def publish(self, vacancy: Vacante) -> Dict[str, Any]:
        """
        Publica una oportunidad laboral en LinkedIn.
        
        Args:
            vacancy: Oportunidad laboral a publicar.
            
        Returns:
            Resultado de la publicación.
        """
        try:
            # Verificar si la vacante debe ser publicada en LinkedIn
            if not await sync_to_async(VacanteManager.should_publish_to_linkedin)(vacancy):
                logger.info(f"Vacante {vacancy.id} no será publicada en LinkedIn porque proviene de scraping o email")
                return {
                    'success': False,
                    'message': 'Vacante no elegible para publicación en LinkedIn'
                }
            
            # Formatear el post
            post_data = self._format_job_post(vacancy)
            
            # Preparar headers
            headers = {
                'Authorization': f'Bearer {self.api_config["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            # Realizar la llamada a la API
            response = requests.post(
                'https://api.linkedin.com/v2/jobs',
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'job_id': response.json().get('id'),
                    'message': 'Publicación exitosa en LinkedIn'
                }
            else:
                logger.error(f"Error al publicar en LinkedIn: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en LinkedInIntegration.publish: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update(self, vacancy: Vacante, linkedin_job_id: str) -> Dict[str, Any]:
        """
        Actualiza una oportunidad laboral existente en LinkedIn.
        
        Args:
            vacancy: Oportunidad laboral a actualizar.
            linkedin_job_id: ID de la publicación en LinkedIn.
            
        Returns:
            Resultado de la actualización.
        """
        try:
            # Formatear el post
            post_data = self._format_job_post(vacancy)
            
            # Preparar headers
            headers = {
                'Authorization': f'Bearer {self.api_config["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            # Realizar la llamada a la API
            response = requests.patch(
                f'https://api.linkedin.com/v2/jobs/{linkedin_job_id}',
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Actualización exitosa en LinkedIn'
                }
            else:
                logger.error(f"Error al actualizar en LinkedIn: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en LinkedInIntegration.update: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete(self, linkedin_job_id: str) -> Dict[str, Any]:
        """
        Elimina una oportunidad laboral de LinkedIn.
        
        Args:
            linkedin_job_id: ID de la publicación en LinkedIn.
            
        Returns:
            Resultado de la eliminación.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_config["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(
                f'https://api.linkedin.com/v2/jobs/{linkedin_job_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Eliminación exitosa en LinkedIn'
                }
            else:
                logger.error(f"Error al eliminar en LinkedIn: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en LinkedInIntegration.delete: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
