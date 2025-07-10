# app/ats/notifications/recruitment_notifications.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo de Notificaciones de Reclutamiento para huntRED®

Este módulo proporciona servicios de notificación específicos para procesos
de reclutamiento, como actualizaciones de candidatos, nuevas vacantes,
entrevistas programadas, y otros eventos relacionados con el reclutamiento.

Utiliza un patrón singleton con lazy loading para evitar acceder a la base de datos
durante la importación del módulo, lo que previene errores durante migraciones.

Características principales:
- Arquitectura orientada a eventos para notificaciones de reclutamiento
- Soporte para múltiples canales de comunicación (email, WhatsApp, Telegram)
- Gestión avanzada de errores y reintentos
- Soporte para operaciones síncronas y asíncronas
- Plantillas personalizables por unidad de negocio
- Integración con sistema de analítica para seguimiento de engagement
- Internacionalización (i18n) para mensajes en múltiples idiomas
"""

import logging
import asyncio
import json
import time
import uuid
import datetime
from functools import wraps
from typing import Optional, Dict, Any, List, Union, Callable, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)

# Notificador singleton (inicialmente None para lazy loading)
_recruitment_notifier = None

# Constantes de configuración
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 2  # segundos
MAX_BATCH_SIZE = 50
NOTIFICATION_TIMEOUT = 30  # segundos


class NotificationPriority(str, Enum):
    """Niveles de prioridad para las notificaciones."""
    LOW = "low"             # Notificaciones informativas, no urgentes
    NORMAL = "normal"       # Prioridad estándar (default)
    HIGH = "high"           # Notificaciones importantes que requieren atención pronta
    URGENT = "urgent"       # Notificaciones críticas que requieren atención inmediata


class NotificationType(str, Enum):
    """Tipos de notificación de reclutamiento."""
    # Relacionados con candidatos
    NEW_CANDIDATE = "new_candidate"
    CANDIDATE_STATUS_CHANGE = "candidate_status_change"
    CANDIDATE_MATCH = "candidate_match"
    CANDIDATE_ASSESSMENT = "candidate_assessment"
    CANDIDATE_FEEDBACK = "candidate_feedback"
    
    # Notificaciones especiales centradas en el candidato
    CANDIDATE_PROCESS_START = "candidate_process_start"     # Inicio del proceso de selección
    CANDIDATE_APPLICATION_RECEIVED = "candidate_application_received"  # Confirmación de recepción
    CANDIDATE_UNDER_REVIEW = "candidate_under_review"       # CV/perfil en revisión
    CANDIDATE_SHORTLISTED = "candidate_shortlisted"        # Preseleccionado
    CANDIDATE_NOT_SELECTED = "candidate_not_selected"       # No seleccionado para la vacante
    CANDIDATE_PROCESS_UPDATE = "candidate_process_update"    # Actualización general del proceso
    CANDIDATE_ALTERNATIVE_MATCH = "candidate_alternative_match"  # Alternativa para otra vacante
    CANDIDATE_PARALLEL_PROCESS = "candidate_parallel_process"  # Procesos en paralelo
    CANDIDATE_THANK_YOU = "candidate_thank_you"            # Agradecimiento por participar
    CANDIDATE_FEEDBACK_REQUEST = "candidate_feedback_request"  # Solicitud de retroalimentación
    CANDIDATE_FUTURE_OPPORTUNITIES = "candidate_future_opportunities"  # Oportunidades futuras
    
    # Relacionados con vacantes
    NEW_VACANCY = "new_vacancy"
    VACANCY_UPDATE = "vacancy_update"
    VACANCY_CLOSE = "vacancy_close"
    
    # Relacionados con entrevistas
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_REMINDER = "interview_reminder"
    INTERVIEW_RESCHEDULED = "interview_rescheduled"
    INTERVIEW_CANCELLED = "interview_cancelled"
    INTERVIEW_FEEDBACK = "interview_feedback"
    INTERVIEW_NEXT_STEPS = "interview_next_steps"          # Próximos pasos después de entrevista
    INTERVIEW_THANK_YOU = "interview_thank_you"            # Agradecimiento post-entrevista
    
    # Relacionados con colocaciones
    PLACEMENT_OFFER = "placement_offer"
    PLACEMENT_ACCEPTED = "placement_accepted"
    PLACEMENT_REJECTED = "placement_rejected"
    PLACEMENT_DETAILS = "placement_details"                # Detalles del contrato/posición
    PLACEMENT_ONBOARDING = "placement_onboarding"          # Proceso de onboarding
    
    # Relacionados con el sistema
    SYSTEM_ALERT = "system_alert"
    TASK_REMINDER = "task_reminder"


@dataclass
class NotificationEvent:
    """Representa un evento de notificación en el sistema."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.SYSTEM_ALERT
    subject: str = ""
    content: str = ""
    priority: NotificationPriority = NotificationPriority.NORMAL
    recipients: List[Any] = field(default_factory=list)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, sent, failed
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a un diccionario para serialización."""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "subject": self.subject,
            "content": self.content,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "recipients": [str(r) for r in self.recipients],
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime.datetime) else self.timestamp,
            "metadata": self.metadata,
            "context": self.context,
            "status": self.status,
            "retry_count": self.retry_count
        }


class NotificationChannel:
    """Interfaz base para todos los canales de notificación."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    def send(self, event: NotificationEvent) -> bool:
        """Envía una notificación a través de este canal."""
        raise NotImplementedError("Los canales concretos deben implementar este método")
    
    async def send_async(self, event: NotificationEvent) -> bool:
        """Envía una notificación asíncrona a través de este canal."""
        raise NotImplementedError("Los canales concretos deben implementar este método")


def retry_on_failure(max_attempts=DEFAULT_RETRY_ATTEMPTS, delay=DEFAULT_RETRY_DELAY):
    """Decorador que reintenta una función en caso de error."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_exception = e
                    if attempts < max_attempts:
                        logger.warning(f"Error en {func.__name__}, reintentando ({attempts}/{max_attempts}): {str(e)}")
                        time.sleep(delay * attempts)  # Backoff exponencial
            
            logger.error(f"Error persistente en {func.__name__} después de {max_attempts} intentos: {str(last_exception)}")
            raise last_exception
        
        return wrapper
    
    return decorator


class RecruitmentNotifier:
    """    
    Servicio avanzado de notificaciones para procesos de reclutamiento.
    
    Maneja la generación y envío de notificaciones relacionadas con procesos de
    reclutamiento a través de múltiples canales (email, WhatsApp, Telegram),
    con soporte para operaciones síncronas y asíncronas, internacionalización, 
    y analítica de engagement.
    
    Esta clase implementa un patrón singleton con lazy loading para evitar
    accesos a la base de datos durante la importación del módulo.
    """
    
    def __init__(self, business_unit=None):
        """
        Inicializa el notificador de reclutamiento.
        
        Args:
            business_unit: Unidad de negocio para la cual se enviarán las notificaciones.
                          Si es None, se utilizará la primera unidad de negocio disponible.
        """
        self.business_unit = business_unit
        self.event_queue = asyncio.Queue() if asyncio.get_event_loop_policy().get_event_loop().is_running() else None
        self.channels = []
        self.template_engine = None
        self.analytics_tracker = None
        self.notification_history = {}
        self._initialize_services()
        logger.info(f"RecruitmentNotifier inicializado para unidad de negocio: {getattr(self.business_unit, 'name', 'None')}")
    
    def _initialize_services(self):
        """Inicializa todos los servicios y dependencias requeridas."""
        try:
            self._initialize_channels()
            self._initialize_template_engine()
            self._initialize_analytics()
            
            # Iniciar procesador de eventos asíncrono si estamos en un entorno async
            if self.event_queue:
                asyncio.create_task(self._process_event_queue())
                
        except Exception as e:
            logger.error(f"Error al inicializar servicios de notificación: {str(e)}")
    
    def _initialize_channels(self) -> None:
        """Inicializa los canales de notificación basados en la configuración de la unidad de negocio."""
        self.channels = []
            
        # Determinar qué canales están habilitados para esta unidad de negocio usando ConfiguracionBU
        try:
            # Intentar obtener la configuración de la unidad de negocio
            config_bu = None
            try:
                from app.models import ConfiguracionBU
                if self.business_unit and self.business_unit.id:
                    config_bu = ConfiguracionBU.objects.filter(business_unit=self.business_unit).order_by('-updated_at').first()
            except Exception as e:
                logger.warning(f"No se pudo obtener la configuración de la unidad de negocio: {str(e)}")
            
            # Obtener configuración de canales desde ConfiguracionBU o usar valores predeterminados
            channels_config = {}
            if config_bu and hasattr(config_bu, 'config') and isinstance(config_bu.config, dict):
                # Extraer configuración de canales del JSON
                channels_config = config_bu.config.get('notification_channels', {})
                logger.debug(f"Configuración de canales cargada desde ConfiguracionBU: {channels_config}")
            
            # Configuración predeterminada si no hay una específica
            default_channels = {
                'email': True,        # Email habilitado por defecto
                'whatsapp': False,    # WhatsApp deshabilitado por defecto
                'telegram': False,    # Telegram deshabilitado por defecto
                'internal': True      # Sistema interno habilitado por defecto
            }
            
            # Combinar configuración predeterminada con configuración específica
            enabled_channels = {**default_channels, **channels_config}
            
            # Inicializar canales habilitados
            if enabled_channels.get('email', True):
                from app.ats.integrations.notifications.core.channels import EmailChannel
                email_config = config_bu.config.get('email_config', {}) if config_bu else {}
                self.channels.append(EmailChannel(config=email_config))
                logger.debug("Canal de correo electrónico habilitado")
            
            # Importante: NO usar Twilio según política de seguridad estricta
            # Usar solo el sistema interno de mensajería WhatsApp
            if enabled_channels.get('whatsapp', False):
                from app.ats.integrations.channels.whatsapp.whatsapp import WhatsAppChannel
                whatsapp_config = config_bu.config.get('whatsapp_config', {}) if config_bu else {}
                self.channels.append(WhatsAppChannel(config=whatsapp_config))
                logger.debug("Canal de WhatsApp habilitado (sistema interno)")
            
            if enabled_channels.get('telegram', False):
                from app.ats.integrations.notifications.channels.telegram import TelegramChannel
                telegram_config = config_bu.config.get('telegram_config', {}) if config_bu else {}
                self.channels.append(TelegramChannel(config=telegram_config))
                logger.debug("Canal de Telegram habilitado")
                
            # Canal de notificaciones internas del sistema
            if enabled_channels.get('internal', True):
                from app.ats.integrations.notifications.core.channels import InternalChannel
                self.channels.append(InternalChannel())
                logger.debug("Canal de notificaciones internas habilitado")
                
        except ImportError as e:
            logger.error(f"Error al importar canal de notificación: {str(e)}")
            logger.error(f"Asegúrate de que todos los paquetes requeridos estén instalados")
        except Exception as e:
            logger.error(f"Error al inicializar canales de notificación: {str(e)}")
            logger.exception(e)  # Log del stack trace completo para debugging
    
    def _initialize_template_engine(self):
        """Inicializa el motor de plantillas para renderizar contenido de notificaciones."""
        try:
            # Intentar cargar Jinja2 si está disponible (recomendado)
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape, PackageLoader
                
                # Determinar las rutas de plantillas
                template_paths = [
                    # Plantillas específicas de la unidad de negocio (si existen)
                    getattr(self.business_unit, 'templates_path', None),
                    # Plantillas predeterminadas del sistema
                    'app/ats/notifications/templates',
                    'app/ats/integrations/notifications/templates'
                ]
                
                # Filtrar rutas None
                template_paths = [path for path in template_paths if path]
                
                # Si no hay rutas de plantillas, usar cargador de paquetes
                if not template_paths:
                    try:
                        self.template_engine = Environment(
                            loader=PackageLoader('app.ats.notifications', 'templates'),
                            autoescape=select_autoescape(['html', 'xml']),
                            trim_blocks=True,
                            lstrip_blocks=True
                        )
                    except Exception:
                        # Fallback: usar plantillas integradas (sin archivo)
                        self.template_engine = None
                        logger.warning("Usando plantillas integradas (sin motor de plantillas)")
                else:
                    self.template_engine = Environment(
                        loader=FileSystemLoader(template_paths),
                        autoescape=select_autoescape(['html', 'xml']),
                        trim_blocks=True,
                        lstrip_blocks=True
                    )
                    
                logger.debug(f"Motor de plantillas Jinja2 inicializado con rutas: {template_paths}")
                
            except ImportError:
                # Fallback: usar plantillas simples basadas en str.format()
                self.template_engine = None
                logger.warning("Jinja2 no disponible. Usando plantillas básicas con str.format()")
        
        except Exception as e:
            self.template_engine = None
            logger.error(f"Error al inicializar motor de plantillas: {str(e)}")
    
    def _initialize_analytics(self):
        """Inicializa el sistema de seguimiento analítico para notificaciones."""
        try:
            # Intentar cargar el rastreador de analíticas si está disponible
            try:
                from app.analytics.tracking import NotificationTracker
                self.analytics_tracker = NotificationTracker()
                logger.debug("Sistema de analítica de notificaciones inicializado")
            except ImportError:
                # No hay sistema de analítica disponible
                self.analytics_tracker = None
                logger.info("Sistema de analítica no disponible. No se rastrearán métricas de notificaciones.")
        except Exception as e:
            self.analytics_tracker = None
            logger.error(f"Error al inicializar sistema de analítica: {str(e)}")
    
    async def _process_event_queue(self):
        """Procesa eventos de notificación en la cola de forma asíncrona."""
        if not self.event_queue:
            return
            
        logger.debug("Iniciando procesador de cola de eventos de notificación")
        
        while True:
            try:
                event = await self.event_queue.get()
                
                # Priorizar notificaciones urgentes
                if event.priority == NotificationPriority.URGENT:
                    asyncio.create_task(self._send_notification_async(event))
                else:
                    # Procesar en background
                    await self._send_notification_async(event)
                    
                self.event_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("Procesador de cola de notificaciones cancelado")
                break
            except Exception as e:
                logger.error(f"Error procesando evento de notificación: {str(e)}")
                continue
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renderiza una plantilla con el contexto proporcionado.
        
        Args:
            template_name: Nombre de la plantilla (ej: 'new_candidate_email.html')
            context: Diccionario con variables para la plantilla
            
        Returns:
            Contenido renderizado de la plantilla
        """
        # Si no hay motor de plantillas, usar plantillas integradas basadas en context
        if not self.template_engine:
            # Plantillas fallback en caso de no tener motor de plantillas
            built_in_templates = {
                "new_candidate_email.html": """<html>
                <body>
                <h2>Nuevo Candidato: {candidate_name}</h2>
                <p>Se ha registrado un nuevo candidato en el sistema.</p>
                <p><strong>Nombre:</strong> {candidate_name}<br>
                <strong>Email:</strong> {candidate_email}<br>
                <strong>Posición:</strong> {position}</p>
                </body>
                </html>""",
                
                "candidate_status_change_email.html": """<html>
                <body>
                <h2>Cambio de Estado para {candidate_name}</h2>
                <p>El candidato ha cambiado de estado en el proceso.</p>
                <p><strong>Candidato:</strong> {candidate_name}<br>
                <strong>Estado anterior:</strong> {old_status}<br>
                <strong>Nuevo estado:</strong> {new_status}</p>
                </body>
                </html>""",
                
                "new_vacancy_email.html": """<html>
                <body>
                <h2>Nueva Vacante: {vacancy_title}</h2>
                <p>Se ha publicado una nueva vacante.</p>
                <p><strong>Título:</strong> {vacancy_title}<br>
                <strong>Empresa:</strong> {company_name}<br>
                <strong>Ubicación:</strong> {location}</p>
                </body>
                </html>""",
                
                "interview_scheduled_email.html": """<html>
                <body>
                <h2>Entrevista Programada con {candidate_name}</h2>
                <p>Se ha programado una entrevista.</p>
                <p><strong>Candidato:</strong> {candidate_name}<br>
                <strong>Fecha:</strong> {date}<br>
                <strong>Hora:</strong> {time}<br>
                <strong>Modalidad:</strong> {mode}</p>
                </body>
                </html>""",
                
                # Plantillas por defecto para WhatsApp (texto plano)
                "new_candidate_whatsapp.txt": """*Nuevo Candidato: {candidate_name}*\n\nSe ha registrado un nuevo candidato en el sistema.\n\nNombre: {candidate_name}\nEmail: {candidate_email}\nPosición: {position}""",
                
                "candidate_status_change_whatsapp.txt": """*Cambio de Estado para {candidate_name}*\n\nEl candidato ha cambiado de estado en el proceso.\n\nCandidato: {candidate_name}\nEstado anterior: {old_status}\nNuevo estado: {new_status}""",
                
                "new_vacancy_whatsapp.txt": """*Nueva Vacante: {vacancy_title}*\n\nSe ha publicado una nueva vacante.\n\nTítulo: {vacancy_title}\nEmpresa: {company_name}\nUbicación: {location}""",
                
                "interview_scheduled_whatsapp.txt": """*Entrevista Programada con {candidate_name}*\n\nSe ha programado una entrevista.\n\nCandidato: {candidate_name}\nFecha: {date}\nHora: {time}\nModalidad: {mode}"""
            }
            
            # Obtener plantilla o usar mensaje genérico
            template = built_in_templates.get(
                template_name,
                "Notificación de {notification_type} para {recipient}"
            )
            
            # Renderizar con string formatting
            try:
                return template.format(**context)
            except KeyError as e:
                logger.warning(f"Falta la clave {str(e)} en el contexto para la plantilla {template_name}")
                # Rellenar claves faltantes con valores por defecto
                safe_context = {**context}
                for key in ['candidate_name', 'candidate_email', 'position', 
                          'old_status', 'new_status', 'vacancy_title',
                          'company_name', 'location', 'date', 'time', 'mode',
                          'notification_type', 'recipient']:
                    if key not in safe_context:
                        safe_context[key] = f"[{key}]"
                return template.format(**safe_context)
            except Exception as e:
                logger.error(f"Error al renderizar plantilla {template_name}: {str(e)}")
                return f"Error en la plantilla {template_name}. Consulte los logs para más detalles."
        
        # Usar Jinja2 si está disponible
        try:
            template = self.template_engine.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error al renderizar plantilla {template_name} con Jinja2: {str(e)}")
            # Fallback a plantilla básica en caso de error
            return f"Notificación de {context.get('notification_type', 'reclutamiento')} para {context.get('recipient', 'usuario')}"
    
    def _create_notification_event(self, notification_type: NotificationType, 
                                 subject: str, content: str, recipients: List[Any], 
                                 priority: NotificationPriority = NotificationPriority.NORMAL,
                                 **kwargs) -> NotificationEvent:
        """
        Crea un evento de notificación.
        
        Args:
            notification_type: Tipo de notificación
            subject: Asunto de la notificación
            content: Contenido de la notificación
            recipients: Lista de destinatarios
            priority: Prioridad de la notificación
            **kwargs: Parámetros adicionales para el evento
            
        Returns:
            NotificationEvent: Evento de notificación
        """
        # Asegurar que los tipos son correctos
        if isinstance(notification_type, str):
            try:
                notification_type = NotificationType(notification_type)
            except ValueError:
                notification_type = NotificationType.SYSTEM_ALERT
                logger.warning(f"Tipo de notificación desconocido: {notification_type}, usando SYSTEM_ALERT")
                
        if isinstance(priority, str):
            try:
                priority = NotificationPriority(priority)
            except ValueError:
                priority = NotificationPriority.NORMAL
                logger.warning(f"Prioridad desconocida: {priority}, usando NORMAL")
        
        # Crear el evento
        return NotificationEvent(
            id=kwargs.get('id', str(uuid.uuid4())),
            type=notification_type,
            subject=subject,
            content=content,
            priority=priority,
            recipients=recipients,
            timestamp=kwargs.get('timestamp', datetime.datetime.now()),
            metadata=kwargs.get('metadata', {}),
            context=kwargs.get('context', {})
        )
    
    def _prepare_notification_payload(self, notification_type: str, **kwargs) -> Dict[str, Any]:
        """
        Prepara un payload común para todos los tipos de notificación.
        
        Args:
            notification_type: Tipo de notificación (e.g., 'new_candidate', 'status_change')
            **kwargs: Parámetros específicos de la notificación
            
        Returns:
            Dict con el payload de la notificación
        """
        # Asegurar que tengamos un timestamp
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.datetime.now()
            
        # Normalizar la prioridad
        priority = kwargs.get('priority', NotificationPriority.NORMAL)
        if isinstance(priority, str):
            try:
                priority = NotificationPriority(priority)
            except ValueError:
                priority = NotificationPriority.NORMAL
                
        payload = {
            'type': notification_type,
            'business_unit': self.business_unit,
            'timestamp': kwargs.get('timestamp'),
            'priority': priority,
            'context': kwargs.get('context', {}),
            'metadata': kwargs.get('metadata', {}),
        }
        
        # Añadir todos los demás kwargs al payload
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value
                
        return payload
    
    @retry_on_failure(max_attempts=3, delay=1)
    def _send_notification(self, recipients: List[Any], subject: str, content: str, 
                          notification_payload: Dict[str, Any], **kwargs) -> bool:
        """
        Envía una notificación a través de todos los canales disponibles.
        
        Args:
            recipients: Lista de destinatarios
            subject: Asunto de la notificación
            content: Contenido de la notificación
            notification_payload: Payload completo de la notificación
            **kwargs: Parámetros adicionales
            
        Returns:
            bool: True si la notificación se envió correctamente en al menos un canal
        """
        if not self.channels:
            logger.warning("No hay canales de notificación disponibles")
            return False
            
        # Registrar intento de envío en analíticas
        if self.analytics_tracker:
            try:
                self.analytics_tracker.track_notification_attempt(
                    notification_type=notification_payload.get('type'),
                    business_unit_id=getattr(self.business_unit, 'id', None),
                    channel_count=len(self.channels),
                    recipient_count=len(recipients),
                    metadata=notification_payload.get('metadata', {})
                )
            except Exception as e:
                logger.warning(f"Error al registrar intento de notificación en analíticas: {str(e)}")
            
        success = False
        for channel in self.channels:
            try:
                channel_success = channel.send(
                    recipients=recipients,
                    subject=subject,
                    content=content,
                    business_unit=self.business_unit,
                    **kwargs
                )
                success = success or channel_success
                
                # Registrar éxito o fallo en analíticas
                if self.analytics_tracker:
                    self.analytics_tracker.track_channel_result(
                        channel=channel.__class__.__name__,
                        success=channel_success,
                        error=None if channel_success else "Error desconocido"
                    )
                    
            except Exception as e:
                error_msg = f"Error al enviar notificación a través del canal {channel.__class__.__name__}: {str(e)}"
                logger.error(error_msg)
                
                # Registrar error en analíticas
                if self.analytics_tracker:
                    self.analytics_tracker.track_channel_result(
                        channel=channel.__class__.__name__,
                        success=False,
                        error=str(e)
                    )
        
        # Guardar en historial de notificaciones
        notification_id = notification_payload.get('id', str(uuid.uuid4()))
        self.notification_history[notification_id] = {
            'timestamp': datetime.datetime.now(),
            'success': success,
            'recipients_count': len(recipients),
            'channels_attempted': len(self.channels),
            'notification_type': notification_payload.get('type'),
            'subject': subject
        }
        
        return success
        
    async def _send_notification_async(self, recipients: List[Any], subject: str, content: str, 
                                     notification_payload: Dict[str, Any], **kwargs) -> bool:
        """
        Envía una notificación asíncrona a través de todos los canales disponibles.
        
        Args:
            recipients: Lista de destinatarios
            subject: Asunto de la notificación
            content: Contenido de la notificación
            notification_payload: Payload completo de la notificación
            **kwargs: Parámetros adicionales
            
        Returns:
            bool: True si la notificación se envió correctamente en al menos un canal
        """
        if not self.channels:
            logger.warning("No hay canales de notificación disponibles")
            return False
            
        tasks = []
        for channel in self.channels:
            if hasattr(channel, 'send_async'):
                tasks.append(asyncio.create_task(
                    channel.send_async(
                        recipients=recipients,
                        subject=subject,
                        content=content,
                        business_unit=self.business_unit,
                        **kwargs
                    )
                ))
            else:
                # Para canales que no soportan async, ejecutar en un thread pool
                loop = asyncio.get_event_loop()
                tasks.append(loop.run_in_executor(
                    None,
                    lambda: channel.send(
                        recipients=recipients,
                        subject=subject,
                        content=content,
                        business_unit=self.business_unit,
                        **kwargs
                    )
                ))
                
        if not tasks:
            return False
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(result for result in results if not isinstance(result, Exception) and result)
    
    async def notify_new_candidate(self, candidate, recipients=None, **kwargs):
        """
        Envía una notificación sobre un nuevo candidato registrado.
        
        Args:
            candidate: Objeto candidato con la información relevante
            recipients: Lista opcional de destinatarios. Si es None, se enviará a los destinatarios por defecto
            **kwargs: Parámetros adicionales para la notificación
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            if not candidate:
                logger.error("Intento de enviar notificación con candidato nulo")
                return False
                
            # Determinar destinatarios
            if recipients is None:
                recipients = self._get_default_recipients(candidate)
                
            # Construir el asunto y contenido (igual que en la versión síncrona)
            subject = f"Nuevo candidato registrado: {candidate.name}" 
            content = f"Un nuevo candidato ha sido registrado en el sistema.\n\n"
            content += f"Nombre: {candidate.name}\n"
            content += f"Email: {candidate.email}\n"
            content += f"Posición: {getattr(candidate, 'position', 'No especificada')}\n"
            
            # Preparar el payload completo
            payload = self._prepare_notification_payload(
                notification_type='new_candidate',
                candidate=candidate,
                **kwargs
            )
            
            # Enviar la notificación asíncrona
            return await self._send_notification_async(recipients, subject, content, payload, **kwargs)
            
        except Exception as e:
            logger.error(f"Error al notificar nuevo candidato (async): {str(e)}")
            return False
    
    def notify_candidate_status_change(self, candidate, old_status, new_status, recipients=None, **kwargs):
        """
        Envía una notificación sobre un cambio de estatus en un candidato.
        
        Args:
            candidate: Objeto candidato con la información relevante
            old_status: Estado anterior del candidato
            new_status: Nuevo estado del candidato
            recipients: Lista opcional de destinatarios. Si es None, se enviará a los destinatarios por defecto
            **kwargs: Parámetros adicionales para la notificación
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            if not candidate:
                logger.error("Intento de enviar notificación con candidato nulo")
                return False
                
            # Determinar destinatarios
            if recipients is None:
                recipients = self._get_default_recipients(candidate)
                
            # Construir el asunto y contenido
            subject = f"Cambio de estado para candidato: {candidate.name}" 
            content = f"El estado del candidato ha cambiado.\n\n"
            content += f"Candidato: {candidate.name}\n"
            content += f"Estado anterior: {old_status}\n"
            content += f"Nuevo estado: {new_status}\n"
            
            # Preparar el payload completo
            payload = self._prepare_notification_payload(
                notification_type='status_change',
                candidate=candidate,
                old_status=old_status,
                new_status=new_status,
                **kwargs
            )
            
            # Enviar la notificación
            return self._send_notification(recipients, subject, content, payload, **kwargs)
            
        except Exception as e:
            logger.error(f"Error al notificar cambio de estado: {str(e)}")
            return False
    
    def _get_default_recipients(self, context_obj=None):
        """
        Determina los destinatarios por defecto basados en el contexto.
        
        Args:
            context_obj: Objeto de contexto (candidato, vacante, etc.)
            
        Returns:
            Lista de destinatarios
        """
        recipients = []
        
        # Añadir administrador de la unidad de negocio si existe
        if self.business_unit and hasattr(self.business_unit, 'admin_email'):
            recipients.append(self.business_unit.admin_email)
            
        # Si es un candidato, añadir reclutadores asociados
        if context_obj and hasattr(context_obj, 'recruiters'):
            try:
                recruiters = getattr(context_obj, 'recruiters', [])
                if recruiters:
                    for recruiter in recruiters:
                        if hasattr(recruiter, 'email'):
                            recipients.append(recruiter.email)
            except Exception as e:
                logger.warning(f"Error al obtener reclutadores para notificación: {str(e)}")
                
        # Si está vacío, usar un destinatario de fallback
        if not recipients and hasattr(self.business_unit, 'fallback_notification_email'):
            recipients.append(self.business_unit.fallback_notification_email)
            
        return recipients
    
    def notify_new_vacancy(self, vacancy, recipients=None, **kwargs):
        """
        Envía una notificación sobre una nueva vacante publicada.
        
        Args:
            vacancy: Objeto vacante con la información relevante
            recipients: Lista opcional de destinatarios. Si es None, se enviará a los destinatarios por defecto
            **kwargs: Parámetros adicionales para la notificación
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            if not vacancy:
                logger.error("Intento de enviar notificación con vacante nula")
                return False
                
            # Determinar destinatarios
            if recipients is None:
                # Si no se especificaron destinatarios, notificar a los usuarios configurados para recibir 
                # notificaciones de nuevas vacantes
                recipients = self._get_default_recipients(vacancy)
                
            # Construir el asunto y contenido
            subject = f"Nueva vacante publicada: {vacancy.title}" 
            content = f"Una nueva vacante ha sido publicada en el sistema.\n\n"
            content += f"Título: {vacancy.title}\n"
            content += f"Empresa: {getattr(vacancy, 'company_name', 'No especificada')}\n"
            content += f"Ubicación: {getattr(vacancy, 'location', 'No especificada')}\n"
            
            # Preparar el payload completo
            payload = self._prepare_notification_payload(
                notification_type='new_vacancy',
                vacancy=vacancy,
                **kwargs
            )
            
            # Enviar la notificación
            return self._send_notification(recipients, subject, content, payload, **kwargs)
            
        except Exception as e:
            logger.error(f"Error al notificar nueva vacante: {str(e)}")
            return False
    
    def notify_interview_scheduled(self, interview, recipients=None, **kwargs):
        """
        Envía una notificación sobre una entrevista programada.
        
        Args:
            interview: Objeto entrevista con la información relevante
            recipients: Lista opcional de destinatarios. Si es None, se enviará a los destinatarios por defecto
            **kwargs: Parámetros adicionales para la notificación
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            if not interview:
                logger.error("Intento de enviar notificación con entrevista nula")
                return False
                
            # Determinar destinatarios
            if recipients is None:
                # Incluir al candidato, entrevistadores y reclutadores relevantes
                recipients = []
                
                # Añadir candidato si tiene email
                if hasattr(interview, 'candidate') and hasattr(interview.candidate, 'email'):
                    recipients.append(interview.candidate.email)
                    
                # Añadir entrevistadores
                if hasattr(interview, 'interviewers'):
                    for interviewer in interview.interviewers:
                        if hasattr(interviewer, 'email'):
                            recipients.append(interviewer.email)
                
                # Si no se encontraron destinatarios específicos, usar los predeterminados
                if not recipients:
                    recipients = self._get_default_recipients(interview)
                
            # Construir el asunto y contenido
            candidate_name = getattr(interview.candidate, 'name', 'Candidato') if hasattr(interview, 'candidate') else 'Candidato'
            subject = f"Entrevista programada con {candidate_name}" 
            
            content = f"Se ha programado una nueva entrevista.\n\n"
            content += f"Candidato: {candidate_name}\n"
            content += f"Fecha: {getattr(interview, 'date', 'No especificada')}\n"
            content += f"Hora: {getattr(interview, 'time', 'No especificada')}\n"
            content += f"Modalidad: {getattr(interview, 'mode', 'No especificada')}\n"
            
            if hasattr(interview, 'location'):
                content += f"Ubicación: {interview.location}\n"
                
            if hasattr(interview, 'meeting_link'):
                content += f"Enlace: {interview.meeting_link}\n"
            
            # Preparar el payload completo
            payload = self._prepare_notification_payload(
                notification_type='interview_scheduled',
                interview=interview,
                **kwargs
            )
            
            # Enviar la notificación
            return self._send_notification(recipients, subject, content, payload, **kwargs)
            
        except Exception as e:
            logger.error(f"Error al notificar entrevista programada: {str(e)}")
            return False

    def notify_interview_scheduled(self, candidate, vacancy, date, time, **kwargs):
        """Notifica sobre una nueva entrevista programada."""
        try:
            # Extraer datos básicos
            candidate_name = getattr(candidate, 'nombre_completo', getattr(candidate, 'name', 'Candidato'))
            candidate_email = getattr(candidate, 'email', '')
            position = getattr(vacancy, 'titulo', getattr(vacancy, 'title', 'Posición'))
            company_name = getattr(getattr(vacancy, 'empresa', None), 'nombre', 'Empresa')
            
            # Datos adicionales de la entrevista
            interview_mode = kwargs.get('mode', 'Presencial')
            location = kwargs.get('location', 'Por confirmar')
            duration = kwargs.get('duration', '1 hora')
            interviewer = kwargs.get('interviewer', 'Equipo de Recursos Humanos')
            preparation = kwargs.get('preparation', 'Repasar tu CV y estar preparado para preguntas sobre tu experiencia')
            
            # Notificar al reclutador/equipo interno
            internal_recipients = self._get_hr_recipients(vacancy)
            internal_context = {
                'candidate_name': candidate_name,
                'position': position,
                'company_name': company_name,
                'date': date,
                'time': time,
                'mode': interview_mode,
                'location': location,
                'duration': duration,
                'interviewer': interviewer,
                'notification_type': 'entrevista programada',
                'recipient': 'equipo'
            }
            
            # Renderizar contenido para equipo interno
            internal_content = self._render_template('interview_scheduled_email.html', internal_context)
            internal_subject = f"Entrevista programada: {candidate_name} - {date}, {time}"
            
            # Payload para notificación interna
            internal_payload = self._prepare_notification_payload(
                notification_type=NotificationType.INTERVIEW_SCHEDULED,
                candidate=candidate,
                vacancy=vacancy,
                date=date,
                time=time,
                context=internal_context,
                **kwargs
            )
            
            # Enviar notificación interna
            self._send_notification(internal_recipients, internal_subject, internal_content, internal_payload, **kwargs)
            
            # Notificar al candidato
            # Esta es una notificación fundamental para el enfoque centrado en candidatos
            candidate_recipients = [{'email': candidate_email, 'name': candidate_name}]
            candidate_context = {
                'candidate_name': candidate_name,
                'position': position,
                'company_name': company_name,
                'date': date,
                'time': time,
                'mode': interview_mode,
                'location': location,
                'duration': duration,
                'interviewer': interviewer,
                'preparation': preparation,
                'contact_person': kwargs.get('contact_person', None),
                'contact_email': kwargs.get('contact_email', None),
                'contact_phone': kwargs.get('contact_phone', None),
                'notification_type': 'entrevista',
                'recipient': candidate_name
            }
            
            # Incluir datos de conferencia si es virtual
            if interview_mode.lower() in ['virtual', 'remoto', 'en línea', 'online', 'zoom', 'teams', 'meet']:
                candidate_context.update({
                    'conference_link': kwargs.get('conference_link', 'Se enviará próximamente'),
                    'conference_id': kwargs.get('conference_id', ''),
                    'conference_password': kwargs.get('conference_password', ''),
                    'conference_platform': kwargs.get('conference_platform', 'Zoom/Teams/Meet'),
                    'technical_requirements': kwargs.get('technical_requirements', 'Navegador moderno con cámara y micrófono')
                })
            
            # Renderizar contenido para candidato
            candidate_content = self._render_template('interview_scheduled_candidate.html', candidate_context)
            candidate_subject = f"Entrevista programada para {position} en {company_name} - {date}, {time}"
            
            # Payload para notificación al candidato
            candidate_payload = self._prepare_notification_payload(
                notification_type=NotificationType.INTERVIEW_SCHEDULED,
                candidate=candidate,
                vacancy=vacancy,
                date=date,
                time=time,
                context=candidate_context,
                **kwargs
            )
            
            # Enviar notificación al candidato
            return self._send_notification(candidate_recipients, candidate_subject, 
                                       candidate_content, candidate_payload, **kwargs)
            
        except Exception as e:
            logger.error(f"Error al notificar entrevista programada: {str(e)}")
            logger.exception(e)
            return False
            
    def notify_interview_alternatives(self, candidate, vacancy, alternatives, **kwargs):
        """Notifica al candidato sobre alternativas de horarios para entrevistas."""
        try:
            # Datos básicos
            candidate_name = getattr(candidate, 'nombre_completo', getattr(candidate, 'name', 'Candidato'))
            candidate_email = getattr(candidate, 'email', '')
            position = getattr(vacancy, 'titulo', getattr(vacancy, 'title', 'Posición'))
            company_name = getattr(getattr(vacancy, 'empresa', None), 'nombre', 'Empresa')
            
            # Verificar que tenemos alternativas válidas
            if not alternatives or not isinstance(alternatives, list) or len(alternatives) == 0:
                logger.error("No se proporcionaron alternativas válidas para la entrevista")
                return False
                
            # Notificar al candidato sobre las alternativas
            candidate_recipients = [{'email': candidate_email, 'name': candidate_name}]
            candidate_context = {
                'candidate_name': candidate_name,
                'position': position,
                'company_name': company_name,
                'alternatives': alternatives,
                'response_method': kwargs.get('response_method', 'Responder a este correo con tu opción preferida'),
                'response_deadline': kwargs.get('response_deadline', 'En las próximas 24 horas'),
                'contact_person': kwargs.get('contact_person', 'Equipo de Reclutamiento'),
                'contact_email': kwargs.get('contact_email', ''),
                'contact_phone': kwargs.get('contact_phone', ''),
                'notification_type': 'alternativas de entrevista',
                'recipient': candidate_name
            }
            
            # Renderizar contenido para candidato
            candidate_content = self._render_template('interview_alternatives.html', candidate_context)
            candidate_subject = f"Alternativas de horario para tu entrevista en {company_name}"
            
            # Payload para notificación al candidato
            candidate_payload = self._prepare_notification_payload(
                notification_type=NotificationType.INTERVIEW_SCHEDULED,
                candidate=candidate,
                vacancy=vacancy,
                alternatives=alternatives,
                context=candidate_context,
                **kwargs
            )
            
            # Enviar notificación al candidato
            return self._send_notification(candidate_recipients, candidate_subject, 
                                       candidate_content, candidate_payload, **kwargs)
            
        except Exception as e:
            logger.error(f"Error al notificar alternativas de entrevista: {str(e)}")
            logger.exception(e)
            return False
            
    def notify_multiple_interviews(self, candidate, vacancy, interviews, **kwargs):
        """Notifica al candidato sobre múltiples entrevistas programadas en un proceso."""
        try:
            # Datos básicos
            candidate_name = getattr(candidate, 'nombre_completo', getattr(candidate, 'name', 'Candidato'))
            candidate_email = getattr(candidate, 'email', '')
            position = getattr(vacancy, 'titulo', getattr(vacancy, 'title', 'Posición'))
            company_name = getattr(getattr(vacancy, 'empresa', None), 'nombre', 'Empresa')
            
            # Verificar que tenemos entrevistas válidas
            if not interviews or not isinstance(interviews, list) or len(interviews) == 0:
                logger.error("No se proporcionaron entrevistas válidas")
                return False
                
            # Notificar al candidato sobre las múltiples entrevistas
            candidate_recipients = [{'email': candidate_email, 'name': candidate_name}]
            candidate_context = {
                'candidate_name': candidate_name,
                'position': position,
                'company_name': company_name,
                'interviews': interviews,  # Lista de diccionarios con info de cada entrevista
                'process_name': kwargs.get('process_name', 'Proceso de selección'),
                'process_stages': kwargs.get('process_stages', len(interviews)),
                'contact_person': kwargs.get('contact_person', 'Equipo de Reclutamiento'),
                'contact_email': kwargs.get('contact_email', ''),
                'contact_phone': kwargs.get('contact_phone', ''),
                'notification_type': 'múltiples entrevistas',
                'recipient': candidate_name
            }
            
            # Renderizar contenido para candidato
            candidate_content = self._render_template('multiple_interviews.html', candidate_context)
            candidate_subject = f"Proceso de entrevistas para {position} en {company_name}"
            
            # Payload para notificación al candidato
            candidate_payload = self._prepare_notification_payload(
                notification_type=NotificationType.INTERVIEW_SCHEDULED,
                candidate=candidate,
                vacancy=vacancy,
                interviews=interviews,
                context=candidate_context,
                **kwargs
            )
            
            # Enviar notificación al candidato
            candidate_result = self._send_notification(candidate_recipients, candidate_subject, 
                                       candidate_content, candidate_payload, **kwargs)
            
            # Notificar también al equipo interno
            internal_recipients = self._get_hr_recipients(vacancy)
            internal_context = {
                'candidate_name': candidate_name,
                'position': position,
                'company_name': company_name,
                'interviews': interviews,
                'process_name': kwargs.get('process_name', 'Proceso de selección'),
                'notification_type': 'programación de entrevistas',
                'recipient': 'equipo'
            }
            
            # Renderizar contenido para equipo interno
            internal_content = self._render_template('multiple_interviews_internal.html', internal_context)
            internal_subject = f"Proceso de entrevistas programado para {candidate_name} - {position}"
            
            # Payload para notificación interna
            internal_payload = self._prepare_notification_payload(
                notification_type=NotificationType.INTERVIEW_SCHEDULED,
                candidate=candidate,
                vacancy=vacancy,
                interviews=interviews,
                context=internal_context,
                **kwargs
            )
            
            # Enviar notificación interna
            internal_result = self._send_notification(internal_recipients, internal_subject, 
                                                internal_content, internal_payload, **kwargs)
            
            return candidate_result or internal_result
            
        except Exception as e:
            logger.error(f"Error al notificar múltiples entrevistas: {str(e)}")
            logger.exception(e)
            return False


def get_recruitment_notifier():
    """
    Obtiene una instancia singleton del notificador de reclutamiento.
    
    Utiliza lazy loading para evitar consultar la base de datos durante la importación
    del módulo, lo que previene errores durante migraciones.
    
    Returns:
        RecruitmentNotifier: Instancia del notificador de reclutamiento
    """
    global _recruitment_notifier
    
    if _recruitment_notifier is None:
        try:
            from app.models import BusinessUnit
            business_unit = None
            try:
                business_unit = BusinessUnit.objects.first()
            except Exception as e:
                logger.warning(f"No se pudo obtener la unidad de negocio para el notificador: {str(e)}")
                
            _recruitment_notifier = RecruitmentNotifier(business_unit)
            
        except ImportError as e:
            logger.error(f"Error al importar dependencias para el notificador: {str(e)}")
            # Crear una instancia sin business_unit para evitar errores
            _recruitment_notifier = RecruitmentNotifier(None)
        except Exception as e:
            logger.error(f"Error al inicializar el notificador de reclutamiento: {str(e)}")
            # Crear una instancia sin business_unit para evitar errores
            _recruitment_notifier = RecruitmentNotifier(None)
            
    return _recruitment_notifier


# Alias para mantener compatibilidad con código existente
RecruitmentNotifier = get_recruitment_notifier
