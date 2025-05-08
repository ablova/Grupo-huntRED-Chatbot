"""
Manejo de intents para el chatbot de Amigro/HuntRED/HuntU/SEXSI.
Este módulo combina las mejores características de los sistemas de intents anteriores,
proporcionando un manejo más robusto y organizado de las interacciones del usuario.
"""

from typing import Dict, Any, Optional, List, Union, Type
import re
import logging
import asyncio
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q

from app.models import (
    Person, Vacante, Application, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState,
    WorkflowStage, SmartOption, TemplateMessage,
    ConfiguracionBU
)
from app.chatbot.utils import ChatbotUtils
from app.chatbot.integrations.services import send_message, send_options, send_menu
from app.chatbot.workflow.common import (
    calcular_salario_chatbot, iniciar_creacion_perfil,
    iniciar_perfil_conversacional, iniciar_prueba,
    send_welcome_message
)
from app.ml.ml_model import MatchmakingLearningSystem, BUSINESS_UNIT_HIERARCHY
from app.chatbot.intents_optimizer import intent_optimizer
from app.chatbot.channel_config import ChannelConfig
from app.chatbot.metrics import chatbot_metrics

logger = logging.getLogger(__name__)

# Cache para almacenar respuestas previas
response_cache = {}

# Diccionario de intents y sus patrones
INTENT_PATTERNS = {
    "start_command": {
        "patterns": [r"\/start"],
        "responses": ["¡Hola! Bienvenido al mejor asistente de reclutamiento. ¿Cómo puedo ayudarte hoy?"],
        "priority": 1
    },
    "saludo": {
        "patterns": [r"\b(hola|hi|buenos\s+días|buenas\s+tardes|buenas\s+noches|saludos|hey)\b"],
        "responses": {
            "amigro": ["¡Hola! 👋 Soy Amigro, aquí para apoyarte en tu búsqueda laboral en México, encontrando trabajo digno y alineado a tu experiencia e interéses."],
            "huntu": ["¡Hola! 🌟 Huntu está listo para ayudarte a dar pasos profesionales sólidos y de gran impacto para tu carrera."],
            "huntred": ["¡Saludos! 🤝 HuntRED te ayuda a encontrar roles gerenciales clave."],
            "huntred_executive": ["¡Hola! HuntRED® Executive, tu aliado para posiciones de alto nivel."],
            "sexsi": ["¡Saludos! Sexsi asegura que todo sea claro y consensuado. ¿En qué te ayudo?"],
            "default": ["¡Hola! Soy tu asistente de reclutamiento. ¿En qué puedo ayudarte?"]
        },
        "priority": 2
    },
    "tos_accept": {
        "patterns": [r"\b(tos_accept|accept_tos)\b"],
        "responses": ["Aceptaste los Términos de Servicio. ¡Continuemos!"],
        "priority": 3
    },
    "show_menu": {
        "patterns": [r"\b(menú|menu|opciones\s+disponibles|qué\s+puedes\s+hacer|qué\s+haces|servicios)\b"],
        "responses": ["Aquí tienes las opciones disponibles:"],
        "priority": 4
    },
    "presentacion_bu": {
        "patterns": [r"\b(qué\s+es\s+amigro|qué\s+hace\s+amigro|acerca\s+de\s+amigro|quiénes\s+son\s+ustedes|about\s+amigro)\b"],
        "responses": {
            "amigro": ["Amigro® 🌍 (amigro.org) usa IA para facilitar el acceso laboral a migrantes en México."],
            "huntu": ["Huntu 🚀 conecta estudiantes con internships y empleos de inicio profesional."],
            "huntred": ["HuntRED 💼 especializa en colocar gerentes y directivos en roles clave."],
            "huntred_executive": ["HuntRED® Executive 🎯 encuentra líderes para consejos y direcciones."],
            "sexsi": ["Sexsi 📜 crea contratos consensuados para relaciones sexuales seguras y legales."],
            "default": ["Somos un asistente de reclutamiento para diversas necesidades laborales."]
        },
        "priority": 5
    },
    "show_jobs": {
        "patterns": [r"\b(ver\s+vacantes|mostrar\s+vacantes|vacante(s)?|oportunidad(es)?|empleo(s)?|trabajo(s)?|puestos|listado\s+de\s+vacantes)\b"],
        "responses": ["Te voy a mostrar vacantes recomendadas según tu perfil. Un momento..."],
        "priority": 10
    },
    "upload_cv": {
        "patterns": [r"\b(subir\s+cv|enviar\s+cv|cv|currículum|curriculum|resume|hoja\s+de\s+vida)\b"],
        "responses": ["¡Perfecto! Envíame tu CV en PDF o Word y lo procesaré para actualizar tu perfil. Adjunta el archivo en tu próximo mensaje."],
        "priority": 15
    },
    "cargar_cv": {
        "patterns": [r"\bcargar_cv\b"],
        "responses": ["¡Perfecto! Envíame tu CV en PDF o Word para cargarlo."],
        "priority": 18
    },
    "prueba_personalidad": {
        "patterns": [r"\bprueba_personalidad\b"],
        "responses": ["¡Vamos a iniciar tu prueba de personalidad! Esto te ayudará a conocer mejor tu perfil profesional."],
        "priority": 20
    },
    "contacto": {
        "patterns": [r"\bcontacto\b"],
        "responses": ["Te conectaré con un reclutador. Espera un momento."],
        "priority": 24
    },
    "ayuda": {
        "patterns": [r"\b(ayuda|faq)\b"],
        "responses": ["¿En qué necesitas ayuda? Puedo explicarte cómo usar el bot o resolver dudas comunes."],
        "priority": 25
    },
    "solicitar_ayuda_postulacion": {
        "patterns": [r"\b(ayuda\s+con\s+postulación|cómo\s+postular(me)?|aplicar\s+a\s+vacante|postular(me)?)\b"],
        "responses": ["Te puedo guiar para postularte. ¿A qué vacante te interesa aplicar o necesitas ayuda con el proceso?"],
        "priority": 20
    },
    "consultar_estado_postulacion": {
        "patterns": [r"\b(estado\s+de\s+mi\s+postulación|seguimiento\s+a\s+mi\s+aplicación|cómo\s+va\s+mi\s+proceso)\b"],
        "responses": ["Dame tu correo asociado a la postulación y te daré el estado actual."],
        "priority": 25
    },
    "crear_perfil": {
        "patterns": [r"\b(crear\s+perfil|iniciar\s+perfil|comenzar\s+perfil)\b"],
        "responses": ["¡Vamos a crear tu perfil! Empecemos con tu nombre."],
        "priority": 30
    },
    "actualizar_perfil": {
        "patterns": [r"\b(actualizar\s+perfil|cambiar\s+datos|modificar\s+información|editar\s+mi\s+perfil)\b"],
        "responses": ["¿Qué quieres actualizar? Puedes decirme: nombre, email, teléfono, habilidades, experiencia o salario esperado."],
        "priority": 30
    },
    "travel_in_group": {
        "patterns": [
            r"\b(travel_in_group|invitar|invita|invitar\s+a|invitación|"
            r"pasa\s+la\s+voz|pasar\s+la\s+voz|corre\s+la\s+voz|"
            r"reclutamiento\s+en\s+grupo|grupo\s+de\s+reclutamiento|"
            r"traer\s+a\s+alguien|recomendar\s+a\s+alguien|"
            r"amigo|conocido|familiar|compañero)\b"
        ],
        "responses": ["Voy a ayudarte a invitar a alguien. ¿Cuál es su nombre?"],
        "priority": 35
    },
    "solicitar_tips_entrevista": {
        "patterns": [r"\b(tips\s+para\s+entrevista|consejos\s+entrevista|preparación\s+entrevista|cómo\s+prepararme\s+para\s+entrevista)\b"],
        "responses": [
            "Claro, aquí tienes algunos consejos: investiga la empresa, llega puntual, prepara ejemplos de tus logros y practica respuestas a preguntas comunes. ¿Te gustaría más ayuda con algo específico?"
        ],
        "priority": 40
    },
    "calcular_salario": {
        "patterns": [r"\bcalcular_salario\b", r"salario\s*(bruto|neto)\s*=\s*[\d,\.]+k?"],
        "responses": ["Voy a calcular tu salario. Por favor, dime cuánto ganas (ej. 'salario bruto = 20k MXN mensual') y cualquier detalle extra como bonos o prestaciones, o en qué moneda lo tienes (yo te lo convierto si es necesario)."],
        "priority": 17
    },
    "consultar_sueldo_mercado": {
        "patterns": [r"\b(sueldo\s+mercado|rango\s+salarial|cuánto\s+pagan|salario\s+para\s+.*)\b"],
        "responses": ["¿Para qué posición o nivel quieres saber el rango salarial? Puedo darte una estimación basada en el mercado."],
        "priority": 50
    },
    "solicitar_contacto_reclutador": {
        "patterns": [r"\b(hablar\s+con\s+reclutador|contactar\s+a\s+alguien|necesito\s+un\s+reclutador)\b"],
        "responses": ["Te conectaré con un reclutador. Por favor, espera mientras te asigno uno."],
        "priority": 55
    },
    "busqueda_impacto": {
        "patterns": [r"\b(impacto\s+social|trabajo\s+con\s+propósito|vacantes\s+con\s+impacto)\b"],
        "responses": ["¿Buscas trabajo con impacto social? Puedo mostrarte vacantes con propósito. ¿Te interesa?"],
        "priority": 60
    },
    "agradecimiento": {
        "patterns": [r"\b(gracias|muchas\s+gracias|te\s+agradezco|thank\s+you)\b"],
        "responses": ["¡De nada! 😊 ¿En qué más puedo ayudarte?"],
        "priority": 65
    },
    "despedida": {
        "patterns": [r"\b(adiós|hasta\s+luego|bye|chao|nos\s+vemos)\b"],
        "responses": [
            "¡Hasta pronto! 👋 Si necesitas más ayuda, aquí estaré.",
            "¡Adiós! 🌟 Que tengas un gran día. Vuelve cuando quieras.",
            "¡Chao! 😊 Estoy a un mensaje de distancia si me necesitas."
        ],
        "priority": 70
    },
    "retry_conversation": {
        "patterns": [r"\b(intentemos\s+de\s+nuevo|volvamos\s+a\s+intentar|retry|de\s+nuevo|empezar\s+otra\s+vez)\b"],
        "responses": ["¡Claro! Vamos a empezar de nuevo. ¿En qué te ayudo ahora?"],
        "priority": 75
    },
    "migratory_status": {
        "patterns": [r"\b(estatus\s+migratorio|permiso\s+trabajo|visa|refugio)\b"],
        "responses": {
            "amigro": ["Puedo ayudarte con tu estatus migratorio. ¿Tienes permiso de trabajo o necesitas apoyo con eso?"],
            "default": ["Este servicio está disponible solo para Amigro. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "internship_search": {
        "patterns": [r"\b(prácticas|internship|pasantía|empleo\s+estudiantil)\b"],
        "responses": {
            "huntu": ["Busco internships perfectos para estudiantes como tú. ¿Qué área te interesa?"],
            "default": ["Este servicio está disponible solo para Huntu. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "executive_roles": {
        "patterns": [r"\b(director|consejo|ejecutivo|alto\s+nivel)\b"],
        "responses": {
            "huntred": ["Te ayudo a encontrar roles gerenciales. ¿Qué nivel buscas?"],
            "huntred_executive": ["Conecto líderes con posiciones ejecutivas. ¿Qué rol te interesa?"],
            "default": ["Este servicio es para HuntRED o Executive. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "create_contract": {
        "patterns": [r"\b(crear\s+contrato|acuerdo|consentimiento)\b"],
        "responses": {
            "sexsi": ["Vamos a crear un contrato consensuado. ¿Qué términos quieres incluir?"],
            "default": ["Este servicio está disponible solo para Sexsi. ¿En qué más te ayudo?"]
        },
        "priority": 30
    },
    "transition_to_higher_bu": {
        "patterns": [r"\b(transicionar|subir de nivel|ascender)\b"],
        "responses": ["Voy a evaluar si cumples con los requisitos para subir de nivel."],
        "priority": 30
    }
}

# Lista de botones principales
main_options = [
    {"title": "💼 Ver Vacantes", "payload": "show_jobs"},
    # ... (otros botones)
]

class IntentHandler:
    """Clase base para el manejo de intents."""
    
    def __init__(self, user: Person, intent: str, message: str, business_unit: BusinessUnit):
        self.user = user
        self.intent = intent
        self.message = message
        self.business_unit = business_unit
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
                    text="Ver detalles de la entrevista",
                    data={'action': 'view_interview_details'}
                ),
                SmartOption(
                    text="Cancelar entrevista",
                    data={'action': 'cancel_interview'}
                )
            ]
            
            # Preparar mensaje de plantilla
            self.template_messages = [
                TemplateMessage(
                    title="Próxima entrevista",
                    description=f"Fecha: {next_interview.date}\n"
                           f"Hora: {next_interview.time}\n"
                           f"Vacante: {next_interview.vacancy.title}",
                    footer="¿Necesitas ayuda con algo más?",
                    buttons=[
                        {
                            'type': 'quick_reply',
                            'text': 'Ver detalles',
                            'payload': json.dumps({'action': 'view_interview_details'})
                        },
                        {
                            'type': 'quick_reply',
                            'text': 'Cancelar',
                            'payload': json.dumps({'action': 'cancel_interview'})
                        }
                    ]
                )
            ]
            
            return f"Tienes una entrevista programada para {next_interview.date} a las {next_interview.time}."
        else:
            return "No tienes entrevistas programadas en este momento."

class GamificationIntentHandler(IntentHandler):
    """Maneja la gamificación del usuario."""
    
    async def _process_intent(self) -> str:
        # Obtener estadísticas de gamificación
        stats = await ChatbotUtils.get_gamification_stats(self.user)
        
        # Preparar opciones inteligentes
        self.smart_options = [
            SmartOption(
                text="Ver logros",
                data={'action': 'view_achievements'}
            ),
            SmartOption(
                text="Ver ranking",
                data={'action': 'view_ranking'}
            )
        ]
        
        # Preparar mensaje de plantilla
        self.template_messages = [
            TemplateMessage(
                title="Estadísticas de gamificación",
                description=f"Puntos: {stats['points']}\n"
                       f"Nivel: {stats['level']}\n"
                       f"Logros: {stats['achievements_count']}",
                footer="¿Quieres ver más detalles?",
                buttons=[
                    {
                        'type': 'quick_reply',
                        'text': 'Ver logros',
                        'payload': json.dumps({'action': 'view_achievements'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Ver ranking',
                        'payload': json.dumps({'action': 'view_ranking'})
                    }
                ]
            )
        ]
        
        return "Aquí tienes tus estadísticas de gamificación. ¡Sigue mejorando!"

class HelpIntentHandler(IntentHandler):
    """Maneja las solicitudes de ayuda."""
    
    async def _process_intent(self) -> str:
        # Obtener información de ayuda
        help_info = await ChatbotUtils.get_help_info(self.business_unit)
        
        # Preparar opciones inteligentes
        self.smart_options = [
            SmartOption(
                text="Ver FAQ",
                data={'action': 'view_faq'}
            ),
            SmartOption(
                text="Contactar soporte",
                data={'action': 'contact_support'}
            )
        ]
        
        # Preparar mensaje de plantilla
        self.template_messages = [
            TemplateMessage(
                title="Centro de ayuda",
                description=f"{help_info['description']}",
                footer="¿Necesitas ayuda con algo más?",
                buttons=[
                    {
                        'type': 'quick_reply',
                        'text': 'Ver FAQ',
                        'payload': json.dumps({'action': 'view_faq'})
                    },
                    {
                        'type': 'quick_reply',
                        'text': 'Contactar soporte',
                        'payload': json.dumps({'action': 'contact_support'})
                    }
                ]
            )
        ]
        
        return "¿En qué puedo ayudarte?"

class SalaryCalculatorIntentHandler(IntentHandler):
    """Maneja el cálculo de salarios."""
    
    async def _process_intent(self) -> str:
        # Extraer salario del mensaje
        match = re.search(r'salario\s*(bruto|neto)\s*=\s*([\d,\.]+)k?', self.message, re.IGNORECASE)
        if match:
            salary_type = match.group(1).lower()
            amount = float(match.group(2).replace(',', ''))
            
            # Calcular salario neto/bruto
            if salary_type == 'bruto':
                net_salary = await calcular_salario_chatbot(amount, 'bruto')
                response = f"Tu salario neto aproximado es: {net_salary} MXN mensual"
            else:
                gross_salary = await calcular_salario_chatbot(amount, 'neto')
                response = f"Tu salario bruto aproximado es: {gross_salary} MXN mensual"
            
            return response
        
        return "Por favor, especifica tu salario (ej. 'salario bruto = 20k MXN mensual')"

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

class IntentProcessor:
    """Procesador de intents para el chatbot."""
    
    def __init__(self, user: Person, business_unit: BusinessUnit):
        self.user = user
        self.business_unit = business_unit
        self.handlers = {
            'job_search': JobSearchIntentHandler,
            'application_status': ApplicationStatusIntentHandler,
            'profile_update': ProfileUpdateIntentHandler,
            'interview_schedule': InterviewScheduleIntentHandler,
            'gamification': GamificationIntentHandler,
            'help': HelpIntentHandler,
            'salary_calculator': SalaryCalculatorIntentHandler,
            # Agregar más handlers según sea necesario
        }
    
    async def process_intent(self, intent: str, message: str) -> Dict[str, Any]:
        """Procesa un intent específico."""
        handler_class = self.handlers.get(intent)
        if handler_class:
            handler = handler_class(self.user, intent, message, self.business_unit)
            return await handler.handle()
        return {
            'response': "Lo siento, no entiendo esa solicitud.",
            'smart_options': [],
            'template_messages': [],
            'context': {}
        }

async def detect_intents(text: str) -> List[str]:
    """Detecta intents en el texto, incluyendo payloads exactos, ordenados por prioridad."""
    intents = []
    for intent_name, data in INTENT_PATTERNS.items():
        for pattern in data['patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                intents.append(intent_name)
    return sorted(intents, key=lambda x: INTENT_PATTERNS[x]['priority'])

async def handle_known_intents(
    text: str, 
    platform: str, 
    user_id: str, 
    business_unit: BusinessUnit,
    chat_state: ChatState
) -> Dict[str, Any]:
    """Maneja los intents conocidos de manera optimizada."""
    intents = await detect_intents(text)
    
    # Obtener o crear el usuario
    user = await Person.objects.aget_or_create(
        external_id=user_id,
        platform=platform,
        defaults={'business_unit': business_unit}
    )
    
    # Crear procesador de intents
    intent_processor = IntentProcessor(user, business_unit)
    
    # Procesar el intent más prioritario
    if intents:
        intent = intents[0]
        return await intent_processor.process_intent(intent, text)
    
    return {
        'response': "Lo siento, no entiendo esa solicitud.",
        'smart_options': [],
        'template_messages': [],
        'context': {}
    }
