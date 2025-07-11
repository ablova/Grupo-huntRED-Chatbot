"""
Servicio de verificación de antecedentes.
Integra con proveedores como BlackTrust y otros servicios de verificación.
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class BackgroundCheckService:
    """
    Servicio para realizar verificaciones de antecedentes.
    Soporta múltiples proveedores y tipos de verificación.
    """
    
    def __init__(self, provider: str = 'blacktrust'):
        self.provider = provider
        self.api_key = getattr(settings, f'{provider.upper()}_API_KEY', None)
        self.base_url = getattr(settings, f'{provider.upper()}_BASE_URL', None)
        self.webhook_url = getattr(settings, f'{provider.upper()}_WEBHOOK_URL', None)
        
        if not self.api_key:
            logger.warning(f"{provider.upper()}_API_KEY no configurada en settings")
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene los headers necesarios para las peticiones."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def create_check(self, candidate_data: Dict[str, Any], 
                    check_type: str = 'basic') -> Optional[str]:
        """
        Crea una nueva verificación de antecedentes.
        
        Args:
            candidate_data: Datos del candidato
            check_type: Tipo de verificación ('basic', 'comprehensive', etc.)
            
        Returns:
            check_id: ID de la verificación creada
        """
        try:
            url = f"{self.base_url}/checks"
            payload = {
                'type': check_type,
                'candidate': candidate_data,
                'webhook_url': self.webhook_url,
                'expires_at': (timezone.now() + timedelta(days=30)).isoformat()
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            check_id = data.get('check_id')
            
            logger.info(f"Verificación de antecedentes creada: {check_id}")
            return check_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creando verificación de antecedentes: {str(e)}")
            return None
    
    def verify_identity(self, full_name: str, date_of_birth: str, 
                       national_id: str = None) -> Dict[str, Any]:
        """
        Verifica la identidad del candidato.
        
        Args:
            full_name: Nombre completo
            date_of_birth: Fecha de nacimiento
            national_id: Número de identificación nacional
            
        Returns:
            Dict con los resultados de verificación de identidad
        """
        try:
            url = f"{self.base_url}/identity-verify"
            payload = {
                'full_name': full_name,
                'date_of_birth': date_of_birth,
                'national_id': national_id
            }
            
            # Limpiar campos None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación de identidad completada: {full_name}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en verificación de identidad: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def criminal_check(self, full_name: str, date_of_birth: str, 
                      address: str = None) -> Dict[str, Any]:
        """
        Realiza verificación de antecedentes penales.
        
        Args:
            full_name: Nombre completo
            date_of_birth: Fecha de nacimiento
            address: Dirección (opcional)
            
        Returns:
            Dict con los resultados de verificación penal
        """
        try:
            url = f"{self.base_url}/criminal-check"
            payload = {
                'full_name': full_name,
                'date_of_birth': date_of_birth,
                'address': address
            }
            
            # Limpiar campos None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación penal completada: {full_name}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en verificación penal: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def employment_verification(self, company_name: str, position: str, 
                              start_date: str, end_date: str = None) -> Dict[str, Any]:
        """
        Verifica el historial laboral.
        
        Args:
            company_name: Nombre de la empresa
            position: Cargo ocupado
            start_date: Fecha de inicio
            end_date: Fecha de fin (opcional)
            
        Returns:
            Dict con los resultados de verificación laboral
        """
        try:
            url = f"{self.base_url}/employment-verify"
            payload = {
                'company_name': company_name,
                'position': position,
                'start_date': start_date,
                'end_date': end_date
            }
            
            # Limpiar campos None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación laboral completada: {company_name}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en verificación laboral: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def education_verification(self, institution: str, degree: str, 
                             graduation_date: str) -> Dict[str, Any]:
        """
        Verifica el historial educativo.
        
        Args:
            institution: Institución educativa
            degree: Título obtenido
            graduation_date: Fecha de graduación
            
        Returns:
            Dict con los resultados de verificación educativa
        """
        try:
            url = f"{self.base_url}/education-verify"
            payload = {
                'institution': institution,
                'degree': degree,
                'graduation_date': graduation_date
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación educativa completada: {institution}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en verificación educativa: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def credit_check(self, full_name: str, national_id: str) -> Dict[str, Any]:
        """
        Realiza verificación de historial crediticio.
        
        Args:
            full_name: Nombre completo
            national_id: Número de identificación nacional
            
        Returns:
            Dict con los resultados de verificación crediticia
        """
        try:
            url = f"{self.base_url}/credit-check"
            payload = {
                'full_name': full_name,
                'national_id': national_id
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación crediticia completada: {full_name}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en verificación crediticia: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def social_media_check(self, full_name: str, email: str = None, 
                          phone: str = None) -> Dict[str, Any]:
        """
        Realiza verificación de redes sociales.
        
        Args:
            full_name: Nombre completo
            email: Email (opcional)
            phone: Teléfono (opcional)
            
        Returns:
            Dict con los resultados de verificación de redes sociales
        """
        try:
            url = f"{self.base_url}/social-media-check"
            payload = {
                'full_name': full_name,
                'email': email,
                'phone': phone
            }
            
            # Limpiar campos None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación de redes sociales completada: {full_name}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en verificación de redes sociales: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def get_check_status(self, check_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual de una verificación.
        
        Args:
            check_id: ID de la verificación
            
        Returns:
            Dict con el estado de la verificación
        """
        try:
            url = f"{self.base_url}/checks/{check_id}"
            
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Estado de verificación obtenido: {check_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo estado de verificación: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa los datos recibidos por webhook.
        
        Args:
            webhook_data: Datos recibidos del webhook
            
        Returns:
            Dict con los datos procesados
        """
        try:
            check_id = webhook_data.get('check_id')
            status = webhook_data.get('status')
            results = webhook_data.get('results', {})
            
            logger.info(f"Webhook procesado: {check_id} - {status}")
            
            return {
                'check_id': check_id,
                'status': status,
                'results': results,
                'processed_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def calculate_trust_score(self, results: Dict[str, Any]) -> float:
        """
        Calcula una puntuación de confianza basada en los resultados.
        
        Args:
            results: Resultados de la verificación
            
        Returns:
            float: Puntuación de confianza (0-1)
        """
        try:
            score = 0.0
            total_checks = 0
            
            # Verificación de identidad
            if 'identity_verification' in results:
                id_score = results['identity_verification'].get('confidence', 0)
                score += id_score
                total_checks += 1
            
            # Verificación penal
            if 'criminal_check' in results:
                criminal_score = results['criminal_check'].get('confidence', 0)
                score += criminal_score
                total_checks += 1
            
            # Verificación laboral
            if 'employment_verification' in results:
                emp_score = results['employment_verification'].get('confidence', 0)
                score += emp_score
                total_checks += 1
            
            # Verificación educativa
            if 'education_verification' in results:
                edu_score = results['education_verification'].get('confidence', 0)
                score += edu_score
                total_checks += 1
            
            # Verificación crediticia
            if 'credit_check' in results:
                credit_score = results['credit_check'].get('confidence', 0)
                score += credit_score
                total_checks += 1
            
            if total_checks > 0:
                return score / total_checks
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculando puntuación de confianza: {str(e)}")
            return 0.0
    
    def calculate_risk_score(self, results: Dict[str, Any]) -> float:
        """
        Calcula una puntuación de riesgo basada en los resultados.
        
        Args:
            results: Resultados de la verificación
            
        Returns:
            float: Puntuación de riesgo (0-1)
        """
        try:
            risk_factors = []
            
            # Antecedentes penales
            if results.get('criminal_record_found', False):
                risk_factors.append(0.8)
            
            # Identidad no verificada
            if results.get('identity_verification_failed', False):
                risk_factors.append(0.6)
            
            # Empleo no verificado
            if results.get('employment_verification_failed', False):
                risk_factors.append(0.4)
            
            # Educación no verificada
            if results.get('education_verification_failed', False):
                risk_factors.append(0.3)
            
            # Problemas crediticios
            if results.get('credit_issues_found', False):
                risk_factors.append(0.5)
            
            # Red flags en redes sociales
            if results.get('social_media_red_flags', False):
                risk_factors.append(0.4)
            
            if risk_factors:
                return max(risk_factors)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculando puntuación de riesgo: {str(e)}")
            return 0.0
    
    def get_areas_covered(self, check_type: str) -> List[str]:
        """
        Obtiene las áreas cubiertas según el tipo de verificación.
        
        Args:
            check_type: Tipo de verificación
            
        Returns:
            Lista de áreas cubiertas
        """
        coverage_map = {
            'basic': ['identity_verification', 'basic_criminal_check'],
            'standard': ['identity_verification', 'criminal_check', 'employment_verification'],
            'comprehensive': ['identity_verification', 'criminal_check', 'employment_verification', 
                            'education_verification', 'credit_check'],
            'executive': ['identity_verification', 'criminal_check', 'employment_verification', 
                         'education_verification', 'credit_check', 'social_media_check'],
            'compliance': ['identity_verification', 'criminal_check', 'employment_verification', 
                          'education_verification', 'credit_check', 'social_media_check', 
                          'regulatory_check']
        }
        
        return coverage_map.get(check_type, []) 