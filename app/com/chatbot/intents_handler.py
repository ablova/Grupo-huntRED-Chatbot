"""
Manejo de intents para el chatbot de Amigro/HuntRED/HuntU/SEXSI.
Este módulo combina las mejores características de los sistemas de intents anteriores,
proporcionando un manejo más robusto y organizado de las interacciones del usuario.
"""

from typing import Dict, Any, Optional, List, Union, Type, Callable
import re
import json
import os
import time
import asyncio
from functools import wraps, lru_cache
from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q, Count, F
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from app.models import (
    Person, Vacante, Application, BusinessUnit,
    EnhancedNetworkGamificationProfile, ChatState,
    WorkflowStage, ConfiguracionBU, Template, Intent
)
from app.com.chatbot.utils import ChatbotUtils
from app.com.chatbot.integrations.services import send_message, send_smart_options, send_options, send_menu
from app.com.chatbot.workflow.common import (
    calcular_salario_chatbot, iniciar_creacion_perfil,
    iniciar_perfil_conversacional, iniciar_prueba,
    send_welcome_message
)
from app.ml.core.models import MatchmakingModel
from app.ml.core.utils import BUSINESS_UNIT_HIERARCHY
from app.com.chatbot.intents_optimizer import intent_optimizer
from app.com.chatbot.channel_config import ChannelConfig
from app.com.chatbot.metrics import chatbot_metrics
from app.com.utils.logger_utils import get_module_logger, log_async_function_call, ResourceMonitor

# Configuración del sistema de logging avanzado
logger = get_module_logger('intents_handler')

# Métricas y monitoreo de rendimiento
class IntentMetrics:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.intent_counts = Counter()
        self.intent_timing = defaultdict(list)
        self.intent_success = Counter()
        self.intent_failures = Counter()
        self.pattern_matches = defaultdict(int)
        self.last_reset = time.time()
    
    def record_intent(self, intent_name: str, duration: float, success: bool = True):
        """Registra métricas para un intent procesado"""
        self.intent_counts[intent_name] += 1
        self.intent_timing[intent_name].append(duration)
        if success:
            self.intent_success[intent_name] += 1
        else:
            self.intent_failures[intent_name] += 1
    
    def record_pattern_match(self, pattern: str, intent_name: str):
        """Registra cuando un patrón específico coincide"""
        key = f"{pattern}:{intent_name}"
        self.pattern_matches[key] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de intents para análisis"""
        avg_timing = {}
        for intent, times in self.intent_timing.items():
            if times:
                avg_timing[intent] = sum(times) / len(times)
        
        success_rates = {}
        for intent in self.intent_counts:
            total = self.intent_success[intent] + self.intent_failures[intent]
            if total > 0:
                success_rates[intent] = (self.intent_success[intent] / total) * 100
            else:
                success_rates[intent] = 0
        
        return {
            "intent_counts": dict(self.intent_counts),
            "avg_timing": avg_timing,
            "success_rates": success_rates,
            "pattern_matches": dict(self.pattern_matches),
            "elapsed_since_reset": time.time() - self.last_reset
        }

# Instancia global para métricas
intent_metrics = IntentMetrics()

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

class IntentsHandler:
    """
    Clase para manejar intents de manera escalable y eficiente.
    Proporciona clasificación, coincidencia y generación de respuestas.
    """
    def __init__(self, business_unit_name: str):
        self.business_unit_name = business_unit_name.lower()
        self.utils = ChatbotUtils()
        self.matchmaking = MatchmakingModel()
        
        # Configuración avanzada de caché
        self.MAX_CACHE_AGE = 86400  # 24 horas
        self.CACHE_PREFIX = f"intents_{self.business_unit_name}"  # Prefijo específico por BU
        self.CACHE_HIT_RATIO = 0.0  # Métrica de eficacia del caché
        self.CACHE_REQUESTS = 0  # Total de solicitudes de caché
        
        # Respuestas y plantillas
        self.DEFAULT_RESPONSE = "Lo siento, no entendí lo que quieres decir. ¿Podrías reformularlo?"
        self.TEMPLATES = {}
        self._intent_patterns = None  # Lazy loading
        
        # Contador de errores para circuit breaker
        self.error_counts = defaultdict(int)
        self.error_threshold = 5  # Umbral para activar fallbacks
        self.reset_interval = 300  # 5 minutos para resetear contadores
        self.last_reset = time.time()
        
        # Registro de inicialización
        logger.info(f"IntentsHandler inicializado para {business_unit_name}", 
                  extra={"data": {"business_unit": business_unit_name}})
        
        # Registro de consumo de recursos al inicio
        ResourceMonitor.log_memory_usage(logger, f"IntentsHandler_{business_unit_name}_init")
        
        # Manejadores dinámicos de respuestas por tipo de intent
        self.dynamic_responders = {
            "show_menu": self._show_menu,
            "show_jobs": self._show_jobs,
            "aplicar_vacante": self._aplicar_vacante,
            "ver_aplicaciones": self._ver_aplicaciones,
            "menu_principal": self._menu_principal,
            "preguntar_salario": self._preguntar_salario,
            "prueba_personalidad": self._iniciar_prueba_personalidad,
            "crear_perfil": self._iniciar_creacion_perfil,
            "obtener_username": self._get_username,
        }
        
        # Spam detector para mensajes repetitivos
        self.spam_detector = SpamDetector()
        
    @log_async_function_call(logger)
    async def process(self, text: str, channel: str = "whatsapp", person_id: str = None) -> Dict[str, Any]:
        """Procesa un texto para encontrar intents y generar respuestas apropiadas.
        
        Args:
            text: Texto a procesar para extraer intents
            channel: Canal de comunicación (whatsapp, telegram, etc.)
            person_id: ID de la persona que envió el mensaje
            
        Returns:
            Diccionario con la respuesta, intent detectado y opciones
        """
        start_time = time.time()
        context = {"channel": channel, "person_id": person_id, "text_length": len(text), "bu": self.business_unit_name}
        
        # Monitoreo de recursos durante el procesamiento
        memory_usage_start = ResourceMonitor.get_current_memory_usage()
        
        # Resetear contadores de error si ha pasado suficiente tiempo
        if time.time() - self.last_reset > self.reset_interval:
            self.error_counts.clear()
            self.last_reset = time.time()
            logger.debug("Contadores de error reseteados", extra={"data": context})
        
        try:
            # Verificar si el mensaje es spam
            if await self.spam_detector.is_spam(text, person_id, channel):
                logger.warning(f"Mensaje de spam detectado: '{text[:30]}...'")
                return {
                    "intent": "spam",
                    "confidence": 1.0,
                    "response": "Por favor, evita enviar mensajes repetitivos o spam.",
                    "smart_options": [],
                    "elapsed_time": time.time() - start_time
                }
            
            # Verificar caché para evitar procesamiento repetitivo
            self.CACHE_REQUESTS += 1
            cache_key = f"{self.CACHE_PREFIX}:{hash(text)}:{channel}"
            cached_response = await sync_to_async(lambda: cache.get)(cache_key)()
            
            if cached_response:
                # Actualizar métricas de caché
                self.CACHE_HIT_RATIO = (self.CACHE_HIT_RATIO * (self.CACHE_REQUESTS - 1) + 1) / self.CACHE_REQUESTS
                
                logger.debug(f"Respuesta encontrada en caché para: '{text[:20]}...'", 
                           extra={"data": {"cache_hit_ratio": f"{self.CACHE_HIT_RATIO * 100:.1f}%"}})
                return cached_response
            else:
                # Actualizar métricas de caché (miss)
                self.CACHE_HIT_RATIO = (self.CACHE_HIT_RATIO * (self.CACHE_REQUESTS - 1)) / self.CACHE_REQUESTS
                
            # Sanitizar entrada (eliminar caracteres especiales, normalizar espacios)
            cleaned_text = self._sanitize_input(text)
            
            # Buscar coincidencias de patrones de intents
            detected_intents = self._match_intents(cleaned_text)
            logger.debug(f"Intents detectados para '{cleaned_text[:30]}...': {detected_intents}", 
                       extra={"data": {"intents": detected_intents}})
            
            # Manejo de comando start (caso especial)
            if not detected_intents and cleaned_text.strip().lower() == "start":
                detected_intents = self._match_intents("/start")
                logger.debug("Reemplazando 'start' con comando '/start'")
            
            # Optimización de texto si no se detectaron intents
            if not detected_intents:
                try:
                    # Intentar optimizar el texto para mejor detección
                    optimized_text = await intent_optimizer.optimize(cleaned_text)
                    if optimized_text != cleaned_text:
                        logger.info(f"Texto optimizado: '{cleaned_text[:20]}...' -> '{optimized_text[:20]}...'")
                        detected_intents = self._match_intents(optimized_text)
                except Exception as opt_error:
                    logger.warning(f"Error en optimización de texto: {str(opt_error)}")
                    # Continuar con el flujo normal sin optimización
            
            # Intent de fallback si no se detectó ninguno
            if not detected_intents:
                logger.info(f"No se detectó ningún intent para: '{cleaned_text[:30]}...'", 
                          extra={"data": context})
                
                # Preparar opciones inteligentes para el fallback
                smart_options = self._get_fallback_options(cleaned_text)
                
                fallback_response = {
                    "intent": "unknown",
                    "confidence": 0.0,
                    "response": self.DEFAULT_RESPONSE,
                    "smart_options": smart_options,
                    "elapsed_time": time.time() - start_time
                }
                
                # Registrar métricas
                intent_metrics.record_intent("unknown", time.time() - start_time, success=True)
                
                # No guardar en caché los fallbacks para evitar respuestas repetitivas
                return fallback_response
                
            # Ordenar intents por prioridad y seleccionar el más prioritario
            intent_name = detected_intents[0]
            logger.info(f"Intent seleccionado: {intent_name}", extra={"data": {"all_intents": detected_intents}})
            
            # Registrar coincidencia de patrón
            matching_pattern = self._get_matching_pattern(cleaned_text, intent_name)
            if matching_pattern:
                intent_metrics.record_pattern_match(matching_pattern, intent_name)
            
            # Responder dinámicamente si el intent lo requiere
            if intent_name in self.dynamic_responders:
                try:
                    dynamic_start = time.time()
                    response = await self.dynamic_responders[intent_name](cleaned_text, channel, person_id)
                    dynamic_time = time.time() - dynamic_start
                    
                    logger.debug(f"Respuesta dinámica generada para {intent_name} en {dynamic_time:.3f}s")
                    response["intent"] = intent_name
                    response["elapsed_time"] = time.time() - start_time
                    
                    # Registrar métricas
                    intent_metrics.record_intent(intent_name, time.time() - start_time, success=True)
                    
                    # Registrar uso de recursos
                    memory_used = ResourceMonitor.get_current_memory_usage() - memory_usage_start
                    logger.debug(f"Memoria utilizada: {memory_used/1024/1024:.2f} MB para intent {intent_name}")
                    
                    # Guardar en caché con tiempo de expiración más corto para respuestas dinámicas
                    await sync_to_async(lambda: cache.set)(cache_key, response, timeout=300)()
                    
                    return response
                except Exception as dynamic_error:
                    # Si falla el responder dinámico, incrementar contador de errores
                    self.error_counts[intent_name] += 1
                    logger.error(f"Error en respuesta dinámica para {intent_name}: {str(dynamic_error)}", 
                               exc_info=True)
                    
                    # Si se alcanza el umbral, usar respuesta estática como fallback
                    if self.error_counts[intent_name] >= self.error_threshold:
                        logger.warning(f"Circuit breaker activado para {intent_name} después de {self.error_counts[intent_name]} errores")
                    else:
                        # Propagar error si aún no se alcanza el umbral
                        raise
            
            # Generar respuesta estática (si el intent no tiene responder dinámico o falló)
            templates = INTENT_PATTERNS[intent_name].get("responses", [])
            
            if isinstance(templates, dict):
                # Seleccionar plantilla específica para la unidad de negocio
                responses = templates.get(self.business_unit_name, templates.get("default", ["No tengo una respuesta específica para eso."]))
            else:
                responses = templates

            # Seleccionar respuesta aleatoria del conjunto disponible
            import random
            response_text = random.choice(responses) if responses else self.DEFAULT_RESPONSE
            
            # Generar opciones inteligentes contextuales
            smart_options = []
            if intent_name == "saludo":
                smart_options = MENU_BUTTONS
            else:
                smart_options = await self._get_relevant_smart_options(intent_name, person_id)
            
            final_response = {
                "intent": intent_name,
                "confidence": 1.0,  # Confianza máxima para coincidencias exactas
                "response": response_text,
                "smart_options": smart_options,
                "elapsed_time": time.time() - start_time
            }
            
            # Registrar métricas de éxito
            intent_metrics.record_intent(intent_name, time.time() - start_time, success=True)
            
            # Guardar en caché para futuras consultas similares
            await sync_to_async(lambda: cache.set)(cache_key, final_response, timeout=1800)()
            
            return final_response
            
        except Exception as e:
            # Registrar error detallado
            elapsed = time.time() - start_time
            logger.error(f"Error procesando intent: {str(e)}", 
                       exc_info=True, 
                       extra={"data": {**context, "elapsed_time": elapsed}})
            
            # Registrar métricas de fallo
            intent_metrics.record_intent("error", elapsed, success=False)
            
            # Monitorear uso de recursos para diagnosticar problemas
            ResourceMonitor.log_memory_usage(logger, "intent_process_error")
            
            return {
                "intent": "error",
                "confidence": 0.0,
                "response": "Lo siento, ocurrió un error al procesar tu mensaje. Intentemos con otra pregunta.",
                "smart_options": MENU_BUTTONS,  # Añadir opciones de menú para facilitar recuperación
                "elapsed_time": elapsed
            }
            
    def _match_intents(self, text: str) -> List[str]:
        """Busca coincidencias de patrones en el texto y devuelve los intents ordenados por prioridad."""
        matched_intents = []
        
        for intent_name, data in INTENT_PATTERNS.items():
            for pattern in data.get("patterns", []):
                if re.search(pattern, text, re.IGNORECASE):
                    matched_intents.append(intent_name)
                    break  # Solo necesitamos una coincidencia por intent
        
        # Ordenar por prioridad
        return sorted(matched_intents, key=lambda x: INTENT_PATTERNS[x].get("priority", 999))
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitiza el texto de entrada para procesamiento más seguro y efectivo."""
        if not text:
            return ""
            
        # Eliminar caracteres especiales peligrosos y normalizar espacios
        import re
        sanitized = re.sub(r'[\x00-\x1F\x7F]', '', text)  # Eliminar caracteres de control
        sanitized = re.sub(r'\s+', ' ', sanitized)  # Normalizar espacios
        return sanitized.strip()
        
    def _get_matching_pattern(self, text: str, intent_name: str) -> Optional[str]:
        """Encuentra el patrón exacto que coincidió con el texto para el intent dado."""
        if intent_name not in INTENT_PATTERNS:
            return None
            
        for pattern in INTENT_PATTERNS[intent_name]["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return pattern
                
        return None
        
    async def _get_relevant_smart_options(self, intent_name: str, person_id: str = None) -> List[Dict[str, Any]]:
        """Genera opciones inteligentes relevantes al intent y contexto del usuario."""
        # Opciones básicas por defecto
        basic_options = [
            {"title": "📝 Ver menú", "payload": "menu"}
        ]
        
        # Si no tenemos person_id, devolver opciones básicas
        if not person_id:
            return basic_options
            
        try:
            # Intentar obtener usuario y su historial para personalizar opciones
            user = await Person.objects.filter(external_id=person_id).afirst()
            if not user:
                return basic_options
                
            # Personalizar opciones según el intent y el historial del usuario
            if intent_name == "saludo":
                return MENU_BUTTONS
            elif intent_name == "show_jobs":
                return [
                    {"title": "💼 Ver más vacantes", "payload": "more_jobs"},
                    {"title": "📝 Filtrar resultados", "payload": "filter_jobs"},
                    {"title": "⬅️ Regresar al menú", "payload": "menu"}
                ]
            elif intent_name == "aplicar_vacante":
                return [
                    {"title": "📧 Subir CV", "payload": "upload_cv"},
                    {"title": "💼 Ver vacantes similares", "payload": "similar_jobs"},
                    {"title": "⬅️ Regresar al menú", "payload": "menu"}
                ]
            # Añadir más casos según sea necesario
            
            # Devolver opciones básicas si no hay personalización específica
            return basic_options
                
        except Exception as e:
            logger.warning(f"Error obteniendo opciones inteligentes: {str(e)}")
            return basic_options
            
    def _get_fallback_options(self, text: str) -> List[Dict[str, Any]]:
        """Genera opciones inteligentes para casos donde no se detectó ningún intent."""
        # Analizar el texto para sugerir opciones relevantes
        if re.search(r'\b(trabajo|vacante|empleo|job)\b', text, re.IGNORECASE):
            return [
                {"title": "💼 Ver vacantes disponibles", "payload": "show_jobs"},
                {"title": "📝 Menú principal", "payload": "menu"}
            ]
        elif re.search(r'\b(cv|curriculum|resume|perfil)\b', text, re.IGNORECASE):
            return [
                {"title": "📧 Subir mi CV", "payload": "upload_cv"},
                {"title": "💼 Actualizar perfil", "payload": "update_profile"},
                {"title": "📝 Menú principal", "payload": "menu"}
            ]
        elif re.search(r'\b(ayuda|help|soporte|support)\b', text, re.IGNORECASE):
            return [
                {"title": "❓ Preguntas frecuentes", "payload": "faq"},
                {"title": "💬 Hablar con reclutador", "payload": "contact_recruiter"},
                {"title": "📝 Menú principal", "payload": "menu"}
            ]
        # Opciones por defecto
        return MENU_BUTTONS
    
    # Implementaciones de los manejadores dinámicos
    async def _show_menu(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        """Muestra el menú principal con opciones relevantes."""
        # Implementar lógica para mostrar menú personalizado
        return {
            "response": "Aquí está el menú principal. ¿En qué puedo ayudarte?",
            "smart_options": MENU_BUTTONS,
            "template_messages": []
        }
        
    async def _show_jobs(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        """Muestra las vacantes disponibles."""
        # Implementar lógica para mostrar vacantes
        return {
            "response": "Aquí tienes algunas vacantes que podrían interesarte:",
            "smart_options": [],
            "template_messages": []
        }
        
    # Métodos vacíos para los demás manejadores dinámicos (implementar según sea necesario)
    async def _aplicar_vacante(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        return {"response": "Implementación pendiente", "smart_options": [], "template_messages": []}
        
    async def _ver_aplicaciones(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        return {"response": "Implementación pendiente", "smart_options": [], "template_messages": []}
        
    async def _menu_principal(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        return {"response": "Implementación pendiente", "smart_options": [], "template_messages": []}
        
    async def _preguntar_salario(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        return {"response": "Implementación pendiente", "smart_options": [], "template_messages": []}
        
    async def _iniciar_prueba_personalidad(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        return {"response": "Implementación pendiente", "smart_options": [], "template_messages": []}
        
    async def _iniciar_creacion_perfil(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        return {"response": "Implementación pendiente", "smart_options": [], "template_messages": []}
        
    async def _get_username(self, text: str, channel: str, person_id: str) -> Dict[str, Any]:
        return {"response": "Implementación pendiente", "smart_options": [], "template_messages": []}

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
        options = [
            {
                'title': 'Ver FAQ',
                'payload': json.dumps({'action': 'view_faq'})
            },
            {
                'title': 'Contactar soporte',
                'payload': json.dumps({'action': 'contact_support'})
            }
        ]
        
        # Enviar opciones usando send_smart_options
        await send_smart_options(platform, user_id, "¿En qué puedo ayudarte?", options, bu_key)
        
        # Preparar mensaje de plantilla
        template = Template(
            name="help_center",
            whatsapp_api=self.business_unit.whatsapp_apis.first(),
            template_type="BUTTON",
            language_code="es_MX"
        )
        self.template = template
        
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



class SpamDetector:
    """Detector de spam para mensajes del chatbot."""

    def __init__(self):
        self.message_cache = cache
        self.spam_threshold = 3  # Número máximo de mensajes idénticos permitidos
        self.time_window = timedelta(minutes=5)  # Ventana de tiempo para detectar spam
        self.suspicious_patterns = [
            r'\b(free|gratis|ganar|dinero|cash|bitcoin|crypto)\b',
            r'\b(work|job|employment|remote|online)\b',
            r'\b(click|visit|link|website|url)\b',
            r'\b(watch|video|tutorial|guide)\b',
            r'\b(scam|fraud|phishing|hacking)\b'
        ]

    async def is_spam(self, message: str) -> bool:
        """Detecta si un mensaje es spam."""
        try:
            # Verificar patrones sospechosos
            if self._contains_suspicious_patterns(message):
                return True

            # Verificar mensajes repetidos
            if await self._is_repeated_message(message):
                return True

            return False
        except Exception as e:
            logger.error(f"Error en SpamDetector: {str(e)}", exc_info=True)
            return False

    def _contains_suspicious_patterns(self, message: str) -> bool:
        """Verifica si el mensaje contiene patrones sospechosos."""
        for pattern in self.suspicious_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    async def _is_repeated_message(self, message: str) -> bool:
        """Verifica si el mensaje es repetido dentro de la ventana de tiempo."""
        try:
            # Normalizar el mensaje
            normalized = self._normalize_message(message)
            
            # Obtener mensajes recientes
            recent_messages = await self._get_recent_messages()
            
            # Contar ocurrencias del mensaje
            message_count = recent_messages.count(normalized)
            
            if message_count >= self.spam_threshold:
                return True
            
            # Guardar mensaje actual
            await self._save_message(normalized)
            return False
            
        except Exception as e:
            logger.error(f"Error en _is_repeated_message: {str(e)}", exc_info=True)
            return False

    def _normalize_message(self, message: str) -> str:
        """Normaliza el mensaje para comparación."""
        return message.lower().strip()

    async def _get_recent_messages(self) -> List[str]:
        """Obtiene mensajes recientes dentro de la ventana de tiempo."""
        current_time = datetime.now()
        start_time = current_time - self.time_window
        
        # Clave para caché de mensajes
        cache_key = f"recent_messages:{self.user.id}"
        
        # Obtener mensajes de caché
        messages = self.message_cache.get(cache_key, [])
        
        # Filtrar mensajes fuera de la ventana de tiempo
        filtered_messages = []
        for msg in messages:
            if msg.get('timestamp', datetime.min) >= start_time:
                filtered_messages.append(msg)
        
        # Actualizar caché
        self.message_cache.set(cache_key, filtered_messages, timeout=self.time_window.total_seconds())
        
        return [msg['message'] for msg in filtered_messages]

    async def _save_message(self, message: str):
        """Guarda un mensaje en la caché de mensajes recientes."""
        current_time = datetime.now()
        cache_key = f"recent_messages:{self.user.id}"
        
        messages = self.message_cache.get(cache_key, [])
        messages.append({'message': message, 'timestamp': current_time})
        
        # Mantener solo los últimos mensajes
        messages = messages[-10:]  # Mantener solo los últimos 10 mensajes
        
        self.message_cache.set(cache_key, messages, timeout=self.time_window.total_seconds())

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
        self.cache = cache
        self.cache_timeout = 300  # 5 minutos
        self.metrics = chatbot_metrics
        self.spam_detector = SpamDetector()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def process_intent(self, intent: str, message: str) -> Dict[str, Any]:
        """Procesa un intent específico."""
        try:
            # Verificar si el mensaje es spam
            if await self.spam_detector.is_spam(message):
                return {'response': "Por favor, no envíes mensajes repetidos o spam.", 'is_spam': True}

            # Obtener handler desde caché o inicializar nuevo
            handler_key = f"handler:{self.user.id}:{intent}"
            handler = self.cache.get(handler_key)
            
            if not handler:
                handler_class = self.handlers.get(intent)
                if not handler_class:
                    return {'response': "No se reconoció tu intención. ¿En qué puedo ayudarte?", 'is_error': True}
                
                handler = handler_class(self.user, intent, message, self.business_unit)
                self.cache.set(handler_key, handler, self.cache_timeout)

            # Procesar intent con métricas
            with self.metrics.measure_intent_processing_time(intent):
                response = await handler.handle()
                
            # Actualizar métricas
            self.metrics.increment_intent_count(intent)
            
            return response
            
        except Exception as e:
            logger.error(f"Error procesando intent {intent}: {str(e)}", exc_info=True)
            self.metrics.increment_intent_error_count(intent)
            return {'response': "Lo siento, hubo un error procesando tu mensaje.", 'is_error': True}
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
