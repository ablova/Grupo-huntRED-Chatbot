"""
Tareas asíncronas para el procesamiento de perfiles de LinkedIn.

Este módulo proporciona tareas Celery para el scraping y procesamiento
de perfiles de LinkedIn de manera asíncrona y escalable.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

from celery import shared_task, current_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from app.ats.config.api_config import LINKEDIN_CONFIG
from app.ats.utils.linkedin import (
    scrape_linkedin_profile,
    scrape_with_selenium,
    extract_skills,
    normalize_skills,
    associate_divisions
)
from app.models import Person, BusinessUnit

logger = get_task_logger(__name__)

# Bloquear para evitar múltiples ejecuciones simultáneas
LOCK_EXPIRE = 60 * 5  # 5 minutos


def get_lock_id(task_name: str, *args) -> str:
    """Genera un ID único para el bloqueo de tarea."""
    return f"{task_name}-lock-{'-'.join(str(arg) for arg in args) if args else 'single'}"


@shared_task(
    bind=True,
    max_retries=3,
    soft_time_limit=300,  # 5 minutos
    default_retry_delay=60,  # 1 minuto
    rate_limit='2/m'  # 2 peticiones por minuto
)
def scrape_linkedin_profile_task(self, profile_url: str, unit: str) -> Dict[str, Any]:
    """
    Tarea para extraer información de un perfil de LinkedIn.
    
    Args:
        profile_url: URL del perfil de LinkedIn
        unit: Unidad de negocio para el procesamiento de habilidades
        
    Returns:
        Dict con la información del perfil o error
    """
    lock_id = get_lock_id('scrape_linkedin_profile', profile_url)
    
    # Adquirir bloqueo para evitar procesamiento duplicado
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)
    
    if not acquire_lock():
        logger.warning(f"Tarea ya en ejecución para {profile_url}")
        return {"status": "error", "message": "Tarea ya en ejecución"}
    
    try:
        logger.info(f"Iniciando scraping de perfil: {profile_url}")
        
        # Actualizar el estado de la tarea
        current_task.update_state(
            state='PROGRESS',
            meta={'status': 'procesando', 'url': profile_url}
        )
        
        # Ejecutar el scraping con Playwright (con reintentos)
        result = asyncio.run(scrape_linkedin_profile(profile_url, unit))
        
        # Si falla, intentar con Selenium
        if not result:
            logger.warning("Playwright falló, intentando con Selenium...")
            result = asyncio.run(scrape_with_selenium(profile_url, unit))
        
        if not result:
            raise ValueError("No se pudo obtener información del perfil")
        
        logger.info(f"Scraping completado para {profile_url}")
        return {
            "status": "success",
            "data": result,
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en scrape_linkedin_profile_task: {str(e)}", exc_info=True)
        # Reintentar la tarea si es posible
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea (intento {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))  # Backoff exponencial
        return {
            "status": "error",
            "message": str(e),
            "url": profile_url,
            "retries": self.request.retries
        }
    finally:
        # Liberar el bloqueo
        release_lock()


@shared_task(bind=True)
def process_linkedin_profiles_batch(self, profile_urls: List[str], unit: str) -> Dict[str, Any]:
    """
    Procesa un lote de perfiles de LinkedIn en paralelo.
    
    Args:
        profile_urls: Lista de URLs de perfiles de LinkedIn
        unit: Unidad de negocio para el procesamiento
        
    Returns:
        Dict con los resultados del procesamiento
    """
    from celery import group
    
    try:
        # Crear un grupo de tareas para procesar en paralelo
        task_group = group(
            scrape_linkedin_profile_task.s(url, unit) for url in profile_urls
        )
        
        # Ejecutar el grupo de tareas
        group_result = task_group.apply_async()
        
        # Esperar a que todas las tareas terminen (opcional)
        # group_result.join()
        
        return {
            "status": "started",
            "task_id": group_result.id,
            "total_profiles": len(profile_urls),
            "started_at": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en process_linkedin_profiles_batch: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "total_profiles": len(profile_urls) if profile_urls else 0
        }


@shared_task
def update_person_from_linkedin(person_id: int, linkedin_url: str) -> Dict[str, Any]:
    """
    Actualiza los datos de una persona con la información de su perfil de LinkedIn.
    
    Args:
        person_id: ID de la persona en la base de datos
        linkedin_url: URL del perfil de LinkedIn
        
    Returns:
        Dict con el resultado de la actualización
    """
    from django.db import transaction
    
    try:
        person = Person.objects.get(id=person_id)
        logger.info(f"Actualizando datos de {person} desde LinkedIn: {linkedin_url}")
        
        # Ejecutar el scraping
        result = scrape_linkedin_profile_task.delay(linkedin_url, person.business_unit.name if person.business_unit else 'huntRED')
        
        # Esperar el resultado (opcional, podría ser asíncrono)
        profile_data = result.get(timeout=300)  # 5 minutos de timeout
        
        if profile_data.get('status') != 'success':
            raise ValueError(f"Error al obtener datos de LinkedIn: {profile_data.get('message')}")
        
        # Actualizar los datos de la persona
        with transaction.atomic():
            # Actualizar campos básicos
            if 'personal_info' in profile_data['data']:
                personal_info = profile_data['data']['personal_info']
                person.first_name = personal_info.get('first_name', person.first_name)
                person.last_name = personal_info.get('last_name', person.last_name)
                person.headline = personal_info.get('headline', person.headline)
            
            # Actualizar habilidades
            if 'skills' in profile_data['data']:
                skills = profile_data['data']['skills']
                person.skills = list(set((person.skills or []) + skills))
            
            # Guardar la URL de LinkedIn si no estaba establecida
            if not person.linkedin_url:
                person.linkedin_url = linkedin_url
            
            # Actualizar metadatos
            person.metadata = {
                **(person.metadata or {}),
                'linkedin_data': profile_data['data'],
                'last_updated': timezone.now().isoformat()
            }
            
            person.save()
        
        return {
            "status": "success",
            "person_id": person_id,
            "updated_fields": ["first_name", "last_name", "headline", "skills", "linkedin_url", "metadata"]
        }
        
    except Person.DoesNotExist:
        logger.error(f"Persona no encontrada con ID: {person_id}")
        return {"status": "error", "message": f"Persona no encontrada con ID: {person_id}"}
    except Exception as e:
        logger.error(f"Error al actualizar persona {person_id} desde LinkedIn: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e), "person_id": person_id}


@shared_task
def monitor_linkedin_tasks() -> Dict[str, Any]:
    """
    Monitorea el estado de las tareas de LinkedIn.
    
    Returns:
        Dict con estadísticas de las tareas
    """
    from celery.task.control import inspect
    
    try:
        inspector = inspect()
        
        # Obtener tareas activas, programadas y reservadas
        active = inspector.active() or {}
        scheduled = inspector.scheduled() or {}
        reserved = inspector.reserved() or {}
        
        # Contar tareas por tipo
        task_counts = {}
        for tasks in [active, scheduled, reserved]:
            for worker, task_list in tasks.items():
                for task in task_list:
                    task_name = task.get('name', 'unknown')
                    task_counts[task_name] = task_counts.get(task_name, 0) + 1
        
        return {
            "status": "success",
            "stats": {
                "active_tasks": sum(len(tasks) for tasks in active.values()),
                "scheduled_tasks": sum(len(tasks) for tasks in scheduled.values()),
                "reserved_tasks": sum(len(tasks) for tasks in reserved.values()),
                "task_counts": task_counts,
                "timestamp": timezone.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error en monitor_linkedin_tasks: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}
