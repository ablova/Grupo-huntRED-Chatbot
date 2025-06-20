"""
Tareas de Celery para el Sistema AURA

Procesamiento asíncrono de análisis de aura, construcción de redes
y actualización de insights.
"""

import logging
from typing import Dict, List, Any, Optional
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
import asyncio

from app.models import Person, BusinessUnit
from app.ats.models import Candidate, Job
from app.ml.aura.integration_layer import AuraIntegrationLayer
from app.ml.aura.models.gnn_models import GNNAnalyzer
from app.ml.aura.graph_builder import ProfessionalNetworkBuilder

logger = logging.getLogger(__name__)

# Inicializar componentes de AURA
aura_integration = AuraIntegrationLayer()
gnn_analyzer = GNNAnalyzer()
network_builder = ProfessionalNetworkBuilder()

@shared_task(bind=True, name='aura.analyze_person_aura')
def analyze_person_aura(self, person_id: int, force_update: bool = False):
    """
    Analiza el aura de una persona de forma asíncrona.
    
    Args:
        person_id: ID de la persona
        force_update: Forzar actualización aunque ya exista
    """
    try:
        logger.info(f"Iniciando análisis de aura para persona {person_id}")
        
        # Verificar si ya existe análisis reciente
        cache_key = f"aura_person_{person_id}"
        if not force_update and cache.get(cache_key):
            logger.info(f"Análisis de aura para persona {person_id} ya existe en caché")
            return {'status': 'cached', 'person_id': person_id}
        
        # Obtener datos enriquecidos
        person_data = asyncio.run(aura_integration.get_enriched_person_data(person_id))
        
        if not person_data:
            logger.warning(f"No se encontraron datos para persona {person_id}")
            return {'status': 'error', 'message': 'Persona no encontrada', 'person_id': person_id}
        
        # Generar insights de red
        network_insights = asyncio.run(aura_integration.generate_network_insights(person_id))
        
        # Construir red profesional
        network_data = asyncio.run(network_builder.build_professional_network(person_id))
        
        # Análisis GNN
        gnn_analysis = gnn_analyzer.analyze_professional_network(network_data)
        
        # Guardar en caché
        result = {
            'person_data': person_data,
            'network_insights': network_insights,
            'gnn_analysis': gnn_analysis,
            'aura_score': person_data.get('aura_metrics', {}).get('overall_score', 0),
            'analyzed_at': timezone.now().isoformat()
        }
        
        cache.set(cache_key, result, timeout=3600)  # 1 hora
        
        logger.info(f"Análisis de aura completado para persona {person_id}")
        return {'status': 'success', 'person_id': person_id, 'aura_score': result['aura_score']}
        
    except Exception as e:
        logger.error(f"Error analizando aura de persona {person_id}: {str(e)}")
        return {'status': 'error', 'message': str(e), 'person_id': person_id}

@shared_task(bind=True, name='aura.analyze_candidate_aura')
def analyze_candidate_aura(self, candidate_id: int, job_id: Optional[int] = None):
    """
    Analiza el aura de un candidato de forma asíncrona.
    
    Args:
        candidate_id: ID del candidato
        job_id: ID del trabajo específico (opcional)
    """
    try:
        logger.info(f"Iniciando análisis de aura para candidato {candidate_id}")
        
        # Analizar aura del candidato
        aura_analysis = asyncio.run(aura_integration.analyze_candidate_aura(
            candidate_id, job_id
        ))
        
        if 'error' in aura_analysis:
            logger.warning(f"Error en análisis de aura para candidato {candidate_id}: {aura_analysis['error']}")
            return {'status': 'error', 'message': aura_analysis['error'], 'candidate_id': candidate_id}
        
        # Guardar en caché
        cache_key = f"aura_candidate_{candidate_id}_{job_id or 'general'}"
        cache.set(cache_key, aura_analysis, timeout=1800)  # 30 minutos
        
        logger.info(f"Análisis de aura completado para candidato {candidate_id}")
        return {
            'status': 'success',
            'candidate_id': candidate_id,
            'job_id': job_id,
            'aura_score': aura_analysis.get('aura_score', 0)
        }
        
    except Exception as e:
        logger.error(f"Error analizando aura de candidato {candidate_id}: {str(e)}")
        return {'status': 'error', 'message': str(e), 'candidate_id': candidate_id}

@shared_task(bind=True, name='aura.find_job_matches')
def find_job_aura_matches(self, job_id: int, max_candidates: int = 10):
    """
    Encuentra candidatos con mejor aura para un trabajo de forma asíncrona.
    
    Args:
        job_id: ID del trabajo
        max_candidates: Máximo número de candidatos a retornar
    """
    try:
        logger.info(f"Buscando matches de aura para trabajo {job_id}")
        
        # Encontrar matches de aura
        aura_matches = asyncio.run(aura_integration.find_aura_matches(
            job_id, max_candidates
        ))
        
        # Guardar en caché
        cache_key = f"aura_job_matches_{job_id}"
        cache.set(cache_key, aura_matches, timeout=1800)  # 30 minutos
        
        logger.info(f"Encontrados {len(aura_matches)} matches para trabajo {job_id}")
        return {
            'status': 'success',
            'job_id': job_id,
            'matches_count': len(aura_matches),
            'top_match_score': aura_matches[0]['aura_score'] if aura_matches else 0
        }
        
    except Exception as e:
        logger.error(f"Error encontrando matches para trabajo {job_id}: {str(e)}")
        return {'status': 'error', 'message': str(e), 'job_id': job_id}

@shared_task(bind=True, name='aura.build_network')
def build_professional_network(self, person_id: int):
    """
    Construye la red profesional de una persona de forma asíncrona.
    
    Args:
        person_id: ID de la persona
    """
    try:
        logger.info(f"Construyendo red profesional para persona {person_id}")
        
        # Construir red profesional
        network_data = asyncio.run(network_builder.build_professional_network(person_id))
        
        # Análisis GNN
        gnn_analysis = gnn_analyzer.analyze_professional_network(network_data)
        
        # Detectar comunidades
        communities_analysis = gnn_analyzer.detect_communities(network_data)
        
        # Análisis de influencia
        influence_analysis = gnn_analyzer.analyze_influence(network_data)
        
        # Guardar en caché
        cache_key = f"aura_network_{person_id}"
        result = {
            'network_data': network_data,
            'gnn_analysis': gnn_analysis,
            'communities_analysis': communities_analysis,
            'influence_analysis': influence_analysis,
            'built_at': timezone.now().isoformat()
        }
        cache.set(cache_key, result, timeout=3600)  # 1 hora
        
        logger.info(f"Red profesional construida para persona {person_id}")
        return {
            'status': 'success',
            'person_id': person_id,
            'network_size': len(network_data.get('nodes', [])),
            'communities_count': len(communities_analysis.get('communities', []))
        }
        
    except Exception as e:
        logger.error(f"Error construyendo red para persona {person_id}: {str(e)}")
        return {'status': 'error', 'message': str(e), 'person_id': person_id}

@shared_task(bind=True, name='aura.validate_experience')
def validate_experience_cross_reference(
    self,
    person_id: int,
    company: str,
    position: str,
    start_date: str,
    end_date: Optional[str] = None
):
    """
    Valida experiencia laboral usando referencias cruzadas de forma asíncrona.
    
    Args:
        person_id: ID de la persona
        company: Empresa
        position: Posición
        start_date: Fecha de inicio
        end_date: Fecha de fin (opcional)
    """
    try:
        logger.info(f"Validando experiencia para persona {person_id} en {company}")
        
        # Convertir fechas
        from datetime import datetime
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        # Validar experiencia
        validation_result = asyncio.run(aura_integration.validate_experience_cross_reference(
            person_id, company, position, start_date_obj, end_date_obj
        ))
        
        if 'error' in validation_result:
            logger.warning(f"Error validando experiencia: {validation_result['error']}")
            return {'status': 'error', 'message': validation_result['error'], 'person_id': person_id}
        
        # Guardar en caché
        cache_key = f"aura_validation_{person_id}_{company}_{position}"
        cache.set(cache_key, validation_result, timeout=7200)  # 2 horas
        
        logger.info(f"Experiencia validada para persona {person_id} con confianza: {validation_result.get('overall_confidence', 0):.2%}")
        return {
            'status': 'success',
            'person_id': person_id,
            'company': company,
            'position': position,
            'confidence': validation_result.get('overall_confidence', 0)
        }
        
    except Exception as e:
        logger.error(f"Error validando experiencia: {str(e)}")
        return {'status': 'error', 'message': str(e), 'person_id': person_id}

@shared_task(bind=True, name='aura.sync_dashboard')
def sync_aura_dashboard(self, person_id: int):
    """
    Sincroniza insights de AURA al dashboard de forma asíncrona.
    
    Args:
        person_id: ID de la persona
    """
    try:
        logger.info(f"Sincronizando dashboard de AURA para persona {person_id}")
        
        # Sincronizar insights al dashboard
        sync_result = asyncio.run(aura_integration.sync_aura_insights_to_dashboard(person_id))
        
        if 'error' in sync_result:
            logger.warning(f"Error sincronizando dashboard: {sync_result['error']}")
            return {'status': 'error', 'message': sync_result['error'], 'person_id': person_id}
        
        logger.info(f"Dashboard sincronizado para persona {person_id}")
        return {
            'status': 'success',
            'person_id': person_id,
            'sync_timestamp': sync_result.get('sync_timestamp')
        }
        
    except Exception as e:
        logger.error(f"Error sincronizando dashboard: {str(e)}")
        return {'status': 'error', 'message': str(e), 'person_id': person_id}

@shared_task(bind=True, name='aura.bulk_analysis')
def bulk_aura_analysis(self, person_ids: List[int]):
    """
    Realiza análisis de aura en lote para múltiples personas.
    
    Args:
        person_ids: Lista de IDs de personas
    """
    try:
        logger.info(f"Iniciando análisis en lote para {len(person_ids)} personas")
        
        results = []
        for person_id in person_ids:
            try:
                # Analizar aura de cada persona
                result = analyze_person_aura.delay(person_id)
                results.append({
                    'person_id': person_id,
                    'task_id': result.id,
                    'status': 'queued'
                })
                
            except Exception as e:
                logger.warning(f"Error encolando análisis para persona {person_id}: {str(e)}")
                results.append({
                    'person_id': person_id,
                    'status': 'error',
                    'message': str(e)
                })
        
        logger.info(f"Análisis en lote encolado para {len(results)} personas")
        return {
            'status': 'success',
            'total_persons': len(person_ids),
            'queued_tasks': len([r for r in results if r['status'] == 'queued']),
            'errors': len([r for r in results if r['status'] == 'error']),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error en análisis en lote: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task(bind=True, name='aura.cleanup_cache')
def cleanup_aura_cache(self):
    """
    Limpia el caché de AURA de forma periódica.
    """
    try:
        logger.info("Iniciando limpieza de caché de AURA")
        
        # Obtener todas las claves de caché de AURA
        cache_keys = cache.keys("aura_*")
        
        cleaned_count = 0
        for key in cache_keys:
            try:
                cache.delete(key)
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"Error eliminando clave de caché {key}: {str(e)}")
        
        logger.info(f"Limpieza de caché completada: {cleaned_count} claves eliminadas")
        return {
            'status': 'success',
            'cleaned_keys': cleaned_count,
            'cleaned_at': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de caché: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task(bind=True, name='aura.health_check')
def aura_health_check(self):
    """
    Verifica el estado de salud del sistema AURA.
    """
    try:
        logger.info("Iniciando verificación de salud de AURA")
        
        # Verificar componentes
        health_status = asyncio.run(aura_integration.get_aura_health())
        
        # Obtener métricas
        aura_metrics = asyncio.run(aura_integration.get_aura_metrics())
        
        # Verificar caché
        cache_test_key = "aura_health_test"
        cache.set(cache_test_key, "test", timeout=60)
        cache_working = cache.get(cache_test_key) == "test"
        cache.delete(cache_test_key)
        
        health_result = {
            'health_status': health_status,
            'aura_metrics': aura_metrics,
            'cache_working': cache_working,
            'checked_at': timezone.now().isoformat()
        }
        
        logger.info("Verificación de salud de AURA completada")
        return {
            'status': 'success',
            'health_result': health_result
        }
        
    except Exception as e:
        logger.error(f"Error en verificación de salud: {str(e)}")
        return {'status': 'error', 'message': str(e)} 