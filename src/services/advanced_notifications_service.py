"""
🔔 ADVANCED NOTIFICATIONS SERVICE - GHUNTRED V2
Sistema avanzado de notificaciones multicanal con múltiples responsabilidades
Para candidatos, clientes y diferentes roles en el proceso de reclutamiento
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import requests
import uuid

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Canales de notificación disponibles"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    TELEGRAM = "telegram"
    DISCORD = "discord"

class NotificationPriority(Enum):
    """Prioridades de notificación"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class RecipientType(Enum):
    """Tipos de destinatarios"""
    CANDIDATE = "candidate"
    CLIENT = "client"
    RECRUITER = "recruiter"
    HR_MANAGER = "hr_manager"
    HIRING_MANAGER = "hiring_manager"
    ADMIN = "admin"
    SYSTEM = "system"

class NotificationStatus(Enum):
    """Estados de notificación"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class NotificationTemplate:
    """Plantilla de notificación"""
    id: str
    name: str
    subject: str
    content: str
    channel: NotificationChannel
    recipient_type: RecipientType
    priority: NotificationPriority
    variables: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    scheduling: Dict[str, Any] = field(default_factory=dict)
    personalization: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationRecipient:
    """Destinatario de notificación"""
    id: str
    type: RecipientType
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    timezone: str = "UTC"
    language: str = "es"
    quiet_hours: Dict[str, str] = field(default_factory=dict)
    subscription_status: Dict[NotificationChannel, bool] = field(default_factory=dict)

@dataclass
class NotificationContext:
    """Contexto de la notificación"""
    process_id: str
    process_type: str  # recruitment, onboarding, feedback, etc.
    stage: str
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    client_id: Optional[str] = None
    recruiter_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NotificationDelivery:
    """Registro de entrega de notificación"""
    id: str
    notification_id: str
    recipient_id: str
    channel: NotificationChannel
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class AdvancedNotificationsService:
    """
    Servicio avanzado de notificaciones multicanal
    Maneja múltiples responsabilidades y tipos de destinatarios
    """
    
    def __init__(self):
        self.templates = {}
        self.recipients = {}
        self.delivery_log = {}
        self.channel_providers = {}
        self.notification_rules = {}
        self.campaigns = {}
        self.analytics = {}
        
        # Configuración de canales
        self.channel_config = {
            NotificationChannel.EMAIL: {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': 'notifications@ghuntred.com',
                'password': 'app_password',
                'rate_limit': 100,  # por hora
                'retry_attempts': 3
            },
            NotificationChannel.SMS: {
                'provider': 'twilio',
                'api_key': 'twilio_api_key',
                'rate_limit': 50,
                'retry_attempts': 2
            },
            NotificationChannel.WHATSAPP: {
                'provider': 'whatsapp_business',
                'api_key': 'whatsapp_api_key',
                'rate_limit': 80,
                'retry_attempts': 3
            },
            NotificationChannel.SLACK: {
                'webhook_url': 'https://hooks.slack.com/services/...',
                'rate_limit': 1,  # por segundo
                'retry_attempts': 2
            }
        }
        
        self.initialized = False
        
    async def initialize_service(self):
        """Inicializa el servicio de notificaciones"""
        if self.initialized:
            return
            
        logger.info("🔔 Inicializando Advanced Notifications Service...")
        
        # Cargar plantillas predefinidas
        await self._load_notification_templates()
        
        # Configurar proveedores de canales
        await self._setup_channel_providers()
        
        # Cargar reglas de notificación
        await self._load_notification_rules()
        
        # Inicializar sistema de analytics
        await self._initialize_analytics()
        
        self.initialized = True
        logger.info("✅ Advanced Notifications Service inicializado")
    
    async def _load_notification_templates(self):
        """Carga plantillas de notificación predefinidas"""
        logger.info("📋 Cargando plantillas de notificación...")
        
        # Plantillas para CANDIDATOS
        candidate_templates = [
            # Proceso de aplicación
            NotificationTemplate(
                id="candidate_application_received",
                name="Aplicación Recibida",
                subject="Tu aplicación ha sido recibida - {job_title}",
                content="""
                Hola {candidate_name},
                
                Hemos recibido tu aplicación para el puesto de {job_title} en {company_name}.
                
                Detalles de tu aplicación:
                - Fecha de aplicación: {application_date}
                - ID de referencia: {application_id}
                - Recruiter asignado: {recruiter_name}
                
                Próximos pasos:
                1. Revisión inicial de tu perfil (1-2 días hábiles)
                2. Evaluación técnica (si aplica)
                3. Entrevistas con el equipo
                
                Te mantendremos informado sobre el progreso de tu aplicación.
                
                ¡Gracias por tu interés en formar parte de nuestro equipo!
                
                Saludos,
                Equipo de Reclutamiento
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.CANDIDATE,
                priority=NotificationPriority.MEDIUM,
                variables=["candidate_name", "job_title", "company_name", "application_date", "application_id", "recruiter_name"]
            ),
            
            # Avance en el proceso
            NotificationTemplate(
                id="candidate_process_advancement",
                name="Avance en Proceso",
                subject="¡Avanzas a la siguiente etapa! - {job_title}",
                content="""
                ¡Excelentes noticias {candidate_name}!
                
                Has avanzado a la siguiente etapa del proceso de selección para {job_title}.
                
                Etapa actual: {current_stage}
                Próxima etapa: {next_stage}
                
                Detalles de la siguiente etapa:
                {next_stage_details}
                
                Fecha programada: {scheduled_date}
                Duración estimada: {estimated_duration}
                
                Preparación recomendada:
                {preparation_tips}
                
                Si tienes alguna pregunta, no dudes en contactar a {recruiter_name} al {recruiter_contact}.
                
                ¡Sigue así!
                
                Saludos,
                {recruiter_name}
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.CANDIDATE,
                priority=NotificationPriority.HIGH,
                variables=["candidate_name", "job_title", "current_stage", "next_stage", "next_stage_details", 
                          "scheduled_date", "estimated_duration", "preparation_tips", "recruiter_name", "recruiter_contact"]
            ),
            
            # Recordatorio de entrevista
            NotificationTemplate(
                id="candidate_interview_reminder",
                name="Recordatorio de Entrevista",
                subject="Recordatorio: Entrevista mañana - {job_title}",
                content="""
                Hola {candidate_name},
                
                Te recordamos tu entrevista programada para mañana:
                
                📅 Fecha: {interview_date}
                🕐 Hora: {interview_time}
                📍 Lugar: {interview_location}
                👥 Entrevistadores: {interviewers}
                ⏱️ Duración: {duration}
                
                Modalidad: {interview_mode}
                {connection_details}
                
                Documentos a llevar:
                {required_documents}
                
                Consejos para la entrevista:
                - Llega 10 minutos antes
                - Prepara preguntas sobre la empresa
                - Revisa tu CV y el job description
                - Viste de manera profesional
                
                ¡Te deseamos mucho éxito!
                
                Saludos,
                {recruiter_name}
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.CANDIDATE,
                priority=NotificationPriority.HIGH,
                variables=["candidate_name", "job_title", "interview_date", "interview_time", 
                          "interview_location", "interviewers", "duration", "interview_mode", 
                          "connection_details", "required_documents", "recruiter_name"]
            ),
            
            # Solicitud de feedback
            NotificationTemplate(
                id="candidate_feedback_request",
                name="Solicitud de Feedback",
                subject="Tu opinión es importante - Feedback del proceso",
                content="""
                Hola {candidate_name},
                
                Esperamos que hayas tenido una buena experiencia en tu {process_stage} para {job_title}.
                
                Tu feedback es muy valioso para nosotros y nos ayuda a mejorar nuestro proceso.
                
                ¿Podrías dedicar 3-5 minutos a compartir tu experiencia?
                
                Enlace al formulario: {feedback_link}
                
                Aspectos que nos gustaría conocer:
                - Claridad del proceso
                - Comunicación del equipo
                - Experiencia en la entrevista
                - Sugerencias de mejora
                
                Tu feedback es completamente confidencial y será usado únicamente para mejorar nuestros procesos.
                
                ¡Gracias por tu tiempo!
                
                Saludos,
                {recruiter_name}
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.CANDIDATE,
                priority=NotificationPriority.MEDIUM,
                variables=["candidate_name", "process_stage", "job_title", "feedback_link", "recruiter_name"]
            )
        ]
        
        # Plantillas para CLIENTES
        client_templates = [
            # Nuevo candidato disponible
            NotificationTemplate(
                id="client_new_candidate",
                name="Nuevo Candidato Disponible",
                subject="Nuevo candidato para {job_title} - Match {match_score}%",
                content="""
                Hola {client_name},
                
                Tenemos un nuevo candidato que podría ser perfecto para tu posición de {job_title}.
                
                📊 Match Score: {match_score}%
                
                Perfil del candidato:
                👤 Nombre: {candidate_name}
                🎓 Experiencia: {experience_years} años
                🏢 Empresa actual: {current_company}
                💼 Posición actual: {current_position}
                💰 Expectativa salarial: {salary_expectation}
                
                Fortalezas destacadas:
                {key_strengths}
                
                Habilidades técnicas:
                {technical_skills}
                
                ¿Te gustaría revisar el perfil completo?
                
                Acciones disponibles:
                - Ver perfil completo: {profile_link}
                - Programar entrevista: {schedule_link}
                - Solicitar más información: {contact_link}
                
                Saludos,
                {recruiter_name}
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.CLIENT,
                priority=NotificationPriority.HIGH,
                variables=["client_name", "job_title", "match_score", "candidate_name", "experience_years",
                          "current_company", "current_position", "salary_expectation", "key_strengths",
                          "technical_skills", "profile_link", "schedule_link", "contact_link", "recruiter_name"]
            ),
            
            # Feedback post-entrevista
            NotificationTemplate(
                id="client_interview_feedback_request",
                name="Feedback Post-Entrevista",
                subject="Feedback requerido - Entrevista con {candidate_name}",
                content="""
                Hola {client_name},
                
                Esperamos que la entrevista con {candidate_name} para {job_title} haya sido productiva.
                
                Detalles de la entrevista:
                📅 Fecha: {interview_date}
                👥 Entrevistadores: {interviewers}
                ⏱️ Duración: {duration}
                
                Para continuar con el proceso, necesitamos tu feedback:
                
                📝 Formulario de feedback: {feedback_link}
                
                Aspectos a evaluar:
                - Fit técnico (1-10)
                - Fit cultural (1-10)
                - Habilidades de comunicación
                - Potencial de crecimiento
                - Recomendación general
                
                Opciones de seguimiento:
                ✅ Avanzar a siguiente etapa
                📋 Solicitar segunda entrevista
                🔄 Necesito más información
                ❌ No continuar con el candidato
                
                Tiempo estimado: 5-7 minutos
                
                ¡Tu feedback es crucial para tomar la mejor decisión!
                
                Saludos,
                {recruiter_name}
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.CLIENT,
                priority=NotificationPriority.HIGH,
                variables=["client_name", "candidate_name", "job_title", "interview_date", "interviewers",
                          "duration", "feedback_link", "recruiter_name"]
            ),
            
            # Reporte semanal de progreso
            NotificationTemplate(
                id="client_weekly_progress_report",
                name="Reporte Semanal de Progreso",
                subject="Reporte semanal - {job_title} | {active_candidates} candidatos activos",
                content="""
                Hola {client_name},
                
                Aquí tienes el reporte semanal del progreso para {job_title}:
                
                📊 RESUMEN EJECUTIVO
                • Candidatos activos: {active_candidates}
                • Nuevos candidatos esta semana: {new_candidates}
                • Entrevistas programadas: {scheduled_interviews}
                • Candidatos en proceso final: {final_stage_candidates}
                
                🎯 ACTIVIDADES DE LA SEMANA
                {weekly_activities}
                
                📈 MÉTRICAS CLAVE
                • Tiempo promedio por etapa: {avg_stage_time}
                • Tasa de conversión: {conversion_rate}%
                • Satisfacción del candidato: {candidate_satisfaction}/10
                
                🔥 CANDIDATOS DESTACADOS
                {top_candidates}
                
                📅 PRÓXIMA SEMANA
                {next_week_plan}
                
                🚨 ATENCIÓN REQUERIDA
                {action_items}
                
                ¿Necesitas discutir algún aspecto del proceso?
                📞 Programar call: {schedule_call_link}
                
                Saludos,
                {recruiter_name}
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.CLIENT,
                priority=NotificationPriority.MEDIUM,
                variables=["client_name", "job_title", "active_candidates", "new_candidates", 
                          "scheduled_interviews", "final_stage_candidates", "weekly_activities",
                          "avg_stage_time", "conversion_rate", "candidate_satisfaction", 
                          "top_candidates", "next_week_plan", "action_items", "schedule_call_link", "recruiter_name"]
            )
        ]
        
        # Plantillas para RECRUITERS
        recruiter_templates = [
            # Nuevo requisito recibido
            NotificationTemplate(
                id="recruiter_new_requirement",
                name="Nuevo Requisito Asignado",
                subject="Nueva búsqueda asignada - {job_title} | Prioridad: {priority}",
                content="""
                Hola {recruiter_name},
                
                Se te ha asignado una nueva búsqueda:
                
                🎯 DETALLES DE LA POSICIÓN
                • Título: {job_title}
                • Cliente: {client_name}
                • Prioridad: {priority}
                • Fecha límite: {deadline}
                • Presupuesto: {budget}
                
                📋 REQUERIMIENTOS
                {job_requirements}
                
                🎯 PERFIL IDEAL
                {ideal_profile}
                
                📊 MÉTRICAS OBJETIVO
                • Candidatos a presentar: {target_candidates}
                • Tiempo objetivo: {target_time}
                • Tasa de conversión esperada: {expected_conversion}%
                
                🔍 ESTRATEGIA SUGERIDA
                {suggested_strategy}
                
                📞 CONTACTO DEL CLIENTE
                {client_contact_info}
                
                Acciones inmediatas:
                - Revisar brief completo: {brief_link}
                - Agendar kick-off con cliente: {kickoff_link}
                - Iniciar búsqueda: {search_link}
                
                ¡Éxito en la búsqueda!
                
                Saludos,
                {manager_name}
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.RECRUITER,
                priority=NotificationPriority.HIGH,
                variables=["recruiter_name", "job_title", "client_name", "priority", "deadline", "budget",
                          "job_requirements", "ideal_profile", "target_candidates", "target_time",
                          "expected_conversion", "suggested_strategy", "client_contact_info",
                          "brief_link", "kickoff_link", "search_link", "manager_name"]
            ),
            
            # Alerta de deadline
            NotificationTemplate(
                id="recruiter_deadline_alert",
                name="Alerta de Deadline",
                subject="⚠️ URGENTE: Deadline próximo - {job_title}",
                content="""
                ⚠️ ALERTA DE DEADLINE
                
                Hola {recruiter_name},
                
                La búsqueda de {job_title} para {client_name} tiene deadline próximo:
                
                📅 Deadline: {deadline}
                ⏰ Tiempo restante: {time_remaining}
                
                📊 ESTADO ACTUAL
                • Candidatos presentados: {presented_candidates}/{target_candidates}
                • En proceso: {candidates_in_process}
                • Pendientes de feedback: {pending_feedback}
                
                🚨 ACCIONES REQUERIDAS
                {required_actions}
                
                💡 RECOMENDACIONES
                {recommendations}
                
                ¿Necesitas apoyo adicional?
                📞 Contactar manager: {manager_contact}
                👥 Solicitar ayuda del equipo: {team_support_link}
                
                ¡Vamos por el cierre exitoso!
                
                Saludos,
                Sistema de Alertas
                """,
                channel=NotificationChannel.EMAIL,
                recipient_type=RecipientType.RECRUITER,
                priority=NotificationPriority.URGENT,
                variables=["recruiter_name", "job_title", "client_name", "deadline", "time_remaining",
                          "presented_candidates", "target_candidates", "candidates_in_process",
                          "pending_feedback", "required_actions", "recommendations", 
                          "manager_contact", "team_support_link"]
            )
        ]
        
        # Registrar todas las plantillas
        all_templates = candidate_templates + client_templates + recruiter_templates
        
        for template in all_templates:
            self.templates[template.id] = template
            logger.info(f"   • Plantilla '{template.name}' cargada")
        
        logger.info(f"✅ {len(all_templates)} plantillas cargadas exitosamente")
    
    async def _setup_channel_providers(self):
        """Configura los proveedores de canales"""
        logger.info("🔧 Configurando proveedores de canales...")
        
        # Email provider
        self.channel_providers[NotificationChannel.EMAIL] = EmailProvider(
            self.channel_config[NotificationChannel.EMAIL]
        )
        
        # SMS provider
        self.channel_providers[NotificationChannel.SMS] = SMSProvider(
            self.channel_config[NotificationChannel.SMS]
        )
        
        # WhatsApp provider
        self.channel_providers[NotificationChannel.WHATSAPP] = WhatsAppProvider(
            self.channel_config[NotificationChannel.WHATSAPP]
        )
        
        # Slack provider
        self.channel_providers[NotificationChannel.SLACK] = SlackProvider(
            self.channel_config[NotificationChannel.SLACK]
        )
        
        logger.info("✅ Proveedores de canales configurados")
    
    async def _load_notification_rules(self):
        """Carga reglas de notificación"""
        logger.info("📜 Cargando reglas de notificación...")
        
        # Reglas por tipo de destinatario
        self.notification_rules = {
            RecipientType.CANDIDATE: {
                'default_channels': [NotificationChannel.EMAIL, NotificationChannel.SMS],
                'urgent_channels': [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.WHATSAPP],
                'quiet_hours': {'start': '22:00', 'end': '08:00'},
                'max_daily_notifications': 5,
                'retry_policy': {'max_retries': 3, 'backoff_factor': 2}
            },
            RecipientType.CLIENT: {
                'default_channels': [NotificationChannel.EMAIL],
                'urgent_channels': [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                'quiet_hours': {'start': '20:00', 'end': '09:00'},
                'max_daily_notifications': 10,
                'retry_policy': {'max_retries': 2, 'backoff_factor': 1.5}
            },
            RecipientType.RECRUITER: {
                'default_channels': [NotificationChannel.EMAIL, NotificationChannel.SLACK],
                'urgent_channels': [NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.SMS],
                'quiet_hours': {'start': '23:00', 'end': '07:00'},
                'max_daily_notifications': 20,
                'retry_policy': {'max_retries': 3, 'backoff_factor': 1.2}
            }
        }
        
        logger.info("✅ Reglas de notificación cargadas")
    
    async def _initialize_analytics(self):
        """Inicializa sistema de analytics"""
        logger.info("📊 Inicializando sistema de analytics...")
        
        self.analytics = {
            'delivery_rates': {},
            'engagement_metrics': {},
            'channel_performance': {},
            'template_effectiveness': {},
            'recipient_preferences': {}
        }
        
        logger.info("✅ Sistema de analytics inicializado")
    
    async def send_notification(self, 
                              template_id: str,
                              recipient_id: str,
                              context: NotificationContext,
                              variables: Dict[str, Any] = None,
                              override_channel: Optional[NotificationChannel] = None,
                              override_priority: Optional[NotificationPriority] = None,
                              schedule_for: Optional[datetime] = None) -> str:
        """
        Envía una notificación usando una plantilla
        """
        if not self.initialized:
            await self.initialize_service()
        
        try:
            # Obtener plantilla
            template = self.templates.get(template_id)
            if not template:
                raise ValueError(f"Plantilla {template_id} no encontrada")
            
            # Obtener destinatario
            recipient = self.recipients.get(recipient_id)
            if not recipient:
                raise ValueError(f"Destinatario {recipient_id} no encontrado")
            
            # Generar ID único para la notificación
            notification_id = str(uuid.uuid4())
            
            # Determinar canal y prioridad
            channel = override_channel or template.channel
            priority = override_priority or template.priority
            
            # Verificar preferencias del destinatario
            if not self._check_recipient_preferences(recipient, channel, priority):
                logger.info(f"Notificación {notification_id} omitida por preferencias del destinatario")
                return notification_id
            
            # Verificar quiet hours
            if self._is_quiet_hours(recipient):
                logger.info(f"Notificación {notification_id} programada para después de quiet hours")
                schedule_for = self._calculate_next_active_time(recipient)
            
            # Preparar variables
            final_variables = variables or {}
            final_variables.update(self._get_context_variables(context))
            
            # Personalizar contenido
            personalized_content = self._personalize_content(template, recipient, final_variables)
            
            # Programar o enviar inmediatamente
            if schedule_for:
                await self._schedule_notification(notification_id, template, recipient, 
                                                personalized_content, channel, priority, schedule_for)
            else:
                await self._send_immediate_notification(notification_id, template, recipient,
                                                      personalized_content, channel, priority)
            
            logger.info(f"✅ Notificación {notification_id} procesada exitosamente")
            return notification_id
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
            raise
    
    async def send_bulk_notification(self,
                                   template_id: str,
                                   recipient_ids: List[str],
                                   context: NotificationContext,
                                   variables: Dict[str, Any] = None,
                                   batch_size: int = 100) -> List[str]:
        """
        Envía notificaciones en lote
        """
        notification_ids = []
        
        # Procesar en lotes
        for i in range(0, len(recipient_ids), batch_size):
            batch = recipient_ids[i:i + batch_size]
            
            # Enviar lote en paralelo
            tasks = []
            for recipient_id in batch:
                task = self.send_notification(template_id, recipient_id, context, variables)
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error en lote: {result}")
                else:
                    notification_ids.append(result)
        
        logger.info(f"✅ Lote de {len(notification_ids)} notificaciones procesado")
        return notification_ids
    
    async def create_notification_campaign(self,
                                         name: str,
                                         template_id: str,
                                         target_criteria: Dict[str, Any],
                                         schedule: Dict[str, Any],
                                         variables: Dict[str, Any] = None) -> str:
        """
        Crea una campaña de notificaciones
        """
        campaign_id = str(uuid.uuid4())
        
        campaign = {
            'id': campaign_id,
            'name': name,
            'template_id': template_id,
            'target_criteria': target_criteria,
            'schedule': schedule,
            'variables': variables or {},
            'status': 'active',
            'created_at': datetime.now(),
            'metrics': {
                'total_recipients': 0,
                'sent': 0,
                'delivered': 0,
                'read': 0,
                'failed': 0
            }
        }
        
        self.campaigns[campaign_id] = campaign
        
        # Programar ejecución de la campaña
        await self._schedule_campaign_execution(campaign)
        
        logger.info(f"✅ Campaña '{name}' creada con ID {campaign_id}")
        return campaign_id
    
    def _check_recipient_preferences(self, recipient: NotificationRecipient, 
                                   channel: NotificationChannel, 
                                   priority: NotificationPriority) -> bool:
        """Verifica las preferencias del destinatario"""
        
        # Verificar suscripción al canal
        if channel in recipient.subscription_status:
            if not recipient.subscription_status[channel]:
                return False
        
        # Verificar límite diario
        daily_count = self._get_daily_notification_count(recipient.id)
        max_daily = self.notification_rules[recipient.type]['max_daily_notifications']
        
        if daily_count >= max_daily and priority != NotificationPriority.CRITICAL:
            return False
        
        return True
    
    def _is_quiet_hours(self, recipient: NotificationRecipient) -> bool:
        """Verifica si está en horario de silencio"""
        if not recipient.quiet_hours:
            return False
        
        # Lógica simplificada - en producción consideraría timezone
        current_time = datetime.now().time()
        start_time = datetime.strptime(recipient.quiet_hours.get('start', '22:00'), '%H:%M').time()
        end_time = datetime.strptime(recipient.quiet_hours.get('end', '08:00'), '%H:%M').time()
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            return current_time >= start_time or current_time <= end_time
    
    def _calculate_next_active_time(self, recipient: NotificationRecipient) -> datetime:
        """Calcula el próximo horario activo"""
        # Lógica simplificada
        tomorrow = datetime.now() + timedelta(days=1)
        end_time = recipient.quiet_hours.get('end', '08:00')
        next_active = datetime.strptime(f"{tomorrow.date()} {end_time}", '%Y-%m-%d %H:%M')
        return next_active
    
    def _get_context_variables(self, context: NotificationContext) -> Dict[str, Any]:
        """Obtiene variables del contexto"""
        return {
            'process_id': context.process_id,
            'process_type': context.process_type,
            'stage': context.stage,
            'candidate_id': context.candidate_id,
            'job_id': context.job_id,
            'client_id': context.client_id,
            'recruiter_id': context.recruiter_id,
            **context.additional_data
        }
    
    def _personalize_content(self, template: NotificationTemplate, 
                           recipient: NotificationRecipient, 
                           variables: Dict[str, Any]) -> Dict[str, str]:
        """Personaliza el contenido de la notificación"""
        
        # Reemplazar variables en subject y content
        subject = template.subject
        content = template.content
        
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            subject = subject.replace(placeholder, str(var_value))
            content = content.replace(placeholder, str(var_value))
        
        # Aplicar personalizaciones adicionales
        if recipient.language != 'es':
            # Aquí se aplicaría traducción
            pass
        
        return {
            'subject': subject,
            'content': content
        }
    
    async def _send_immediate_notification(self, notification_id: str, 
                                         template: NotificationTemplate,
                                         recipient: NotificationRecipient,
                                         content: Dict[str, str],
                                         channel: NotificationChannel,
                                         priority: NotificationPriority):
        """Envía notificación inmediatamente"""
        
        # Crear registro de entrega
        delivery = NotificationDelivery(
            id=str(uuid.uuid4()),
            notification_id=notification_id,
            recipient_id=recipient.id,
            channel=channel,
            status=NotificationStatus.PENDING
        )
        
        try:
            # Obtener proveedor del canal
            provider = self.channel_providers.get(channel)
            if not provider:
                raise ValueError(f"Proveedor para canal {channel} no encontrado")
            
            # Enviar notificación
            await provider.send(recipient, content, priority)
            
            # Actualizar estado
            delivery.status = NotificationStatus.SENT
            delivery.sent_at = datetime.now()
            
            logger.info(f"✅ Notificación {notification_id} enviada por {channel}")
            
        except Exception as e:
            delivery.status = NotificationStatus.FAILED
            delivery.failed_reason = str(e)
            logger.error(f"❌ Error enviando notificación {notification_id}: {e}")
            
            # Programar reintento si es necesario
            await self._schedule_retry(delivery, template, recipient, content, channel, priority)
        
        # Guardar registro
        self.delivery_log[delivery.id] = delivery
    
    async def _schedule_notification(self, notification_id: str,
                                   template: NotificationTemplate,
                                   recipient: NotificationRecipient,
                                   content: Dict[str, str],
                                   channel: NotificationChannel,
                                   priority: NotificationPriority,
                                   schedule_for: datetime):
        """Programa una notificación para envío posterior"""
        
        # En una implementación real, esto se haría con un scheduler como Celery
        logger.info(f"📅 Notificación {notification_id} programada para {schedule_for}")
        
        # Simular programación
        delay = (schedule_for - datetime.now()).total_seconds()
        if delay > 0:
            await asyncio.sleep(min(delay, 1))  # Limitar para demo
        
        await self._send_immediate_notification(notification_id, template, recipient, 
                                              content, channel, priority)
    
    async def _schedule_retry(self, delivery: NotificationDelivery,
                            template: NotificationTemplate,
                            recipient: NotificationRecipient,
                            content: Dict[str, str],
                            channel: NotificationChannel,
                            priority: NotificationPriority):
        """Programa reintento de notificación"""
        
        retry_policy = self.notification_rules[recipient.type]['retry_policy']
        max_retries = retry_policy['max_retries']
        backoff_factor = retry_policy['backoff_factor']
        
        if delivery.retry_count < max_retries:
            delivery.retry_count += 1
            
            # Calcular delay exponencial
            delay = (backoff_factor ** delivery.retry_count) * 60  # minutos
            retry_time = datetime.now() + timedelta(minutes=delay)
            
            logger.info(f"🔄 Programando reintento {delivery.retry_count}/{max_retries} para {retry_time}")
            
            # Programar reintento
            await self._schedule_notification(delivery.notification_id, template, recipient,
                                            content, channel, priority, retry_time)
    
    def _get_daily_notification_count(self, recipient_id: str) -> int:
        """Obtiene el conteo diario de notificaciones para un destinatario"""
        today = datetime.now().date()
        count = 0
        
        for delivery in self.delivery_log.values():
            if (delivery.recipient_id == recipient_id and 
                delivery.sent_at and 
                delivery.sent_at.date() == today):
                count += 1
        
        return count
    
    async def _schedule_campaign_execution(self, campaign: Dict[str, Any]):
        """Programa la ejecución de una campaña"""
        logger.info(f"📊 Programando ejecución de campaña '{campaign['name']}'")
        
        # Lógica de programación de campañas
        # En producción esto sería más sofisticado
        pass
    
    async def get_notification_status(self, notification_id: str) -> Dict[str, Any]:
        """Obtiene el estado de una notificación"""
        deliveries = [d for d in self.delivery_log.values() if d.notification_id == notification_id]
        
        if not deliveries:
            return {'status': 'not_found'}
        
        return {
            'notification_id': notification_id,
            'deliveries': [
                {
                    'id': d.id,
                    'channel': d.channel.value,
                    'status': d.status.value,
                    'sent_at': d.sent_at.isoformat() if d.sent_at else None,
                    'delivered_at': d.delivered_at.isoformat() if d.delivered_at else None,
                    'read_at': d.read_at.isoformat() if d.read_at else None,
                    'retry_count': d.retry_count
                }
                for d in deliveries
            ]
        }
    
    async def get_analytics_report(self, 
                                 start_date: datetime,
                                 end_date: datetime,
                                 filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Genera reporte de analytics"""
        
        # Filtrar deliveries por fecha
        filtered_deliveries = [
            d for d in self.delivery_log.values()
            if d.sent_at and start_date <= d.sent_at <= end_date
        ]
        
        # Aplicar filtros adicionales
        if filters:
            if 'channel' in filters:
                filtered_deliveries = [d for d in filtered_deliveries if d.channel == filters['channel']]
            if 'recipient_type' in filters:
                # Necesitaríamos acceso a recipient info
                pass
        
        # Calcular métricas
        total_sent = len(filtered_deliveries)
        total_delivered = len([d for d in filtered_deliveries if d.status == NotificationStatus.DELIVERED])
        total_read = len([d for d in filtered_deliveries if d.status == NotificationStatus.READ])
        total_failed = len([d for d in filtered_deliveries if d.status == NotificationStatus.FAILED])
        
        # Métricas por canal
        channel_metrics = {}
        for channel in NotificationChannel:
            channel_deliveries = [d for d in filtered_deliveries if d.channel == channel]
            if channel_deliveries:
                channel_metrics[channel.value] = {
                    'sent': len(channel_deliveries),
                    'delivered': len([d for d in channel_deliveries if d.status == NotificationStatus.DELIVERED]),
                    'delivery_rate': len([d for d in channel_deliveries if d.status == NotificationStatus.DELIVERED]) / len(channel_deliveries) * 100
                }
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_sent': total_sent,
                'total_delivered': total_delivered,
                'total_read': total_read,
                'total_failed': total_failed,
                'delivery_rate': (total_delivered / total_sent * 100) if total_sent > 0 else 0,
                'read_rate': (total_read / total_delivered * 100) if total_delivered > 0 else 0
            },
            'channel_performance': channel_metrics,
            'generated_at': datetime.now().isoformat()
        }

# Proveedores de canales
class EmailProvider:
    """Proveedor de email"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send(self, recipient: NotificationRecipient, 
                  content: Dict[str, str], priority: NotificationPriority):
        """Envía email"""
        if not recipient.email:
            raise ValueError("Recipient email not provided")
        
        # Simulación de envío de email
        logger.info(f"📧 Enviando email a {recipient.email}")
        logger.info(f"   Asunto: {content['subject']}")
        
        # En producción, aquí se enviaría el email real
        await asyncio.sleep(0.1)  # Simular latencia
        
        logger.info("✅ Email enviado exitosamente")

class SMSProvider:
    """Proveedor de SMS"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send(self, recipient: NotificationRecipient, 
                  content: Dict[str, str], priority: NotificationPriority):
        """Envía SMS"""
        if not recipient.phone:
            raise ValueError("Recipient phone not provided")
        
        logger.info(f"📱 Enviando SMS a {recipient.phone}")
        
        # Truncar contenido para SMS
        sms_content = content['content'][:160]
        logger.info(f"   Contenido: {sms_content}")
        
        await asyncio.sleep(0.05)  # Simular latencia
        
        logger.info("✅ SMS enviado exitosamente")

class WhatsAppProvider:
    """Proveedor de WhatsApp"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send(self, recipient: NotificationRecipient, 
                  content: Dict[str, str], priority: NotificationPriority):
        """Envía WhatsApp"""
        if not recipient.phone:
            raise ValueError("Recipient phone not provided")
        
        logger.info(f"💬 Enviando WhatsApp a {recipient.phone}")
        logger.info(f"   Mensaje: {content['subject']}")
        
        await asyncio.sleep(0.1)  # Simular latencia
        
        logger.info("✅ WhatsApp enviado exitosamente")

class SlackProvider:
    """Proveedor de Slack"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def send(self, recipient: NotificationRecipient, 
                  content: Dict[str, str], priority: NotificationPriority):
        """Envía mensaje a Slack"""
        logger.info(f"💬 Enviando mensaje a Slack")
        logger.info(f"   Canal: {recipient.preferences.get('slack_channel', '#general')}")
        
        await asyncio.sleep(0.05)  # Simular latencia
        
        logger.info("✅ Mensaje de Slack enviado exitosamente")

# Instancia global del servicio
advanced_notifications_service = AdvancedNotificationsService()