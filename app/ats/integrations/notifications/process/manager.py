# app/ats/integrations/notifications/process/manager.py   
"""
Módulo de notificaciones de procesos para Grupo huntRED®.

Este módulo maneja notificaciones específicas de procesos como entrevistas y vacantes,
integrando con el sistema central de notificaciones y añadiendo lógica de negocio específica.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async

from app.models import Person, Vacante, BusinessUnit, ConfiguracionBU
from app.ml.analyzers.location_analyzer import LocationAnalyzer
from app.ats.integrations.notifications.core.core import NotificationManager as CoreNotificationManager

logger = logging.getLogger(__name__)

class ProcessNotificationManager(CoreNotificationManager):
    """
    Gestor de notificaciones de procesos que extiende el gestor central
    con funcionalidad específica para entrevistas y vacantes.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el gestor de notificaciones de procesos.
        
        Args:
            business_unit: Unidad de negocio requerida para las notificaciones
        """
        if not business_unit:
            raise ValueError("Se requiere especificar una unidad de negocio")
            
        super().__init__(business_unit)
        self.location_analyzer = LocationAnalyzer(business_unit)
        self.notification_templates = self._load_templates()
    
    async def _get_business_unit_channels(self) -> List[str]:
        """
        Obtiene los canales configurados para la unidad de negocio.
        
        Returns:
            Lista de nombres de canales configurados
        """
        try:
            config = await sync_to_async(ConfiguracionBU.objects.get)(
                business_unit=self.business_unit
            )
            return config.notification_channels or ['email']  # Default to email if not configured
        except ConfiguracionBU.DoesNotExist:
            logger.warning(f"No se encontró configuración de canales para {self.business_unit}")
            return ['email']
    
    def _load_templates(self) -> Dict:
        """
        Carga las plantillas de notificación según la unidad de negocio.
        
        Returns:
            Dict con las plantillas configuradas
        """
        return {
            'new_vacancy': {
                'HUNTRED': {
                    'title': 'Nueva oportunidad en huntRED',
                    'template': 'Hemos encontrado una nueva oportunidad que coincide con tu perfil en {company}. Tiempo estimado de viaje: {commute_time} minutos.'
                },
                'HUNTU': {
                    'title': 'Nueva oportunidad en huntU',
                    'template': '¡Oportunidad destacada en {company}! Tiempo de viaje: {commute_time} minutos. Nivel de tráfico: {traffic_level}.'
                },
                'SEXSI': {
                    'title': 'Nueva oportunidad en SEXSI',
                    'template': 'Oportunidad en {company}. Tiempo de viaje: {commute_time} minutos. Rutas alternativas disponibles.'
                }
            },
            'interview': {
                'HUNTRED': {
                    'title': 'Entrevista programada - huntRED',
                    'template': 'Tienes una entrevista programada el {datetime} en {location}. Tiempo estimado de viaje: {commute_time} minutos.'
                },
                'HUNTU': {
                    'title': '¡Entrevista confirmada! - huntU',
                    'template': '¡Preparate para tu entrevista el {datetime} en {location}! 🚀 Tiempo estimado: {commute_time} minutos.'
                },
                'SEXSI': {
                    'title': 'Cita confirmada - SEXSI',
                    'template': 'Tu cita está programada para el {datetime} en {location}. Llega con tiempo, el viaje toma aprox. {commute_time} minutos.'
                }
            },
            'interview_reminder': {
                'HUNTRED': {
                    'title': 'Recordatorio de entrevista - huntRED',
                    'template': 'Recordatorio: Tu entrevista en {location} comienza en {time_until}.'
                },
                'HUNTU': {
                    'title': '¡No olvides tu entrevista! - huntU',
                    'template': '¡Tu entrevista en {location} comienza en {time_until}! 🚀'
                },
                'SEXSI': {
                    'title': 'Recordatorio de cita - SEXSI',
                    'template': 'Tu cita en {location} comienza en {time_until}.'
                }
            }
        }
    
    async def _get_bu_template(self, template_type: str) -> Dict[str, str]:
        """
        Obtiene la plantilla para el tipo y unidad de negocio actual.
        
        Args:
            template_type: Tipo de plantilla (ej. 'new_vacancy', 'interview')
            
        Returns:
            Dict con las plantillas para la unidad de negocio actual
        """
        bu_name = self.business_unit.name.upper()
        return self.notification_templates.get(template_type, {}).get(bu_name, {})
