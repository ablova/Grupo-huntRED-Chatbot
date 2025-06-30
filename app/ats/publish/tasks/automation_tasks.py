"""
Tareas Automáticas Avanzadas para el Sistema de Publicación.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
import asyncio
import json

from app.ats.publish.models import (
    MarketingCampaign, CampaignApproval, CampaignMetrics, 
    CampaignAuditLog, AudienceSegment, ContentTemplate
)
from app.models import BusinessUnit

# Importaciones de motores
from app.ats.publish.segmentation.aura_segmentation import AURASegmentationEngine
from app.ats.publish.retargeting.retargeting_engine import IntelligentRetargetingEngine
from app.ats.publish.content.content_generator import IntelligentContentGenerator
from app.ats.publish.tasks.marketing_tasks import MarketingAutomationEngine

logger = logging.getLogger(__name__)

@shared_task
def automated_campaign_workflow_task():
    """
    Tarea que automatiza el workflow completo de campañas.
    """
    try:
        logger.info("Iniciando workflow automático de campañas")
        
        # 1. Crear aprobaciones automáticas para campañas pendientes
        pending_campaigns = MarketingCampaign.objects.filter(
            status='pending',
            approvals__isnull=True
        )
        
        for campaign in pending_campaigns:
            create_automatic_approval.delay(campaign.id)
        
        # 2. Ejecutar campañas aprobadas
        approved_campaigns = MarketingCampaign.objects.filter(
            status='active',
            scheduled_date__lte=timezone.now()
        )
        
        for campaign in approved_campaigns:
            execute_campaign.delay(campaign.id)
        
        # 3. Actualizar métricas de campañas activas
        active_campaigns = MarketingCampaign.objects.filter(status='active')
        
        for campaign in active_campaigns:
            update_campaign_metrics.delay(campaign.id)
        
        # 4. Generar contenido automático
        generate_automated_content.delay()
        
        # 5. Ejecutar retargeting automático
        execute_automated_retargeting.delay()
        
        logger.info("Workflow automático de campañas completado")
        
    except Exception as e:
        logger.error(f"Error en workflow automático: {str(e)}")

@shared_task
def create_automatic_approval(campaign_id: int):
    """
    Crea aprobación automática para una campaña.
    """
    try:
        campaign = MarketingCampaign.objects.get(id=campaign_id)
        
        # Verificar si ya existe una aprobación
        if campaign.approvals.exists():
            return
        
        # Crear aprobación automática
        approval = CampaignApproval.objects.create(
            campaign=campaign,
            status='approved',
            required_level='system',
            created_by=campaign.created_by,
            approved_by=campaign.created_by,
            approved_at=timezone.now(),
            approval_notes='Aprobación automática del sistema',
            digital_signature='auto_approved_' + str(int(timezone.now().timestamp()))
        )
        
        # Activar la campaña
        campaign.status = 'active'
        campaign.save()
        
        # Log de auditoría
        CampaignAuditLog.log_action(
            campaign=campaign,
            user=campaign.created_by,
            action='approved',
            notes='Aprobación automática del sistema'
        )
        
        logger.info(f"Aprobación automática creada para campaña {campaign.name}")
        
    except Exception as e:
        logger.error(f"Error creando aprobación automática: {str(e)}")

@shared_task
def execute_campaign(campaign_id: int):
    """
    Ejecuta una campaña aprobada.
    """
    try:
        campaign = MarketingCampaign.objects.get(id=campaign_id)
        
        # Verificar que la campaña esté aprobada
        if not campaign.approvals.filter(status='approved').exists():
            logger.warning(f"Campaña {campaign.name} no está aprobada")
            return
        
        # Ejecutar en loop asíncrono
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Generar contenido
            content_generator = IntelligentContentGenerator(campaign.business_unit)
            content = loop.run_until_complete(
                content_generator.generate_campaign_content(campaign)
            )
            
            # Ejecutar campaña
            automation_engine = MarketingAutomationEngine(campaign.business_unit)
            results = loop.run_until_complete(
                automation_engine.execute_campaign(campaign)
            )
            
            # Actualizar métricas iniciales
            if results:
                CampaignMetrics.objects.create(
                    campaign=campaign,
                    total_sent=results.get('targets_reached', 0),
                    total_delivered=results.get('targets_reached', 0),
                    engagement_score=results.get('engagement_rate', 0) * 10,
                    total_revenue=results.get('revenue', 0),
                    total_spent=campaign.budget or 0
                )
            
            # Log de auditoría
            CampaignAuditLog.log_action(
                campaign=campaign,
                user=campaign.created_by,
                action='activated',
                notes=f'Campaña ejecutada automáticamente. Resultados: {results}'
            )
            
            logger.info(f"Campaña {campaign.name} ejecutada exitosamente")
            
        finally:
            loop.close()
        
    except Exception as e:
        logger.error(f"Error ejecutando campaña {campaign_id}: {str(e)}")

@shared_task
def update_campaign_metrics(campaign_id: int):
    """
    Actualiza métricas de una campaña en tiempo real.
    """
    try:
        campaign = MarketingCampaign.objects.get(id=campaign_id)
        
        # Simular métricas en tiempo real (en producción esto vendría de APIs externas)
        import random
        
        # Obtener métricas actuales
        current_metrics = campaign.metrics.first()
        
        if current_metrics:
            # Simular incrementos
            new_opens = current_metrics.total_opened + random.randint(0, 10)
            new_clicks = current_metrics.total_clicked + random.randint(0, 5)
            new_conversions = current_metrics.total_converted + random.randint(0, 2)
            
            # Calcular nuevas tasas
            total_sent = current_metrics.total_sent
            open_rate = (new_opens / total_sent * 100) if total_sent > 0 else 0
            click_rate = (new_clicks / total_sent * 100) if total_sent > 0 else 0
            conversion_rate = (new_conversions / total_sent * 100) if total_sent > 0 else 0
            
            # Actualizar métricas
            current_metrics.total_opened = new_opens
            current_metrics.total_clicked = new_clicks
            current_metrics.total_converted = new_conversions
            current_metrics.open_rate = open_rate
            current_metrics.click_rate = click_rate
            current_metrics.conversion_rate = conversion_rate
            current_metrics.calculate_engagement_score()
            current_metrics.calculate_roi()
            current_metrics.save()
            
            logger.info(f"Métricas actualizadas para campaña {campaign.name}")
        
    except Exception as e:
        logger.error(f"Error actualizando métricas de campaña {campaign_id}: {str(e)}")

@shared_task
def generate_automated_content():
    """
    Genera contenido automático basado en análisis.
    """
    try:
        business_units = BusinessUnit.objects.all()
        
        for business_unit in business_units:
            # Ejecutar en loop asíncrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                automation_engine = MarketingAutomationEngine(business_unit)
                content_plan = loop.run_until_complete(
                    automation_engine.generate_weekly_marketing_content()
                )
                
                # Guardar contenido generado
                if content_plan:
                    save_generated_content.delay(business_unit.id, content_plan)
                
            finally:
                loop.close()
        
        logger.info("Contenido automático generado para todas las unidades de negocio")
        
    except Exception as e:
        logger.error(f"Error generando contenido automático: {str(e)}")

@shared_task
def save_generated_content(business_unit_id: int, content_plan: Dict[str, Any]):
    """
    Guarda el contenido generado automáticamente.
    """
    try:
        business_unit = BusinessUnit.objects.get(id=business_unit_id)
        
        # Crear campaña automática con el contenido generado
        campaign = MarketingCampaign.objects.create(
            name=f"Contenido Automático - {timezone.now().strftime('%Y-%m-%d')}",
            description="Contenido generado automáticamente por el sistema",
            campaign_type='awareness',
            business_unit=business_unit,
            status='pending',
            scheduled_date=timezone.now() + timedelta(hours=1),
            metadata={'auto_generated': True, 'content_plan': content_plan}
        )
        
        # Crear aprobación automática
        CampaignApproval.objects.create(
            campaign=campaign,
            status='approved',
            required_level='system',
            created_by=business_unit.owner if hasattr(business_unit, 'owner') else None,
            approved_by=business_unit.owner if hasattr(business_unit, 'owner') else None,
            approved_at=timezone.now(),
            approval_notes='Contenido generado automáticamente',
            digital_signature='auto_content_' + str(int(timezone.now().timestamp()))
        )
        
        logger.info(f"Contenido automático guardado para {business_unit.name}")
        
    except Exception as e:
        logger.error(f"Error guardando contenido generado: {str(e)}")

@shared_task
def execute_automated_retargeting():
    """
    Ejecuta campañas de retargeting automático.
    """
    try:
        business_units = BusinessUnit.objects.all()
        
        for business_unit in business_units:
            # Ejecutar en loop asíncrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                retargeting_engine = IntelligentRetargetingEngine(business_unit)
                
                # Obtener segmentos que necesitan retargeting
                segments_needing_retargeting = AudienceSegment.objects.filter(
                    business_unit=business_unit,
                    active=True
                )
                
                for segment in segments_needing_retargeting:
                    # Crear campaña de retargeting
                    campaign = loop.run_until_complete(
                        retargeting_engine.create_intelligent_retargeting_campaign(
                            name=f"Retargeting {segment.name}",
                            retargeting_type='engagement',
                            target_segments=[segment],
                            budget=100.0,
                            lookback_days=7
                        )
                    )
                    
                    # Ejecutar campaña
                    results = loop.run_until_complete(
                        retargeting_engine.execute_retargeting_campaign(campaign)
                    )
                    
                    logger.info(f"Retargeting ejecutado para segmento {segment.name}")
                
            finally:
                loop.close()
        
        logger.info("Retargeting automático completado")
        
    except Exception as e:
        logger.error(f"Error ejecutando retargeting automático: {str(e)}")

@shared_task
def cleanup_expired_approvals():
    """
    Limpia aprobaciones expiradas.
    """
    try:
        expired_approvals = CampaignApproval.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        )
        
        for approval in expired_approvals:
            approval.status = 'expired'
            approval.save()
            
            # Log de auditoría
            CampaignAuditLog.log_action(
                campaign=approval.campaign,
                user=approval.created_by,
                action='expired',
                notes='Aprobación expirada automáticamente'
            )
        
        logger.info(f"{expired_approvals.count()} aprobaciones expiradas limpiadas")
        
    except Exception as e:
        logger.error(f"Error limpiando aprobaciones expiradas: {str(e)}")

@shared_task
def generate_performance_report():
    """
    Genera reporte de rendimiento semanal.
    """
    try:
        # Obtener métricas de la última semana
        week_ago = timezone.now() - timedelta(days=7)
        
        campaigns = MarketingCampaign.objects.filter(
            created_at__gte=week_ago
        )
        
        report_data = {
            'total_campaigns': campaigns.count(),
            'active_campaigns': campaigns.filter(status='active').count(),
            'total_revenue': sum(
                campaign.metrics.aggregate(Sum('total_revenue'))['total_revenue__sum'] or 0 
                for campaign in campaigns
            ),
            'total_spent': sum(
                campaign.metrics.aggregate(Sum('total_spent'))['total_spent__sum'] or 0 
                for campaign in campaigns
            ),
            'avg_engagement': CampaignMetrics.objects.filter(
                campaign__in=campaigns
            ).aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0,
            'top_performing_campaigns': list(
                campaigns.annotate(
                    avg_engagement=Avg('metrics__engagement_score')
                ).order_by('-avg_engagement')[:5].values('name', 'avg_engagement')
            )
        }
        
        # Guardar reporte
        report_file = f"performance_report_{timezone.now().strftime('%Y%m%d')}.json"
        with open(f"reports/{report_file}", 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"Reporte de rendimiento generado: {report_file}")
        
    except Exception as e:
        logger.error(f"Error generando reporte de rendimiento: {str(e)}")

@shared_task
def optimize_campaigns_automatically():
    """
    Optimiza campañas automáticamente basado en métricas.
    """
    try:
        # Obtener campañas con bajo rendimiento
        low_performing_campaigns = MarketingCampaign.objects.filter(
            status='active',
            metrics__engagement_score__lt=5
        ).distinct()
        
        for campaign in low_performing_campaigns:
            # Ejecutar en loop asíncrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Optimizar campaña
                retargeting_engine = IntelligentRetargetingEngine(campaign.business_unit)
                
                # Obtener optimizaciones
                optimizations = loop.run_until_complete(
                    retargeting_engine.optimize_retargeting_campaign(campaign)
                )
                
                # Aplicar optimizaciones
                if optimizations:
                    campaign.metadata.update({
                        'optimizations_applied': optimizations,
                        'optimized_at': timezone.now().isoformat()
                    })
                    campaign.save()
                    
                    # Log de auditoría
                    CampaignAuditLog.log_action(
                        campaign=campaign,
                        user=campaign.created_by,
                        action='updated',
                        notes=f'Optimizaciones automáticas aplicadas: {optimizations}'
                    )
                
            finally:
                loop.close()
        
        logger.info(f"{low_performing_campaigns.count()} campañas optimizadas automáticamente")
        
    except Exception as e:
        logger.error(f"Error optimizando campañas automáticamente: {str(e)}")

# Configuración de tareas periódicas
@shared_task
def schedule_periodic_tasks():
    """
    Programa tareas periódicas.
    """
    from celery import current_app
    
    # Tarea cada 5 minutos
    current_app.conf.beat_schedule = {
        'automated-campaign-workflow': {
            'task': 'app.ats.publish.tasks.automation_tasks.automated_campaign_workflow_task',
            'schedule': 300.0,  # 5 minutos
        },
        'update-campaign-metrics': {
            'task': 'app.ats.publish.tasks.automation_tasks.update_campaign_metrics',
            'schedule': 600.0,  # 10 minutos
        },
        'cleanup-expired-approvals': {
            'task': 'app.ats.publish.tasks.automation_tasks.cleanup_expired_approvals',
            'schedule': 3600.0,  # 1 hora
        },
        'generate-automated-content': {
            'task': 'app.ats.publish.tasks.automation_tasks.generate_automated_content',
            'schedule': 86400.0,  # 1 día
        },
        'execute-automated-retargeting': {
            'task': 'app.ats.publish.tasks.automation_tasks.execute_automated_retargeting',
            'schedule': 43200.0,  # 12 horas
        },
        'optimize-campaigns-automatically': {
            'task': 'app.ats.publish.tasks.automation_tasks.optimize_campaigns_automatically',
            'schedule': 7200.0,  # 2 horas
        },
        'generate-performance-report': {
            'task': 'app.ats.publish.tasks.automation_tasks.generate_performance_report',
            'schedule': 604800.0,  # 1 semana
        },
    }
    
    logger.info("Tareas periódicas programadas") 