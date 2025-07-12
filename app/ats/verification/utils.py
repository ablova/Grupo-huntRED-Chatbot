# app/ats/verification/utils.py
"""
Utilidades para el módulo de verificación.

Este módulo proporciona funciones de alto nivel para:
- Procesamiento de verificaciones
- Análisis de riesgo
- Verificación con INCODE
"""

import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.cache import cache

from .services.incode_service import INCODEService
from .services.background_check_service import BackgroundCheckService

logger = logging.getLogger(__name__)


def get_verification_processor(verification_type: str = 'standard'):
    """
    Obtener el procesador de verificación apropiado.
    
    Args:
        verification_type: Tipo de verificación ('standard', 'premium', 'comprehensive')
    
    Returns:
        Procesador de verificación configurado
    """
    try:
        if verification_type in ['premium', 'comprehensive']:
            return BackgroundCheckService()
        else:
            return INCODEService()
    except Exception as e:
        logger.error(f"Error obteniendo procesador de verificación: {e}")
        return None


def analyze_risk(verification, risk_factors: List[str] = None, custom_risk_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Realizar análisis de riesgo para una verificación.
    
    Args:
        verification: Objeto de verificación
        risk_factors: Lista de factores de riesgo a evaluar
        custom_risk_data: Datos adicionales para el análisis
    
    Returns:
        Resultado del análisis de riesgo
    """
    try:
        risk_factors = risk_factors or []
        custom_risk_data = custom_risk_data or {}
        
        # Análisis básico de riesgo
        risk_score = 0
        risk_details = {}
        
        # Evaluar factores de riesgo
        for factor in risk_factors:
            if factor == 'document_verification':
                risk_score += 10
                risk_details['document_verification'] = 'Requiere verificación de documentos'
            elif factor == 'background_check':
                risk_score += 20
                risk_details['background_check'] = 'Requiere verificación de antecedentes'
            elif factor == 'identity_verification':
                risk_score += 15
                risk_details['identity_verification'] = 'Requiere verificación de identidad'
        
        # Evaluar datos personalizados
        if custom_risk_data.get('high_risk_country'):
            risk_score += 25
            risk_details['high_risk_country'] = 'País de alto riesgo'
        
        if custom_risk_data.get('suspicious_activity'):
            risk_score += 30
            risk_details['suspicious_activity'] = 'Actividad sospechosa detectada'
        
        # Determinar nivel de riesgo
        if risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 25:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_details': risk_details,
            'recommendations': _get_risk_recommendations(risk_level, risk_details)
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de riesgo: {e}")
        return {
            'error': str(e),
            'risk_score': 100,
            'risk_level': 'high'
        }


def verify_incode(verification, document_type: str = None, document_number: str = None, 
                 document_front: str = None, document_back: str = None, selfie: str = None) -> Dict[str, Any]:
    """
    Realizar verificación con INCODE.
    
    Args:
        verification: Objeto de verificación
        document_type: Tipo de documento
        document_number: Número de documento
        document_front: Imagen frontal del documento
        document_back: Imagen trasera del documento
        selfie: Foto selfie del usuario
    
    Returns:
        Resultado de la verificación INCODE
    """
    try:
        incode_service = INCODEService()
        
        # Crear sesión de verificación
        session_data = incode_service.create_session(
            flow_id='identity_verification',
            user_id=str(verification.candidate.id)
        )
        
        if 'error' in session_data:
            return {
                'status': 'error',
                'message': 'Error creando sesión de verificación',
                'details': session_data['error']
            }
        
        # Simular procesamiento de verificación
        # En un entorno real, esto se haría con la API de INCODE
        verification_result = {
            'session_id': session_data.get('sessionId'),
            'status': 'pending',
            'document_verified': document_type is not None,
            'identity_verified': selfie is not None,
            'confidence_score': 0.85,
            'verification_data': {
                'document_type': document_type,
                'document_number': document_number,
                'has_front_image': document_front is not None,
                'has_back_image': document_back is not None,
                'has_selfie': selfie is not None
            }
        }
        
        # Actualizar estado de verificación
        verification.status = 'in_progress'
        verification.results = verification_result
        verification.save()
        
        return {
            'status': 'success',
            'message': 'Verificación INCODE iniciada',
            'result': verification_result
        }
        
    except Exception as e:
        logger.error(f"Error en verificación INCODE: {e}")
        return {
            'status': 'error',
            'message': 'Error en verificación INCODE',
            'details': str(e)
        }


def _get_risk_recommendations(risk_level: str, risk_details: Dict[str, Any]) -> List[str]:
    """
    Obtener recomendaciones basadas en el nivel de riesgo.
    
    Args:
        risk_level: Nivel de riesgo ('low', 'medium', 'high')
        risk_details: Detalles del análisis de riesgo
    
    Returns:
        Lista de recomendaciones
    """
    recommendations = []
    
    if risk_level == 'high':
        recommendations.extend([
            'Realizar verificación completa de antecedentes',
            'Verificar identidad con múltiples fuentes',
            'Revisar documentos originales en persona',
            'Implementar monitoreo continuo'
        ])
    elif risk_level == 'medium':
        recommendations.extend([
            'Realizar verificación básica de antecedentes',
            'Verificar identidad con al menos una fuente',
            'Revisar documentos digitales'
        ])
    else:
        recommendations.extend([
            'Verificación estándar de identidad',
            'Revisión básica de documentos'
        ])
    
    # Recomendaciones específicas basadas en factores de riesgo
    if 'high_risk_country' in risk_details:
        recommendations.append('Verificación adicional para país de alto riesgo')
    
    if 'suspicious_activity' in risk_details:
        recommendations.append('Investigación adicional de actividad sospechosa')
    
    return recommendations 