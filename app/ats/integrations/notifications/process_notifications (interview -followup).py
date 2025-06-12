# /home/pablo/app/ats/utils/process_notifications.py
"""
Módulo de notificaciones de procesos para Grupo huntRED®.
Maneja notificaciones específicas de procesos como entrevistas y vacantes,
integrando con el sistema central de notificaciones.
"""
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from django.conf import settings
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
    
    async def _get_commute_time(self, traffic_data: Dict[str, Any]) -> str:
        """
        Formatea el tiempo de viaje a partir de los datos de tráfico.
        
        Args:
            traffic_data: Datos de tráfico del LocationAnalyzer
            
        Returns:
            Tiempo de viaje formateado como string
        """
        if not traffic_data or 'duration' not in traffic_data:
            return "no disponible"
        return f"{int(traffic_data['duration'] / 60)}"
    
    async def _get_traffic_level(self, traffic_data: Dict[str, Any]) -> str:
        """
        Obtiene el nivel de tráfico en formato legible.
        
        Args:
            traffic_data: Datos de tráfico del LocationAnalyzer
            
        Returns:
            Nivel de tráfico formateado
        """
        levels = {
            'LOW': 'bajo',
            'MODERATE': 'moderado',
            'HEAVY': 'intenso',
            'STANDSTILL': 'congestionado'
        }
        return levels.get(traffic_data.get('traffic_level', '').upper(), 'normal')
    
    async def notify_new_vacancy(self, person: Person, vacancy: Vacante) -> bool:
        """
        Notifica sobre una nueva vacante con información de ubicación.
        
        Args:
            person: Persona a notificar
            vacancy: Vacante sobre la que se notifica
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Obtener análisis de ubicación
            location_data = {
                'origin': person.metadata.get('location'),
                'destination': vacancy.ubicacion
            }
            
            analysis = await self.location_analyzer.analyze(location_data)
            traffic_data = analysis.get('traffic_analysis', {}) if analysis else {}
            
            # Obtener plantilla para la unidad de negocio
            template = await self._get_bu_template('new_vacancy')
            if not template:
                logger.warning(f"No se encontró plantilla para nueva vacante en {self.business_unit.name}")
                return False
            
            # Formatear mensaje
            message = template['template'].format(
                company=vacancy.company_name,
                commute_time=await self._get_commute_time(traffic_data),
                traffic_level=await self._get_traffic_level(traffic_data)
            )
            
            # Obtener canales configurados
            channels = await self._get_business_unit_channels()
            
            # Enviar notificación
            result = await self.send_notification(
                message=message,
                channels=channels,
                options={
                    'type': 'new_vacancy',
                    'vacancy_id': str(vacancy.id),
                    'person_id': str(person.id)
                },
                title=template['title']
            )
            
            return all(result.values())
            
        except Exception as e:
            logger.error(f"Error notificando nueva vacante: {str(e)}", exc_info=True)
            return False
    
    async def notify_interview_scheduled(
        self, 
        person: Person, 
        interview_datetime: datetime,
        location: str,
        interview_type: str = 'entrevista',
        additional_notes: str = ''
    ) -> bool:
        """
        Notifica sobre una entrevista programada con información de ubicación.
        
        Args:
            person: Persona a notificar
            interview_datetime: Fecha y hora de la entrevista
            location: Ubicación de la entrevista
            interview_type: Tipo de entrevista (ej. 'entrevista', 'prueba técnica')
            additional_notes: Notas adicionales a incluir
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Obtener análisis de ubicación
            location_data = {
                'origin': person.metadata.get('location'),
                'destination': location
            }
            
            analysis = await self.location_analyzer.analyze(location_data)
            traffic_data = analysis.get('traffic_analysis', {}) if analysis else {}
            
            # Obtener plantilla para la unidad de negocio
            template = await self._get_bu_template('interview')
            if not template:
                logger.warning(f"No se encontró plantilla de entrevista en {self.business_unit.name}")
                return False
            
            # Formatear fecha/hora
            tz = timezone.get_current_timezone()
            local_dt = timezone.localtime(interview_datetime, timezone=tz)
            formatted_dt = local_dt.strftime('%A %d de %B a las %H:%M').capitalize()
            
            # Formatear mensaje
            message = template['template'].format(
                datetime=formatted_dt,
                location=location,
                commute_time=await self._get_commute_time(traffic_data),
                interview_type=interview_type,
                notes=f"\n\nNotas: {additional_notes}" if additional_notes else ''
            )
            
            # Obtener canales configurados
            channels = await self._get_business_unit_channels()
            
            # Enviar notificación
            result = await self.send_notification(
                message=message,
                channels=channels,
                options={
                    'type': 'interview_scheduled',
                    'interview_datetime': interview_datetime.isoformat(),
                    'location': location,
                    'person_id': str(person.id)
                },
                title=template['title']
            )
            
            return all(result.values())
            
        except Exception as e:
            logger.error(f"Error notificando entrevista: {str(e)}", exc_info=True)
            return False
        
    async def send_interview_reminder(
        self,
        person: Person,
        interview_datetime: datetime,
        location: str,
        reminder_minutes: int = 60,
        interview_type: str = 'entrevista'
    ) -> bool:
        """
        Envía un recordatorio de entrevista programada.
        
        Args:
            person: Persona a notificar
            interview_datetime: Fecha y hora de la entrevista
            location: Ubicación de la entrevista
            reminder_minutes: Minutos de anticipación para el recordatorio
            interview_type: Tipo de entrevista
            
        Returns:
            bool: True si el recordatorio se programó correctamente
        """
        try:
            now = timezone.now()
            reminder_time = interview_datetime - timedelta(minutes=reminder_minutes)
            
            # Si el recordatorio ya pasó, no hacer nada
            if reminder_time <= now:
                logger.warning(f"El recordatorio para la entrevista ya pasó: {reminder_time}")
                return False
                
            # Calcular tiempo restante
            time_until = reminder_time - now
            hours, remainder = divmod(int(time_until.total_seconds() / 60), 60)
            minutes = remainder % 60
            
            # Obtener plantilla
            template = await self._get_bu_template('interview_reminder')
            if not template:
                logger.warning(f"No se encontró plantilla de recordatorio en {self.business_unit.name}")
                return False
            
            # Formatear mensaje
            message = template['template'].format(
                time_until=f"{hours}h {minutes}m" if hours else f"{minutes} minutos",
                interview_type=interview_type,
                location=location
            )
            
            # Obtener canales configurados
            channels = await self._get_business_unit_channels()
            
            # Programar notificación
            result = await self.schedule_notification(
                message=message,
                scheduled_time=reminder_time,
                channels=channels,
                options={
                    'type': 'interview_reminder',
                    'interview_datetime': interview_datetime.isoformat(),
                    'location': location,
                    'person_id': str(person.id)
                },
                title=template['title']
            )
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error programando recordatorio: {str(e)}", exc_info=True)
            return False
    
    async def notify_new_vacancy(self, person: Person, vacancy: Vacante) -> bool:
        """
        Notifica sobre una nueva vacante con información de ubicación.
        
        Args:
            person: Candidato
            vacancy: Vacante
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Obtener análisis de ubicación
            location_data = {
                'origin': person.metadata.get('location'),
                'destination': vacancy.ubicacion
            }
            
            analysis = await self.location_analyzer.analyze(location_data)
            
            if not analysis or 'error' in analysis:
                return await self._send_basic_notification(person, vacancy)
            
            # Obtener datos de tráfico
            traffic_data = analysis.get('traffic_analysis', {})
            
            # Preparar datos para la notificación
            notification_data = {
                'company': vacancy.company_name,
                'commute_time': self._get_commute_time(traffic_data),
                'traffic_level': self._get_traffic_level(traffic_data),
                'alternative_routes': self._get_alternative_routes(analysis.get('alternative_routes', []))
            }
            
            # Obtener template según unidad de negocio
            bu_name = vacancy.business_unit.name
            template = self.notification_templates['new_vacancy'].get(
                bu_name,
                self.notification_templates['new_vacancy']['HUNTRED']
            )
            
            # Crear notificación
            notification = Notification.objects.create(
                person=person,
                title=template['title'],
                message=template['template'].format(**notification_data),
                type='vacancy',
                metadata={
                    'vacancy_id': vacancy.id,
                    'traffic_data': traffic_data,
                    'match_score': await self._calculate_match_score(person, vacancy)
                }
            )
            
            # Enviar notificación
            return await self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return False
    
    def _get_commute_time(self, traffic_data: Dict) -> str:
        """Obtiene el tiempo de viaje formateado."""
        if not traffic_data:
            return "No disponible"
        
        # Obtener el peor tiempo de viaje
        max_duration = max(
            time.get('duration', 0)
            for time in traffic_data.values()
            if isinstance(time, dict) and 'duration' in time
        )
        
        return f"{max_duration} minutos"
    
    def _get_traffic_level(self, traffic_data: Dict) -> str:
        """Obtiene el nivel de tráfico en español."""
        if not traffic_data:
            return "No disponible"
        
        # Obtener el peor nivel de tráfico
        traffic_levels = [
            time.get('traffic_level', 'unknown')
            for time in traffic_data.values()
            if isinstance(time, dict) and 'traffic_level' in time
        ]
        
        if not traffic_levels:
            return "No disponible"
        
        worst_level = max(traffic_levels, key=lambda x: {
            'low': 1,
            'medium': 2,
            'high': 3,
            'unknown': 0
        }.get(x, 0))
        
        levels = {
            'low': 'Bajo',
            'medium': 'Moderado',
            'high': 'Alto',
            'unknown': 'No disponible'
        }
        
        return levels.get(worst_level, 'No disponible')
    
    def _get_alternative_routes(self, routes: List[Dict]) -> List[Dict]:
        """Obtiene rutas alternativas formateadas."""
        if not routes:
            return []
        
        return [
            {
                'duration': f"{route['duration']} min",
                'distance': f"{route['distance']:.1f} km",
                'traffic_level': self._get_traffic_level({'traffic_level': route['traffic_level']})
            }
            for route in routes
        ]
    
    async def _calculate_match_score(self, person: Person, vacancy: Vacante) -> float:
        """Calcula el score de matching."""
        from app.ml.core.models.base import MatchmakingLearningSystem
        matcher = MatchmakingLearningSystem()
        return await matcher.calculate_match_score(person, vacancy)
    
    async def _send_basic_notification(self, person: Person, vacancy: Vacante) -> bool:
        """Envía una notificación básica sin datos de tráfico."""
        try:
            notification = Notification.objects.create(
                person=person,
                title=f"Nueva oportunidad en {vacancy.company_name}",
                message=f"Hemos encontrado una nueva oportunidad que coincide con tu perfil.",
                type='vacancy',
                metadata={'vacancy_id': vacancy.id}
            )
            
            return await self._send_notification(notification)
            
        except Exception as e:
            logger.error(f"Error enviando notificación básica: {str(e)}")
            return False
    
    async def _send_notification(self, notification: Notification) -> bool:
        """
        Envía la notificación a través de los canales configurados.
        
        Args:
            notification: Objeto Notification
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Enviar por email
            if notification.person.email:
                await self._send_email_notification(notification)
            
            # Enviar por push
            if notification.person.push_token:
                await self._send_push_notification(notification)
            
            # Enviar por SMS
            if notification.person.phone:
                await self._send_sms_notification(notification)
            
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return False
    
    async def _send_email_notification(self, notification: Notification):
        """Envía notificación por email."""
        if not self.config.get('smtp'):
            logger.warning("No hay configuración SMTP disponible")
            return
            
        try:
            # Implementar envío de email usando la configuración SMTP
            pass
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
    
    async def _send_push_notification(self, notification: Notification):
        """Envía notificación push."""
        try:
            # Implementar envío push
            pass
        except Exception as e:
            logger.error(f"Error enviando push: {str(e)}")
    
    async def _send_sms_notification(self, notification: Notification):
        """Envía notificación por SMS."""
        try:
            # Implementar envío SMS
            pass
        except Exception as e:
            logger.error(f"Error enviando SMS: {str(e)}") 