"""
Monitor de costos para Meta Conversations 2025.

Este módulo proporciona herramientas para monitorear y optimizar costos de mensajería
con la API de Meta, identificando mensajes fuera de la ventana de 24 horas y 
categorías de mayor costo.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Set
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from asgiref.sync import sync_to_async
from app.models import MessageLog, BusinessUnit, Person

logger = logging.getLogger("meta_cost")


class MetaCostMonitor:
    """
    Monitor y optimizador de costos para mensajería Meta (WhatsApp, Instagram, Messenger).
    
    Proporciona:
    - Alertas de mensajes enviados fuera de ventana de 24h
    - Reportes de uso por categoría (service, utility, marketing)
    - Sugerencias de optimización
    """
    
    def __init__(self, alert_threshold: int = 10, cost_threshold: float = 5.0):
        """
        Inicializa el monitor de costos.
        
        Args:
            alert_threshold: Umbral de mensajes fuera de ventana para enviar alertas
            cost_threshold: Umbral de costo estimado para enviar alertas
        """
        self.alert_threshold = alert_threshold
        self.cost_threshold = cost_threshold
        
    async def get_window_violation_stats(self, 
                              business_unit_id: Optional[int] = None,
                              days: int = 1) -> Dict[str, Any]:
        """
        Obtiene estadísticas de mensajes enviados fuera de la ventana de 24 horas.
        
        Args:
            business_unit_id: ID opcional de unidad de negocio para filtrar
            days: Número de días hacia atrás para analizar
            
        Returns:
            Dict con estadísticas de violaciones de ventana
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Filtro base por tiempo y canales de Meta
        base_query = Q(
            sent_at__gte=start_date,
            channel__in=['whatsapp', 'instagram', 'messenger'],
            meta_within_24h_window=False
        )
        
        # Añadir filtro de unidad de negocio si se especifica
        if business_unit_id:
            base_query &= Q(business_unit_id=business_unit_id)
        
        # Ejecutar consulta
        messages = await sync_to_async(lambda: MessageLog.objects.filter(base_query))()
        count = await sync_to_async(lambda: messages.count())()
        
        # Agrupar por tipo de mensaje y calcular costos estimados
        by_type = await sync_to_async(lambda: messages.values('meta_pricing_category')
                                    .annotate(count=Count('id'),
                                             avg_cost=Avg('meta_cost'),
                                             total_cost=Sum('meta_cost')))()
                                             
        # Agrupar por template
        by_template = await sync_to_async(lambda: messages.values('template_name')
                                       .annotate(count=Count('id')))()
        
        return {
            'total_count': count,
            'by_category': list(by_type),
            'by_template': list(by_template),
            'period_days': days,
            'timestamp': timezone.now()
        }
    
    async def get_channel_distribution(self, 
                           business_unit_id: Optional[int] = None,
                           days: int = 30) -> Dict[str, Any]:
        """
        Obtiene la distribución de mensajes por canal y categoría.
        
        Args:
            business_unit_id: ID opcional de unidad de negocio para filtrar
            days: Número de días hacia atrás para analizar
            
        Returns:
            Dict con distribución de mensajes por canal
        """
        start_date = timezone.now() - timedelta(days=days)
        
        # Filtro base por tiempo
        base_query = Q(sent_at__gte=start_date)
        
        # Añadir filtro de unidad de negocio si se especifica
        if business_unit_id:
            base_query &= Q(business_unit_id=business_unit_id)
        
        # Ejecutar consultas
        by_channel = await sync_to_async(lambda: MessageLog.objects.filter(base_query)
                                      .values('channel')
                                      .annotate(count=Count('id')))()
        
        by_category = await sync_to_async(lambda: MessageLog.objects.filter(base_query)
                                       .values('channel', 'meta_pricing_category')
                                       .annotate(count=Count('id')))()
                                       
        return {
            'by_channel': list(by_channel),
            'by_category': list(by_category),
            'period_days': days
        }
    
    async def check_alert_conditions(self, business_unit_id: Optional[int] = None) -> bool:
        """
        Verifica si se cumplen las condiciones para enviar una alerta.
        
        Args:
            business_unit_id: ID opcional de unidad de negocio para filtrar
            
        Returns:
            bool: True si se deben enviar alertas
        """
        # Obtener estadísticas de violaciones de ventana
        stats = await self.get_window_violation_stats(business_unit_id, days=1)
        
        # Verificar condiciones
        if stats['total_count'] >= self.alert_threshold:
            return True
            
        # Verificar costo estimado
        for category in stats['by_category']:
            if category.get('total_cost', 0) and category['total_cost'] >= self.cost_threshold:
                return True
                
        return False
    
    async def send_cost_alert(self, recipients: List[str], business_unit_id: Optional[int] = None):
        """
        Envía una alerta por email sobre costos de mensajería Meta.
        
        Args:
            recipients: Lista de correos electrónicos para recibir la alerta
            business_unit_id: ID opcional de unidad de negocio para filtrar
        """
        try:
            # Obtener datos
            stats = await self.get_window_violation_stats(business_unit_id, days=1)
            distribution = await self.get_channel_distribution(business_unit_id, days=7)
            
            # Obtener nombre de unidad de negocio
            bu_name = "Todas las unidades"
            if business_unit_id:
                bu = await sync_to_async(lambda: BusinessUnit.objects.get(id=business_unit_id))()
                bu_name = bu.name
                
            # Preparar contexto
            context = {
                'business_unit': bu_name,
                'stats': stats,
                'distribution': distribution,
                'date': timezone.now().strftime("%d/%m/%Y %H:%M")
            }
            
            # Renderizar email
            subject = f"[ALERTA] Costos de mensajería Meta - {bu_name}"
            html_content = render_to_string('emails/meta_cost_alert.html', context)
            text_content = f"""
            ALERTA DE COSTOS META CONVERSATIONS
            
            Unidad de negocio: {bu_name}
            Mensajes fuera de ventana 24h: {stats['total_count']}
            Fecha: {context['date']}
            
            Revise el dashboard para más detalles.
            """
            
            # Enviar email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Alerta de costos enviada a {len(recipients)} destinatarios")
            
        except Exception as e:
            logger.error(f"Error enviando alerta de costos: {str(e)}")
    
    async def generate_optimization_suggestions(self, business_unit_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Genera sugerencias para optimizar costos de mensajería.
        
        Args:
            business_unit_id: ID opcional de unidad de negocio
            
        Returns:
            Lista de sugerencias con acciones recomendadas
        """
        # Obtener datos
        window_stats = await self.get_window_violation_stats(business_unit_id, days=7)
        distribution = await self.get_channel_distribution(business_unit_id, days=30)
        
        suggestions = []
        
        # Sugerencia: Plantillas con mayor tasa de mensajes fuera de ventana
        if window_stats['by_template']:
            top_templates = sorted(window_stats['by_template'], key=lambda x: x['count'], reverse=True)[:3]
            if top_templates:
                templates_names = [t['template_name'] for t in top_templates]
                suggestions.append({
                    'type': 'high_window_violation',
                    'templates': templates_names,
                    'action': 'Considerar rediseñar estas plantillas para enviar en horarios óptimos o fusionarlas para maximizar la ventana de 24h.'
                })
        
        # Sugerencia: Migración a canales sin costo
        meta_count = sum(item['count'] for item in distribution['by_channel'] 
                        if item['channel'] in ['whatsapp', 'instagram', 'messenger'])
                        
        other_count = sum(item['count'] for item in distribution['by_channel'] 
                        if item['channel'] not in ['whatsapp', 'instagram', 'messenger'])
                        
        if meta_count > 0 and meta_count > other_count * 2:  # Si usamos el doble de mensajes Meta que otros canales
            suggestions.append({
                'type': 'channel_migration',
                'meta_count': meta_count,
                'other_count': other_count,
                'action': 'Considerar migrar mensajes de marketing o notificaciones no críticas a Telegram o Email para reducir costos.'
            })
        
        # Sugerencia: Optimización de ventana
        if window_stats['total_count'] > self.alert_threshold:
            suggestions.append({
                'type': 'window_optimization',
                'count': window_stats['total_count'],
                'action': 'Implementar mecanismos para reactivar conversaciones antes de que expire la ventana de 24h.'
            })
            
        return suggestions


# Función auxiliar para ejecutar el monitor como tarea programada
async def run_cost_monitoring():
    """
    Ejecuta el monitoreo de costos como tarea programada.
    Verifica condiciones de alerta y envía notificaciones si es necesario.
    """
    monitor = MetaCostMonitor()
    
    # Verificar condiciones de alerta para todas las unidades
    should_alert = await monitor.check_alert_conditions()
    
    if should_alert:
        # Obtener emails de administradores para enviar alertas
        admin_emails = ['admin@example.com']  # Reemplazar con obtención real de emails
        
        # Enviar alerta
        await monitor.send_cost_alert(admin_emails)
        
    # Verificar por unidad de negocio
    business_units = await sync_to_async(lambda: BusinessUnit.objects.filter(is_active=True))()
    
    for bu in business_units:
        should_alert_bu = await monitor.check_alert_conditions(business_unit_id=bu.id)
        
        if should_alert_bu:
            # Obtener emails de administradores de esta unidad
            bu_admin_emails = ['bu_admin@example.com']  # Reemplazar con obtención real
            
            # Enviar alerta específica de esta unidad
            await monitor.send_cost_alert(bu_admin_emails, business_unit_id=bu.id)
