from celery import shared_task
from django.utils import timezone
from app.models import JobChannel, JobOpportunity, Channel, ChannelAnalytics
from app.publish.processors import get_processor
from app.publish.utils.content_adapters import ContentAdapter
import logging

logger = logging.getLogger(__name__)

@shared_task
async def process_new_opportunity(job_id: int):
    """
    Procesa una nueva oportunidad laboral
    """
    try:
        opportunity = await JobOpportunity.objects.aget(id=job_id)
        
        # Si está marcado para publicar
        if opportunity.publish_on_create:
            # Obtener canales relevantes
            relevant_channels = await Channel.objects.filter(
                type__in=['TELEGRAM_BOT', 'WHATSAPP_BROADCAST', 'LINKEDIN_PROFILE']
            ).filter(active=True).all()
            
            for channel in relevant_channels:
                # Crear registro de canal de trabajo
                job_channel = await JobChannel.objects.acreate(
                    opportunity=opportunity,
                    channel=channel,
                    status='pending'
                )
                
                # Programar publicación
                await publish_job_opportunity.delay(job_channel.id)

    except Exception as e:
        logger.error(f"Error processing new opportunity: {str(e)}")

@shared_task
async def publish_job_opportunity(job_channel_id: int):
    """
    Publica una oportunidad laboral en un canal específico
    """
    try:
        job_channel = await JobChannel.objects.aget(id=job_channel_id)
        
        # Obtener procesador específico para el canal
        processor = get_processor(job_channel.channel.type.name)
        
        # Adaptar contenido para el canal
        content = processor.adapt_content({
            'title': job_channel.opportunity.title,
            'description': job_channel.opportunity.description,
            'requirements': job_channel.opportunity.requirements,
            'salary_range': job_channel.opportunity.salary_range,
            'location': job_channel.opportunity.location
        })
        
        # Publicar
        result = await processor.publish(content)
        
        # Actualizar estado
        job_channel.status = 'published' if result else 'failed'
        job_channel.published_at = timezone.now()
        job_channel.save()

    except Exception as e:
        logger.error(f"Error publishing job opportunity: {str(e)}")
        job_channel.status = 'failed'
        job_channel.save()

@shared_task
async def update_channel_analytics():
    """
    Actualiza las métricas de todos los canales
    """
    try:
        active_channels = await Channel.objects.filter(active=True).all()
        
        for channel in active_channels:
            # Obtener procesador específico para el canal
            processor = get_processor(channel.type.name)
            
            # Obtener métricas
            analytics = await processor.get_analytics()
            
            # Crear o actualizar registro de métricas
            await ChannelAnalytics.objects.acreate(
                channel=channel,
                date=timezone.now().date(),
                impressions=analytics.get('impressions', 0),
                clicks=analytics.get('clicks', 0),
                engagement_rate=analytics.get('engagement_rate', 0.0),
                followers_count=analytics.get('followers_count', 0)
            )

    except Exception as e:
        logger.error(f"Error updating channel analytics: {str(e)}")
