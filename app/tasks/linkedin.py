from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import time
import logging
import psutil
import hashlib
from django.core.cache import cache
from app.models import (
    LinkedInProfile, LinkedInMessageTemplate, 
    LinkedInInvitationSchedule, Application,
    Person, BusinessUnit
)
from app.ats.integrations.channels.linkedin.channel import LinkedInChannel
from app.ats.integrations.ai.insights import generate_personalized_message
from app.ats.utils.linkedin import (
    scrape_linkedin_profile, update_person_from_scrape,
    construct_linkedin_url, extract_skills, normalize_skills,
    associate_divisions
)

logger = logging.getLogger(__name__)

def check_system_resources():
    """
    Verifica si hay suficientes recursos del sistema disponibles.
    
    Returns:
        bool: True si hay recursos suficientes, False en caso contrario
    """
    # Obtener uso de CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Obtener uso de memoria
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Obtener uso de disco
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Verificar si hay suficientes recursos
    if cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
        logger.warning(
            f"Recursos del sistema limitados: "
            f"CPU: {cpu_percent}%, "
            f"Memoria: {memory_percent}%, "
            f"Disco: {disk_percent}%"
        )
        return False
        
    return True

@shared_task
def send_linkedin_invitations():
    """
    Envía invitaciones de LinkedIn según la programación configurada.
    Verifica recursos del sistema antes de ejecutar.
    """
    # Verificar recursos del sistema
    if not check_system_resources():
        logger.info("Recursos del sistema insuficientes, posponiendo tarea")
        return
        
    # Obtener la hora actual en la zona horaria del servidor
    current_time = timezone.localtime(timezone.now()).time()
    
    # Obtener programaciones activas para la hora actual
    schedules = LinkedInInvitationSchedule.objects.filter(
        is_active=True,
        time_window_start__lte=current_time,
        time_window_end__gte=current_time
    ).order_by('priority')
    
    if not schedules.exists():
        logger.info("No hay programaciones activas para la hora actual")
        return
        
    # Obtener template de mensaje
    template = LinkedInMessageTemplate.objects.filter(is_active=True).first()
    if not template:
        logger.error("No hay template de mensaje activo para LinkedIn")
        return
        
    # Inicializar canal de LinkedIn
    channel = LinkedInChannel(cookies_path='linkedin_cookies.json')
    
    try:
        for schedule in schedules:
            # Verificar recursos antes de cada programación
            if not check_system_resources():
                logger.info("Recursos del sistema insuficientes, deteniendo ejecución")
                break
                
            # Verificar si se pueden enviar invitaciones hoy
            if not schedule.can_send_today():
                logger.info(
                    f"Programación {schedule.name} no puede enviar invitaciones hoy "
                    f"(límites alcanzados o día no permitido)"
                )
                continue
                
            logger.info(f"Procesando programación: {schedule.name}")
            
            # Obtener perfiles según el tipo de objetivo
            if schedule.target_type == 'ACTIVE_CANDIDATES':
                # Obtener perfiles de candidatos en procesos activos
                active_applications = Application.objects.filter(
                    status__in=['INTERVIEW', 'OFFER', 'NEGOTIATION']
                ).values_list('candidate__linkedin_profile', flat=True)
                
                profiles = LinkedInProfile.objects.filter(
                    id__in=active_applications,
                    is_connected=False
                )
            else:
                # Obtener perfiles generales inactivos
                profiles = LinkedInProfile.objects.filter(
                    is_connected=False,
                    last_invitation_sent__isnull=True
                )
                
            # Obtener información de perfiles
            profiles_with_info = []
            for profile in profiles[:schedule.max_invitations]:
                # Verificar recursos antes de cada perfil
                if not check_system_resources():
                    logger.info("Recursos del sistema insuficientes, deteniendo procesamiento de perfiles")
                    break
                    
                info = channel.get_profile_info(profile.profile_url)
                if info:
                    profiles_with_info.append((profile, info))
                    
            # Enviar invitaciones
            invitations_sent = 0
            for profile, info in profiles_with_info:
                # Verificar recursos antes de cada invitación
                if not check_system_resources():
                    logger.info("Recursos del sistema insuficientes, deteniendo envío de invitaciones")
                    break
                    
                # Verificar límites diarios y semanales
                if not schedule.can_send_today():
                    logger.info(
                        f"Límites alcanzados para la programación {schedule.name}. "
                        f"Enviadas {invitations_sent} invitaciones."
                    )
                    break
                    
                # Generar mensaje personalizado
                message = generate_personalized_message(info, template.template)
                
                success = channel.send_connection_request(
                    profile_url=profile.profile_url,
                    message=message
                )
                
                if success:
                    profile.last_invitation_sent = timezone.now()
                    profile.save()
                    invitations_sent += 1
                    
                    # Registrar el mensaje enviado
                    logger.info(
                        f"Mensaje enviado a {profile.name} "
                        f"(Programación: {schedule.name}):\n{message}"
                    )
                    
                # Esperar el delay configurado
                time.sleep(schedule.delay_between_invitations)
                
            logger.info(
                f"Programación {schedule.name} completada. "
                f"Enviadas {invitations_sent} invitaciones."
            )
                
    except Exception as e:
        logger.error(f"Error en tarea de invitaciones LinkedIn: {str(e)}")
        
    finally:
        channel.close()

@shared_task
def cleanup_linkedin_invitations():
    """
    Limpia el historial de invitaciones enviadas después de 6 meses.
    """
    # Verificar recursos del sistema
    if not check_system_resources():
        logger.info("Recursos del sistema insuficientes, posponiendo limpieza")
        return
        
    # Obtener perfiles con invitaciones enviadas hace más de 6 meses
    six_months_ago = timezone.now() - timedelta(days=180)
    old_invitations = LinkedInProfile.objects.filter(
        last_invitation_sent__lt=six_months_ago
    )
    
    # Resetear el campo last_invitation_sent
    old_invitations.update(last_invitation_sent=None)
    
    logger.info(f"Limpieza de {old_invitations.count()} invitaciones antiguas completada")

@shared_task
def enrich_linkedin_profiles():
    """
    Tarea periódica para enriquecer perfiles de LinkedIn.
    Verifica recursos del sistema antes de ejecutar.
    """
    # Verificar recursos del sistema
    if not check_system_resources():
        logger.info("Recursos del sistema insuficientes, posponiendo enriquecimiento")
        return
        
    # Obtener perfiles que necesitan enriquecimiento
    profiles = LinkedInProfile.objects.filter(
        last_enrichment__isnull=True
    ) | LinkedInProfile.objects.filter(
        last_enrichment__lt=timezone.now() - timedelta(days=30)
    )
    
    if not profiles.exists():
        logger.info("No hay perfiles que necesiten enriquecimiento")
        return
        
    # Inicializar canal de LinkedIn
    channel = LinkedInChannel(cookies_path='linkedin_cookies.json')
    
    try:
        for profile in profiles:
            # Verificar recursos antes de cada perfil
            if not check_system_resources():
                logger.info("Recursos del sistema insuficientes, deteniendo enriquecimiento")
                break
                
            try:
                # Obtener información del perfil
                info = channel.get_profile_info(profile.profile_url)
                if info:
                    # Actualizar perfil con nueva información
                    profile.name = info.get('name', profile.name)
                    profile.headline = info.get('headline', profile.headline)
                    profile.location = info.get('location', profile.location)
                    profile.last_activity = info.get('last_activity')
                    profile.last_enrichment = timezone.now()
                    profile.save()
                    
                    # Actualizar persona asociada si existe
                    if profile.person:
                        person = profile.person
                        if not person.email and info.get('email'):
                            person.email = info['email']
                        if not person.phone and info.get('phone'):
                            person.phone = info['phone']
                        person.save()
                        
                    logger.info(f"Perfil enriquecido: {profile.name}")
                    
                # Esperar entre perfiles para no sobrecargar
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error enriqueciendo perfil {profile.profile_url}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error en tarea de enriquecimiento: {str(e)}")
        
    finally:
        channel.close()

@shared_task
def process_linkedin_updates():
    """
    Tarea para procesar actualizaciones de perfiles de LinkedIn.
    Verifica recursos del sistema antes de ejecutar.
    """
    # Verificar recursos del sistema
    if not check_system_resources():
        logger.info("Recursos del sistema insuficientes, posponiendo actualizaciones")
        return
        
    persons = Person.objects.all()
    processed_count = 0
    constructed_count = 0
    errors_count = 0

    for person in persons:
        # Verificar recursos antes de cada persona
        if not check_system_resources():
            logger.info("Recursos del sistema insuficientes, deteniendo actualizaciones")
            break
            
        linkedin_url = person.linkedin_url
        if not linkedin_url:
            linkedin_url = construct_linkedin_url(person.nombre, person.apellido_paterno)
            person.linkedin_url = linkedin_url
            person.save()
            constructed_count += 1
            logger.info(f"🌐 URL construida para {person.nombre}: {linkedin_url}")

        try:
            logger.info(f"Procesando: {person.nombre} ({linkedin_url})")
            scraped_data = scrape_linkedin_profile(linkedin_url, "amigro")  # Default unit
            update_person_from_scrape(person, scraped_data)
            processed_count += 1
            logger.info(f"✅ Actualizado: {person.nombre}")
        except Exception as e:
            logger.error(f"❌ Error procesando {person.nombre} ({linkedin_url}): {e}")
            errors_count += 1

    logger.info(f"Resumen: Procesados: {processed_count}, URLs construidas: {constructed_count}, Errores: {errors_count}")

@shared_task
def cleanup_linkedin_data():
    """
    Tarea para limpiar datos antiguos de LinkedIn.
    Verifica recursos del sistema antes de ejecutar.
    """
    # Verificar recursos del sistema
    if not check_system_resources():
        logger.info("Recursos del sistema insuficientes, posponiendo limpieza")
        return
        
    # Limpiar perfiles sin actividad reciente
    old_profiles = LinkedInProfile.objects.filter(
        last_activity__lt=timezone.now() - timedelta(days=180)
    )
    old_profiles.delete()
    
    # Limpiar caché de perfiles
    cache.delete_pattern("linkedin_profile_*")
    
    logger.info("Limpieza de datos de LinkedIn completada") 