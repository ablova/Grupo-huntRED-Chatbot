"""
Sistema de notificaciones inteligentes para campañas e insights estratégicos.
Se integra con el módulo de notificaciones existente para alertar a consultores y super admins.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.utils import timezone
from enum import Enum

from app.ats.notifications.notification_manager import NotificationManager
from app.ml.analyzers.scraping_ml_analyzer import ScrapingMLAnalyzer
from app.ats.publish.models import MarketingCampaign, RetargetingCampaign, AudienceSegment

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Tipos de notificaciones estratégicas."""
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_LAUNCHED = "campaign_launched"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    SECTOR_OPPORTUNITY = "sector_opportunity"
    HIGH_VALUE_DOMAIN = "high_value_domain"
    PAYMENT_ALERT = "payment_alert"
    PROCESS_OPTIMIZATION = "process_optimization"
    MARKET_TREND = "market_trend"
    ENVIRONMENTAL_FACTOR = "environmental_factor"
    STRATEGIC_INSIGHT = "strategic_insight"
    ERROR_ALERT = "error_alert"

class NotificationPriority(Enum):
    """Prioridades de notificación."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class StrategicNotificationService:
    """
    Servicio de notificaciones estratégicas para campañas e insights.
    """
    
    def __init__(self):
        self.notification_manager = NotificationManager()
        self.analyzer = ScrapingMLAnalyzer()
        self.last_notifications = {}  # Cache para evitar duplicados
        
    async def monitor_and_notify(self, business_unit: str = None):
        """
        Monitorea eventos y envía notificaciones automáticamente.
        """
        try:
            # 1. Monitorear campañas
            await self._monitor_campaigns(business_unit)
            
            # 2. Monitorear insights estratégicos
            await self._monitor_strategic_insights(business_unit)
            
            # 3. Monitorear métricas críticas
            await self._monitor_critical_metrics(business_unit)
            
            # 4. Monitorear factores del entorno
            await self._monitor_environmental_factors(business_unit)
            
        except Exception as e:
            logger.error(f"Error en monitoreo estratégico: {str(e)}")
            await self._send_error_notification(str(e))
    
    async def _monitor_campaigns(self, business_unit: str = None):
        """
        Monitorea eventos relacionados con campañas.
        """
        try:
            # Campañas recién creadas
            recent_campaigns = MarketingCampaign.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1),
                business_unit=business_unit
            ) if business_unit else MarketingCampaign.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=1)
            )
            
            for campaign in recent_campaigns:
                await self._notify_campaign_created(campaign)
            
            # Campañas lanzadas recientemente
            launched_campaigns = MarketingCampaign.objects.filter(
                status='active',
                launched_at__gte=timezone.now() - timedelta(hours=1),
                business_unit=business_unit
            ) if business_unit else MarketingCampaign.objects.filter(
                status='active',
                launched_at__gte=timezone.now() - timedelta(hours=1)
            )
            
            for campaign in launched_campaigns:
                await self._notify_campaign_launched(campaign)
            
            # Campañas con rendimiento excepcional
            high_performance_campaigns = MarketingCampaign.objects.filter(
                status='active',
                engagement_rate__gte=0.15,  # 15% o más
                business_unit=business_unit
            ) if business_unit else MarketingCampaign.objects.filter(
                status='active',
                engagement_rate__gte=0.15
            )
            
            for campaign in high_performance_campaigns:
                await self._notify_campaign_performance(campaign)
                
        except Exception as e:
            logger.error(f"Error monitoreando campañas: {str(e)}")
    
    async def _monitor_strategic_insights(self, business_unit: str = None):
        """
        Monitorea insights estratégicos y oportunidades.
        """
        try:
            # Obtener insights de movimientos sectoriales
            sector_data = await self.analyzer.analyze_sector_movements(
                business_unit=business_unit,
                timeframe_days=7  # Últimos 7 días
            )
            
            if sector_data.get('success'):
                # Notificar sectores con alto crecimiento
                growing_sectors = sector_data.get('growing_sectors', [])
                for sector in growing_sectors:
                    if sector.get('growth_score', 0) >= 0.8:  # Alto crecimiento
                        await self._notify_sector_opportunity(sector)
                
                # Notificar oportunidades de venta urgentes
                sales_opportunities = sector_data.get('sales_opportunities', [])
                for opportunity in sales_opportunities:
                    if opportunity.get('priority') == 'high' and opportunity.get('timeline') == 'urgent':
                        await self._notify_sales_opportunity(opportunity)
            
            # Obtener métricas globales/locales
            global_local_data = await self.analyzer.analyze_global_local_metrics(business_unit)
            
            if global_local_data.get('success'):
                # Notificar métricas críticas
                global_metrics = global_local_data.get('global_metrics', {})
                
                # Alerta si la tasa de éxito es baja
                if global_metrics.get('success_rate_30d', 1) < 0.8:
                    await self._notify_low_success_rate(global_metrics)
                
                # Alerta si el crecimiento es negativo
                if global_metrics.get('growth_rate_7d', 0) < 0:
                    await self._notify_negative_growth(global_metrics)
                    
        except Exception as e:
            logger.error(f"Error monitoreando insights estratégicos: {str(e)}")
    
    async def _monitor_critical_metrics(self, business_unit: str = None):
        """
        Monitorea métricas críticas del sistema.
        """
        try:
            # Obtener insights periódicos
            periodic_data = await self.analyzer.generate_periodic_insights(
                business_unit=business_unit,
                period='daily'
            )
            
            if periodic_data.get('success'):
                # Alerta por baja conversión
                creation_analysis = periodic_data.get('creation_analysis', {})
                if creation_analysis.get('conversion_rate', 1) < 0.2:
                    await self._notify_low_conversion_rate(creation_analysis)
                
                # Alerta por problemas de proceso
                process_performance = periodic_data.get('process_performance', {})
                for process, metrics in process_performance.get('processes', {}).items():
                    if metrics.get('efficiency_score', 1) < 0.7:
                        await self._notify_process_optimization(process, metrics)
                        
        except Exception as e:
            logger.error(f"Error monitoreando métricas críticas: {str(e)}")
    
    async def _monitor_environmental_factors(self, business_unit: str = None):
        """
        Monitorea factores del entorno que pueden afectar el negocio.
        """
        try:
            environmental_data = await self.analyzer.analyze_environmental_factors(business_unit)
            
            if environmental_data.get('success'):
                # Alerta por cambios regulatorios importantes
                regulatory_analysis = environmental_data.get('regulatory_analysis', {})
                if regulatory_analysis.get('impact_assessment', {}).get('operational_impact') == 'high':
                    await self._notify_regulatory_change(regulatory_analysis)
                
                # Alerta por tendencias tecnológicas críticas
                tech_analysis = environmental_data.get('tech_analysis', {})
                if tech_analysis.get('automation_impact', 0) > 0.5:
                    await self._notify_tech_trend(tech_analysis)
                    
        except Exception as e:
            logger.error(f"Error monitoreando factores del entorno: {str(e)}")
    
    async def _notify_campaign_created(self, campaign):
        """
        Notifica cuando se crea una nueva campaña.
        """
        notification_key = f"campaign_created_{campaign.id}"
        if self._should_send_notification(notification_key):
            await self._send_notification(
                notification_type=NotificationType.CAMPAIGN_CREATED,
                priority=NotificationPriority.MEDIUM,
                title="Nueva Campaña Creada",
                message=f"Se ha creado la campaña '{campaign.name}' en {campaign.business_unit}",
                recipients=['consultants', 'super_admins'],
                context={
                    'campaign': campaign,
                    'business_unit': campaign.business_unit,
                    'created_by': getattr(campaign, 'created_by', 'Sistema')
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_campaign_launched(self, campaign):
        """
        Notifica cuando se lanza una campaña.
        """
        notification_key = f"campaign_launched_{campaign.id}"
        if self._should_send_notification(notification_key):
            await self._send_notification(
                notification_type=NotificationType.CAMPAIGN_LAUNCHED,
                priority=NotificationPriority.HIGH,
                title="Campaña Lanzada",
                message=f"La campaña '{campaign.name}' ha sido lanzada exitosamente",
                recipients=['consultants', 'super_admins'],
                context={
                    'campaign': campaign,
                    'launch_time': getattr(campaign, 'launched_at', timezone.now()),
                    'expected_reach': getattr(campaign, 'target_audience_size', 0)
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_campaign_performance(self, campaign):
        """
        Notifica rendimiento excepcional de campañas.
        """
        notification_key = f"campaign_performance_{campaign.id}"
        if self._should_send_notification(notification_key, hours=24):
            engagement_rate = getattr(campaign, 'engagement_rate', 0)
            await self._send_notification(
                notification_type=NotificationType.CAMPAIGN_PERFORMANCE,
                priority=NotificationPriority.HIGH,
                title="Rendimiento Excepcional",
                message=f"La campaña '{campaign.name}' tiene un engagement del {engagement_rate*100:.1f}%",
                recipients=['consultants', 'super_admins'],
                context={
                    'campaign': campaign,
                    'engagement_rate': engagement_rate,
                    'conversion_rate': getattr(campaign, 'conversion_rate', 0),
                    'roi': getattr(campaign, 'roi', 0)
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_sector_opportunity(self, sector_data: Dict):
        """
        Notifica oportunidades sectoriales.
        """
        sector = sector_data.get('sector', 'Unknown')
        notification_key = f"sector_opportunity_{sector}"
        if self._should_send_notification(notification_key, hours=12):
            await self._send_notification(
                notification_type=NotificationType.SECTOR_OPPORTUNITY,
                priority=NotificationPriority.HIGH,
                title="Oportunidad Sectorial Detectada",
                message=f"El sector {sector} muestra crecimiento del {sector_data.get('growth_score', 0)*100:.1f}%",
                recipients=['consultants', 'super_admins'],
                context={
                    'sector': sector_data,
                    'growth_score': sector_data.get('growth_score'),
                    'total_vacancies': sector_data.get('total_vacancies'),
                    'recommended_action': f"Enfocar esfuerzos de venta en {sector}"
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_sales_opportunity(self, opportunity: Dict):
        """
        Notifica oportunidades de venta urgentes.
        """
        sector = opportunity.get('sector', 'Unknown')
        notification_key = f"sales_opportunity_{sector}_{opportunity.get('type')}"
        if self._should_send_notification(notification_key, hours=6):
            await self._send_notification(
                notification_type=NotificationType.SECTOR_OPPORTUNITY,
                priority=NotificationPriority.URGENT,
                title="Oportunidad de Venta Urgente",
                message=f"Oportunidad en {sector}: {opportunity.get('description')}",
                recipients=['consultants', 'super_admins'],
                context={
                    'opportunity': opportunity,
                    'recommended_action': opportunity.get('recommended_action'),
                    'expected_roi': opportunity.get('expected_roi'),
                    'timeline': opportunity.get('timeline')
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_low_success_rate(self, metrics: Dict):
        """
        Notifica cuando la tasa de éxito es baja.
        """
        notification_key = "low_success_rate"
        if self._should_send_notification(notification_key, hours=6):
            success_rate = metrics.get('success_rate_30d', 0)
            await self._send_notification(
                notification_type=NotificationType.PROCESS_OPTIMIZATION,
                priority=NotificationPriority.HIGH,
                title="Tasa de Éxito Baja",
                message=f"La tasa de éxito del scraping es del {success_rate*100:.1f}%",
                recipients=['super_admins'],
                context={
                    'metrics': metrics,
                    'recommended_action': 'Revisar configuración de scraping y dominios',
                    'impact': 'Puede afectar la calidad de datos y oportunidades'
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_negative_growth(self, metrics: Dict):
        """
        Notifica cuando hay crecimiento negativo.
        """
        notification_key = "negative_growth"
        if self._should_send_notification(notification_key, hours=12):
            growth_rate = metrics.get('growth_rate_7d', 0)
            await self._send_notification(
                notification_type=NotificationType.STRATEGIC_INSIGHT,
                priority=NotificationPriority.HIGH,
                title="Crecimiento Negativo Detectado",
                message=f"El sistema muestra crecimiento negativo del {abs(growth_rate)*100:.1f}%",
                recipients=['super_admins'],
                context={
                    'metrics': metrics,
                    'growth_rate': growth_rate,
                    'recommended_action': 'Analizar causas y ajustar estrategia',
                    'impact': 'Puede indicar problemas en el mercado o configuración'
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_low_conversion_rate(self, analysis: Dict):
        """
        Notifica cuando la tasa de conversión es baja.
        """
        notification_key = "low_conversion_rate"
        if self._should_send_notification(notification_key, hours=6):
            conversion_rate = analysis.get('conversion_rate', 0)
            await self._send_notification(
                notification_type=NotificationType.PROCESS_OPTIMIZATION,
                priority=NotificationPriority.MEDIUM,
                title="Tasa de Conversión Baja",
                message=f"La tasa de conversión es del {conversion_rate*100:.1f}%",
                recipients=['consultants', 'super_admins'],
                context={
                    'analysis': analysis,
                    'recommended_action': 'Revisar filtros de vacantes y criterios',
                    'impact': 'Afecta la calidad de leads generados'
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_process_optimization(self, process: str, metrics: Dict):
        """
        Notifica cuando un proceso necesita optimización.
        """
        notification_key = f"process_optimization_{process}"
        if self._should_send_notification(notification_key, hours=12):
            efficiency = metrics.get('efficiency_score', 0)
            await self._send_notification(
                notification_type=NotificationType.PROCESS_OPTIMIZATION,
                priority=NotificationPriority.MEDIUM,
                title=f"Optimización de Proceso: {process.title()}",
                message=f"La eficiencia de {process} es del {efficiency*100:.1f}%",
                recipients=['super_admins'],
                context={
                    'process': process,
                    'metrics': metrics,
                    'recommended_action': f'Revisar y optimizar flujo de {process}',
                    'impact': f'Puede mejorar rendimiento general del sistema'
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_regulatory_change(self, analysis: Dict):
        """
        Notifica cambios regulatorios importantes.
        """
        notification_key = "regulatory_change"
        if self._should_send_notification(notification_key, hours=24):
            await self._send_notification(
                notification_type=NotificationType.ENVIRONMENTAL_FACTOR,
                priority=NotificationPriority.HIGH,
                title="Cambio Regulatorio Importante",
                message="Se han detectado cambios regulatorios que pueden afectar operaciones",
                recipients=['super_admins'],
                context={
                    'analysis': analysis,
                    'impact': analysis.get('impact_assessment'),
                    'recommendations': analysis.get('recommendations', []),
                    'action_required': 'Revisar compliance y ajustar procesos'
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _notify_tech_trend(self, analysis: Dict):
        """
        Notifica tendencias tecnológicas importantes.
        """
        notification_key = "tech_trend"
        if self._should_send_notification(notification_key, hours=24):
            automation_impact = analysis.get('automation_impact', 0)
            await self._send_notification(
                notification_type=NotificationType.MARKET_TREND,
                priority=NotificationPriority.MEDIUM,
                title="Tendencia Tecnológica Detectada",
                message=f"Impacto de automatización: {automation_impact*100:.1f}%",
                recipients=['consultants', 'super_admins'],
                context={
                    'analysis': analysis,
                    'emerging_technologies': analysis.get('emerging_technologies', []),
                    'recommendations': analysis.get('recommendations', []),
                    'action_required': 'Adaptar servicios y estrategias'
                }
            )
            self._mark_notification_sent(notification_key)
    
    async def _send_error_notification(self, error_message: str):
        """
        Notifica errores críticos.
        """
        await self._send_notification(
            notification_type=NotificationType.ERROR_ALERT,
            priority=NotificationPriority.URGENT,
            title="Error en Sistema de Insights",
            message=f"Error detectado: {error_message}",
            recipients=['super_admins'],
            context={
                'error_message': error_message,
                'timestamp': timezone.now().isoformat(),
                'action_required': 'Revisar logs y corregir problema'
            }
        )
    
    async def _send_notification(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority,
        title: str,
        message: str,
        recipients: List[str],
        context: Dict = None
    ):
        """
        Envía notificación a través del sistema existente.
        """
        try:
            # Determinar canales según prioridad
            channels = self._get_channels_by_priority(priority)
            
            # Determinar destinatarios
            actual_recipients = await self._get_recipients(recipients)
            
            for recipient in actual_recipients:
                for channel in channels:
                    await self.notification_manager.channels[channel].send(
                        recipient=recipient,
                        subject=title,
                        template=self._get_template_by_type(notification_type),
                        context={
                            'title': title,
                            'message': message,
                            'priority': priority.value,
                            'notification_type': notification_type.value,
                            'timestamp': timezone.now().isoformat(),
                            **context or {}
                        }
                    )
                    
            logger.info(f"Notificación enviada: {title} - {recipients}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
    
    def _get_channels_by_priority(self, priority: NotificationPriority) -> List[str]:
        """
        Determina canales según prioridad.
        """
        if priority == NotificationPriority.URGENT:
            return ['telegram', 'email', 'whatsapp']
        elif priority == NotificationPriority.HIGH:
            return ['email', 'telegram']
        elif priority == NotificationPriority.MEDIUM:
            return ['email']
        else:
            return ['email']
    
    async def _get_recipients(self, recipient_types: List[str]) -> List:
        """
        Obtiene destinatarios según tipo.
        """
        recipients = []
        
        # Importar modelos necesarios
        from django.contrib.auth.models import User
        
        if 'consultants' in recipient_types:
            # Obtener consultores
            consultants = User.objects.filter(
                groups__name='Consultants',
                is_active=True
            )
            recipients.extend(consultants)
        
        if 'super_admins' in recipient_types:
            # Obtener super admins
            super_admins = User.objects.filter(
                is_superuser=True,
                is_active=True
            )
            recipients.extend(super_admins)
        
        return recipients
    
    def _get_template_by_type(self, notification_type: NotificationType) -> str:
        """
        Obtiene template según tipo de notificación.
        """
        templates = {
            NotificationType.CAMPAIGN_CREATED: 'strategic/campaign_created.html',
            NotificationType.CAMPAIGN_LAUNCHED: 'strategic/campaign_launched.html',
            NotificationType.CAMPAIGN_PERFORMANCE: 'strategic/campaign_performance.html',
            NotificationType.SECTOR_OPPORTUNITY: 'strategic/sector_opportunity.html',
            NotificationType.PAYMENT_ALERT: 'strategic/payment_alert.html',
            NotificationType.PROCESS_OPTIMIZATION: 'strategic/process_optimization.html',
            NotificationType.MARKET_TREND: 'strategic/market_trend.html',
            NotificationType.ENVIRONMENTAL_FACTOR: 'strategic/environmental_factor.html',
            NotificationType.STRATEGIC_INSIGHT: 'strategic/strategic_insight.html',
            NotificationType.ERROR_ALERT: 'strategic/error_alert.html'
        }
        
        return templates.get(notification_type, 'strategic/generic.html')
    
    def _should_send_notification(self, key: str, hours: int = 1) -> bool:
        """
        Verifica si se debe enviar la notificación (evita duplicados).
        """
        if key not in self.last_notifications:
            return True
        
        last_time = self.last_notifications[key]
        return timezone.now() - last_time > timedelta(hours=hours)
    
    def _mark_notification_sent(self, key: str):
        """
        Marca notificación como enviada.
        """
        self.last_notifications[key] = timezone.now()
    
    async def send_manual_notification(
        self,
        title: str,
        message: str,
        recipients: List[str],
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        context: Dict = None
    ):
        """
        Envía notificación manual.
        """
        await self._send_notification(
            notification_type=NotificationType.STRATEGIC_INSIGHT,
            priority=priority,
            title=title,
            message=message,
            recipients=recipients,
            context=context
        ) 