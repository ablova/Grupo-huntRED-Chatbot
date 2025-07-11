"""
Servicio de integración con INCODE para verificaciones de identidad.
Proporciona métodos para interactuar con la API de INCODE.
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class INCODEService:
    """
    Servicio para interactuar con la API de INCODE.
    Maneja verificaciones de identidad, documentos y biométricas.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'INCODE_API_KEY', None)
        self.base_url = getattr(settings, 'INCODE_BASE_URL', 'https://api.incode.com')
        self.webhook_url = getattr(settings, 'INCODE_WEBHOOK_URL', None)
        
        if not self.api_key:
            logger.warning("INCODE_API_KEY no configurada en settings")
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtiene los headers necesarios para las peticiones a INCODE."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def create_session(self, verification_type: str = 'identity') -> Optional[str]:
        """
        Crea una nueva sesión de verificación en INCODE.
        
        Args:
            verification_type: Tipo de verificación ('identity', 'document', 'biometric')
            
        Returns:
            session_id: ID de la sesión creada
        """
        try:
            url = f"{self.base_url}/sessions"
            payload = {
                'type': verification_type,
                'webhook_url': self.webhook_url,
                'expires_at': (timezone.now() + timedelta(hours=24)).isoformat()
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            session_id = data.get('session_id')
            
            logger.info(f"Sesión INCODE creada: {session_id}")
            return session_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creando sesión INCODE: {str(e)}")
            return None
    
    def verify_identity(self, session_id: str, document_front: str, 
                       document_back: str = None, selfie: str = None) -> Dict[str, Any]:
        """
        Realiza verificación de identidad con documentos y selfie.
        
        Args:
            session_id: ID de la sesión de INCODE
            document_front: URL o base64 del frente del documento
            document_back: URL o base64 del reverso del documento (opcional)
            selfie: URL o base64 de la selfie (opcional)
            
        Returns:
            Dict con los resultados de la verificación
        """
        try:
            url = f"{self.base_url}/sessions/{session_id}/verify"
            payload = {
                'document_front': document_front,
                'document_back': document_back,
                'selfie': selfie
            }
            
            # Limpiar campos None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación INCODE completada para sesión: {session_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en verificación INCODE: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def verify_document(self, session_id: str, document_type: str, 
                       document_number: str) -> Dict[str, Any]:
        """
        Verifica un documento específico contra bases de datos oficiales.
        
        Args:
            session_id: ID de la sesión de INCODE
            document_type: Tipo de documento ('ine', 'passport', etc.)
            document_number: Número del documento
            
        Returns:
            Dict con los resultados de la verificación
        """
        try:
            url = f"{self.base_url}/sessions/{session_id}/document-verify"
            payload = {
                'document_type': document_type,
                'document_number': document_number
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Verificación de documento completada: {document_number}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verificando documento: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def detect_liveness(self, session_id: str, selfie: str) -> Dict[str, Any]:
        """
        Detecta si la selfie es de una persona real (detección de vida).
        
        Args:
            session_id: ID de la sesión de INCODE
            selfie: URL o base64 de la selfie
            
        Returns:
            Dict con los resultados de detección de vida
        """
        try:
            url = f"{self.base_url}/sessions/{session_id}/liveness"
            payload = {
                'selfie': selfie
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Detección de vida completada para sesión: {session_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en detección de vida: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def face_match(self, session_id: str, document_face: str, 
                   selfie_face: str) -> Dict[str, Any]:
        """
        Compara la cara del documento con la selfie.
        
        Args:
            session_id: ID de la sesión de INCODE
            document_face: URL o base64 de la cara del documento
            selfie_face: URL o base64 de la selfie
            
        Returns:
            Dict con los resultados de coincidencia facial
        """
        try:
            url = f"{self.base_url}/sessions/{session_id}/face-match"
            payload = {
                'document_face': document_face,
                'selfie_face': selfie_face
            }
            
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Coincidencia facial completada para sesión: {session_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en coincidencia facial: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual de una sesión de verificación.
        
        Args:
            session_id: ID de la sesión de INCODE
            
        Returns:
            Dict con el estado de la sesión
        """
        try:
            url = f"{self.base_url}/sessions/{session_id}"
            
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Estado de sesión obtenido: {session_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo estado de sesión: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa los datos recibidos por webhook de INCODE.
        
        Args:
            webhook_data: Datos recibidos del webhook
            
        Returns:
            Dict con los datos procesados
        """
        try:
            session_id = webhook_data.get('session_id')
            status = webhook_data.get('status')
            results = webhook_data.get('results', {})
            
            logger.info(f"Webhook INCODE procesado: {session_id} - {status}")
            
            return {
                'session_id': session_id,
                'status': status,
                'results': results,
                'processed_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error procesando webhook INCODE: {str(e)}")
            return {'error': str(e), 'status': 'failed'}
    
    def calculate_confidence_score(self, results: Dict[str, Any]) -> float:
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
            
            # Verificación de documento
            if 'document_verification' in results:
                doc_score = results['document_verification'].get('confidence', 0)
                score += doc_score
                total_checks += 1
            
            # Verificación de identidad
            if 'identity_verification' in results:
                id_score = results['identity_verification'].get('confidence', 0)
                score += id_score
                total_checks += 1
            
            # Detección de vida
            if 'liveness_detection' in results:
                liveness_score = results['liveness_detection'].get('confidence', 0)
                score += liveness_score
                total_checks += 1
            
            # Coincidencia facial
            if 'face_match' in results:
                face_score = results['face_match'].get('confidence', 0)
                score += face_score
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
            
            # Documento expirado
            if results.get('document_expired', False):
                risk_factors.append(0.3)
            
            # Documento sospechoso
            if results.get('document_suspicious', False):
                risk_factors.append(0.5)
            
            # Detección de vida fallida
            if results.get('liveness_failed', False):
                risk_factors.append(0.4)
            
            # Coincidencia facial baja
            face_match_score = results.get('face_match_score', 1.0)
            if face_match_score < 0.7:
                risk_factors.append(0.3)
            
            # Verificación de identidad fallida
            if results.get('identity_verification_failed', False):
                risk_factors.append(0.6)
            
            if risk_factors:
                return max(risk_factors)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculando puntuación de riesgo: {str(e)}")
            return 0.0 