# app/ats/verification/tasks.py
"""
Tareas de verificación para el sistema huntRED.
Maneja procesos asíncronos de verificación de identidad y antecedentes.
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from celery import shared_task
from app.models import Person, INCODEVerification, BackgroundCheck
from .services.incode_service import INCODEService
from .services.background_check_service import BackgroundCheckService

logger = logging.getLogger(__name__)

@shared_task
def process_verification(candidate_id: int, verification_type: str = 'comprehensive') -> Dict[str, Any]:
    """
    Procesa la verificación completa de un candidato.
    
    Args:
        candidate_id: ID del candidato
        verification_type: Tipo de verificación ('basic', 'comprehensive', 'executive')
        
    Returns:
        Dict con los resultados de la verificación
    """
    try:
        candidate = Person.objects.get(id=candidate_id)
        
        results = {
            'candidate_id': candidate_id,
            'verification_type': verification_type,
            'status': 'processing',
            'started_at': timezone.now(),
            'results': {}
        }
        
        # Procesar verificación según el tipo
        if verification_type in ['comprehensive', 'executive']:
            # Verificación completa con INCODE
            incode_result = process_incode_verification.delay(candidate_id)
            results['results']['incode'] = incode_result.id
            
            # Background check
            background_result = process_background_check.delay(candidate_id, verification_type)
            results['results']['background_check'] = background_result.id
            
        elif verification_type == 'basic':
            # Solo background check básico
            background_result = process_background_check.delay(candidate_id, 'basic')
            results['results']['background_check'] = background_result.id
            
        logger.info(f"Verificación iniciada para candidato {candidate_id}")
        return results
        
    except Person.DoesNotExist:
        logger.error(f"Candidato {candidate_id} no encontrado")
        return {'error': 'Candidato no encontrado', 'status': 'failed'}
    except Exception as e:
        logger.error(f"Error procesando verificación: {str(e)}")
        return {'error': str(e), 'status': 'failed'}

@shared_task
def process_incode_verification(candidate_id: int) -> Dict[str, Any]:
    """
    Procesa verificación de identidad con INCODE.
    
    Args:
        candidate_id: ID del candidato
        
    Returns:
        Dict con los resultados de INCODE
    """
    try:
        candidate = Person.objects.get(id=candidate_id)
        
        # Crear registro de verificación INCODE
        verification = INCODEVerification.objects.create(
            candidate=candidate,
            business_unit=candidate.business_unit if hasattr(candidate, 'business_unit') else None,
            verification_type='comprehensive',
            status='in_progress',
            started_at=timezone.now()
        )
        
        # Inicializar servicio INCODE
        incode_service = INCODEService()
        
        # Crear sesión
        session_id = incode_service.create_session('comprehensive')
        if session_id:
            verification.incode_session_id = session_id
            verification.save()
            
            logger.info(f"Verificación INCODE iniciada para candidato {candidate_id}")
            return {
                'verification_id': verification.id,
                'session_id': session_id,
                'status': 'session_created'
            }
        else:
            verification.status = 'failed'
            verification.save()
            return {'error': 'No se pudo crear sesión INCODE', 'status': 'failed'}
            
    except Exception as e:
        logger.error(f"Error en verificación INCODE: {str(e)}")
        return {'error': str(e), 'status': 'failed'}

@shared_task
def process_background_check(candidate_id: int, check_type: str = 'basic') -> Dict[str, Any]:
    """
    Procesa verificación de antecedentes.
    
    Args:
        candidate_id: ID del candidato
        check_type: Tipo de verificación ('basic', 'comprehensive', 'executive')
        
    Returns:
        Dict con los resultados del background check
    """
    try:
        candidate = Person.objects.get(id=candidate_id)
        
        # Crear registro de background check
        background_check = BackgroundCheck.objects.create(
            candidate=candidate,
            business_unit=candidate.business_unit if hasattr(candidate, 'business_unit') else None,
            check_type=check_type,
            status='in_progress',
            full_name=f"{candidate.nombre} {candidate.apellido_paterno or ''} {candidate.apellido_materno or ''}".strip(),
            date_of_birth=candidate.fecha_nacimiento,
            started_at=timezone.now()
        )
        
        # Inicializar servicio de background check
        bg_service = BackgroundCheckService(provider='blacktrust')
        
        # Preparar datos del candidato
        candidate_data = {
            'full_name': background_check.full_name,
            'date_of_birth': candidate.fecha_nacimiento.isoformat() if candidate.fecha_nacimiento else None,
            'email': candidate.email,
            'phone': candidate.phone,
            'national_id': getattr(candidate, 'national_id', None)
        }
        
        # Crear verificación
        check_id = bg_service.create_check(candidate_data, check_type)
        if check_id:
            background_check.reference_id = check_id
            background_check.save()
            
            logger.info(f"Background check iniciado para candidato {candidate_id}")
            return {
                'background_check_id': background_check.id,
                'reference_id': check_id,
                'status': 'check_created'
            }
        else:
            background_check.status = 'failed'
            background_check.save()
            return {'error': 'No se pudo crear background check', 'status': 'failed'}
            
    except Exception as e:
        logger.error(f"Error en background check: {str(e)}")
        return {'error': str(e), 'status': 'failed'}

@shared_task
def update_verification_status(verification_id: int, status: str, results: Dict[str, Any] = None) -> bool:
    """
    Actualiza el estado de una verificación.
    
    Args:
        verification_id: ID de la verificación
        status: Nuevo estado
        results: Resultados de la verificación
        
    Returns:
        bool: True si se actualizó correctamente
    """
    try:
        # Buscar verificación INCODE
        verification = INCODEVerification.objects.filter(id=verification_id).first()
        if verification:
            verification.status = status
            if results:
                verification.results = results
                if 'confidence_score' in results:
                    verification.confidence_score = results['confidence_score']
                if 'risk_score' in results:
                    verification.risk_score = results['risk_score']
            verification.completed_at = timezone.now()
            verification.save()
            return True
            
        # Buscar background check
        background_check = BackgroundCheck.objects.filter(id=verification_id).first()
        if background_check:
            background_check.status = status
            if results:
                background_check.results = results
                if 'trust_score' in results:
                    background_check.trust_score = results['trust_score']
                if 'risk_score' in results:
                    background_check.risk_score = results['risk_score']
            background_check.completed_at = timezone.now()
            background_check.save()
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error actualizando estado de verificación: {str(e)}")
        return False

@shared_task
def process_webhook_incode(webhook_data: Dict[str, Any]) -> bool:
    """
    Procesa webhook de INCODE.
    
    Args:
        webhook_data: Datos del webhook
        
    Returns:
        bool: True si se procesó correctamente
    """
    try:
        incode_service = INCODEService()
        processed_data = incode_service.process_webhook(webhook_data)
        
        session_id = processed_data.get('session_id')
        if session_id:
            verification = INCODEVerification.objects.filter(
                incode_session_id=session_id
            ).first()
            
            if verification:
                verification.webhook_received = True
                verification.status = processed_data.get('status', 'completed')
                verification.results = processed_data.get('results', {})
                verification.completed_at = timezone.now()
                verification.save()
                
                logger.info(f"Webhook INCODE procesado para sesión {session_id}")
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error procesando webhook INCODE: {str(e)}")
        return False

@shared_task
def process_webhook_background_check(webhook_data: Dict[str, Any]) -> bool:
    """
    Procesa webhook de background check.
    
    Args:
        webhook_data: Datos del webhook
        
    Returns:
        bool: True si se procesó correctamente
    """
    try:
        bg_service = BackgroundCheckService()
        processed_data = bg_service.process_webhook(webhook_data)
        
        check_id = processed_data.get('check_id')
        if check_id:
            background_check = BackgroundCheck.objects.filter(
                reference_id=check_id
            ).first()
            
            if background_check:
                background_check.status = processed_data.get('status', 'completed')
                background_check.results = processed_data.get('results', {})
                background_check.completed_at = timezone.now()
                background_check.save()
                
                logger.info(f"Webhook background check procesado para {check_id}")
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error procesando webhook background check: {str(e)}")
        return False 