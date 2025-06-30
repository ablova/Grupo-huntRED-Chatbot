"""
Integración con plataformas de job boards para publicación automática.
"""
import logging
from typing import Dict, Any, List
import requests
from django.conf import settings
from django.utils import timezone
from app.models import Vacante, BusinessUnit
from app.ats.publish.models import JobBoard
from app.ats.publish.integrations.base_integration import BaseIntegration

logger = logging.getLogger(__name__)

class JobBoardIntegration(BaseIntegration):
    """
    Integración base para job boards.
    """
    
    def __init__(self, job_board: JobBoard):
        """
        Inicializa la integración con el job board.
        
        Args:
            job_board: Configuración del job board.
        """
        self.job_board = job_board
        self.api_config = self._get_api_config()
        
    def _get_api_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración de API del job board.
        
        Returns:
            Configuración de API del job board.
        """
        return {
            'api_key': self.job_board.api_key,
            'api_secret': self.job_board.api_secret,
            'endpoint': self.job_board.api_endpoint
        }
    
    def _format_job_data(self, vacancy: Vacante) -> Dict[str, Any]:
        """
        Formatea los datos de la vacante para el job board.
        
        Args:
            vacancy: Vacante a formatear.
            
        Returns:
            Datos formateados para el job board.
        """
        return {
            'title': vacancy.titulo,
            'description': vacancy.descripcion,
            'company_name': vacancy.empresa.company,
            'location': vacancy.ubicacion,
            'salary_min': float(vacancy.salario) if vacancy.salario else None,
            'salary_max': float(vacancy.salario) if vacancy.salario else None,
            'employment_type': vacancy.modalidad,
            'requirements': vacancy.skills_required,
            'benefits': vacancy.beneficios.split('\n') if vacancy.beneficios else [],
            'application_url': f"{settings.BASE_URL}/vacantes/{vacancy.id}/"
        }
    
    async def publish_job(self, vacancy: Vacante) -> Dict[str, Any]:
        """
        Publica una vacante en el job board.
        
        Args:
            vacancy: Vacante a publicar.
            
        Returns:
            Resultado de la publicación.
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
    
    async def update_job(self, vacancy: Vacante, job_id: str) -> Dict[str, Any]:
        """
        Actualiza una vacante existente en el job board.
        
        Args:
            vacancy: Vacante a actualizar.
            job_id: ID de la publicación en el job board.
            
        Returns:
            Resultado de la actualización.
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")
    
    async def delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Elimina una vacante del job board.
        
        Args:
            job_id: ID de la publicación en el job board.
            
        Returns:
            Resultado de la eliminación.
        """
        raise NotImplementedError("Este método debe ser implementado por las subclases")

class IndeedIntegration(JobBoardIntegration):
    """
    Integración con Indeed.
    """
    
    def __init__(self, job_board: JobBoard):
        super().__init__(job_board)
        self.base_url = "https://api.indeed.com"
    
    async def publish_job(self, vacancy: Vacante) -> Dict[str, Any]:
        """
        Publica una vacante en Indeed.
        """
        try:
            job_data = self._format_job_data(vacancy)
            
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.base_url}/jobs",
                headers=headers,
                json=job_data
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'job_id': response.json().get('id'),
                    'message': 'Publicación exitosa en Indeed'
                }
            else:
                logger.error(f"Error al publicar en Indeed: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en IndeedIntegration.publish_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_job(self, vacancy: Vacante, job_id: str) -> Dict[str, Any]:
        """
        Actualiza una vacante en Indeed.
        """
        try:
            job_data = self._format_job_data(vacancy)
            
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.put(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers,
                json=job_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Actualización exitosa en Indeed'
                }
            else:
                logger.error(f"Error al actualizar en Indeed: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en IndeedIntegration.update_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Elimina una vacante de Indeed.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers
            )
            
            if response.status_code == 204:
                return {
                    'success': True,
                    'message': 'Eliminación exitosa en Indeed'
                }
            else:
                logger.error(f"Error al eliminar en Indeed: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en IndeedIntegration.delete_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class GlassdoorIntegration(JobBoardIntegration):
    """
    Integración con Glassdoor.
    """
    
    def __init__(self, job_board: JobBoard):
        super().__init__(job_board)
        self.base_url = "https://api.glassdoor.com"
    
    async def publish_job(self, vacancy: Vacante) -> Dict[str, Any]:
        """
        Publica una vacante en Glassdoor.
        """
        try:
            job_data = self._format_job_data(vacancy)
            
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.base_url}/jobs",
                headers=headers,
                json=job_data
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'job_id': response.json().get('id'),
                    'message': 'Publicación exitosa en Glassdoor'
                }
            else:
                logger.error(f"Error al publicar en Glassdoor: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en GlassdoorIntegration.publish_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_job(self, vacancy: Vacante, job_id: str) -> Dict[str, Any]:
        """
        Actualiza una vacante en Glassdoor.
        """
        try:
            job_data = self._format_job_data(vacancy)
            
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.patch(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers,
                json=job_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Actualización exitosa en Glassdoor'
                }
            else:
                logger.error(f"Error al actualizar en Glassdoor: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en GlassdoorIntegration.update_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Elimina una vacante de Glassdoor.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers
            )
            
            if response.status_code == 204:
                return {
                    'success': True,
                    'message': 'Eliminación exitosa en Glassdoor'
                }
            else:
                logger.error(f"Error al eliminar en Glassdoor: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en GlassdoorIntegration.delete_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class MonsterIntegration(JobBoardIntegration):
    """
    Integración con Monster.
    """
    
    def __init__(self, job_board: JobBoard):
        super().__init__(job_board)
        self.base_url = "https://api.monster.com"
    
    async def publish_job(self, vacancy: Vacante) -> Dict[str, Any]:
        """
        Publica una vacante en Monster.
        """
        try:
            job_data = self._format_job_data(vacancy)
            
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.base_url}/jobs",
                headers=headers,
                json=job_data
            )
            
            if response.status_code == 201:
                return {
                    'success': True,
                    'job_id': response.json().get('id'),
                    'message': 'Publicación exitosa en Monster'
                }
            else:
                logger.error(f"Error al publicar en Monster: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en MonsterIntegration.publish_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_job(self, vacancy: Vacante, job_id: str) -> Dict[str, Any]:
        """
        Actualiza una vacante en Monster.
        """
        try:
            job_data = self._format_job_data(vacancy)
            
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.put(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers,
                json=job_data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Actualización exitosa en Monster'
                }
            else:
                logger.error(f"Error al actualizar en Monster: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en MonsterIntegration.update_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_job(self, job_id: str) -> Dict[str, Any]:
        """
        Elimina una vacante de Monster.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            response = requests.delete(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers
            )
            
            if response.status_code == 204:
                return {
                    'success': True,
                    'message': 'Eliminación exitosa en Monster'
                }
            else:
                logger.error(f"Error al eliminar en Monster: {response.text}")
                return {
                    'success': False,
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Error en MonsterIntegration.delete_job: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class JobBoardFactory:
    """
    Factory para crear integraciones con job boards.
    """
    
    @staticmethod
    def create_integration(job_board: JobBoard) -> JobBoardIntegration:
        """
        Crea una integración específica para el job board.
        
        Args:
            job_board: Configuración del job board.
            
        Returns:
            Integración específica para el job board.
        """
        if job_board.job_board_type == 'indeed':
            return IndeedIntegration(job_board)
        elif job_board.job_board_type == 'glassdoor':
            return GlassdoorIntegration(job_board)
        elif job_board.job_board_type == 'monster':
            return MonsterIntegration(job_board)
        else:
            raise ValueError(f"Job board no soportado: {job_board.job_board_type}") 