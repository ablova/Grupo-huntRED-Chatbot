from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from app.models import (
    Person, Vacante, Application, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState,
    WorkflowStage, SmartOption, TemplateMessage
)
from app.chatbot.utils import ChatbotUtils
import asyncio
import json

logger = logging.getLogger(__name__)

class IntentHandler:
    """Clase base para el manejo de intents."""
    
    def __init__(self, user: Person, intent: str, message: str):
        self.user = user
        self.intent = intent
        self.message = message
        self.context = {}
        self.smart_options = []
        self.template_messages = []
        
    async def handle(self) -> Dict[str, Any]:
        """Maneja el intent y devuelve una respuesta."""
        try:
            response = await self._process_intent()
            return {
                'response': response,
                'smart_options': self.smart_options,
                'template_messages': self.template_messages,
                'context': self.context
            }
        except Exception as e:
            logger.error(f"Error handling intent {self.intent}: {str(e)}")
            return {
                'response': "Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta nuevamente.",
                'smart_options': [],
                'template_messages': [],
                'context': {}
            }
    
    async def _process_intent(self) -> str:
        """Procesa el intent específico. Debe ser implementado por las clases hijas."""
        raise NotImplementedError("Este método debe ser implementado por las clases hijas")

class JobSearchIntentHandler(IntentHandler):
    """Maneja la búsqueda de empleos."""
    
    async def _process_intent(self) -> str:
        # Obtener recomendaciones de vacantes
        recommendations = await ChatbotUtils.get_vacancy_recommendations(self.user)
        
        # Preparar opciones inteligentes
        self.smart_options = [
            SmartOption(
                text="Ver detalles de la vacante",
                data={
                    'action': 'view_vacancy',
                    'vacancy_id': rec.id
                }
            ) for rec in recommendations[:3]
        ]
        
        # Preparar mensajes de plantilla
        self.template_messages = [
            TemplateMessage(
                title=f"{vacancy.title}",
                description=f"{vacancy.description[:100]}...",
                footer=f"{vacancy.location} • {vacancy.required_experience} años exp",
                buttons=[
                    {
                        'type': 'quick_reply',
                        'text': 'Postular',
                        'payload': json.dumps({
                            'action': 'apply',
                            'vacancy_id': vacancy.id
                        })
                    }
                ]
            ) for vacancy in recommendations[:3]
        ]
        
        # Actualizar estado del chat
        await ChatbotUtils.update_chat_state(
            self.user, 'searching_jobs', self.message
        )
        
        return "Aquí tienes algunas oportunidades que podrían interesarte:"

class ApplicationStatusIntentHandler(IntentHandler):
    """Maneja el estado de las aplicaciones."""
    
    async def _process_intent(self) -> str:
        status = await ChatbotUtils.get_application_status(self.user)
        
        # Preparar opciones inteligentes
        self.smart_options = [
            SmartOption(
                text="Ver entrevistas programadas",
                data={'action': 'view_interviews'}
            ),
            SmartOption(
                text="Actualizar perfil",
                data={'action': 'update_profile'}
            )
        ]
        
        # Preparar mensaje de plantilla
        self.template_messages = [
            TemplateMessage(
                title="Estado de tus aplicaciones",
                description=f"Total de aplicaciones: {status['total_applications']}\n"
                       f"En revisión: {status['pending']}\n"
                       f"Entrevistas: {status['interviews']}\n"
                       f"Ofertas: {status['offers']}",
                footer="¿Necesitas ayuda con algo más?",
                buttons=[
                    {
                        'type': 'quick_reply',
                        'text': 'Ver detalles',
                        'payload': json.dumps({'action': 'view_details'})
                    }
                ]
            )
        ]
        
        # Actualizar estado del chat
        await ChatbotUtils.update_chat_state(
            self.user, 'checking_status', self.message
        )
        
        return "Aquí tienes el estado de tus aplicaciones:"

class ProfileUpdateIntentHandler(IntentHandler):
    """Maneja la actualización del perfil del usuario."""
    
    async def _process_intent(self) -> str:
        # Obtener información del perfil
        profile = await self.user.gamification_profile
        
        # Preparar opciones inteligentes
        self.smart_options = [
            SmartOption(
                text="Actualizar experiencia",
                data={'action': 'update_experience'}
            ),
            SmartOption(
                text="Actualizar habilidades",
                data={'action': 'update_skills'}
            ),
            SmartOption(
                text="Actualizar expectativas salariales",
                data={'action': 'update_salary'}
            )
        ]
        
        # Preparar mensaje de plantilla
        self.template_messages = [
            TemplateMessage(
                title="Actualizar perfil",
                description="Selecciona qué información deseas actualizar:",
                footer="",
                buttons=[
                    {
                        'type': 'quick_reply',
                        'text': 'Experiencia',
                        'payload': json.dumps({'action': 'update_experience'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Habilidades',
                        'payload': json.dumps({'action': 'update_skills'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Salario',
                        'payload': json.dumps({'action': 'update_salary'})
                    }
                ]
            )
        ]
        
        # Actualizar estado del chat
        await ChatbotUtils.update_chat_state(
            self.user, 'updating_profile', self.message
        )
        
        return "¿Qué información deseas actualizar en tu perfil?"

class InterviewScheduleIntentHandler(IntentHandler):
    """Maneja el agendamiento de entrevistas."""
    
    async def _process_intent(self) -> str:
        # Obtener próxima entrevista
        next_interview = await ChatbotUtils.get_next_interview(self.user)
        
        if next_interview:
            # Preparar opciones inteligentes
            self.smart_options = [
                SmartOption(
                    text="Confirmar asistencia",
                    data={'action': 'confirm_attendance', 'interview_id': next_interview.id}
                ),
                SmartOption(
                    text="Solicitar cambio de fecha",
                    data={'action': 'reschedule', 'interview_id': next_interview.id}
                )
            ]
            
            # Preparar mensaje de plantilla
            self.template_messages = [
                TemplateMessage(
                    title="Entrevista programada",
                    description=f"Fecha: {next_interview.interview_date.strftime('%d/%m/%Y %H:%M')}\n"
                           f"Puesto: {next_interview.vacancy.title}\n"
                           f"Ubicación: {next_interview.vacancy.location}",
                    footer="¿Necesitas ayuda con algo más?",
                    buttons=[
                        {
                            'type': 'quick_reply',
                            'text': 'Confirmar',
                            'payload': json.dumps({
                                'action': 'confirm_attendance',
                                'interview_id': next_interview.id
                            })
                        },
                        {
                            'type': 'quick_reply',
                            'text': 'Cambiar fecha',
                            'payload': json.dumps({
                                'action': 'reschedule',
                                'interview_id': next_interview.id
                            })
                        }
                    ]
                )
            ]
            
            response = f"Tienes una entrevista programada para el {next_interview.interview_date.strftime('%d/%m/%Y %H:%M')}"
        else:
            response = "No tienes entrevistas programadas en este momento."
            
        # Actualizar estado del chat
        await ChatbotUtils.update_chat_state(
            self.user, 'checking_interviews', self.message
        )
        
        return response

class GamificationIntentHandler(IntentHandler):
    """Maneja la gamificación del usuario."""
    
    async def _process_intent(self) -> str:
        profile = await self.user.gamification_profile
        
        # Preparar opciones inteligentes
        self.smart_options = [
            SmartOption(
                text="Ver logros",
                data={'action': 'view_achievements'}
            ),
            SmartOption(
                text="Ver badges",
                data={'action': 'view_badges'}
            ),
            SmartOption(
                text="Ver progreso",
                data={'action': 'view_progress'}
            )
        ]
        
        # Preparar mensaje de plantilla
        self.template_messages = [
            TemplateMessage(
                title="Gamificación",
                description=f"Nivel: {profile.level}\n"
                       f"Puntos: {profile.points}\n"
                       f"Experiencia: {profile.experience}/100",
                footer="¿Qué te gustaría ver?",
                buttons=[
                    {
                        'type': 'quick_reply',
                        'text': 'Logros',
                        'payload': json.dumps({'action': 'view_achievements'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Badges',
                        'payload': json.dumps({'action': 'view_badges'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Progreso',
                        'payload': json.dumps({'action': 'view_progress'})
                    }
                ]
            )
        ]
        
        # Actualizar estado del chat
        await ChatbotUtils.update_chat_state(
            self.user, 'checking_gamification', self.message
        )
        
        return "Aquí tienes tu progreso en gamificación:"

class HelpIntentHandler(IntentHandler):
    """Maneja las solicitudes de ayuda."""
    
    async def _process_intent(self) -> str:
        # Preparar opciones inteligentes
        self.smart_options = [
            SmartOption(
                text="Búsqueda de empleo",
                data={'action': 'job_search'}
            ),
            SmartOption(
                text="Estado de aplicaciones",
                data={'action': 'application_status'}
            ),
            SmartOption(
                text="Entrevistas",
                data={'action': 'interviews'}
            ),
            SmartOption(
                text="Perfil",
                data={'action': 'profile'}
            ),
            SmartOption(
                text="Gamificación",
                data={'action': 'gamification'}
            )
        ]
        
        # Preparar mensaje de plantilla
        self.template_messages = [
            TemplateMessage(
                title="¿Cómo puedo ayudarte?",
                description="Selecciona una opción para continuar:",
                footer="",
                buttons=[
                    {
                        'type': 'quick_reply',
                        'text': 'Empleo',
                        'payload': json.dumps({'action': 'job_search'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Aplicaciones',
                        'payload': json.dumps({'action': 'application_status'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Entrevistas',
                        'payload': json.dumps({'action': 'interviews'})
                    }
                ]
            )
        ]
        
        # Actualizar estado del chat
        await ChatbotUtils.update_chat_state(
            self.user, 'asking_help', self.message
        )
        
        return "¿En qué puedo ayudarte hoy?"

class IntentProcessor:
    """Procesador de intents para el chatbot."""
    
    def __init__(self, user: Person):
        self.user = user
        self.handlers = {
            'job_search': JobSearchIntentHandler,
            'application_status': ApplicationStatusIntentHandler,
            'profile_update': ProfileUpdateIntentHandler,
            'interview_schedule': InterviewScheduleIntentHandler,
            'gamification': GamificationIntentHandler,
            'help': HelpIntentHandler
        }
    
    async def process_intent(self, intent: str, message: str) -> Dict[str, Any]:
        """Procesa un intent específico."""
        handler_class = self.handlers.get(intent)
        if not handler_class:
            return {
                'response': "Lo siento, no entendí tu solicitud. Por favor, intenta nuevamente.",
                'smart_options': [],
                'template_messages': [],
                'context': {}
            }
        
        handler = handler_class(self.user, intent, message)
        return await handler.handle()

# Configuración de intents para el admin
INTENT_CONFIG = {
    'job_search': {
        'description': 'Búsqueda de empleos',
        'required_fields': ['skills', 'experience', 'location'],
        'template': 'job_search_template.html',
        'smart_options': [
            {
                'text': 'Ver detalles',
                'action': 'view_details'
            },
            {
                'text': 'Postular',
                'action': 'apply'
            }
        ]
    },
    'application_status': {
        'description': 'Estado de aplicaciones',
        'required_fields': [],
        'template': 'application_status_template.html',
        'smart_options': [
            {
                'text': 'Ver entrevistas',
                'action': 'view_interviews'
            },
            {
                'text': 'Actualizar perfil',
                'action': 'update_profile'
            }
        ]
    },
    'profile_update': {
        'description': 'Actualizar perfil',
        'required_fields': [],
        'template': 'profile_update_template.html',
        'smart_options': [
            {
                'text': 'Experiencia',
                'action': 'update_experience'
            },
            {
                'text': 'Habilidades',
                'action': 'update_skills'
            },
            {
                'text': 'Salario',
                'action': 'update_salary'
            }
        ]
    },
    'interview_schedule': {
        'description': 'Agendar entrevistas',
        'required_fields': ['availability'],
        'template': 'interview_schedule_template.html',
        'smart_options': [
            {
                'text': 'Confirmar',
                'action': 'confirm_attendance'
            },
            {
                'text': 'Cambiar fecha',
                'action': 'reschedule'
            }
        ]
    },
    'gamification': {
        'description': 'Gamificación',
        'required_fields': [],
        'template': 'gamification_template.html',
        'smart_options': [
            {
                'text': 'Ver logros',
                'action': 'view_achievements'
            },
            {
                'text': 'Ver badges',
                'action': 'view_badges'
            },
            {
                'text': 'Ver progreso',
                'action': 'view_progress'
            }
        ]
    },
    'help': {
        'description': 'Ayuda',
        'required_fields': [],
        'template': 'help_template.html',
        'smart_options': [
            {
                'text': 'Empleo',
                'action': 'job_search'
            },
            {
                'text': 'Aplicaciones',
                'action': 'application_status'
            },
            {
                'text': 'Entrevistas',
                'action': 'interviews'
            },
            {
                'text': 'Perfil',
                'action': 'profile'
            },
            {
                'text': 'Gamificación',
                'action': 'gamification'
            }
        ]
    }
}
