"""
Tareas asíncronas para verificación

Este módulo implementa tareas asíncronas con Celery para:
1. Iniciar procesos de verificación
2. Procesar verificaciones de identidad
3. Verificar redes sociales
4. Verificar antecedentes

Sigue las normas de optimización:
- Low CPU Usage con operaciones asíncronas
- Caching con Redis para resultados
- Mecanismos de retry para APIs externas
"""

import logging
import os
import asyncio
import json
import aiohttp
import redis
from asgiref.sync import sync_to_async
from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from app.models import (
    VerificationService, VerificationAddon, OpportunityVerificationPackage,
    CandidateVerification, CandidateServiceResult, SocialNetworkVerification,
    Person
)
from app.com.chatbot.validation.truth_analyzer import TruthAnalyzer

# Configurar logging
logger = logging.getLogger(__name__)

# Configurar cliente de Redis para caching
redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)

# Cache TTL (24 horas)
CACHE_TTL = 86400

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def start_verification_process(self, verification_id, immediate=False):
    """
    Inicia el proceso de verificación para un candidato.
    
    Args:
        verification_id: ID de la verificación
        immediate: Si es True, ejecuta la verificación inmediatamente
    """
    try:
        # Obtener verificación
        verification = CandidateVerification.objects.get(id=verification_id)
        
        # Actualizar estado
        verification.status = 'in_progress'
        verification.save()
        
        # Obtener addons del paquete
        addon_details = verification.package.addon_details.all()
        services_to_verify = set()
        
        # Crear registros de servicio para cada addon
        for detail in addon_details:
            addon = detail.addon
            for service in addon.services.all():
                services_to_verify.add(service.id)
                
                # Verificar si ya existe un registro para este servicio
                service_result, created = CandidateServiceResult.objects.get_or_create(
                    verification=verification,
                    service=service,
                    defaults={
                        'addon': addon,
                        'status': 'pending',
                        'started_at': timezone.now() if immediate else None
                    }
                )
                
                # Si se solicita verificación inmediata, programar la tarea
                if immediate and created:
                    if service.category == 'identity':
                        verify_identity.delay(service_result.id)
                    elif service.category == 'social':
                        verify_social_networks.delay(service_result.id)
                    elif service.category == 'background':
                        verify_background.delay(service_result.id)
                    elif service.category == 'education':
                        verify_education.delay(service_result.id)
                    elif service.category == 'experience':
                        verify_experience.delay(service_result.id)
        
        return f"Proceso de verificación iniciado para {verification.candidate.nombre}"
    except Exception as e:
        logger.error(f"Error iniciando verificación: {str(e)}")
        # Reintentar en caso de error
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def verify_identity(self, service_result_id):
    """
    Verifica la identidad de un candidato usando TruthSense™.
    
    Args:
        service_result_id: ID del resultado de servicio
    """
    try:
        # Obtener resultado de servicio
        service_result = CandidateServiceResult.objects.get(id=service_result_id)
        candidate = service_result.verification.candidate
        
        # Marcar como en progreso
        service_result.status = 'in_progress'
        service_result.started_at = timezone.now()
        service_result.save()
        
        # Intentar obtener del cache primero
        cache_key = f"identity_verification:{candidate.id}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            # Usar resultado en cache
            result_data = json.loads(cached_result)
            logger.info(f"Usando resultado en cache para {candidate.nombre}")
        else:
            # Ejecutar verificación TruthSense™
            truth_analyzer = TruthAnalyzer()
            
            # Ejecutar análisis de manera asíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Recopilar datos para verificación
                basic_info = {
                    'nombre': candidate.nombre,
                    'apellido': candidate.apellido,
                    'email': candidate.email,
                    'telefono': candidate.telefono
                }
                
                # Análisis con TruthAnalyzer
                verification_result = loop.run_until_complete(
                    truth_analyzer.verify_identity(candidate, basic_info)
                )
                
                result_data = {
                    'identity_score': verification_result.get('consistency_score', 0.5),
                    'red_flags': verification_result.get('red_flags', []),
                    'verification_details': verification_result
                }
                
                # Guardar en cache para futuras verificaciones
                redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(result_data)
                )
            finally:
                loop.close()
        
        # Actualizar resultado del servicio
        service_result.score = result_data.get('identity_score', 0.5)
        service_result.details = result_data
        service_result.status = 'completed'
        service_result.completed_at = timezone.now()
        service_result.save()
        
        # Actualizar puntuación general de la verificación
        _update_verification_score(service_result.verification.id)
        
        return f"Verificación de identidad completada para {candidate.nombre}"
    except Exception as e:
        logger.error(f"Error en verificación de identidad: {str(e)}")
        # Reintentar en caso de error
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def verify_social_networks(self, service_result_id):
    """
    Verifica las redes sociales de un candidato usando SocialVerify™.
    
    Args:
        service_result_id: ID del resultado de servicio
    """
    try:
        # Obtener resultado de servicio
        service_result = CandidateServiceResult.objects.get(id=service_result_id)
        candidate = service_result.verification.candidate
        
        # Marcar como en progreso
        service_result.status = 'in_progress'
        service_result.started_at = timezone.now()
        service_result.save()
        
        # Intentar obtener del cache primero
        cache_key = f"social_verification:{candidate.id}"
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            # Usar resultado en cache
            result_data = json.loads(cached_result)
            logger.info(f"Usando resultado en cache para {candidate.nombre}")
            
            # Crear registros de verificación para cada red
            for network_result in result_data.get('networks', []):
                SocialNetworkVerification.objects.get_or_create(
                    service_result=service_result,
                    network=network_result.get('network'),
                    profile_url=network_result.get('profile_url'),
                    defaults={
                        'profile_name': network_result.get('profile_name'),
                        'followers_count': network_result.get('followers_count'),
                        'verified_identity': network_result.get('verified_identity', False),
                        'account_age_days': network_result.get('account_age_days'),
                        'reputation_score': network_result.get('reputation_score'),
                        'verification_data': network_result.get('verification_data', {})
                    }
                )
        else:
            # Ejecutar verificación SocialVerify™
            result_data = {'networks': []}
            total_score = 0
            networks_found = 0
            
            # Verificar diferentes redes sociales
            social_networks = [
                ('linkedin', f"https://www.linkedin.com/in/{candidate.nombre.lower()}-{candidate.apellido.lower()}"),
                ('github', f"https://github.com/{candidate.nombre.lower()}{candidate.apellido.lower()}"),
                ('facebook', ""),
                ('twitter', ""),
                ('instagram', ""),
                ('tiktok', "")
            ]
            
            # En una implementación real, obtendríamos estas URLs de fuentes como el CV o
            # buscaríamos en internet. Para este ejemplo, solo usamos algunas predefinidas.
            for network, profile_url in social_networks:
                if not profile_url:
                    continue
                    
                # Verificar red social con API externa (simulado)
                network_score = 0.7  # Puntuación simulada
                networks_found += 1
                total_score += network_score
                
                # Crear registro de verificación
                network_result = {
                    'network': network,
                    'profile_url': profile_url,
                    'profile_name': f"{candidate.nombre} {candidate.apellido}",
                    'followers_count': 100,  # Simulado
                    'verified_identity': network_score > 0.6,
                    'account_age_days': 365,  # Simulado
                    'reputation_score': network_score,
                    'verification_data': {
                        'posts_count': 50,
                        'connections': 200,
                        'last_activity': timezone.now().isoformat()
                    }
                }
                
                result_data['networks'].append(network_result)
                
                # Crear registro en base de datos
                SocialNetworkVerification.objects.create(
                    service_result=service_result,
                    network=network,
                    profile_url=profile_url,
                    profile_name=network_result.get('profile_name'),
                    followers_count=network_result.get('followers_count'),
                    verified_identity=network_result.get('verified_identity'),
                    account_age_days=network_result.get('account_age_days'),
                    reputation_score=network_result.get('reputation_score'),
                    verification_data=network_result.get('verification_data')
                )
            
            # Calcular puntuación promedio
            final_score = total_score / max(networks_found, 1)
            result_data['social_score'] = final_score
            
            # Guardar en cache para futuras verificaciones
            redis_client.setex(
                cache_key,
                CACHE_TTL,
                json.dumps(result_data)
            )
        
        # Actualizar resultado del servicio
        service_result.score = result_data.get('social_score', 0.5)
        service_result.details = result_data
        service_result.status = 'completed'
        service_result.completed_at = timezone.now()
        service_result.save()
        
        # Actualizar puntuación general de la verificación
        _update_verification_score(service_result.verification.id)
        
        return f"Verificación de redes sociales completada para {candidate.nombre}"
    except Exception as e:
        logger.error(f"Error en verificación de redes sociales: {str(e)}")
        # Reintentar en caso de error
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def verify_background(self, service_result_id):
    """
    Verifica antecedentes de un candidato.
    
    Args:
        service_result_id: ID del resultado de servicio
    """
    try:
        # Obtener resultado de servicio
        service_result = CandidateServiceResult.objects.get(id=service_result_id)
        candidate = service_result.verification.candidate
        
        # Marcar como en progreso
        service_result.status = 'in_progress'
        service_result.started_at = timezone.now()
        service_result.save()
        
        # Implementar integración con servicio de verificación de antecedentes
        # Como BlackTrust u otro sistema similar
        
        # Para este ejemplo, simularemos el resultado
        result_data = {
            'background_score': 0.85,
            'criminal_record': False,
            'financial_status': 'good',
            'driving_record': 'clean',
            'verification_details': {
                'verification_date': timezone.now().isoformat(),
                'verification_source': 'BackgroundCheck™'
            }
        }
        
        # Actualizar resultado del servicio
        service_result.score = result_data.get('background_score', 0.5)
        service_result.details = result_data
        service_result.status = 'completed'
        service_result.completed_at = timezone.now()
        service_result.save()
        
        # Actualizar puntuación general de la verificación
        _update_verification_score(service_result.verification.id)
        
        return f"Verificación de antecedentes completada para {candidate.nombre}"
    except Exception as e:
        logger.error(f"Error en verificación de antecedentes: {str(e)}")
        # Reintentar en caso de error
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def verify_education(self, service_result_id):
    """
    Verifica estudios de un candidato.
    
    Args:
        service_result_id: ID del resultado de servicio
    """
    try:
        # Obtener resultado de servicio
        service_result = CandidateServiceResult.objects.get(id=service_result_id)
        candidate = service_result.verification.candidate
        
        # Marcar como en progreso
        service_result.status = 'in_progress'
        service_result.started_at = timezone.now()
        service_result.save()
        
        # Implementar integración con servicios de verificación educativa
        # Para este ejemplo, simularemos el resultado
        result_data = {
            'education_score': 0.9,
            'verifications': []
        }
        
        # Obtener estudios del candidato
        studies = []  # Aquí obtendrías los estudios del candidato
        
        # Simular verificación de cada estudio
        for study in studies:
            result_data['verifications'].append({
                'institution': study.get('institution'),
                'degree': study.get('degree'),
                'verified': True,
                'verification_date': timezone.now().isoformat()
            })
        
        # Actualizar resultado del servicio
        service_result.score = result_data.get('education_score', 0.5)
        service_result.details = result_data
        service_result.status = 'completed'
        service_result.completed_at = timezone.now()
        service_result.save()
        
        # Actualizar puntuación general de la verificación
        _update_verification_score(service_result.verification.id)
        
        return f"Verificación educativa completada para {candidate.nombre}"
    except Exception as e:
        logger.error(f"Error en verificación educativa: {str(e)}")
        # Reintentar en caso de error
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def verify_experience(self, service_result_id):
    """
    Verifica experiencia laboral de un candidato.
    
    Args:
        service_result_id: ID del resultado de servicio
    """
    try:
        # Obtener resultado de servicio
        service_result = CandidateServiceResult.objects.get(id=service_result_id)
        candidate = service_result.verification.candidate
        
        # Marcar como en progreso
        service_result.status = 'in_progress'
        service_result.started_at = timezone.now()
        service_result.save()
        
        # Implementar integración con servicios de verificación de experiencia
        # Para este ejemplo, simularemos el resultado
        result_data = {
            'experience_score': 0.85,
            'verifications': []
        }
        
        # Obtener experiencias del candidato
        experiences = []  # Aquí obtendrías las experiencias del candidato
        
        # Simular verificación de cada experiencia
        for exp in experiences:
            result_data['verifications'].append({
                'company': exp.get('company'),
                'position': exp.get('position'),
                'verified': True,
                'verification_source': 'LinkedIn, Compañía',
                'verification_date': timezone.now().isoformat()
            })
        
        # Actualizar resultado del servicio
        service_result.score = result_data.get('experience_score', 0.5)
        service_result.details = result_data
        service_result.status = 'completed'
        service_result.completed_at = timezone.now()
        service_result.save()
        
        # Actualizar puntuación general de la verificación
        _update_verification_score(service_result.verification.id)
        
        return f"Verificación de experiencia completada para {candidate.nombre}"
    except Exception as e:
        logger.error(f"Error en verificación de experiencia: {str(e)}")
        # Reintentar en caso de error
        raise self.retry(exc=e)

def _update_verification_score(verification_id):
    """
    Actualiza la puntuación general de una verificación basada en los resultados de servicios.
    
    Args:
        verification_id: ID de la verificación
    """
    try:
        with transaction.atomic():
            verification = CandidateVerification.objects.get(id=verification_id)
            
            # Obtener resultados completados
            completed_results = CandidateServiceResult.objects.filter(
                verification=verification,
                status='completed',
                score__isnull=False
            )
            
            # Calcular puntuación promedio
            total_score = sum(result.score for result in completed_results)
            count = completed_results.count()
            
            if count > 0:
                verification.overall_score = total_score / count
            
            # Verificar si todos los servicios están completados
            total_services = CandidateServiceResult.objects.filter(verification=verification).count()
            if completed_results.count() == total_services:
                verification.status = 'completed'
                verification.completed_at = timezone.now()
            
            verification.save()
    except Exception as e:
        logger.error(f"Error actualizando puntuación de verificación: {str(e)}")
        raise
