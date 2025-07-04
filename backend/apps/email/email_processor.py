"""
Advanced Email Processor - huntRED® v2
Procesador avanzado de emails con IA, clasificación automática y respuestas inteligentes.
"""

import email
import imaplib
import smtplib
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import asyncio
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class ProcessedEmail:
    """Estructura de email procesado."""
    message_id: str
    sender: str
    recipient: str
    subject: str
    body: str
    attachments: List[Dict]
    timestamp: datetime
    
    # Análisis IA
    category: str  # job_application, inquiry, complaint, etc.
    sentiment: str
    priority: str  # high, medium, low
    intent: str
    confidence_score: float
    
    # Entidades extraídas
    entities: List[Dict]
    candidate_info: Optional[Dict]
    job_related: bool
    
    # Respuesta automática
    auto_response_sent: bool
    auto_response_content: Optional[str]
    requires_human_review: bool
    
    # Metadata
    processing_time: float
    processor_version: str


@dataclass
class EmailResponse:
    """Respuesta de email generada automáticamente."""
    recipient: str
    subject: str
    body: str
    template_used: str
    personalization_data: Dict[str, Any]
    confidence_score: float
    send_immediately: bool
    review_required: bool


class AdvancedEmailProcessor:
    """
    Procesador avanzado de emails con IA para gestión automatizada de comunicaciones.
    """
    
    def __init__(self, config: Dict[str, Any], db_session: Session):
        self.config = config
        self.db = db_session
        
        # Configuración de email
        self.imap_config = {
            'server': config.get('imap_server'),
            'port': config.get('imap_port', 993),
            'username': config.get('email_username'),
            'password': config.get('email_password'),
            'use_ssl': config.get('imap_ssl', True)
        }
        
        self.smtp_config = {
            'server': config.get('smtp_server'),
            'port': config.get('smtp_port', 587),
            'username': config.get('email_username'),
            'password': config.get('email_password'),
            'use_tls': config.get('smtp_tls', True)
        }
        
        # Configurar clasificadores y analizadores
        self._setup_email_classifiers()
        self._setup_response_templates()
        self._setup_priority_rules()
        
        # Estados de conexión
        self.imap_connection = None
        self.smtp_connection = None
    
    def _setup_email_classifiers(self):
        """Configura clasificadores de email."""
        # Categorías de email
        self.email_categories = {
            'job_application': {
                'keywords': ['application', 'apply', 'resume', 'cv', 'position', 'job'],
                'patterns': [r'applying for', r'interested in.*position', r'attached.*resume'],
                'priority': 'high'
            },
            'candidate_inquiry': {
                'keywords': ['question', 'inquiry', 'interested', 'information', 'details'],
                'patterns': [r'could you.*tell me', r'i would like to know', r'more information'],
                'priority': 'medium'
            },
            'interview_related': {
                'keywords': ['interview', 'meeting', 'schedule', 'availability', 'reschedule'],
                'patterns': [r'interview.*schedule', r'meeting.*time', r'available.*for'],
                'priority': 'high'
            },
            'complaint': {
                'keywords': ['complaint', 'problem', 'issue', 'disappointed', 'unsatisfied'],
                'patterns': [r'not happy', r'poor service', r'disappointed'],
                'priority': 'high'
            },
            'thank_you': {
                'keywords': ['thank you', 'thanks', 'grateful', 'appreciate'],
                'patterns': [r'thank you for', r'i appreciate', r'grateful for'],
                'priority': 'low'
            },
            'spam': {
                'keywords': ['offer', 'deal', 'discount', 'limited time', 'act now'],
                'patterns': [r'limited.*offer', r'act now', r'free.*money'],
                'priority': 'low'
            }
        }
        
        # Patrones de detección de candidatos
        self.candidate_patterns = {
            'cv_attached': r'attach.*(?:cv|resume|curriculum)',
            'experience_mention': r'(\d+).*years?.*experience',
            'skill_mention': r'(?:skilled in|experienced with|proficient in)\s*(.*?)(?:\.|$)',
            'education_mention': r'(?:graduated|degree|university|college)\s*(.*?)(?:\.|$)'
        }
    
    def _setup_response_templates(self):
        """Configura plantillas de respuesta automática."""
        self.response_templates = {
            'job_application_acknowledgment': {
                'subject': 'Recibimos tu aplicación - {job_position}',
                'template': """
                Estimado/a {candidate_name},
                
                Gracias por tu interés en la posición de {job_position} en huntRED®.
                
                Hemos recibido tu aplicación y nuestro equipo de reclutamiento la está revisando. 
                Te contactaremos dentro de los próximos 3-5 días hábiles para informarte sobre 
                los siguientes pasos.
                
                Mientras tanto, puedes:
                • Revisar más oportunidades en nuestro portal
                • Seguirnos en LinkedIn para consejos de carrera
                • Completar tu perfil en nuestra plataforma
                
                ¡Gracias por considerar huntRED® como tu próximo destino profesional!
                
                Saludos cordiales,
                Equipo de Reclutamiento huntRED®
                """,
                'personalization_fields': ['candidate_name', 'job_position'],
                'auto_send': True
            },
            'general_inquiry_response': {
                'subject': 'Respuesta a tu consulta - huntRED®',
                'template': """
                Hola {sender_name},
                
                Gracias por contactarnos. Hemos recibido tu mensaje y nos pondremos en contacto 
                contigo a la brevedad.
                
                Si tu consulta es urgente, puedes:
                • Llamar a nuestro número: +1 (555) 123-4567
                • Usar nuestro chat en línea: huntred.com
                • Escribirnos por WhatsApp: +1 (555) 987-6543
                
                Valoramos tu interés en huntRED® y esperamos poder ayudarte pronto.
                
                Saludos,
                Equipo de Atención al Cliente huntRED®
                """,
                'personalization_fields': ['sender_name'],
                'auto_send': True
            },
            'interview_confirmation': {
                'subject': 'Confirmación de entrevista - {candidate_name}',
                'template': """
                Estimado/a {candidate_name},
                
                Confirmamos tu entrevista para la posición de {job_position}:
                
                📅 Fecha: {interview_date}
                🕒 Hora: {interview_time}
                📍 Ubicación: {interview_location}
                👥 Entrevistador(es): {interviewer_names}
                
                Por favor, confirma tu asistencia respondiendo a este email.
                
                Prepárate para discutir:
                • Tu experiencia relevante
                • Tus objetivos profesionales
                • Preguntas sobre la empresa y el rol
                
                ¡Esperamos conocerte pronto!
                
                Saludos cordiales,
                {interviewer_names}
                huntRED® - Talent Acquisition Team
                """,
                'personalization_fields': [
                    'candidate_name', 'job_position', 'interview_date', 
                    'interview_time', 'interview_location', 'interviewer_names'
                ],
                'auto_send': False  # Requiere revisión humana
            }
        }
    
    def _setup_priority_rules(self):
        """Configura reglas de priorización."""
        self.priority_rules = {
            'high_priority_senders': [
                '@clienteimportante.com',
                '@socioestratégico.com',
                'ceo@',
                'director@'
            ],
            'urgent_keywords': [
                'urgent', 'asap', 'emergency', 'immediate',
                'urgente', 'inmediato', 'emergencia'
            ],
            'vip_patterns': [
                r'c-level',
                r'director.*level',
                r'vp.*',
                r'vice.*president'
            ]
        }
    
    async def connect_email_services(self):
        """Conecta a los servicios de email IMAP y SMTP."""
        try:
            # Conexión IMAP
            if self.imap_config['use_ssl']:
                self.imap_connection = imaplib.IMAP4_SSL(
                    self.imap_config['server'], 
                    self.imap_config['port']
                )
            else:
                self.imap_connection = imaplib.IMAP4(
                    self.imap_config['server'], 
                    self.imap_config['port']
                )
            
            self.imap_connection.login(
                self.imap_config['username'], 
                self.imap_config['password']
            )
            
            # Conexión SMTP
            self.smtp_connection = smtplib.SMTP(
                self.smtp_config['server'], 
                self.smtp_config['port']
            )
            
            if self.smtp_config['use_tls']:
                self.smtp_connection.starttls()
            
            self.smtp_connection.login(
                self.smtp_config['username'], 
                self.smtp_config['password']
            )
            
            logger.info("Email services connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to email services: {str(e)}")
            return False
    
    async def process_inbox_emails(self, folder: str = 'INBOX', 
                                 limit: int = 50) -> List[ProcessedEmail]:
        """Procesa emails del inbox de manera inteligente."""
        processed_emails = []
        
        try:
            if not self.imap_connection:
                await self.connect_email_services()
            
            # Seleccionar folder
            self.imap_connection.select(folder)
            
            # Buscar emails no leídos
            status, messages = self.imap_connection.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.error("Error searching for emails")
                return processed_emails
            
            email_ids = messages[0].split()
            
            # Limitar número de emails a procesar
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            for email_id in email_ids:
                try:
                    processed_email = await self._process_single_email(email_id)
                    if processed_email:
                        processed_emails.append(processed_email)
                        
                        # Enviar respuesta automática si es necesario
                        if self._should_auto_respond(processed_email):
                            await self._send_auto_response(processed_email)
                        
                        # Marcar como procesado
                        await self._mark_email_processed(email_id, processed_email)
                        
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {str(e)}")
                    continue
            
            logger.info(f"Processed {len(processed_emails)} emails")
            return processed_emails
            
        except Exception as e:
            logger.error(f"Error processing inbox: {str(e)}")
            return processed_emails
    
    async def _process_single_email(self, email_id: bytes) -> Optional[ProcessedEmail]:
        """Procesa un email individual."""
        start_time = datetime.now()
        
        try:
            # Obtener email completo
            status, msg_data = self.imap_connection.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                return None
            
            # Parsear email
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extraer información básica
            sender = email_message.get('From', '')
            recipient = email_message.get('To', '')
            subject = email_message.get('Subject', '')
            message_id = email_message.get('Message-ID', str(email_id))
            
            # Extraer fecha
            date_str = email_message.get('Date', '')
            timestamp = email.utils.parsedate_to_datetime(date_str) if date_str else datetime.now()
            
            # Extraer cuerpo del email
            body = self._extract_email_body(email_message)
            
            # Extraer adjuntos
            attachments = self._extract_attachments(email_message)
            
            # Análisis con IA
            analysis = await self._analyze_email_content(sender, subject, body, attachments)
            
            # Crear objeto ProcessedEmail
            processed_email = ProcessedEmail(
                message_id=message_id,
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                attachments=attachments,
                timestamp=timestamp,
                
                # Análisis IA
                category=analysis.get('category', 'general'),
                sentiment=analysis.get('sentiment', 'neutral'),
                priority=analysis.get('priority', 'medium'),
                intent=analysis.get('intent', 'unknown'),
                confidence_score=analysis.get('confidence', 0.0),
                
                # Entidades
                entities=analysis.get('entities', []),
                candidate_info=analysis.get('candidate_info'),
                job_related=analysis.get('job_related', False),
                
                # Respuesta automática
                auto_response_sent=False,
                auto_response_content=None,
                requires_human_review=analysis.get('requires_review', False),
                
                # Metadata
                processing_time=(datetime.now() - start_time).total_seconds(),
                processor_version="2.0.0"
            )
            
            return processed_email
            
        except Exception as e:
            logger.error(f"Error processing single email: {str(e)}")
            return None
    
    def _extract_email_body(self, email_message) -> str:
        """Extrae el cuerpo del email."""
        body = ""
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        body_bytes = part.get_payload(decode=True)
                        if body_bytes:
                            body += body_bytes.decode(charset, errors='ignore')
                    elif part.get_content_type() == "text/html" and not body:
                        charset = part.get_content_charset() or 'utf-8'
                        body_bytes = part.get_payload(decode=True)
                        if body_bytes:
                            html_body = body_bytes.decode(charset, errors='ignore')
                            # Convertir HTML a texto plano (simplificado)
                            body = re.sub('<[^<]+?>', '', html_body)
            else:
                charset = email_message.get_content_charset() or 'utf-8'
                body_bytes = email_message.get_payload(decode=True)
                if body_bytes:
                    body = body_bytes.decode(charset, errors='ignore')
            
            return body.strip()
            
        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
            return ""
    
    def _extract_attachments(self, email_message) -> List[Dict]:
        """Extrae información de adjuntos."""
        attachments = []
        
        try:
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachment_info = {
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b''),
                            'is_cv': self._is_cv_file(filename)
                        }
                        attachments.append(attachment_info)
            
            return attachments
            
        except Exception as e:
            logger.error(f"Error extracting attachments: {str(e)}")
            return []
    
    async def _analyze_email_content(self, sender: str, subject: str, 
                                   body: str, attachments: List[Dict]) -> Dict[str, Any]:
        """Análisis completo del contenido del email."""
        analysis = {}
        
        try:
            # Combinar texto para análisis
            full_text = f"{subject} {body}".lower()
            
            # Clasificar categoría
            category = self._classify_email_category(full_text, attachments)
            analysis['category'] = category
            
            # Análisis de sentimiento (simplificado)
            sentiment = self._analyze_sentiment(full_text)
            analysis['sentiment'] = sentiment
            
            # Determinar prioridad
            priority = self._determine_priority(sender, subject, body, category)
            analysis['priority'] = priority
            
            # Detectar intención
            intent = self._detect_intent(full_text, category, attachments)
            analysis['intent'] = intent
            
            # Extraer entidades
            entities = self._extract_entities(body)
            analysis['entities'] = entities
            
            # Detectar información de candidato
            candidate_info = self._extract_candidate_info(body, attachments)
            analysis['candidate_info'] = candidate_info
            
            # Determinar si está relacionado con trabajos
            job_related = self._is_job_related(full_text, attachments)
            analysis['job_related'] = job_related
            
            # Determinar si requiere revisión humana
            requires_review = self._requires_human_review(category, priority, sentiment)
            analysis['requires_review'] = requires_review
            
            # Calcular confidence score
            confidence = self._calculate_analysis_confidence(analysis)
            analysis['confidence'] = confidence
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing email content: {str(e)}")
            return {'confidence': 0.0}
    
    def _classify_email_category(self, text: str, attachments: List[Dict]) -> str:
        """Clasifica la categoría del email."""
        scores = {}
        
        for category, rules in self.email_categories.items():
            score = 0
            
            # Buscar keywords
            for keyword in rules['keywords']:
                if keyword in text:
                    score += 1
            
            # Buscar patrones
            for pattern in rules['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 2
            
            # Bonus por adjuntos relevantes
            if category == 'job_application' and any(att['is_cv'] for att in attachments):
                score += 3
            
            scores[category] = score
        
        # Retornar categoría con mayor score
        if scores:
            return max(scores, key=scores.get)
        
        return 'general'
    
    def _analyze_sentiment(self, text: str) -> str:
        """Análisis de sentimiento simplificado."""
        positive_words = ['thank', 'great', 'excellent', 'good', 'happy', 'pleased']
        negative_words = ['problem', 'issue', 'bad', 'terrible', 'awful', 'disappointed']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _determine_priority(self, sender: str, subject: str, body: str, category: str) -> str:
        """Determina la prioridad del email."""
        priority_score = 0
        
        # Prioridad por categoría
        if category in ['complaint', 'interview_related', 'job_application']:
            priority_score += 2
        
        # Prioridad por remitente
        for vip_domain in self.priority_rules['high_priority_senders']:
            if vip_domain in sender.lower():
                priority_score += 3
                break
        
        # Prioridad por keywords urgentes
        full_text = f"{subject} {body}".lower()
        for urgent_keyword in self.priority_rules['urgent_keywords']:
            if urgent_keyword in full_text:
                priority_score += 2
                break
        
        # Determinar prioridad final
        if priority_score >= 4:
            return 'high'
        elif priority_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _detect_intent(self, text: str, category: str, attachments: List[Dict]) -> str:
        """Detecta la intención del email."""
        intent_patterns = {
            'apply_for_job': [r'applying for', r'application for', r'interested in.*position'],
            'schedule_interview': [r'schedule.*interview', r'meeting.*time', r'available.*for'],
            'ask_question': [r'question about', r'could you.*tell', r'i would like to know'],
            'provide_feedback': [r'feedback', r'review', r'opinion about'],
            'make_complaint': [r'complaint', r'not satisfied', r'problem with'],
            'express_gratitude': [r'thank you', r'grateful', r'appreciate']
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent
        
        # Intent basado en categoría
        intent_mapping = {
            'job_application': 'apply_for_job',
            'interview_related': 'schedule_interview',
            'candidate_inquiry': 'ask_question',
            'complaint': 'make_complaint',
            'thank_you': 'express_gratitude'
        }
        
        return intent_mapping.get(category, 'general_inquiry')
    
    def _extract_entities(self, text: str) -> List[Dict]:
        """Extrae entidades del texto (simplificado)."""
        entities = []
        
        # Extraer emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        for email_addr in emails:
            entities.append({'type': 'EMAIL', 'value': email_addr})
        
        # Extraer teléfonos
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,14}'
        phones = re.findall(phone_pattern, text)
        for phone in phones:
            if len(phone) >= 7:  # Validación básica
                entities.append({'type': 'PHONE', 'value': phone})
        
        # Extraer años de experiencia
        exp_pattern = r'(\d+)[\s]*(?:years?|yrs?)[\s]*(?:of[\s]*)?(?:experience|exp)'
        experience_matches = re.findall(exp_pattern, text, re.IGNORECASE)
        for exp in experience_matches:
            entities.append({'type': 'EXPERIENCE_YEARS', 'value': int(exp)})
        
        return entities
    
    def _extract_candidate_info(self, body: str, attachments: List[Dict]) -> Optional[Dict]:
        """Extrae información del candidato."""
        if not any(att['is_cv'] for att in attachments):
            return None
        
        candidate_info = {}
        
        # Extraer nombre (simplificado)
        name_patterns = [
            r'my name is ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'i am ([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)(?:\s*,|\s*$)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, body)
            if match:
                candidate_info['name'] = match.group(1)
                break
        
        # Extraer email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', body)
        if email_match:
            candidate_info['email'] = email_match.group(0)
        
        # Extraer experiencia
        exp_match = re.search(r'(\d+)[\s]*(?:years?|yrs?)[\s]*(?:of[\s]*)?(?:experience|exp)', body, re.IGNORECASE)
        if exp_match:
            candidate_info['years_experience'] = int(exp_match.group(1))
        
        return candidate_info if candidate_info else None
    
    def _is_job_related(self, text: str, attachments: List[Dict]) -> bool:
        """Determina si el email está relacionado con trabajos."""
        job_keywords = [
            'job', 'position', 'role', 'career', 'employment', 'work',
            'hiring', 'recruitment', 'cv', 'resume', 'application'
        ]
        
        # Buscar keywords relacionados con trabajos
        for keyword in job_keywords:
            if keyword in text:
                return True
        
        # Si tiene CV adjunto, es relacionado con trabajos
        if any(att['is_cv'] for att in attachments):
            return True
        
        return False
    
    def _requires_human_review(self, category: str, priority: str, sentiment: str) -> bool:
        """Determina si el email requiere revisión humana."""
        # Siempre revisar complaints
        if category == 'complaint':
            return True
        
        # Revisar emails de alta prioridad
        if priority == 'high':
            return True
        
        # Revisar sentimientos negativos
        if sentiment == 'negative':
            return True
        
        # Revisar ciertos tipos de aplicaciones
        if category == 'job_application' and priority == 'medium':
            return True
        
        return False
    
    def _calculate_analysis_confidence(self, analysis: Dict) -> float:
        """Calcula el confidence score del análisis."""
        base_confidence = 0.5
        
        # Bonus por categoría bien definida
        if analysis.get('category') != 'general':
            base_confidence += 0.2
        
        # Bonus por entidades encontradas
        if analysis.get('entities'):
            base_confidence += 0.1
        
        # Bonus por información de candidato
        if analysis.get('candidate_info'):
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)
    
    def _should_auto_respond(self, processed_email: ProcessedEmail) -> bool:
        """Determina si debe enviar respuesta automática."""
        # No responder a spam
        if processed_email.category == 'spam':
            return False
        
        # No responder si requiere revisión humana crítica
        if processed_email.requires_human_review and processed_email.priority == 'high':
            return False
        
        # Responder a aplicaciones de trabajo
        if processed_email.category == 'job_application':
            return True
        
        # Responder a inquiries generales
        if processed_email.category == 'candidate_inquiry':
            return True
        
        return False
    
    async def _send_auto_response(self, processed_email: ProcessedEmail) -> bool:
        """Envía respuesta automática."""
        try:
            # Seleccionar template apropiado
            template_key = self._select_response_template(processed_email)
            
            if not template_key:
                return False
            
            template = self.response_templates[template_key]
            
            # Generar respuesta personalizada
            response = await self._generate_personalized_response(processed_email, template)
            
            # Enviar respuesta si auto_send está habilitado
            if template.get('auto_send', False):
                success = await self._send_email_response(response)
                if success:
                    processed_email.auto_response_sent = True
                    processed_email.auto_response_content = response.body
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending auto response: {str(e)}")
            return False
    
    def _select_response_template(self, processed_email: ProcessedEmail) -> Optional[str]:
        """Selecciona el template de respuesta apropiado."""
        if processed_email.category == 'job_application':
            return 'job_application_acknowledgment'
        elif processed_email.category == 'candidate_inquiry':
            return 'general_inquiry_response'
        elif processed_email.category == 'interview_related':
            return 'interview_confirmation'
        
        return None
    
    async def _generate_personalized_response(self, processed_email: ProcessedEmail, 
                                            template: Dict) -> EmailResponse:
        """Genera respuesta personalizada."""
        # Extraer datos de personalización
        personalization_data = {}
        
        # Extraer nombre del sender
        sender_name = self._extract_sender_name(processed_email.sender)
        personalization_data['sender_name'] = sender_name
        personalization_data['candidate_name'] = sender_name
        
        # Datos específicos por categoría
        if processed_email.category == 'job_application':
            job_position = self._extract_job_position(processed_email.subject, processed_email.body)
            personalization_data['job_position'] = job_position or 'la posición solicitada'
        
        # Personalizar subject y body
        subject = template['subject'].format(**personalization_data)
        body = template['template'].format(**personalization_data)
        
        return EmailResponse(
            recipient=processed_email.sender,
            subject=subject,
            body=body,
            template_used=template.get('template_name', 'unknown'),
            personalization_data=personalization_data,
            confidence_score=0.8,
            send_immediately=template.get('auto_send', False),
            review_required=not template.get('auto_send', True)
        )
    
    async def _send_email_response(self, response: EmailResponse) -> bool:
        """Envía respuesta por email."""
        try:
            if not self.smtp_connection:
                await self.connect_email_services()
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = response.recipient
            msg['Subject'] = response.subject
            
            # Añadir cuerpo
            msg.attach(MIMEText(response.body, 'plain', 'utf-8'))
            
            # Enviar
            self.smtp_connection.send_message(msg)
            
            logger.info(f"Auto-response sent to {response.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email response: {str(e)}")
            return False
    
    # Métodos auxiliares
    def _is_cv_file(self, filename: str) -> bool:
        """Verifica si un archivo es un CV."""
        cv_extensions = ['pdf', 'doc', 'docx', 'txt']
        cv_keywords = ['cv', 'resume', 'curriculum', 'curriculo']
        
        extension = filename.split('.')[-1].lower()
        filename_lower = filename.lower()
        
        return (extension in cv_extensions and 
                any(keyword in filename_lower for keyword in cv_keywords))
    
    def _extract_sender_name(self, sender: str) -> str:
        """Extrae el nombre del remitente."""
        # Parsear formato "Name <email@domain.com>"
        name_match = re.match(r'^([^<]+)<', sender)
        if name_match:
            return name_match.group(1).strip().strip('"')
        
        # Si no hay nombre, usar parte local del email
        email_match = re.search(r'([^@]+)@', sender)
        if email_match:
            return email_match.group(1).replace('.', ' ').title()
        
        return 'Usuario'
    
    def _extract_job_position(self, subject: str, body: str) -> Optional[str]:
        """Extrae la posición de trabajo mencionada."""
        position_patterns = [
            r'(?:position|role|job).*?(?:of|for|as)\s+([A-Z][a-z\s]+)',
            r'applying for\s+([A-Z][a-z\s]+)',
            r'interested in.*?([A-Z][a-z\s]+)\s+position'
        ]
        
        full_text = f"{subject} {body}"
        
        for pattern in position_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    async def _mark_email_processed(self, email_id: bytes, processed_email: ProcessedEmail):
        """Marca el email como procesado."""
        try:
            # Marcar como leído
            self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
            
            # Añadir label personalizado si es soportado
            try:
                label = f"huntRED_{processed_email.category}"
                self.imap_connection.store(email_id, '+X-GM-LABELS', f'({label})')
            except:
                pass  # No todos los servidores soportan labels
            
        except Exception as e:
            logger.error(f"Error marking email as processed: {str(e)}")
    
    def disconnect(self):
        """Desconecta de los servicios de email."""
        try:
            if self.imap_connection:
                self.imap_connection.close()
                self.imap_connection.logout()
            
            if self.smtp_connection:
                self.smtp_connection.quit()
                
        except Exception as e:
            logger.error(f"Error disconnecting email services: {str(e)}")
    
    def __del__(self):
        """Cleanup al destruir el objeto."""
        self.disconnect()