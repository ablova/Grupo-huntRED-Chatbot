"""
Integración con el API de INCODE para validación biométrica y de firmas.
"""
import requests
import logging
from typing import Dict, Optional, Tuple
from django.core.cache import cache
from .config import get_incode_config, get_biometric_config

logger = logging.getLogger(__name__)

class IncodeIntegration:
    """Clase para manejar la integración con INCODE."""
    
    def __init__(self):
        self.config = get_incode_config()
        self.biometric_config = get_biometric_config()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json'
        })
        
    def _make_request(self, endpoint: str, method: str = 'POST', data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Realiza una petición al API de INCODE.
        
        Args:
            endpoint: Endpoint del API
            method: Método HTTP
            data: Datos a enviar
            
        Returns:
            Tupla con (éxito, respuesta)
        """
        try:
            url = f"{self.config['base_url']}{endpoint}"
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.config['timeout']
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                logger.error(f"Error en petición a INCODE: {response.text}")
                return False, {'error': response.text}
                
        except Exception as e:
            logger.error(f"Error en petición a INCODE: {str(e)}")
            return False, {'error': str(e)}
            
    def validate_face(self, image_data: bytes, reference_image: Optional[bytes] = None) -> Tuple[bool, str]:
        """
        Valida la identidad facial usando INCODE.
        
        Args:
            image_data: Imagen a validar
            reference_image: Imagen de referencia (opcional)
            
        Returns:
            Tupla con (éxito, mensaje)
        """
        cache_key = f"face_validation:{hash(image_data)}"
        cached_result = cache.get(cache_key)
        
        if cached_result and self.biometric_config['cache']['enabled']:
            return cached_result
            
        try:
            data = {
                'image': image_data.decode('utf-8'),
                'threshold': self.config['thresholds']['face_match']
            }
            
            if reference_image:
                data['reference_image'] = reference_image.decode('utf-8')
                
            success, response = self._make_request(
                self.config['endpoints']['face_match'],
                data=data
            )
            
            if success:
                result = (
                    response['score'] >= self.config['thresholds']['face_match'],
                    f"Score de coincidencia: {response['score']}"
                )
                
                if self.biometric_config['cache']['enabled']:
                    cache.set(
                        cache_key,
                        result,
                        timeout=self.biometric_config['cache']['ttl']
                    )
                    
                return result
                
            return False, response.get('error', 'Error en validación facial')
            
        except Exception as e:
            logger.error(f"Error en validación facial: {str(e)}")
            return False, str(e)
            
    def verify_liveness(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Verifica que la imagen sea de una persona real.
        
        Args:
            image_data: Imagen a verificar
            
        Returns:
            Tupla con (éxito, mensaje)
        """
        cache_key = f"liveness_verification:{hash(image_data)}"
        cached_result = cache.get(cache_key)
        
        if cached_result and self.biometric_config['cache']['enabled']:
            return cached_result
            
        try:
            data = {
                'image': image_data.decode('utf-8'),
                'threshold': self.config['thresholds']['liveness']
            }
            
            success, response = self._make_request(
                self.config['endpoints']['liveness'],
                data=data
            )
            
            if success:
                result = (
                    response['score'] >= self.config['thresholds']['liveness'],
                    f"Score de liveness: {response['score']}"
                )
                
                if self.biometric_config['cache']['enabled']:
                    cache.set(
                        cache_key,
                        result,
                        timeout=self.biometric_config['cache']['ttl']
                    )
                    
                return result
                
            return False, response.get('error', 'Error en verificación de liveness')
            
        except Exception as e:
            logger.error(f"Error en verificación de liveness: {str(e)}")
            return False, str(e)
            
    def verify_document(self, document_data: bytes) -> Tuple[bool, str]:
        """
        Verifica la autenticidad de un documento.
        
        Args:
            document_data: Datos del documento
            
        Returns:
            Tupla con (éxito, mensaje)
        """
        try:
            data = {
                'document': document_data.decode('utf-8'),
                'threshold': self.config['thresholds']['document_verification']
            }
            
            success, response = self._make_request(
                self.config['endpoints']['document_verification'],
                data=data
            )
            
            if success:
                return (
                    response['score'] >= self.config['thresholds']['document_verification'],
                    f"Score de autenticidad: {response['score']}"
                )
                
            return False, response.get('error', 'Error en verificación de documento')
            
        except Exception as e:
            logger.error(f"Error en verificación de documento: {str(e)}")
            return False, str(e)
            
    def verify_signature(self, signature_data: bytes) -> Tuple[bool, str]:
        """
        Verifica la autenticidad de una firma.
        
        Args:
            signature_data: Datos de la firma
            
        Returns:
            Tupla con (éxito, mensaje)
        """
        try:
            data = {
                'signature': signature_data.decode('utf-8'),
                'threshold': self.config['thresholds']['signature_verification']
            }
            
            success, response = self._make_request(
                self.config['endpoints']['electronic_signature'],
                data=data
            )
            
            if success:
                return (
                    response['score'] >= self.config['thresholds']['signature_verification'],
                    f"Score de autenticidad: {response['score']}"
                )
                
            return False, response.get('error', 'Error en verificación de firma')
            
        except Exception as e:
            logger.error(f"Error en verificación de firma: {str(e)}")
            return False, str(e) 