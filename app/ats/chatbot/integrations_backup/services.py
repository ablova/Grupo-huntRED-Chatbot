# /home/pablo/app/ats/chatbot/integrations/services.py
#
# Módulo de servicios compartidos para el chatbot.
# Incluye funcionalidades para manejo de mensajes, gamificación, correo electrónico y más.
# Optimizado para bajo uso de CPU, escalabilidad, y robustez frente a fallos.

import logging
import smtplib
import asyncio
import ssl
import itertools
import time
from asgiref.sync import sync_to_async
from typing import Optional, List, Dict, Union, Any, Tuple
from django.core.cache import cache
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from app.models import (
    BusinessUnit, ConfiguracionBU, WhatsAppAPI, TelegramAPI, SlackAPI,
    InstagramAPI, MessengerAPI, ChatState, Person,
    EnhancedNetworkGamificationProfile
)
from app.ats.chatbot.components.rate_limiter import RateLimiter
from app.ats.chatbot.workflow.assessments.professional_dna.analysis import ProfessionalDNAAnalysis
from app.ats.chatbot.workflow.assessments.professional_dna.questions import QuestionCategory
from app.ats.chatbot.workflow.assessments.professional_dna.presentation import ResultPresentation
from app.ats.chatbot.workflow.assessments.professional_dna.core import ProfessionalDNAWorkflow
from app.ats.chatbot.workflow.assessments.cultural.cultural_fit_workflow import CulturalFitWorkflow
from app.ats.chatbot.workflow.assessments.talent.talent_analysis_workflow import TalentAnalysisWorkflow
from app.ats.chatbot.workflow.assessments.personality.personality_workflow import PersonalityAssessment
from app.ats.chatbot.workflow.assessments.compensation.compensation_workflow import CompensationAssessment
# Importaciones directas siguiendo estándares de Django
# Import handlers at runtime to avoid circular imports
def get_whatsapp_handler():
    from app.ats.chatbot.integrations.whatsapp import WhatsAppHandler
    return WhatsAppHandler

def get_telegram_handler():
    from app.ats.chatbot.integrations.telegram import TelegramHandler, fetch_telegram_user_data
    return TelegramHandler, fetch_telegram_user_data

def get_instagram_handler():
    from app.ats.chatbot.integrations.instagram import InstagramHandler, fetch_instagram_user_data
    return InstagramHandler, fetch_instagram_user_data

def get_slack_handler():
    from app.ats.chatbot.integrations.slack import fetch_slack_user_data
    return fetch_slack_user_data

import tracemalloc
tracemalloc.start()
logger = logging.getLogger('chatbot')

# Constantes globales
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10.0
CACHE_TIMEOUT = 600  # 10 minutos
whatsapp_semaphore = asyncio.Semaphore(10)

# Menús dinámicos por unidad de negocio con submenús
MENU_OPTIONS_BY_BU = {
    "amigro": [
        {
            "title": "👤 Mi Perfil",
            "payload": "mi_perfil",
            "description": "Crea y gestiona tu perfil profesional.",
            "submenu": [
                {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                {"title": "👀 Ver Perfil", "payload": "ver_perfil"},
                {"title": "✏️ Editar Perfil", "payload": "editar_perfil"},
                {"title": "📊 Ver Evaluaciones", "payload": "ver_evaluaciones"}
            ]
        },
        {
            "title": "🎯 Evaluaciones",
            "payload": "evaluaciones",
            "description": "Completa evaluaciones para mejorar tu perfil.",
            "submenu": [
                {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad"},
                {"title": "🌍 Análisis de Movilidad", "payload": "analisis_movilidad"},
                {"title": "👥 Análisis Generacional", "payload": "analisis_generacional"},
                {"title": "💪 Análisis Motivacional", "payload": "analisis_motivacional"},
                {"title": "🎯 Análisis de Estilos", "payload": "analisis_estilos"}
            ]
        },
        {
            "title": "💰 Calcular Salario",
            "payload": "calcular_salario",
            "description": "Calcula salario neto o bruto.",
            "submenu": [
                {"title": "💵 Neto a Bruto", "payload": "neto_a_bruto"},
                {"title": "💵 Bruto a Neto", "payload": "bruto_a_neto"}
            ]
        },
        {
            "title": "📄 Cargar CV",
            "payload": "cargar_cv",
            "description": "Sube tu currículum.",
            "submenu": [
                {"title": "📤 Subir Nuevo CV", "payload": "subir_cv"},
                {"title": "📋 Ver CV Actual", "payload": "ver_cv"},
                {"title": "✏️ Editar CV", "payload": "editar_cv"}
            ]
        },
        {
            "title": "🔍 Ver Vacantes",
            "payload": "ver_vacantes",
            "description": "Explora oportunidades laborales disponibles.",
            "submenu": [
                {"title": "🔎 Buscar Vacantes", "payload": "buscar_vacantes"},
                {"title": "⭐ Vacantes Recomendadas", "payload": "vacantes_recomendadas"},
                {"title": "📊 Mis Postulaciones", "payload": "mis_postulaciones"}
            ]
        },
        {
            "title": "📊 Consultar Estatus",
            "payload": "consultar_estatus",
            "description": "Revisa el estado de tus aplicaciones.",
            "submenu": [
                {"title": "📈 Estado de Postulaciones", "payload": "estado_postulaciones"},
                {"title": "📅 Próximas Entrevistas", "payload": "proximas_entrevistas"},
                {"title": "📝 Historial de Aplicaciones", "payload": "historial_aplicaciones"}
            ]
        },
        {
            "title": "📞 Contacto",
            "payload": "contacto",
            "description": "Habla con un asesor.",
            "submenu": [
                {"title": "💬 Chat con Asesor", "payload": "chat_asesor"},
                {"title": "📧 Enviar Mensaje", "payload": "enviar_mensaje"},
                {"title": "📞 Llamar Asesor", "payload": "llamar_asesor"}
            ]
        },
        {
            "title": "❓ Ayuda",
            "payload": "ayuda",
            "description": "Resuelve dudas generales.",
            "submenu": [
                {"title": "❔ Preguntas Frecuentes", "payload": "faq"},
                {"title": "📚 Guías de Uso", "payload": "guias"},
                {"title": "📝 Tutoriales", "payload": "tutoriales"}
            ]
        }
    ],
    "huntred": [
        {
            "title": "👤 Mi Perfil",
            "payload": "mi_perfil",
            "description": "Crea y gestiona tu perfil profesional.",
            "submenu": [
                {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                {"title": "👀 Ver Perfil", "payload": "ver_perfil"},
                {"title": "✏️ Editar Perfil", "payload": "editar_perfil"},
                {"title": "📊 Ver Evaluaciones", "payload": "ver_evaluaciones"}
            ]
        },
        {
            "title": "🎯 Evaluaciones",
            "payload": "evaluaciones",
            "description": "Completa evaluaciones para mejorar tu perfil.",
            "submenu": [
                {
                    "title": "🧬 ADN Profesional",
                    "payload": "adn_profesional",
                    "description": "Evaluación integral de tu perfil profesional",
                    "submenu": [
                        {"title": "👥 Liderazgo", "payload": "analisis_liderazgo"},
                        {"title": "💡 Innovación", "payload": "analisis_innovacion"},
                        {"title": "🗣️ Comunicación", "payload": "analisis_comunicacion"},
                        {"title": "🔄 Resiliencia", "payload": "analisis_resiliencia"},
                        {"title": "📈 Resultados", "payload": "analisis_resultados"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_adn_profesional"}
                    ]
                },
                {
                    "title": "🧠 Personalidad",
                    "payload": "personalidad",
                    "description": "Descubre tu perfil de personalidad",
                    "submenu": [
                        {"title": "🎭 Rasgos de Personalidad", "payload": "analisis_rasgos"},
                        {"title": "🤝 Estilos de Comportamiento", "payload": "analisis_estilos"},
                        {"title": "💼 Preferencias Laborales", "payload": "analisis_preferencias"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_personalidad"}
                    ]
                },
                {
                    "title": "💫 Talento",
                    "payload": "talento",
                    "description": "Evalúa tus competencias y potencial",
                    "submenu": [
                        {"title": "🔧 Habilidades Técnicas", "payload": "analisis_habilidades"},
                        {"title": "🌟 Competencias Clave", "payload": "analisis_competencias"},
                        {"title": "🌱 Potencial de Desarrollo", "payload": "analisis_potencial"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_talento"}
                    ]
                },
                {
                    "title": "🌍 Cultural",
                    "payload": "cultural",
                    "description": "Analiza tu adaptación cultural",
                    "submenu": [
                        {"title": "🎯 Valores", "payload": "analisis_valores"},
                        {"title": "💼 Estilo de Trabajo", "payload": "analisis_estilo_trabajo"},
                        {"title": "🗣️ Preferencias de Comunicación", "payload": "analisis_comunicacion_cultural"},
                        {"title": "🔄 Adaptabilidad", "payload": "analisis_adaptabilidad"},
                        {"title": "📊 Reporte Completo", "payload": "reporte_cultural"}
                    ]
                },
                {
                    "title": "👥 Análisis Generacional",
                    "payload": "analisis_generacional",
                    "description": "Descubre tu perfil generacional",
                    "submenu": [
                        {"title": "📊 Perfil Generacional", "payload": "perfil_generacional"},
                        {"title": "🔄 Patrones de Comportamiento", "payload": "patrones_generacionales"},
                        {"title": "💡 Insights Generacionales", "payload": "insights_generacionales"},
                        {"title": "📈 Reporte Completo", "payload": "reporte_generacional"}
                    ]
                },
                {
                    "title": "💰 Compensación",
                    "payload": "compensacion",
                    "description": "Análisis y satisfacción salarial",
                    "submenu": [
                        {"title": "📊 Competitividad Salarial", "payload": "competitividad_salarial"},
                        {"title": "😊 Satisfacción", "payload": "satisfaccion_salarial"},
                        {"title": "📈 Proyecciones", "payload": "proyecciones_salariales"},
                        {"title": "🔍 Recomendaciones", "payload": "recomendaciones_salariales"},
                        {"title": "📑 Reporte Completo", "payload": "reporte_compensacion"}
                    ]
                }
            ]
        },
        {
            "title": "🔍 Buscar Empleo",
            "payload": "buscar_empleo",
            "description": "Encuentra trabajos específicos.",
            "submenu": [
                {"title": "🔎 Búsqueda Avanzada", "payload": "busqueda_avanzada"},
                {"title": "⭐ Recomendados", "payload": "trabajos_recomendados"},
                {"title": "📊 Mis Postulaciones", "payload": "mis_postulaciones"}
            ]
        },
        {
            "title": "📊 Ver Vacantes",
            "payload": "ver_vacantes",
            "description": "Lista de empleos disponibles.",
            "submenu": [
                {"title": "📋 Todas las Vacantes", "payload": "todas_vacantes"},
                {"title": "🎯 Por Categoría", "payload": "vacantes_categoria"},
                {"title": "📍 Por Ubicación", "payload": "vacantes_ubicacion"}
            ]
        },
        {
            "title": "📄 Cargar CV",
            "payload": "cargar_cv",
            "description": "Sube tu currículum.",
            "submenu": [
                {"title": "📤 Subir Nuevo CV", "payload": "subir_cv"},
                {"title": "📋 Ver CV Actual", "payload": "ver_cv"},
                {"title": "✏️ Editar CV", "payload": "editar_cv"}
            ]
        },
        {
            "title": "📅 Agendar Entrevista",
            "payload": "agendar_entrevista",
            "description": "Programa una entrevista.",
            "submenu": [
                {"title": "📅 Nueva Entrevista", "payload": "nueva_entrevista"},
                {"title": "📋 Ver Entrevistas", "payload": "ver_entrevistas"},
                {"title": "✏️ Modificar Entrevista", "payload": "modificar_entrevista"}
            ]
        },
        {
            "title": "💰 Calcular Salario",
            "payload": "calcular_salario",
            "description": "Calcula salario neto o bruto.",
            "submenu": [
                {"title": "💵 Neto a Bruto", "payload": "neto_a_bruto"},
                {"title": "💵 Bruto a Neto", "payload": "bruto_a_neto"}
            ]
        },
        {
            "title": "💡 Tips Entrevista",
            "payload": "preparacion_entrevista",
            "description": "Consejos para entrevistas.",
            "submenu": [
                {"title": "📝 Preparación", "payload": "preparacion"},
                {"title": "👔 Vestimenta", "payload": "vestimenta"},
                {"title": "💬 Preguntas Comunes", "payload": "preguntas_comunes"}
            ]
        }
    ],
    "huntu": [
        {
            "title": "👤 Mi Perfil",
            "payload": "mi_perfil",
            "description": "Crea y gestiona tu perfil profesional.",
            "submenu": [
                {"title": "📝 Crear Perfil", "payload": "crear_perfil"},
                {"title": "👀 Ver Perfil", "payload": "ver_perfil"},
                {"title": "✏️ Editar Perfil", "payload": "editar_perfil"},
                {"title": "📊 Ver Evaluaciones", "payload": "ver_evaluaciones"}
            ]
        },
        {
            "title": "🎯 Evaluaciones",
            "payload": "evaluaciones",
            "description": "Completa evaluaciones para mejorar tu perfil.",
            "submenu": [
                {"title": "🧠 Prueba de Personalidad", "payload": "prueba_personalidad"},
                {"title": "🎓 Análisis de Habilidades", "payload": "analisis_habilidades"},
                {"title": "👥 Análisis Generacional", "payload": "analisis_generacional"},
                {"title": "💪 Análisis Motivacional", "payload": "analisis_motivacional"},
                {"title": "🎯 Análisis de Estilos", "payload": "analisis_estilos"}
            ]
        },
        {
            "title": "🔍 Explorar Vacantes",
            "payload": "explorar_vacantes",
            "description": "Descubre oportunidades únicas.",
            "submenu": [
                {"title": "🔎 Búsqueda Avanzada", "payload": "busqueda_avanzada"},
                {"title": "⭐ Recomendados", "payload": "trabajos_recomendados"},
                {"title": "📊 Mis Postulaciones", "payload": "mis_postulaciones"}
            ]
        },
        {
            "title": "📄 Cargar CV",
            "payload": "cargar_cv",
            "description": "Sube tu currículum.",
            "submenu": [
                {"title": "📤 Subir Nuevo CV", "payload": "subir_cv"},
                {"title": "📋 Ver CV Actual", "payload": "ver_cv"},
                {"title": "✏️ Editar CV", "payload": "editar_cv"}
            ]
        },
        {
            "title": "🧑‍🏫 Asesoría Profesional",
            "payload": "asesoria_profesional",
            "description": "Recibe orientación.",
            "submenu": [
                {"title": "💬 Chat con Asesor", "payload": "chat_asesor"},
                {"title": "📅 Agendar Cita", "payload": "agendar_cita"},
                {"title": "📝 Ver Historial", "payload": "historial_asesoria"}
            ]
        },
        {
            "title": "🤝 Programa de Mentores",
            "payload": "mentores",
            "description": "Conéctate con mentores.",
            "submenu": [
                {"title": "👥 Ver Mentores", "payload": "ver_mentores"},
                {"title": "📅 Agendar Sesión", "payload": "agendar_sesion"},
                {"title": "📝 Ver Historial", "payload": "historial_mentoria"}
            ]
        }
    ]
}

# Menú de evaluaciones por unidad de negocio
EVALUATIONS_MENU = {
    "huntred": [
        {
            "title": "🧬 ADN Profesional",
            "payload": "adn_profesional",
            "description": "Evaluación integral de tu perfil profesional",
            "points": 100,
            "required": True,
            "generational_analysis": True
        },
        {
            "title": "🧠 Prueba de Personalidad",
            "payload": "prueba_personalidad",
            "description": "Descubre tu perfil profesional",
            "points": 50,
            "required": True,
            "generational_analysis": True
        },
        {
            "title": "💫 Análisis de Talento 360°",
            "payload": "analisis_talento",
            "description": "Evaluación integral de talento",
            "points": 75,
            "required": True,
            "generational_analysis": True
        },
        {
            "title": "🌍 Compatibilidad Cultural",
            "payload": "analisis_cultural",
            "description": "Mide tu fit con empresas",
            "points": 50,
            "required": True,
            "generational_analysis": True
        },
        {
            "title": "👥 Análisis Generacional",
            "payload": "analisis_generacional",
            "description": "Descubre tu perfil generacional",
            "points": 40,
            "required": True,
            "generational_analysis": True
        },
        {
            "title": "🎮 Análisis de Gamificación",
            "payload": "analisis_gamificacion",
            "description": "Descubre tu perfil gamer y estilo de aprendizaje",
            "points": 30,
            "required": False
        },
        {
            "title": "🤖 Análisis de Adaptación a IA",
            "payload": "analisis_ia",
            "description": "Evalúa tu capacidad de trabajar con IA",
            "points": 40,
            "required": False
        },
        {
            "title": "🌱 Análisis de Sostenibilidad",
            "payload": "analisis_sostenibilidad",
            "description": "Mide tu compromiso con prácticas sostenibles",
            "points": 35,
            "required": False
        },
        {
            "title": "🎨 Análisis de Creatividad",
            "payload": "analisis_creatividad",
            "description": "Descubre tu potencial creativo e innovador",
            "points": 45,
            "required": False
        },
        {
            "title": "🌐 Análisis de Inteligencia Cultural",
            "payload": "analisis_inteligencia_cultural",
            "description": "Evalúa tu capacidad para trabajar en entornos multiculturales",
            "points": 40,
            "required": False
        },
        {
            "title": "💡 Análisis de Resolución de Problemas",
            "payload": "analisis_resolucion_problemas",
            "description": "Mide tu capacidad para resolver problemas complejos",
            "points": 50,
            "required": False
        },
        {
            "title": "🤝 Análisis de Colaboración Digital",
            "payload": "analisis_colaboracion_digital",
            "description": "Evalúa tu efectividad en entornos de trabajo remoto",
            "points": 35,
            "required": False
        }
    ],
    "amigro": [
        {
            "title": "🧠 Prueba de Personalidad",
            "payload": "prueba_personalidad",
            "description": "Descubre tu perfil profesional",
            "points": 50,
            "required": True
        },
        {
            "title": "🌍 Análisis de Movilidad",
            "payload": "analisis_movilidad",
            "description": "Evalúa tu disposición a la movilidad",
            "points": 50,
            "required": True
        },
        {
            "title": "🎮 Análisis de Gamificación",
            "payload": "analisis_gamificacion",
            "description": "Descubre tu perfil gamer y estilo de aprendizaje",
            "points": 30,
            "required": False
        },
        {
            "title": "🤖 Análisis de Adaptación a IA",
            "payload": "analisis_ia",
            "description": "Evalúa tu capacidad de trabajar con IA",
            "points": 40,
            "required": False
        },
        {
            "title": "🌱 Análisis de Sostenibilidad",
            "payload": "analisis_sostenibilidad",
            "description": "Mide tu compromiso con prácticas sostenibles",
            "points": 35,
            "required": False
        },
        {
            "title": "🎨 Análisis de Creatividad",
            "payload": "analisis_creatividad",
            "description": "Descubre tu potencial creativo e innovador",
            "points": 45,
            "required": False
        }
    ],
    "huntu": [
        {
            "title": "🧠 Prueba de Personalidad",
            "payload": "prueba_personalidad",
            "description": "Descubre tu perfil profesional",
            "points": 50,
            "required": True
        },
        {
            "title": "🎓 Análisis de Habilidades",
            "payload": "analisis_habilidades",
            "description": "Evalúa tus competencias",
            "points": 50,
            "required": True
        },
        {
            "title": "🎮 Análisis de Gamificación",
            "payload": "analisis_gamificacion",
            "description": "Descubre tu perfil gamer y estilo de aprendizaje",
            "points": 30,
            "required": False
        },
        {
            "title": "🤖 Análisis de Adaptación a IA",
            "payload": "analisis_ia",
            "description": "Evalúa tu capacidad de trabajar con IA",
            "points": 40,
            "required": False
        },
        {
            "title": "🌱 Análisis de Sostenibilidad",
            "payload": "analisis_sostenibilidad",
            "description": "Mide tu compromiso con prácticas sostenibles",
            "points": 35,
            "required": False
        },
        {
            "title": "🎨 Análisis de Creatividad",
            "payload": "analisis_creatividad",
            "description": "Descubre tu potencial creativo e innovador",
            "points": 45,
            "required": False
        }
    ]
}

def get_greeting_by_time() -> str:
    """Devuelve un saludo basado en la hora actual."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "🌅 Buenos días"
    elif 12 <= hour < 19:
        return "🌇 Buenas tardes"
    else:
        return "🌙 Buenas noches"


class UserDataFetcher:
    """Clase base abstracta para estandarizar la obtención de datos de usuario."""
    async def fetch(self, user_id: str, api_instance: Any, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        raise NotImplementedError

class WhatsAppUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: WhatsAppAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        return await WhatsAppHandler.fetch_whatsapp_user_data(user_id, api_instance, payload)

class TelegramUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: TelegramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        return await fetch_telegram_user_data(user_id, api_instance, payload)

class MessengerUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: MessengerAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        return await fetch_messenger_user_data(user_id, api_instance, payload)

class InstagramUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: InstagramAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        return await fetch_instagram_user_data(user_id, api_instance, payload)

class SlackUserDataFetcher(UserDataFetcher):
    async def fetch(self, user_id: str, api_instance: SlackAPI, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        return await fetch_slack_user_data(user_id, api_instance, payload)

async def apply_rate_limit(platform: str, user_id: str, message: dict) -> bool:
    limiter = RateLimiter(max_requests=10, time_window=60)
    if not await limiter.check_rate_limit(user_id):
        await send_message(platform, user_id, "Por favor, espera un momento antes de enviar más mensajes.", "default")
        return False
    return True

class Button:
    """Clase para representar botones interactivos."""
    def __init__(self, title: str, payload: Optional[str] = None, url: Optional[str] = None):
        self.title = title
        self.payload = payload
        self.url = url

    @classmethod
    def from_dict(cls, button_dict: Dict) -> 'Button':
        return cls(
            title=button_dict.get('title', ''),
            payload=button_dict.get('payload'),
            url=button_dict.get('url')
        )

class EmailService:
    """Servicio para enviar correos electrónicos."""
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._config = None

    async def get_config(self) -> ConfiguracionBU:
        """Obtiene la configuración de correo de la unidad de negocio."""
        if not self._config:
            self._config = await sync_to_async(ConfiguracionBU.objects.select_related('business_unit').get)(
                business_unit=self.business_unit
            )
        return self._config

    async def send_email(
        self,
        subject: str,
        to_email: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict[str, str]:
        """Envía un correo electrónico."""
        server = None
        try:
            config = await self.get_config()
            
            smtp_host = config.smtp_host or "mail.huntred.com"
            smtp_port = config.smtp_port or 465
            smtp_username = config.smtp_username or config.correo_bu
            smtp_password = config.smtp_password
            from_email = from_email or smtp_username

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
            
            logger.info(f"Correo enviado a {to_email} con asunto: {subject}")
            return {"status": "success", "message": "Correo enviado correctamente."}
        except Exception as e:
            logger.error(f"[send_email] Error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
        finally:
            if server:
                server.quit()

class GamificationService:
    """Servicio para gestionar gamificación."""
    def __init__(self):
        pass

    async def award_points(self, user: Person, activity_type: str, points: int = 10):
        """Otorga puntos al usuario por una actividad."""
        try:
            profile, created = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get_or_create)(
                user=user,
                defaults={'points': 0, 'level': 1}
            )
            
            await sync_to_async(profile.award_points)(activity_type, points)
            await sync_to_async(profile.save)()
            
            logger.info(f"[GamificationService] Otorgados {points} puntos a {user.nombre}")
            await self.notify_user_gamification_update(user, activity_type)
        except Exception as e:
            logger.error(f"[GamificationService] Error otorgando puntos a {user.nombre}: {e}", exc_info=True)

    async def notify_user_gamification_update(self, user: Person, activity_type: str):
        """Notifica al usuario sobre la actualización de puntos de gamificación."""
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos."
            platform = user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp'
            business_unit = user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            if platform and business_unit:
                await send_message(
                    platform=platform,
                    user_id=user.phone,
                    message=message,
                    business_unit=business_unit
                )
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            logger.warning(f"[GamificationService] No se encontró perfil de gamificación para {user.nombre}")
        except Exception as e:
            logger.error(f"[GamificationService] Error notificando gamificación a {user.nombre}: {e}", exc_info=True)

    async def generate_challenges(self, user: Person):
        """Genera desafíos personalizados para el usuario."""
        try:
            profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=user)
            return profile.generate_networking_challenges()
        except EnhancedNetworkGamificationProfile.DoesNotExist:
            return []

    async def notify_user_challenges(self, user: Person):
        """Notifica al usuario sobre nuevos desafíos."""
        challenges = await self.generate_challenges(user)
        if challenges:
            message = f"Tienes nuevos desafíos: {', '.join(challenges)}"
            await send_message(
                platform=user.chat_state.platform if hasattr(user, 'chat_state') else 'whatsapp',
                user_id=user.phone,
                message=message,
                business_unit=user.chat_state.business_unit if hasattr(user, 'chat_state') else user.business_unit
            )


class MessageService:
    """Servicio para manejar mensajes y datos de usuario en múltiples plataformas."""
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self._api_instances: Dict[str, Any] = {}
        self._handlers: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """Inicializa el servicio de mensajería."""
        try:
            for platform in ['whatsapp', 'telegram', 'messenger', 'instagram', 'slack']:
                await self.get_api_instance(platform)
            logger.info(f"MessageService inicializado para BU: {self.business_unit.name}")
            return True
        except Exception as e:
            logger.error(f"Error inicializando MessageService: {str(e)}")
            return False

    async def get_api_instance(self, platform: str) -> Optional[Any]:
        """Obtiene o cachea la instancia de API para la plataforma especificada."""
        if not platform or not isinstance(platform, str):
            logger.error(f"Plataforma inválida: {platform}")
            return None

        cache_key = f"api_instance:{platform}:{self.business_unit.id}"
        if platform in self._api_instances and self._api_instances[platform]:
            return self._api_instances[platform]

        cached_api = cache.get(cache_key)
        if cached_api:
            self._api_instances[platform] = cached_api
            return cached_api

        model_mapping = {
            'whatsapp': WhatsAppAPI,
            'telegram': TelegramAPI,
            'messenger': MessengerAPI,
            'instagram': InstagramAPI,
            'slack': SlackAPI
        }
        handler_mapping = {
            'whatsapp': lambda: get_whatsapp_handler(),
            'telegram': lambda: TelegramHandler,
            'messenger': lambda: MessengerHandler,
            'instagram': lambda: InstagramHandler,
            'slack': lambda: SlackHandler
        }
        model_class = model_mapping.get(platform)
        handler_class = handler_mapping.get(platform)
        if not model_class or not handler_class:
            logger.error(f"Plataforma no soportada: {platform}")
            self._api_instances[platform] = None
            return None

        try:
            api_instance = await model_class.objects.aget_or_create(
                business_unit=self.business_unit,
                defaults={'api_key': 'default'}
            )
            self._api_instances[platform] = api_instance[0]
            self._handlers[platform] = handler_class()
            cache.set(cache_key, api_instance[0], CACHE_TIMEOUT)
            return api_instance[0]

        except ValueError as ve:
            logger.error(f"Error de validación en {platform}: {str(ve)}")
            self._api_instances[platform] = None
            return None
            
        except Exception as e:
            logger.error(f"Error inesperado obteniendo API para {platform}: {str(e)}", exc_info=True)
            self._api_instances[platform] = None
            return None

    async def get_handler(self, platform: str, user_id: str) -> Optional[Any]:
        """
        Obtiene o crea un manejador para la plataforma especificada.
        
        Args:
            platform (str): Plataforma (whatsapp, telegram, etc.)
            user_id (str): ID del usuario
            
        Returns:
            Optional[Any]: Manejador de la plataforma o None si no está disponible
        """
        if platform not in self._handlers:
            try:
                api_instance = await self.get_api_instance(platform)
                if not api_instance:
                    logger.error(f"No se pudo obtener la instancia de API para {platform}")
                    return None

                if platform == 'whatsapp':
                    WhatsAppHandler = get_whatsapp_handler()
                    self._handlers[platform] = WhatsAppHandler(
                        user_id=user_id,
                        phone_number_id=api_instance.phone_number_id,
                        business_unit=self.business_unit
                    )
                elif platform == 'telegram':
                    TelegramHandler, _ = get_telegram_handler()
                    self._handlers[platform] = TelegramHandler(
                        user_id=user_id,
                        bot_name=api_instance.bot_name,
                        business_unit=self.business_unit
                    )
                elif platform in ['messenger', 'instagram']:
                    if platform == 'messenger':
                        from .messenger import MessengerHandler
                        self._handlers[platform] = MessengerHandler(
                            user_id=user_id,
                            page_id=api_instance.page_id,
                            business_unit=self.business_unit
                        )
                    else:  # instagram
                        InstagramHandler, _ = get_instagram_handler()
                        self._handlers[platform] = InstagramHandler(
                            user_id=user_id,
                            phone_id=api_instance.phone_id,
                            business_unit=self.business_unit
                        )
                elif platform == 'slack':
                    # Slack uses direct functions, no handler needed
                    pass
                    
                # Initialize the handler if it has an initialize method
                if hasattr(self._handlers.get(platform), 'initialize'):
                    await self._handlers[platform].initialize()
                    
            except Exception as e:
                logger.error(f"Error creando manejador para {platform}: {str(e)}", exc_info=True)
                return None

        return self._handlers.get(platform)

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_message(self, platform: str, user_id: str, message: str, options: Optional[List[Dict]] = None) -> bool:
        """
        Envía un mensaje al usuario en la plataforma especificada.
        
        Args:
            platform (str): Plataforma (whatsapp, telegram, etc.)
            user_id (str): ID del usuario
            message (str): Mensaje a enviar
            options (Optional[List[Dict]]): Opciones adicionales (botones, etc.)
            
        Returns:
            bool: True si el mensaje se envió correctamente, False en caso contrario
        """
        """Envía un mensaje al usuario en la plataforma especificada."""
        try:
            handler = await self.get_handler(platform, user_id)
            if not handler and platform != 'slack':
                logger.error(f"No se encontró manejador para {platform}")
                return False

            if options:
                if platform == 'whatsapp':
                    async with WHATSAPP_SEMAPHORE:
                        return await handler.send_whatsapp_buttons(user_id, message, options)
                elif platform == 'telegram':
                    chat_id = int(user_id.split(":")[-1]) if ":" in user_id else int(user_id)
                    return await handler.send_telegram_buttons(chat_id, message, options)
                elif platform == 'messenger':
                    return await handler.send_messenger_buttons(user_id, message, options)
                elif platform == 'instagram':
                    return await handler.send_instagram_buttons(user_id, message, options)
                elif platform == 'slack':
                    from app.ats.chatbot.integrations.slack import send_slack_message_with_buttons
                    api_instance = await self.get_api_instance(platform)
                    slack_buttons = [
                        {"type": "button", "text": {"type": "plain_text", "text": btn["title"]}, "value": btn["payload"] or "default"}
                        for btn in options
                    ]
                    return await send_slack_message_with_buttons(
                        channel_id=user_id,
                        message=message,
                        buttons=slack_buttons,
                        bot_token=api_instance.bot_token
                    )
            else:
                if platform == 'slack':
                    from app.ats.chatbot.integrations.slack import send_slack_message
                    api_instance = await self.get_api_instance(platform)
                    return await send_slack_message(
                        channel_id=user_id,
                        message=message,
                        bot_token=api_instance.bot_token
                    )
                else:
                    return await handler._send_response(user_id, {'response': message})
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje en {platform}: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_image(self, platform: str, user_id: str, message: str, image_url: str) -> bool:
        """Envía una imagen al usuario."""
        try:
            api_instance = await self.get_api_instance(platform)
            if not api_instance:
                logger.error(f"No se encontró configuración API para {platform}")
                return False

            if platform == 'whatsapp':
                from app.ats.chatbot.integrations.whatsapp import send_whatsapp_image
                return await send_whatsapp_image(
                    user_id=user_id,
                    message=message,
                    image_url=image_url,
                    phone_id=api_instance.phoneID,
                    business_unit=self.business_unit
                )
            elif platform == 'telegram':
                from app.ats.chatbot.integrations.telegram import send_telegram_image
                chat_id = int(user_id.split(":")[-1]) if ":" in user_id else int(user_id)
                return await send_telegram_image(
                    chat_id=chat_id,
                    image_url=image_url,
                    caption=message,
                    telegram_api=api_instance,
                    business_unit_name=self.business_unit.name
                )
            elif platform in ['messenger', 'instagram']:
                from app.ats.chatbot.integrations.messenger import send_messenger_image
                return await send_messenger_image(
                    user_id=user_id,
                    image_url=image_url,
                    caption=message,
                    access_token=api_instance.page_access_token if platform == 'messenger' else api_instance.access_token
                )
            elif platform == 'slack':
                from app.ats.chatbot.integrations.slack import send_slack_message
                return await send_slack_message(
                    channel_id=user_id,
                    message=f"{message}\n{image_url}",
                    bot_token=api_instance.bot_token
                )
            else:
                logger.error(f"Plataforma no soportada: {platform}")
                return False
        except Exception as e:
            logger.error(f"Error enviando imagen en {platform}: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_document(self, platform: str, user_id: str, file_url: str, caption: str) -> bool:
        """Envía un documento al usuario."""
        try:
            api_instance = await self.get_api_instance(platform)
            if not api_instance:
                logger.error(f"No se encontró configuración para {platform}")
                return False

            if platform == 'whatsapp':
                from app.ats.chatbot.integrations.whatsapp import send_whatsapp_document
                return await send_whatsapp_document(
                    user_id=user_id,
                    file_url=file_url,
                    caption=caption,
                    whatsapp_api=api_instance,
                    business_unit=self.business_unit
                )
            elif platform == 'telegram':
                from app.ats.chatbot.integrations.telegram import send_telegram_document
                chat_id = int(user_id.split(":")[-1]) if ":" in user_id else int(user_id)
                return await send_telegram_document(
                    chat_id=chat_id,
                    file_url=file_url,
                    caption=caption,
                    telegram_api=api_instance,
                    business_unit_name=self.business_unit.name
                )
            elif platform in ['messenger', 'instagram']:
                from app.ats.chatbot.integrations.messenger import send_messenger_document
                return await send_messenger_document(
                    user_id=user_id,
                    file_url=file_url,
                    caption=caption,
                    api_instance=api_instance
                )
            elif platform == 'slack':
                from app.ats.chatbot.integrations.slack import send_slack_document
                return await send_slack_document(
                    channel_id=user_id,
                    file_url=file_url,
                    caption=caption,
                    bot_token=api_instance.bot_token
                )
            else:
                logger.error(f"Envío de documentos no soportado para {platform}")
                return False
        except Exception as e:
            logger.error(f"Error enviando documento en {platform}: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_menu(self, platform: str, user_id: str) -> bool:
        """Envía el menú principal dinámico basado en el estado del ChatState."""
        try:
            chat_state = await ChatState.objects.filter(
                user_id=user_id, business_unit=self.business_unit
            ).afirst()
            
            if not chat_state:
                logger.error(f"No se encontró ChatState para {user_id}")
                return False

                bu_name = self.business_unit.name.lower()
            menu_options = MENU_OPTIONS_BY_BU.get(bu_name, [])
            
            if not menu_options:
                logger.error(f"No se encontraron opciones de menú para {bu_name}")
                return False

            # Construir mensaje principal
            message = f"📱 *Menú de {bu_name.upper()}*\n\n"
            message += "Selecciona una opción para continuar:\n\n"
            
            # Agregar opciones principales
            for i, option in enumerate(menu_options, 1):
                message += f"{i}. {option['title']}\n"
                message += f"   _{option['description']}_\n\n"

            # Enviar menú principal
            success = await self.send_message(platform, user_id, message)
            if not success:
                return False

            # Enviar botones de navegación
            navigation_buttons = [
                {"title": "⬅️ Anterior", "payload": "menu_prev"},
                {"title": "➡️ Siguiente", "payload": "menu_next"},
                {"title": "🔍 Buscar", "payload": "menu_search"}
            ]
            
            return await self.send_options(platform, user_id, "Navega por el menú:", navigation_buttons)

        except Exception as e:
            logger.error(f"Error enviando menú: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_url(self, platform: str, user_id: str, url: str) -> bool:
        """Envía un enlace al usuario."""
        return await self.send_message(platform, user_id, f"Aquí tienes el enlace: {url}")

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_options(self, platform: str, user_id: str, message: str, buttons: Optional[List[Dict]] = None) -> bool:
        """Envía mensaje con opciones interactivas al usuario."""
        try:
            if not buttons:
                buttons = [{"title": "Continuar", "payload": "continue"}]

            return await self.send_message(platform, user_id, message, buttons)
        except Exception as e:
            logger.error(f"Error enviando opciones en {platform}: {str(e)}")
            return False

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(min=1, max=10))
    async def send_smart_options(self, platform: str, user_id: str, message: str, options: List[Dict]) -> Tuple[bool, Optional[str]]:
        """Envía opciones interactivas de manera optimizada."""
        try:
            handler = await self.get_handler(platform, user_id)
            if not handler and platform != 'slack':
                logger.error(f"No se encontró manejador para {platform}")
                return False, None

            url_buttons = [opt for opt in options if "url" in opt]
            normal_buttons = [opt for opt in options if "url" not in opt]

            if url_buttons and not normal_buttons:
                for opt in url_buttons:
                    await self.send_message(platform, user_id, f"🔗 {opt['title']}: {opt['url']}")
                return True, None

            if len(url_buttons) == 1 and normal_buttons:
                await self.send_message(platform, user_id, f"🔗 {url_buttons[0]['title']}: {url_buttons[0]['url']}")
                await asyncio.sleep(2)

            if platform == 'whatsapp' and len(normal_buttons) > 3:
                async with WHATSAPP_SEMAPHORE:
                    return await handler.send_whatsapp_list(user_id, message, normal_buttons), "msg_id_placeholder"
            else:
                return await self.send_options(platform, user_id, message, normal_buttons), "msg_id_placeholder"
        except Exception as e:
            logger.error(f"Error enviando smart options: {str(e)}")
            return False, None

    async def fetch_user_data(self, platform: str, user_id: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Obtiene datos de usuario de manera estandarizada."""
        cache_key = f"user_data:{platform}:{user_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        api_instance = await self.get_api_instance(platform)
        if not api_instance:
            logger.error(f"No se encontró instancia de API para {platform}")
            return {}

        fetcher_mapping = {
            'whatsapp': WhatsAppUserDataFetcher(),
            'telegram': TelegramUserDataFetcher(),
            'messenger': MessengerUserDataFetcher(),
            'instagram': InstagramUserDataFetcher(),
            'slack': SlackUserDataFetcher(),
        }
        fetcher = fetcher_mapping.get(platform)
        if not fetcher:
            logger.error(f"No hay fetcher definido para {platform}")
            return {}

        try:
            data = await fetcher.fetch(user_id, api_instance, payload)
            cache.set(cache_key, data, timeout=3600)
            return data
        except Exception as e:
            logger.error(f"Error obteniendo datos de usuario: {str(e)}")
            return {}

    async def invalidate_cache(self, platform: str) -> None:
        """Invalida el caché para una plataforma específica."""
        cache_key = f"api_instance:{platform}:{self.business_unit.id}"
        cache.delete(cache_key)
        if platform in self._api_instances:
            del self._api_instances[platform]
        if platform in self._handlers:
            del self._handlers[platform]
        logger.info(f"Caché invalidado para {platform}")

    async def send_evaluations_menu(self, platform: str, user_id: str, business_unit: str) -> bool:
        """Envía el menú de evaluaciones con el progreso del usuario."""
        try:
            # Obtener el usuario
            user = await Person.objects.filter(phone=user_id).first()
            if not user:
                return False

            # Obtener evaluaciones completadas
            completed_evaluations = user.completed_evaluations or []
            
            # Obtener menú de evaluaciones para la BU
            evaluations = EVALUATIONS_MENU.get(business_unit, [])
            
            # Calcular progreso
            total_evaluations = len(evaluations)
            completed_count = len(completed_evaluations)
            progress_percentage = (completed_count / total_evaluations) * 100 if total_evaluations > 0 else 0
            
            # Calcular puntos ganados
            total_points = sum(eval["points"] for eval in evaluations)
            earned_points = sum(eval["points"] for eval in evaluations if eval["payload"] in completed_evaluations)
            
            # Construir mensaje
            message = f"🎯 *Evaluaciones Disponibles*\n\n"
            message += f"📊 *Progreso:* {progress_percentage:.1f}%\n"
            message += f"⭐ *Puntos Ganados:* {earned_points}/{total_points}\n\n"
            
            # Agregar evaluaciones
            for eval in evaluations:
                status = "✅" if eval["payload"] in completed_evaluations else "🔴" if eval["required"] else "🔵"
                message += f"{status} *{eval['title']}*\n"
                message += f"_{eval['description']}_\n"
                message += f"Puntos: {eval['points']}\n\n"
            
            # Agregar opción para ver CV completo si está al 100%
            if progress_percentage == 100:
                message += "\n🎉 ¡Felicidades! Has completado todas las evaluaciones.\n"
                message += "Puedes ver tu CV completo en cualquier momento."
            
            # Enviar mensaje
            return await self.send_message(platform, user_id, message)
            
        except Exception as e:
            logger.error(f"Error al enviar menú de evaluaciones: {str(e)}")
            return False

    async def send_submenu(self, platform: str, user_id: str, parent_payload: str) -> bool:
        """Envía el submenú correspondiente a una opción del menú principal."""
        try:
            bu_name = self.business_unit.name.lower()
            menu_options = MENU_OPTIONS_BY_BU.get(bu_name, [])
            
            # Encontrar la opción padre
            parent_option = next((opt for opt in menu_options if opt["payload"] == parent_payload), None)
            if not parent_option or "submenu" not in parent_option:
                return False

            # Construir mensaje del submenú
            message = f"📱 *{parent_option['title']}*\n\n"
            message += f"{parent_option['description']}\n\n"
            message += "Selecciona una opción:\n\n"

            # Agregar opciones del submenú
            for i, option in enumerate(parent_option["submenu"], 1):
                message += f"{i}. {option['title']}\n"

            # Enviar submenú
            success = await self.send_message(platform, user_id, message)
            if not success:
                return False

            # Enviar botones de navegación
            navigation_buttons = [
                {"title": "⬅️ Volver", "payload": "menu"},
                {"title": "🔍 Buscar", "payload": f"search_{parent_payload}"}
            ]
            
            return await self.send_options(platform, user_id, "Navega por el submenú:", navigation_buttons)

        except Exception as e:
            logger.error(f"Error enviando submenú: {str(e)}")
            return False


async def notify_employer(worker, message):
    """Notifica al empleador que un evento ha ocurrido."""
    try:
        if worker.whatsapp:
            whatsapp_api = await sync_to_async(lambda: WhatsAppAPI.objects.filter(
                business_unit=worker.business_unit, is_active=True
            ).select_related('business_unit').first())()
            if whatsapp_api:
                from app.ats.chatbot.integrations.whatsapp import send_whatsapp_message
                await send_whatsapp_message(
                    user_id=worker.whatsapp,
                    message=message,
                    phone_id=whatsapp_api.phoneID,
                    business_unit=whatsapp_api.business_unit
                )
                logger.info(f"[notify_employer] Notificación enviada al empleador {worker.name} vía WhatsApp.")
            else:
                logger.error("[notify_employer] No se encontró configuración de WhatsAppAPI.")
        else:
            logger.warning(f"[notify_employer] El empleador {worker.name} no tiene número de WhatsApp configurado.")
    except Exception as e:
        logger.error(f"[notify_employer] Error enviando notificación al empleador {worker.name}: {e}", exc_info=True)

async def get_business_unit(name: Optional[str] = None) -> Optional[BusinessUnit]:
    """Obtiene una instancia de BusinessUnit por nombre."""
    try:
        if not name:
            return None
        
        normalized_name = str(name).lower().replace('®', '').strip() if isinstance(name, str) else name
        
        if isinstance(name, BusinessUnit):
            return name
            
        business_unit = await sync_to_async(BusinessUnit.objects.filter)(
            name__iexact=normalized_name
        )
        return await sync_to_async(business_unit.first)()
    except Exception as e:
        logger.error(f"[get_business_unit] Error obteniendo BusinessUnit ({name}): {e}")
        return None

def run_async(func, *args, **kwargs):
    """Ejecuta la función en modo síncrono o asíncrono según el contexto."""
    try:
        loop = asyncio.get_running_loop()
        return func(*args, **kwargs)
    except RuntimeError:
        return asyncio.run(func(*args, **kwargs))

async def reset_chat_state(user_id: str, business_unit: BusinessUnit, platform: Optional[str] = None):
    """Reinicia el estado de la conversación (ChatState) para un usuario."""
    try:
        chat_state = await sync_to_async(ChatState.objects.get)(user_id=user_id, business_unit=business_unit)
        await sync_to_async(chat_state.delete)()
        logger.info(f"🧹 ChatState reiniciado para {user_id} en {business_unit.name}")
        
        if platform:
            await send_message(platform, user_id, "🧹 Conversación reiniciada. Envía un mensaje para comenzar de nuevo.", business_unit)
    except ChatState.DoesNotExist:
        logger.info(f"🧹 No se encontró ChatState para {user_id} en {business_unit.name}, no hay nada que reiniciar.")
        if platform:
            await send_message(platform, user_id, "🧹 No había conversación activa, pero estás listo para comenzar de nuevo.", business_unit)


async def send_message_async(platform: str, user_id: str, message: str, business_unit_name: str = None) -> bool:
    """Envía un mensaje de forma asíncrona."""
    try:
        business_unit = await get_business_unit(business_unit_name or 'default')
        if not business_unit:
            logger.error(f"Business unit no encontrado: {business_unit_name}")
            return False

        message_service = MessageService(business_unit)
        return await message_service.send_message(platform, user_id, message)
    except Exception as e:
        logger.error(f"Error enviando mensaje: {str(e)}")
        return False

def send_message(platform: str, user_id: str, message: str, business_unit: str = None) -> bool:
    """Envío de mensaje compatible con entornos síncronos y asíncronos."""
    return run_async(send_message_async, platform, user_id, message, business_unit)

async def send_menu_async(platform: str, user_id: str, business_unit: Optional[str] = None) -> bool:
    """Envía el menú principal al usuario en la plataforma especificada."""
    try:
        business_unit = await get_business_unit(business_unit)
        if not business_unit:
            logger.error(f"No se encontró la unidad de negocio para {platform} - Usuario: {user_id}")
            return False

        message_service = MessageService(business_unit)
        return await message_service.send_menu(platform, user_id)
    except Exception as e:
        logger.error(f"Error enviando menú: {str(e)}")
        return False

def send_menu(platform: str, user_id: str, business_unit_name: str = None) -> bool:
    """Wrapper de send_menu compatible con entornos síncronos y asíncronos."""
    return run_async(send_menu_async, platform, user_id, business_unit_name)

async def send_image_async(platform: str, user_id: str, message: str, image_url: str, business_unit: Optional[str] = None) -> bool:
    """Envía una imagen al usuario en la plataforma especificada."""
    try:
        business_unit = await get_business_unit(business_unit)
        if not business_unit:
            logger.error(f"No se encontró la unidad de negocio para {platform} - Usuario: {user_id}")
            return False

        message_service = MessageService(business_unit)
        return await message_service.send_image(platform, user_id, message, image_url)
    except Exception as e:
        logger.error(f"Error enviando imagen: {str(e)}")
        return False

def send_image(platform: str, user_id: str, message: str, image_url: str, business_unit_name: str = None) -> bool:
    """Wrapper de send_image compatible con entornos síncronos y asíncronos."""
    return run_async(send_image_async, platform, user_id, message, image_url, business_unit_name)

async def send_url_async(platform: str, user_id: str, url: str, business_unit: Optional[str] = None) -> bool:
    """Envía un enlace al usuario en la plataforma especificada."""
    try:
        business_unit = await get_business_unit(business_unit)
        if not business_unit:
            logger.error(f"No se encontró la unidad de negocio para {platform} - Usuario: {user_id}")
            return False

        message_service = MessageService(business_unit)
        return await message_service.send_url(platform, user_id, url)
    except Exception as e:
        logger.error(f"Error enviando URL: {str(e)}")
        return False

def send_url(platform: str, user_id: str, url: str, business_unit_name: str = None) -> bool:
    """Wrapper de send_url compatible con entornos síncronos y asíncronos."""
    return run_async(send_url_async, platform, user_id, url, business_unit_name)

async def send_list_options(platform: str, user_id: str, message: str, buttons: List[Dict], business_unit_name: str):
    """Envía una lista interactiva en WhatsApp si hay más de 3 opciones."""
    from app.ats.chatbot.integrations.whatsapp import send_whatsapp_list
    if platform != "whatsapp":
        success = await send_options(platform, user_id, message, buttons, business_unit_name)
        return success, None
    sections = [{"title": "Opciones", "rows": [{"id": btn["payload"], "title": btn["title"]} for btn in buttons]}]
    success = await send_whatsapp_list(user_id, message, sections, business_unit_name)
    msg_id = "msg_id_placeholder" if success else None
    return success, msg_id

async def send_smart_options(platform, user_id, message, options, business_unit_name):
    """Envía opciones interactivas de manera optimizada."""
    try:
        business_unit = await get_business_unit(business_unit_name)
        if not business_unit:
            logger.error(f"[send_smart_options] No se encontró BusinessUnit para {business_unit_name}")
            return False, None

        service = MessageService(business_unit)

        if platform == "whatsapp":
            url_buttons = [opt for opt in options if "url" in opt]
            normal_buttons = [opt for opt in options if "url" not in opt]

            if url_buttons and not normal_buttons:
                logger.info("[send_smart_options] 📤 Enviando botones URL como mensajes separados.")
                for opt in url_buttons:
                    await service.send_message(platform, user_id, f"🔗 {opt['title']}: {opt['url']}")
                return True, None

            if len(url_buttons) == 1 and normal_buttons:
                logger.info(f"[send_smart_options] 📤 Enviando primero el enlace: {url_buttons[0]['url']}")
                await service.send_message(platform, user_id, f"🔗 {url_buttons[0]['title']}: {url_buttons[0]['url']}")
                await asyncio.sleep(2)

            if len(normal_buttons) > 3:
                success, msg_id = await send_list_options(platform, user_id, message, normal_buttons, business_unit_name)
                if success:
                    return True, msg_id
                logger.warning("[send_smart_options] ❌ Listas interactivas fallaron, usando fallback.")

            last_msg_id = None
            option_batches = [normal_buttons[i:i+3] for i in range(0, len(normal_buttons), 3)]
            for batch in option_batches:
                success = await service.send_options(platform, user_id, message, batch)
                if not success:
                    logger.error("[send_smart_options] ❌ Falló el envío de opciones.")
                    return False, None
                last_msg_id = "msg_id_placeholder"
                await asyncio.sleep(0.5)

            return True, last_msg_id

        else:
            success = await service.send_options(platform, user_id, message, options)
            return success, "msg_id_placeholder" if success else None

    except Exception as e:
        logger.error(f"[send_smart_options] ❌ Error enviando opciones a {user_id}: {e}", exc_info=True)
        return False, None

async def send_options_async(platform: str, user_id: str, message: str, buttons=None, business_unit_name: str = None):
    """Envío de mensaje con botones interactivos de forma asíncrona."""
    try:
        business_unit = await get_business_unit(business_unit_name)
        if not business_unit:
            logger.error(f"[send_options_async] ❌ No se encontró BusinessUnit para {business_unit_name}")
            return False

        service = MessageService(business_unit)

        if platform == "whatsapp":
            if not buttons:
                logger.error(f"[send_options_async] ⚠️ No hay botones válidos para enviar a WhatsApp.")
                return False
            
            formatted_buttons = []
            for i, btn in enumerate(buttons[:3]):
                if "title" in btn and "payload" in btn:
                    formatted_buttons.append({
                        "type": "reply",
                        "reply": {
                            "id": btn["payload"],
                            "title": btn["title"][:20]
                        }
                    })
                else:
                    logger.warning(f"[send_options_async] ⚠️ Botón inválido: {btn}")

            logger.info(f"[send_options_async] 🚀 Botones generados para WhatsApp: {formatted_buttons}")

            if not formatted_buttons:
                logger.error(f"[send_options_async] ⚠️ No se generaron botones válidos para WhatsApp.")
                return False

            from app.ats.chatbot.integrations.whatsapp import send_whatsapp_decision_buttons
            success = await send_whatsapp_decision_buttons(
                user_id=user_id,
                message=message,
                buttons=formatted_buttons,
                business_unit=business_unit
            )
        else:
            success = await service.send_options(platform, user_id, message, buttons)

        if success:
            logger.info(f"[send_options_async] ✅ Opciones enviadas a {user_id} en {platform}")
        else:
            logger.warning(f"[send_options_async] ⚠️ Fallo en el envío de opciones a {user_id} en {platform}")

        return success

    except Exception as e:
        logger.error(f"[send_options_async] ❌ Error enviando opciones a {user_id} en {platform}: {e}", exc_info=True)
        return False

class AssessmentService:
    def __init__(self):
        self.professional_dna = ProfessionalDNAAnalysis()
        self.cultural_fit = CulturalFitWorkflow()
        self.talent_analysis = TalentAnalysisWorkflow()
        self.personality = PersonalityAssessment()

    def get_available_assessments(self) -> Dict[str, List[str]]:
        """Retorna los assessments disponibles organizados por categoría"""
        return {
            "professional_dna": [
                "leadership",
                "innovation",
                "communication",
                "resilience",
                "results"
            ],
            "cultural": [
                "values",
                "work_style",
                "communication_preferences",
                "adaptability"
            ],
            "talent": [
                "technical_skills",
                "key_competencies",
                "development_potential",
                "improvement_areas"
            ],
            "personality": [
                "personality_traits",
                "behavioral_styles",
                "work_preferences",
                "interaction_patterns"
            ]
        }

    def get_assessment_questions(
        self,
        assessment_type: str,
        category: str,
        business_unit: Optional[BusinessUnit] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene las preguntas para un tipo específico de assessment"""
        if assessment_type == "professional_dna":
            return self.professional_dna.get_questions_by_category(
                QuestionCategory(category)
            )
        elif assessment_type == "cultural":
            return self.cultural_fit.get_questions(category)
        elif assessment_type == "talent":
            return self.talent_analysis.get_questions(category)
        elif assessment_type == "personality":
            return self.personality.get_questions(category)
        return []

    def analyze_assessment(
        self,
        assessment_type: str,
        answers: Dict[str, Any],
        generation: str,
        business_unit: Optional[BusinessUnit] = None
    ) -> Dict[str, Any]:
        """Analiza las respuestas de un assessment específico"""
        if assessment_type == "professional_dna":
            return self.professional_dna.analyze_answers(
                answers,
                generation,
                business_unit
            )
        elif assessment_type == "cultural":
            return self.cultural_fit.analyze_answers(answers)
        elif assessment_type == "talent":
            return self.talent_analysis.analyze_answers(answers)
        elif assessment_type == "personality":
            return self.personality.analyze_answers(answers)
        return {}

    def get_assessment_summary(
        self,
        assessment_type: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Obtiene un resumen del análisis de un assessment"""
        if assessment_type == "professional_dna":
            return self.professional_dna.get_analysis_summary(results)
        elif assessment_type == "cultural":
            return self.cultural_fit.get_summary(results)
        elif assessment_type == "talent":
            return self.talent_analysis.get_summary(results)
        elif assessment_type == "personality":
            return self.personality.get_summary(results)
        return {}
