"""
Advanced Notification Engine - huntRED® v2
Sistema completo de notificaciones multi-canal con personalización, priorización y analíticas.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import websockets
import firebase_admin
from firebase_admin import credentials, messaging
from twilio.rest import Client
import slack_sdk
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Canales de notificación disponibles."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SLACK = "slack"
    PUSH = "push_notification"
    IN_APP = "in_app"
    WEBHOOK = "webhook"
    VOICE = "voice_call"


class NotificationPriority(Enum):
    """Niveles de prioridad de notificaciones."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationStatus(Enum):
    """Estados de una notificación."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class NotificationRecipient:
    """Destinatario de notificación."""
    user_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    telegram_id: Optional[str] = None
    slack_user_id: Optional[str] = None
    push_token: Optional[str] = None
    language: str = "es"
    timezone: str = "UTC"
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationTemplate:
    """Plantilla de notificación."""
    id: str
    name: str
    category: str
    subject_template: str
    body_template: str
    html_template: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    channels: List[NotificationChannel] = field(default_factory=list)
    priority: NotificationPriority = NotificationPriority.MEDIUM
    expires_after: Optional[timedelta] = None
    retry_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """Notificación individual."""
    id: str
    template_id: str
    recipient: NotificationRecipient
    channel: NotificationChannel
    priority: NotificationPriority
    subject: str
    content: str
    html_content: Optional[str] = None
    variables: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict] = field(default_factory=list)
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationCampaign:
    """Campaña de notificaciones masivas."""
    id: str
    name: str
    description: str
    template_id: str
    recipients: List[NotificationRecipient]
    channels: List[NotificationChannel]
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "draft"
    statistics: Dict[str, Any] = field(default_factory=dict)


class AdvancedNotificationEngine:
    """
    Motor avanzado de notificaciones con:
    - Múltiples canales de comunicación
    - Templates personalizables
    - Priorización inteligente
    - Retry automático con backoff
    - Analíticas y métricas
    - Control de preferencias por usuario
    - Campañas masivas
    """
    
    def __init__(self, config: Dict[str, Any], db_session: Session):
        self.config = config
        self.db = db_session
        
        # Templates de notificación
        self.templates: Dict[str, NotificationTemplate] = {}
        
        # Cola de notificaciones
        self.notification_queue: List[Notification] = []
        self.priority_queue: Dict[NotificationPriority, List[Notification]] = {
            priority: [] for priority in NotificationPriority
        }
        
        # Configurar proveedores
        self._setup_providers()
        
        # Configurar templates predefinidos
        self._setup_default_templates()
        
        # Estado del motor
        self.running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # Métricas
        self.metrics = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_failed': 0,
            'by_channel': {channel.value: 0 for channel in NotificationChannel},
            'by_priority': {priority.value: 0 for priority in NotificationPriority}
        }
    
    def _setup_providers(self):
        """Configura proveedores de notificaciones."""
        # Email (SMTP)
        self.smtp_config = {
            'server': self.config.get('smtp_server'),
            'port': self.config.get('smtp_port', 587),
            'username': self.config.get('smtp_username'),
            'password': self.config.get('smtp_password'),
            'use_tls': self.config.get('smtp_tls', True)
        }
        
        # SMS (Twilio)
        self.twilio_client = None
        if self.config.get('twilio_sid') and self.config.get('twilio_token'):
            self.twilio_client = Client(
                self.config.get('twilio_sid'),
                self.config.get('twilio_token')
            )
        
        # WhatsApp Business API
        self.whatsapp_config = {
            'access_token': self.config.get('whatsapp_access_token'),
            'phone_number_id': self.config.get('whatsapp_phone_number_id'),
            'api_url': 'https://graph.facebook.com/v18.0'
        }
        
        # Telegram Bot
        self.telegram_config = {
            'bot_token': self.config.get('telegram_bot_token'),
            'api_url': f"https://api.telegram.org/bot{self.config.get('telegram_bot_token')}"
        }
        
        # Slack
        self.slack_client = None
        if self.config.get('slack_token'):
            self.slack_client = slack_sdk.WebClient(token=self.config.get('slack_token'))
        
        # Firebase (Push Notifications)
        self.firebase_app = None
        if self.config.get('firebase_credentials'):
            cred = credentials.Certificate(self.config.get('firebase_credentials'))
            self.firebase_app = firebase_admin.initialize_app(cred)
    
    def _setup_default_templates(self):
        """Configura templates de notificación predefinidos."""
        templates = [
            NotificationTemplate(
                id="job_application_received",
                name="Aplicación Recibida",
                category="recruitment",
                subject_template="Tu aplicación ha sido recibida - {job_title}",
                body_template="""
                Estimado/a {candidate_name},
                
                Hemos recibido tu aplicación para la posición de {job_title} en {company_name}.
                
                Tu aplicación está siendo revisada por nuestro equipo de reclutamiento y te contactaremos 
                dentro de los próximos {review_days} días hábiles.
                
                Número de referencia: {application_id}
                
                ¡Gracias por tu interés en unirte a nuestro equipo!
                
                Saludos cordiales,
                Equipo de Reclutamiento
                {company_name}
                """,
                html_template="""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #2c3e50;">Tu aplicación ha sido recibida</h2>
                    <p>Estimado/a <strong>{candidate_name}</strong>,</p>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #27ae60; margin-top: 0;">✅ Aplicación Confirmada</h3>
                        <p><strong>Posición:</strong> {job_title}</p>
                        <p><strong>Empresa:</strong> {company_name}</p>
                        <p><strong>Referencia:</strong> {application_id}</p>
                    </div>
                    <p>Tu aplicación está siendo revisada y te contactaremos dentro de <strong>{review_days} días hábiles</strong>.</p>
                    <p>¡Gracias por tu interés!</p>
                </div>
                """,
                variables=["candidate_name", "job_title", "company_name", "application_id", "review_days"],
                channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.WHATSAPP],
                priority=NotificationPriority.HIGH
            ),
            
            NotificationTemplate(
                id="interview_scheduled",
                name="Entrevista Programada",
                category="interviews",
                subject_template="Entrevista programada - {job_title}",
                body_template="""
                Hola {candidate_name},
                
                ¡Excelentes noticias! Hemos programado una entrevista contigo para la posición de {job_title}.
                
                📅 Fecha: {interview_date}
                🕒 Hora: {interview_time}
                📍 Ubicación: {interview_location}
                👥 Entrevistador(es): {interviewer_names}
                ⏱️ Duración estimada: {duration} minutos
                
                {interview_instructions}
                
                Por favor confirma tu asistencia respondiendo a este mensaje.
                
                ¡Esperamos conocerte!
                
                Saludos,
                {recruiter_name}
                {company_name}
                """,
                variables=["candidate_name", "job_title", "interview_date", "interview_time", 
                          "interview_location", "interviewer_names", "duration", "interview_instructions", 
                          "recruiter_name", "company_name"],
                channels=[NotificationChannel.EMAIL, NotificationChannel.WHATSAPP, NotificationChannel.SMS],
                priority=NotificationPriority.HIGH
            ),
            
            NotificationTemplate(
                id="offer_extended",
                name="Oferta de Trabajo",
                category="offers",
                subject_template="¡Oferta de trabajo! - {job_title}",
                body_template="""
                Estimado/a {candidate_name},
                
                ¡Tenemos excelentes noticias! Nos complace extenderte una oferta para la posición de {job_title}.
                
                💼 Detalles de la oferta:
                • Posición: {job_title}
                • Salario: {salary_offer}
                • Beneficios: {benefits_summary}
                • Fecha de inicio: {start_date}
                
                Esta oferta es válida hasta el {offer_expiry}.
                
                Adjunto encontrarás el documento formal de la oferta con todos los detalles.
                
                ¡Esperamos que te unas a nuestro equipo!
                
                Saludos cordiales,
                {recruiter_name}
                {company_name}
                """,
                variables=["candidate_name", "job_title", "salary_offer", "benefits_summary", 
                          "start_date", "offer_expiry", "recruiter_name", "company_name"],
                channels=[NotificationChannel.EMAIL],
                priority=NotificationPriority.CRITICAL
            ),
            
            NotificationTemplate(
                id="feedback_request",
                name="Solicitud de Feedback",
                category="feedback",
                subject_template="Tu opinión es importante - {process_type}",
                body_template="""
                Hola {recipient_name},
                
                Esperamos que hayas tenido una buena experiencia durante {process_description}.
                
                Tu feedback es muy valioso para nosotros y nos ayuda a mejorar continuamente.
                
                ¿Podrías tomarte 3 minutos para completar esta breve encuesta?
                
                👉 {feedback_url}
                
                Tus respuestas son completamente confidenciales.
                
                ¡Gracias por tu tiempo!
                
                Equipo huntRED®
                """,
                variables=["recipient_name", "process_type", "process_description", "feedback_url"],
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
                priority=NotificationPriority.MEDIUM
            ),
            
            NotificationTemplate(
                id="reference_request",
                name="Solicitud de Referencia",
                category="references",
                subject_template="Solicitud de referencia - {candidate_name}",
                body_template="""
                Estimado/a {reference_name},
                
                Espero que este mensaje te encuentre bien.
                
                {candidate_name} ha aplicado para una posición en {company_name} y te ha indicado 
                como referencia profesional.
                
                ¿Podrías ayudarnos proporcionando una breve referencia sobre su desempeño y 
                habilidades profesionales?
                
                Puedes completar el formulario aquí: {reference_url}
                
                El proceso toma aproximadamente 5 minutos y toda la información será tratada 
                con total confidencialidad.
                
                Gracias por tu tiempo y colaboración.
                
                Saludos cordiales,
                {recruiter_name}
                huntRED® - Talent Acquisition
                """,
                variables=["reference_name", "candidate_name", "company_name", "reference_url", "recruiter_name"],
                channels=[NotificationChannel.EMAIL],
                priority=NotificationPriority.MEDIUM
            ),
            
            NotificationTemplate(
                id="system_alert",
                name="Alerta del Sistema",
                category="system",
                subject_template="[ALERTA] {alert_type} - huntRED®",
                body_template="""
                ALERTA DEL SISTEMA
                
                Tipo: {alert_type}
                Severidad: {severity}
                Timestamp: {timestamp}
                
                Descripción:
                {alert_description}
                
                Detalles técnicos:
                {technical_details}
                
                Acción requerida: {action_required}
                
                Sistema huntRED® v2
                """,
                variables=["alert_type", "severity", "timestamp", "alert_description", 
                          "technical_details", "action_required"],
                channels=[NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.SLACK],
                priority=NotificationPriority.URGENT
            )
        ]
        
        for template in templates:
            self.register_template(template)
    
    def register_template(self, template: NotificationTemplate):
        """Registra una nueva plantilla de notificación."""
        self.templates[template.id] = template
        logger.info(f"Template '{template.name}' registered successfully")
    
    async def send_notification(self, template_id: str, recipient: NotificationRecipient,
                              variables: Dict[str, Any], channels: Optional[List[NotificationChannel]] = None,
                              priority: Optional[NotificationPriority] = None,
                              scheduled_at: Optional[datetime] = None) -> List[str]:
        """Envía una notificación usando un template."""
        try:
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Template '{template_id}' not found")
            
            # Usar canales del template si no se especifican
            if channels is None:
                channels = template.channels
            
            # Usar prioridad del template si no se especifica
            if priority is None:
                priority = template.priority
            
            notification_ids = []
            
            # Crear notificación para cada canal
            for channel in channels:
                # Verificar si el recipient tiene configurado este canal
                if not self._can_send_via_channel(recipient, channel):
                    logger.warning(f"Recipient {recipient.user_id} cannot receive {channel.value} notifications")
                    continue
                
                # Renderizar contenido
                subject = self._render_template(template.subject_template, variables)
                content = self._render_template(template.body_template, variables)
                html_content = None
                if template.html_template:
                    html_content = self._render_template(template.html_template, variables)
                
                # Crear notificación
                notification = Notification(
                    id=str(uuid.uuid4()),
                    template_id=template_id,
                    recipient=recipient,
                    channel=channel,
                    priority=priority,
                    subject=subject,
                    content=content,
                    html_content=html_content,
                    variables=variables,
                    scheduled_at=scheduled_at
                )
                
                # Añadir a la cola apropiada
                if scheduled_at and scheduled_at > datetime.now():
                    # Programar para más tarde
                    await self._schedule_notification(notification)
                else:
                    # Enviar inmediatamente
                    await self._queue_notification(notification)
                
                notification_ids.append(notification.id)
            
            return notification_ids
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            raise
    
    async def send_campaign(self, campaign: NotificationCampaign) -> Dict[str, Any]:
        """Envía una campaña de notificaciones masivas."""
        try:
            campaign.status = "sending"
            stats = {
                'total_recipients': len(campaign.recipients),
                'total_notifications': 0,
                'sent': 0,
                'failed': 0,
                'start_time': datetime.now()
            }
            
            template = self.templates.get(campaign.template_id)
            if not template:
                raise ValueError(f"Template '{campaign.template_id}' not found")
            
            # Enviar a cada recipient
            for recipient in campaign.recipients:
                try:
                    # Variables dinámicas por recipient
                    variables = {
                        'recipient_name': recipient.name,
                        'campaign_name': campaign.name,
                        **campaign.statistics.get('global_variables', {})
                    }
                    
                    notification_ids = await self.send_notification(
                        campaign.template_id,
                        recipient,
                        variables,
                        campaign.channels,
                        scheduled_at=campaign.scheduled_at
                    )
                    
                    stats['total_notifications'] += len(notification_ids)
                    stats['sent'] += len(notification_ids)
                    
                except Exception as e:
                    logger.error(f"Failed to send to recipient {recipient.user_id}: {str(e)}")
                    stats['failed'] += 1
            
            stats['end_time'] = datetime.now()
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
            
            campaign.status = "completed"
            campaign.statistics = stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error sending campaign: {str(e)}")
            campaign.status = "failed"
            raise
    
    def _can_send_via_channel(self, recipient: NotificationRecipient, 
                             channel: NotificationChannel) -> bool:
        """Verifica si se puede enviar por un canal específico."""
        channel_requirements = {
            NotificationChannel.EMAIL: recipient.email,
            NotificationChannel.SMS: recipient.phone,
            NotificationChannel.WHATSAPP: recipient.whatsapp or recipient.phone,
            NotificationChannel.TELEGRAM: recipient.telegram_id,
            NotificationChannel.SLACK: recipient.slack_user_id,
            NotificationChannel.PUSH: recipient.push_token,
            NotificationChannel.IN_APP: True,  # Siempre disponible
            NotificationChannel.WEBHOOK: True,  # Configurado por sistema
            NotificationChannel.VOICE: recipient.phone
        }
        
        return bool(channel_requirements.get(channel))
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Renderiza un template con variables."""
        try:
            # Simple template rendering (en producción usarías Jinja2)
            rendered = template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))
            return rendered
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template
    
    async def _queue_notification(self, notification: Notification):
        """Añade notificación a la cola de prioridad."""
        self.priority_queue[notification.priority].append(notification)
        logger.debug(f"Notification {notification.id} queued with priority {notification.priority.value}")
    
    async def _schedule_notification(self, notification: Notification):
        """Programa una notificación para envío futuro."""
        # En producción, esto se almacenaría en base de datos con scheduler
        await asyncio.sleep((notification.scheduled_at - datetime.now()).total_seconds())
        await self._queue_notification(notification)
    
    async def start_workers(self, num_workers: int = 5):
        """Inicia workers para procesar notificaciones."""
        self.running = True
        
        for i in range(num_workers):
            task = asyncio.create_task(self._notification_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        logger.info(f"Started {num_workers} notification workers")
    
    async def stop_workers(self):
        """Detiene todos los workers."""
        self.running = False
        
        for task in self.worker_tasks:
            task.cancel()
        
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        logger.info("All notification workers stopped")
    
    async def _notification_worker(self, worker_id: str):
        """Worker que procesa notificaciones de la cola."""
        logger.info(f"Notification worker {worker_id} started")
        
        while self.running:
            try:
                notification = await self._get_next_notification()
                
                if notification:
                    await self._process_notification(notification)
                else:
                    # No hay notificaciones, esperar un poco
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {str(e)}")
                await asyncio.sleep(5)  # Pausa en caso de error
        
        logger.info(f"Notification worker {worker_id} stopped")
    
    async def _get_next_notification(self) -> Optional[Notification]:
        """Obtiene la siguiente notificación de la cola por prioridad."""
        # Procesar por orden de prioridad
        for priority in [NotificationPriority.CRITICAL, NotificationPriority.URGENT, 
                        NotificationPriority.HIGH, NotificationPriority.MEDIUM, 
                        NotificationPriority.LOW]:
            if self.priority_queue[priority]:
                return self.priority_queue[priority].pop(0)
        
        return None
    
    async def _process_notification(self, notification: Notification):
        """Procesa una notificación individual."""
        try:
            notification.status = NotificationStatus.PENDING
            logger.info(f"Processing notification {notification.id} via {notification.channel.value}")
            
            # Enviar por el canal correspondiente
            success = await self._send_via_channel(notification)
            
            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now()
                self.metrics['total_sent'] += 1
                self.metrics['by_channel'][notification.channel.value] += 1
                self.metrics['by_priority'][notification.priority.value] += 1
            else:
                await self._handle_notification_failure(notification)
            
        except Exception as e:
            logger.error(f"Error processing notification {notification.id}: {str(e)}")
            notification.error_message = str(e)
            await self._handle_notification_failure(notification)
    
    async def _send_via_channel(self, notification: Notification) -> bool:
        """Envía notificación por el canal especificado."""
        try:
            if notification.channel == NotificationChannel.EMAIL:
                return await self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                return await self._send_sms(notification)
            elif notification.channel == NotificationChannel.WHATSAPP:
                return await self._send_whatsapp(notification)
            elif notification.channel == NotificationChannel.TELEGRAM:
                return await self._send_telegram(notification)
            elif notification.channel == NotificationChannel.SLACK:
                return await self._send_slack(notification)
            elif notification.channel == NotificationChannel.PUSH:
                return await self._send_push(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                return await self._send_in_app(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(notification)
            elif notification.channel == NotificationChannel.VOICE:
                return await self._send_voice(notification)
            else:
                logger.error(f"Unknown notification channel: {notification.channel}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending via {notification.channel.value}: {str(e)}")
            return False
    
    async def _send_email(self, notification: Notification) -> bool:
        """Envía notificación por email."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.subject
            msg['From'] = self.smtp_config['username']
            msg['To'] = notification.recipient.email
            
            # Texto plano
            text_part = MIMEText(notification.content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML si está disponible
            if notification.html_content:
                html_part = MIMEText(notification.html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Adjuntos
            for attachment in notification.attachments:
                # Implementar lógica de adjuntos
                pass
            
            # Enviar
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    async def _send_sms(self, notification: Notification) -> bool:
        """Envía notificación por SMS."""
        try:
            if not self.twilio_client:
                logger.error("Twilio client not configured")
                return False
            
            message = self.twilio_client.messages.create(
                body=notification.content,
                from_=self.config.get('twilio_from_number'),
                to=notification.recipient.phone
            )
            
            notification.metadata['sms_sid'] = message.sid
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return False
    
    async def _send_whatsapp(self, notification: Notification) -> bool:
        """Envía notificación por WhatsApp."""
        try:
            url = f"{self.whatsapp_config['api_url']}/{self.whatsapp_config['phone_number_id']}/messages"
            
            headers = {
                'Authorization': f"Bearer {self.whatsapp_config['access_token']}",
                'Content-Type': 'application/json'
            }
            
            data = {
                'messaging_product': 'whatsapp',
                'to': notification.recipient.whatsapp or notification.recipient.phone,
                'type': 'text',
                'text': {'body': notification.content}
            }
            
            response = requests.post(url, headers=headers, json=data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}")
            return False
    
    async def _send_telegram(self, notification: Notification) -> bool:
        """Envía notificación por Telegram."""
        try:
            url = f"{self.telegram_config['api_url']}/sendMessage"
            
            data = {
                'chat_id': notification.recipient.telegram_id,
                'text': f"*{notification.subject}*\n\n{notification.content}",
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending Telegram: {str(e)}")
            return False
    
    async def _send_slack(self, notification: Notification) -> bool:
        """Envía notificación por Slack."""
        try:
            if not self.slack_client:
                logger.error("Slack client not configured")
                return False
            
            response = self.slack_client.chat_postMessage(
                channel=notification.recipient.slack_user_id,
                text=f"{notification.subject}\n{notification.content}"
            )
            
            return response['ok']
            
        except Exception as e:
            logger.error(f"Error sending Slack: {str(e)}")
            return False
    
    async def _send_push(self, notification: Notification) -> bool:
        """Envía push notification."""
        try:
            if not self.firebase_app:
                logger.error("Firebase not configured")
                return False
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.subject,
                    body=notification.content
                ),
                token=notification.recipient.push_token
            )
            
            response = messaging.send(message)
            notification.metadata['push_response'] = response
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return False
    
    async def _send_in_app(self, notification: Notification) -> bool:
        """Envía notificación in-app."""
        try:
            # Almacenar en base de datos para mostrar en la aplicación
            # En producción, esto se integraría con WebSockets para tiempo real
            notification.metadata['in_app_stored'] = True
            return True
            
        except Exception as e:
            logger.error(f"Error sending in-app notification: {str(e)}")
            return False
    
    async def _send_webhook(self, notification: Notification) -> bool:
        """Envía notificación via webhook."""
        try:
            webhook_url = notification.metadata.get('webhook_url')
            if not webhook_url:
                logger.error("Webhook URL not provided")
                return False
            
            payload = {
                'notification_id': notification.id,
                'subject': notification.subject,
                'content': notification.content,
                'recipient': notification.recipient.user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(webhook_url, json=payload, timeout=30)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending webhook: {str(e)}")
            return False
    
    async def _send_voice(self, notification: Notification) -> bool:
        """Envía notificación por llamada de voz."""
        try:
            if not self.twilio_client:
                logger.error("Twilio client not configured for voice")
                return False
            
            # Crear TwiML para la llamada
            twiml_url = f"{self.config.get('base_url')}/twiml/{notification.id}"
            
            call = self.twilio_client.calls.create(
                to=notification.recipient.phone,
                from_=self.config.get('twilio_voice_number'),
                url=twiml_url
            )
            
            notification.metadata['call_sid'] = call.sid
            return True
            
        except Exception as e:
            logger.error(f"Error sending voice call: {str(e)}")
            return False
    
    async def _handle_notification_failure(self, notification: Notification):
        """Maneja fallos en el envío de notificaciones."""
        notification.retry_count += 1
        template = self.templates.get(notification.template_id)
        
        max_retries = template.retry_config.get('max_retries', 3) if template else 3
        
        if notification.retry_count <= max_retries:
            # Reintento con backoff exponencial
            delay = template.retry_config.get('base_delay', 60) if template else 60
            backoff_delay = delay * (2 ** (notification.retry_count - 1))
            
            logger.info(f"Retrying notification {notification.id} in {backoff_delay} seconds")
            
            # Programar reintento
            await asyncio.sleep(backoff_delay)
            await self._queue_notification(notification)
        else:
            # Fallo permanente
            notification.status = NotificationStatus.FAILED
            self.metrics['total_failed'] += 1
            
            logger.error(f"Notification {notification.id} failed permanently after {notification.retry_count} retries")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema de notificaciones."""
        total = self.metrics['total_sent'] + self.metrics['total_failed']
        
        return {
            'total_notifications': total,
            'total_sent': self.metrics['total_sent'],
            'total_delivered': self.metrics['total_delivered'],
            'total_failed': self.metrics['total_failed'],
            'success_rate': self.metrics['total_sent'] / total if total > 0 else 0,
            'by_channel': self.metrics['by_channel'],
            'by_priority': self.metrics['by_priority'],
            'queue_sizes': {
                priority.value: len(notifications) 
                for priority, notifications in self.priority_queue.items()
            }
        }
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Lista todas las plantillas disponibles."""
        return [
            {
                'id': template.id,
                'name': template.name,
                'category': template.category,
                'channels': [channel.value for channel in template.channels],
                'priority': template.priority.value,
                'variables': template.variables
            }
            for template in self.templates.values()
        ]
    
    async def mark_as_delivered(self, notification_id: str):
        """Marca una notificación como entregada."""
        # En producción, esto se almacenaría en base de datos
        logger.info(f"Notification {notification_id} marked as delivered")
        self.metrics['total_delivered'] += 1
    
    async def mark_as_read(self, notification_id: str):
        """Marca una notificación como leída."""
        # En producción, esto se almacenaría en base de datos
        logger.info(f"Notification {notification_id} marked as read")
    
    def create_campaign(self, name: str, description: str, template_id: str,
                       recipients: List[NotificationRecipient],
                       channels: List[NotificationChannel],
                       scheduled_at: Optional[datetime] = None) -> NotificationCampaign:
        """Crea una nueva campaña de notificaciones."""
        campaign = NotificationCampaign(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            template_id=template_id,
            recipients=recipients,
            channels=channels,
            scheduled_at=scheduled_at
        )
        
        return campaign