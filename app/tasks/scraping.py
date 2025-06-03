"""
Módulo de tareas de scraping para Grupo huntRED.
Gestiona la extracción de vacantes y oportunidades de diversas fuentes.
Implementa optimizaciones para bajo uso de CPU y mejor rendimiento.
"""

import logging
import asyncio
import json
import os
import aiohttp
from datetime import datetime, timedelta
from asgiref.sync import sync_to_async, async_to_sync
from celery import shared_task, chain, group, chord
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from app.models import (
    DominioScraping, RegistroScraping, Vacante, BusinessUnit
)
from app.ats.utils.scraping import (
    validar_url, ScrapingPipeline, scrape_and_publish, process_domain
)
from app.ats.utils.scraping_utils import ScrapingMetrics
from app.ml.utils.scrape import MLScraper
from app.ats.utils.email_scraper import EmailScraperV2
from app.ats.tasks.base import with_retry

# Configuración de logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_cv_emails_task(self, business_unit_id):
    """
    Procesa correos electrónicos con CVs adjuntos.
    
    Args:
        business_unit_id: ID de la unidad de negocio
        
    Returns:
        dict: Resultado del procesamiento
    """
    try:
        from app.ats.utils.parser import IMAPCVProcessor
        processor = IMAPCVProcessor(business_unit_id=business_unit_id)
        result = processor.process_emails()
        logger.info(f"Procesados {result['procesados']} correos, {result['nuevos']} nuevos CVs")
        return result
    except Exception as e:
        logger.error(f"Error procesando correos CV: {str(e)}")
        raise self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def ejecutar_scraping(self, dominio_id=None):
    """
    Ejecuta el scraping para todos los dominios o un dominio específico.
    
    Args:
        dominio_id: ID opcional del dominio a scrapear
        
    Returns:
        dict: Resultado del scraping
    """
    async def run_scraping():
        start_time = datetime.now()
        metrics = ScrapingMetrics()
        
        logger.info("🚀 Iniciando ejecución de scraping...")
        
        # Obtener dominios activos
        dominios_query = DominioScraping.objects.filter(activo=True)
        if dominio_id:
            dominios_query = dominios_query.filter(id=dominio_id)
        
        dominios = list(dominios_query)
        total_dominios = len(dominios)
        
        if total_dominios == 0:
            logger.warning("⚠️ No hay dominios activos para ejecutar scraping")
            return {
                "status": "warning",
                "message": "No hay dominios activos para ejecutar scraping"
            }
        
        logger.info(f"📋 Procesando {total_dominios} dominios de scraping")
        
        # Crear pipeline y tareas asíncronas
        pipeline = ScrapingPipeline()
        tasks = []
        
        for dominio in dominios:
            logger.debug(f"Añadiendo dominio a la cola: {dominio.dominio}")
            task = process_domain(dominio)
            tasks.append(task)
        
        # Ejecutar tareas asíncronas
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        successful_domains = 0
        failed_domains = 0
        total_jobs = 0
        new_jobs = 0
        
        for i, result in enumerate(results):
            dominio = dominios[i]
            
            if isinstance(result, Exception):
                logger.error(f"❌ Error procesando {dominio.dominio}: {str(result)}")
                failed_domains += 1
                continue
            
            successful_domains += 1
            total_jobs += result.get('total_jobs', 0)
            new_jobs += result.get('new_jobs', 0)
            
            # Actualizar métricas
            metrics.add_domain_result(dominio.dominio, result)
            
            # Retroalimentación para MLScraper
            if result.get('job_urls'):
                for job_url in result.get('job_urls', []):
                    await log_feedback_for_job(job_url)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Scraping completado en {duration:.2f}s. Dominios: {successful_domains}/{total_dominios}, Vacantes: {total_jobs} (nuevas: {new_jobs})")
        
        # Actualizar estadísticas globales
        metrics.finish_execution(duration, total_dominios, successful_domains, total_jobs, new_jobs)
        
        return {
            "status": "success",
            "duration": duration,
            "domains_total": total_dominios,
            "domains_success": successful_domains,
            "domains_failed": failed_domains,
            "jobs_total": total_jobs,
            "jobs_new": new_jobs,
            "metrics": metrics.get_serializable_metrics()
        }
    
    async def log_feedback_for_job(job_url):
        """Registra retroalimentación para mejorar el scraper ML."""
        try:
            # Buscar la vacante en la base de datos
            vacante = await sync_to_async(Vacante.objects.filter(url=job_url).first)()
            if not vacante:
                return
            
            # Si la vacante fue procesada correctamente, registrarla para entrenamiento
            if vacante.title and vacante.description:
                logger.debug(f"✅ Vacante procesada correctamente: {job_url}")
                # Aquí se podría guardar la vacante para entrenar el modelo ML
            else:
                logger.debug(f"⚠️ Vacante sin datos completos: {job_url}")
        except Exception as e:
            logger.error(f"Error registrando feedback para {job_url}: {str(e)}")
    
    try:
        # Ejecutar el scraping de manera asíncrona
        result = async_to_sync(run_scraping)()
        return result
    except Exception as e:
        logger.error(f"❌ Error global en ejecutar_scraping: {str(e)}")
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=2)
def retrain_ml_scraper(self):
    """
    Reentrena el modelo MLScraper con los datos acumulados.
    
    Returns:
        dict: Resultado del reentrenamiento
    """
    try:
        logger.info("🧠 Iniciando reentrenamiento de MLScraper...")
        
        # Crear instancia del scraper ML
        ml_scraper = MLScraper()
        
        # Obtener datos para reentrenamiento
        # Idealmente deberíamos obtener vacantes bien procesadas de la base de datos
        training_data = Vacante.objects.filter(
            Q(creation_date__gte=timezone.now() - timedelta(days=30)) &
            ~Q(title='') & 
            ~Q(description='')
        ).values('url', 'html_content', 'title', 'description')[:1000]
        
        if not training_data:
            logger.warning("⚠️ No hay datos suficientes para reentrenar el modelo")
            return {"status": "warning", "message": "No hay datos suficientes para reentrenar"}
        
        # Reentrenar modelo
        result = ml_scraper.train(training_data)
        
        logger.info(f"✅ Reentrenamiento completado. Precisión: {result.get('accuracy', 'N/A')}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"❌ Error reentrenando MLScraper: {str(e)}")
        raise self.retry(exc=e, countdown=600)

@shared_task(bind=True, max_retries=2)
def verificar_dominios_scraping(self):
    """
    Verifica que los dominios de scraping sean accesibles.
    
    Returns:
        dict: Resultado de la verificación
    """
    async def check_domains():
        dominios = DominioScraping.objects.filter(activo=True)
        results = {"accessible": [], "inaccessible": []}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for dominio in dominios:
                task = validar_url(session, dominio.dominio)
                tasks.append((dominio, task))
            
            for dominio, task in tasks:
                try:
                    is_valid = await task
                    if is_valid:
                        results["accessible"].append(dominio.dominio)
                        dominio.ultimo_estado = "OK"
                    else:
                        results["inaccessible"].append(dominio.dominio)
                        dominio.ultimo_estado = "ERROR"
                    
                    dominio.ultima_verificacion = timezone.now()
                    await sync_to_async(dominio.save)()
                except Exception as e:
                    logger.error(f"Error verificando {dominio.dominio}: {str(e)}")
                    results["inaccessible"].append(dominio.dominio)
                    dominio.ultimo_estado = f"ERROR: {str(e)}"
                    dominio.ultima_verificacion = timezone.now()
                    await sync_to_async(dominio.save)()
        
        return results
    
    try:
        logger.info("🔍 Verificando accesibilidad de dominios de scraping...")
        results = async_to_sync(check_domains)()
        
        logger.info(f"✅ Verificación completada. Accesibles: {len(results['accessible'])}, Inaccesibles: {len(results['inaccessible'])}")
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"❌ Error verificando dominios: {str(e)}")
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=3)
def procesar_scraping_dominio(self, dominio_id):
    """
    Ejecuta el scraping para un dominio específico.
    
    Args:
        dominio_id: ID del dominio a scrapear
        
    Returns:
        dict: Resultado del scraping
    """
    try:
        dominio = DominioScraping.objects.get(id=dominio_id)
        
        if not dominio.activo:
            logger.warning(f"⚠️ El dominio {dominio.dominio} está inactivo")
            return {"status": "warning", "message": "Dominio inactivo"}
        
        logger.info(f"🚀 Ejecutando scraping para {dominio.dominio}")
        
        # Crear nuevo registro de scraping
        registro = RegistroScraping.objects.create(
            dominio=dominio,
            fecha_inicio=timezone.now(),
            estado="INICIADO"
        )
        
        # Ejecutar la tarea principal de scraping
        result = ejecutar_scraping.delay(dominio_id=dominio_id)
        
        return {"status": "success", "task_id": result.id}
    except Exception as e:
        logger.error(f"❌ Error iniciando scraping para dominio {dominio_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=3)
def procesar_sublinks_task(self, vacante_id, sublink):
    """
    Procesa sublinks de una vacante específica.
    
    Args:
        vacante_id: ID de la vacante
        sublink: URL del sublink a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    async def run():
        try:
            # Obtener la vacante
            vacante = await sync_to_async(Vacante.objects.get)(id=vacante_id)
            
            # Validar sublink
            if not sublink.startswith(('http://', 'https://')):
                return {"status": "error", "message": "URL inválida"}
            
            # Crear pipeline y procesar sublink
            pipeline = ScrapingPipeline()
            result = await pipeline.process_url(sublink)
            
            # Actualizar vacante con información adicional
            if result and result.get('job_info'):
                job_info = result.get('job_info', {})
                
                # Actualizar descripción si está vacía
                if not vacante.description and job_info.get('description'):
                    vacante.description = job_info.get('description')
                
                # Guardar cambios
                await sync_to_async(vacante.save)()
            
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Error procesando sublink {sublink}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    try:
        logger.info(f"🔗 Procesando sublink {sublink} para vacante {vacante_id}")
        result = async_to_sync(run)()
        return result
    except Exception as e:
        logger.error(f"❌ Error global procesando sublink: {str(e)}")
        raise self.retry(exc=e, countdown=60)

@shared_task(bind=True, max_retries=2)
def execute_ml_and_scraping(self):
    """
    Ejecuta el proceso de Machine Learning y scraping en cadena.
    
    Returns:
        dict: Resultado de la ejecución
    """
    logger.info("🔄 Iniciando cadena ML → Scraping → ML")
    
    # Crear cadena de tareas
    return chain(
        train_ml_task.s(),
        ejecutar_scraping.s(),
        retrain_ml_scraper.s()
    ).apply_async()

@shared_task(name="tasks.execute_email_scraper")
def execute_email_scraper(dominio_id=None, batch_size=10):
    """
    Ejecuta la extracción de vacantes desde correos electrónicos, opcionalmente para un dominio específico.
    
    Args:
        dominio_id (int, optional): ID del dominio específico para filtrar correos (si aplica).
        batch_size (int): Número de correos a procesar por lote.
    
    Returns:
        dict: Resultado de la ejecución con estadísticas.
    """
    try:
        # Obtener credenciales desde el entorno
        EMAIL_ACCOUNT = os.environ.get("EMAIL_ACCOUNT", "")
        EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")

        if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
            logger.error("Faltan credenciales para el email scraper")
            return {"status": "error", "message": "Faltan credenciales"}

        # Instanciar el scraper
        scraper = EmailScraperV2(EMAIL_ACCOUNT, EMAIL_PASSWORD)

        if dominio_id:
            dominio = DominioScraping.objects.get(id=dominio_id)
            logger.info(f"🚀 Ejecutando email scraper para {dominio.dominio} con batch_size={batch_size}...")
            # Nota: Actualmente EmailScraperV2 no filtra por dominio_id, pero lo dejamos preparado
        else:
            logger.info(f"🚀 Ejecutando email scraper para todos los correos con batch_size={batch_size}...")

        # Ejecutar el scraper de manera asíncrona
        asyncio.run(scraper.process_all_emails(batch_size=batch_size))

        # Retornar estadísticas
        result = {
            "status": "success",
            "correos_procesados": scraper.stats["correos_procesados"],
            "correos_exitosos": scraper.stats["correos_exitosos"],
            "correos_error": scraper.stats["correos_error"],
            "vacantes_extraidas": scraper.stats["vacantes_extraidas"],
            "vacantes_guardadas": scraper.stats["vacantes_guardadas"]
        }
        logger.info(f"✅ Email scraper ejecutado: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Error en email_scraper: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
