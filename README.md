# Documentación del Sistema de Chatbot, Machine Learning, Scraping & Parser de Grupo huntRED
## Índice

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Integraciones de Plataformas](#integraciones-de-plataformas)
    - [WhatsApp](#whatsapp)
    - [Messenger](#messenger)
    - [Telegram](#telegram)
    - [Instagram](#instagram)
4. [Flujo de Conversación](#flujo-de-conversación)
5. [Manejo de Estados de Chat](#manejo-de-estados-de-chat)
6. [Envío de Mensajes](#envío-de-mensajes)
7. [Manejo de Errores y Logs](#manejo-de-errores-y-logs)
8. [Configuración y Despliegue](#configuración-y-despliegue)
9. [Pruebas](#pruebas)
10. [Mantenimiento](#mantenimiento)

---

## Introducción

Este documento describe la arquitectura, las funcionalidades y las integraciones del sistema de chatbot de Amigro.org. El chatbot está diseñado para interactuar con los usuarios a través de múltiples plataformas de mensajería, proporcionando asistencia en tiempo real, gestión de perfiles, búsqueda de vacantes laborales y más.

## Arquitectura del Sistema

El sistema de chatbot de Amigro.org está construido utilizando Django como framework principal, aprovechando la capacidad asíncrona de Python para manejar múltiples solicitudes simultáneamente. Las principales componentes incluyen:

- **Django Models:** Definen las estructuras de datos para usuarios, estados de chat, configuraciones de API, y flujos de conversación.
- **Integraciones de Plataformas:** Módulos dedicados para manejar la comunicación con diferentes plataformas de mensajería (WhatsApp, Messenger, Telegram, Instagram).
- **Servicios de Mensajería:** Funciones reutilizables para enviar mensajes, imágenes, botones y otros elementos interactivos.
- **ChatBotHandler:** Núcleo del chatbot que procesa los mensajes entrantes, determina las respuestas y gestiona el flujo de conversación.
- **Utilidades NLP:** Herramientas para análisis de texto, detección de intenciones y sentimientos.

## Integraciones de Plataformas

### WhatsApp

- **Archivo:** `/home/amigro/app/integrations/whatsapp.py`
- **Funciones Principales:**
    - `whatsapp_webhook`: Maneja la verificación del webhook y los mensajes entrantes.
    - `send_whatsapp_response`: Envía respuestas al usuario, incluyendo botones interactivos.
    - `send_whatsapp_buttons`: Envía botones de decisión (Sí/No) al usuario.

- **Configuraciones Clave:**
    - **WhatsAppAPI:** Modelo que almacena las credenciales y configuraciones necesarias para interactuar con la API de WhatsApp.

### Messenger

- **Archivo:** `/home/amigro/app/integrations/messenger.py`
- **Funciones Principales:**
    - `messenger_webhook`: Maneja la verificación del webhook y los mensajes entrantes.
    - `send_messenger_response`: Envía respuestas al usuario, incluyendo botones interactivos.
    - `send_messenger_buttons`: Envía botones de respuesta rápida al usuario.

- **Configuraciones Clave:**
    - **MessengerAPI:** Modelo que almacena las credenciales y configuraciones necesarias para interactuar con la API de Messenger.

### Telegram

- **Archivo:** `/home/amigro/app/integrations/telegram.py`
- **Funciones Principales:**
    - `telegram_webhook`: Maneja los mensajes entrantes y las configuraciones de webhook.
    - `send_telegram_response`: Envía respuestas al usuario, incluyendo botones interactivos.
    - `send_telegram_buttons`: Envía botones de respuesta rápida al usuario.

- **Configuraciones Clave:**
    - **TelegramAPI:** Modelo que almacena las credenciales y configuraciones necesarias para interactuar con la API de Telegram.

### Instagram

- **Archivo:** `/home/amigro/app/integrations/instagram.py`
- **Funciones Principales:**
    - `instagram_webhook`: Maneja la verificación del webhook y los mensajes entrantes.
    - `send_instagram_response`: Envía respuestas al usuario, incluyendo botones interactivos.
    - `send_instagram_buttons`: Envía botones de respuesta rápida al usuario.

- **Configuraciones Clave:**
    - **InstagramAPI:** Modelo que almacena las credenciales y configuraciones necesarias para interactuar con la API de Instagram.

## Flujo de Conversación

1. **Recepción del Mensaje:**
    - El usuario envía un mensaje a través de una plataforma soportada.
    - El webhook correspondiente recibe el mensaje y lo procesa.

2. **Procesamiento del Mensaje:**
    - `ChatBotHandler` analiza el mensaje utilizando herramientas NLP para detectar intenciones y entidades.
    - Basado en el análisis, determina la respuesta adecuada y el siguiente paso en el flujo de conversación.

3. **Envío de Respuesta:**
    - La respuesta es enviada al usuario a través de la plataforma correspondiente.
    - Si se requieren botones o elementos interactivos, se incluyen en el mensaje.

4. **Gestión del Estado de Chat:**
    - El estado de la conversación se almacena en `ChatState`, permitiendo mantener el contexto entre mensajes.

## Manejo de Estados de Chat

El modelo `ChatState` almacena información relevante sobre la conversación actual con cada usuario, incluyendo:

- **user_id:** Identificador único del usuario en la plataforma.
- **platform:** Plataforma de mensajería (WhatsApp, Messenger, etc.).
- **business_unit:** Unidad de negocio asociada.
- **current_question:** Pregunta actual en el flujo de conversación.
- **context:** Información adicional relevante para la conversación.

## Envío de Mensajes

Las funciones de envío de mensajes (`send_message`, `send_whatsapp_buttons`, `send_messenger_buttons`, etc.) están diseñadas para ser reutilizables y manejar diferentes tipos de contenido, incluyendo texto, imágenes y botones interactivos.

### Envío de Botones Interactivos

Los botones interactivos permiten a los usuarios responder rápidamente a través de opciones predefinidas, mejorando la experiencia de usuario y facilitando la navegación en el flujo de conversación.

## Manejo de Errores y Logs

El sistema utiliza el módulo `logging` para registrar eventos importantes, errores y información de depuración. Esto facilita el monitoreo y la resolución de problemas.

- **Niveles de Log:**
    - **INFO:** Información general sobre el funcionamiento del sistema.
    - **DEBUG:** Información detallada para depuración.
    - **WARNING:** Advertencias sobre situaciones inesperadas que no detienen el sistema.
    - **ERROR:** Errores que impiden la correcta ejecución de una función.
    - **CRITICAL:** Errores graves que pueden requerir intervención inmediata.

## Configuración y Despliegue

### Requisitos Previos

- **Python 3.8+**
- **Django 3.2+**
- **Dependencias Asíncronas:**
    - `httpx`
    - `asgiref`
    - `celery` (para tareas asíncronas en Telegram)
- **Configuraciones de API:** Asegúrate de tener las credenciales y tokens necesarios para cada plataforma de mensajería.

### Pasos de Configuración

1. **Renombrar Archivos Actuales:**
    - Antes de cargar los nuevos archivos, renombra los existentes añadiendo `_old` para preservarlos.
        ```bash
        mv /home/amigro/app/integrations/messenger.py /home/amigro/app/integrations/messenger_old.py
        mv /home/amigro/app/integrations/telegram.py /home/amigro/app/integrations/telegram_old.py
        mv /home/amigro/app/integrations/instagram.py /home/amigro/app/integrations/instagram_old.py
        ```

2. **Cargar los Nuevos Archivos:**
    - Reemplaza los archivos antiguos con los nuevos proporcionados anteriormente.

3. **Instalar Dependencias:**
    - Asegúrate de instalar todas las dependencias necesarias.
        ```bash
        pip install httpx asgiref celery
        ```

4. **Configurar Webhooks:**
    - Configura los webhooks en cada plataforma de mensajería para apuntar a los endpoints correspondientes de tu servidor.

5. **Migraciones de Base de Datos:**
    - Aplica las migraciones para asegurarte de que todos los modelos estén actualizados.
        ```bash
        python manage.py migrate
        ```

6. **Iniciar el Servidor:**
    - Inicia el servidor de Django y cualquier worker de Celery si estás utilizando tareas asíncronas.
        ```bash
        python manage.py runserver
        celery -A amigro worker --loglevel=info
        ```

## Pruebas

1. **Verificación de Webhooks:**
    - Asegúrate de que los webhooks estén correctamente configurados y que la verificación funcione sin errores.

2. **Envío de Mensajes de Prueba:**
    - Envía mensajes de prueba desde cada plataforma para verificar que el chatbot responde adecuadamente.

3. **Prueba de Botones Interactivos:**
    - Verifica que los botones interactivos se muestren correctamente y que las respuestas sean manejadas adecuadamente.

4. **Manejo de Errores:**
    - Prueba escenarios de errores, como mensajes vacíos o fallos en la API, para asegurar que el sistema maneja estos casos sin interrupciones.

## Mantenimiento

1. **Monitoreo de Logs:**
    - Revisa regularmente los logs para identificar y solucionar problemas.

2. **Actualización de Dependencias:**
    - Mantén las dependencias actualizadas para aprovechar mejoras y parches de seguridad.

3. **Mejoras Continuas:**
    - Añade nuevas funcionalidades y patrones de conversación según las necesidades de los usuarios y del negocio.

4. **Respaldo de Datos:**
    - Implementa estrategias de respaldo para asegurar que los datos importantes estén protegidos.

## Integraciones de Servicios

### `services.py`

Este módulo contiene funciones de utilidad para interactuar con servicios externos y realizar tareas reutilizables en todo el proyecto.

**Funciones Principales:**
- `send_message`: Envía mensajes a diferentes plataformas de mensajería.
- `send_email`: Envía correos electrónicos utilizando configuraciones SMTP.
- `reset_chat_state`: Reinicia el estado de chat de un usuario.
- `get_api_instance`: Obtiene configuraciones de API para plataformas específicas.
- Otras funciones de servicio necesarias.

### `chatbot.py`

Este módulo maneja la lógica central del chatbot, incluyendo el procesamiento de mensajes entrantes, gestión de estados de chat y determinación de respuestas basadas en el flujo de conversación.

**Funciones Principales:**
- `process_message`: Procesa mensajes recibidos y coordina respuestas.
- `handle_intents`: Maneja diferentes intenciones detectadas en los mensajes.
- `notify_employer`: Envía notificaciones específicas al empleador.
- Otras funciones relacionadas directamente con la interacción del chatbot.
---

## Conclusión

Con estas mejoras, tu sistema de chatbot debería ser más robusto, eficiente y fácil de mantener. La estructura modular y las funciones claras facilitan la adición de nuevas funcionalidades y la integración con más plataformas en el futuro. No dudes en realizar pruebas exhaustivas para asegurar que todo funcione según lo esperado y en mantener una documentación actualizada para facilitar el desarrollo continuo.

¡Éxito en tus pruebas y en la implementación del chatbot!



___________
# /home/amigro/app/chatbot.py
import logging
import asyncio
import re
from typing import Optional, Tuple, List, Dict, Any
from asgiref.sync import sync_to_async
from app.models import (
    ChatState, Pregunta, Person, FlowModel, Invitacion,
    MetaAPI, WhatsAppAPI, TelegramAPI, MessengerAPI,
    InstagramAPI, Interview, BusinessUnit
)
from app.vacantes import VacanteManager
from app.integrations.services import (
    send_message, send_options, send_menu, render_dynamic_content, send_image, 
    send_logo, send_email, reset_chat_state, get_api_instance
)
from app.integrations.whatsapp import send_whatsapp_decision_buttons  # Asegúrate de que esta función existe
from app.utils import analyze_text, clean_text, detect_intents, matcher, nlp  # Importa detect_intents
from django.core.cache import cache

# Inicializa el logger y Cache
logger = logging.getLogger(__name__)
CACHE_TIMEOUT = 600  # 10 minutes

class ChatBotHandler:
    async def process_message(self, platform: str, user_id: str, text: str, business_unit: BusinessUnit):
        """
        Procesa un mensaje entrante del usuario y gestiona el flujo de conversación.
        """
        logger.info(f"Processing message for {user_id} on {platform} for business unit {business_unit}")

        try:
            # Etapa 1: Preprocesamiento del Mensaje
            logger.info("Stage 1: Preprocessing the message")
            text = clean_text(text)
            analysis = analyze_text(text)
            intents = analysis.get("intents", [])
            entities = analysis.get("entities", {})
            if not isinstance(intents, list):
                logger.error(f"Invalid intents format: {intents}")
                intents = []
            cache_key = f"analysis_{user_id}"
            cache.set(cache_key, analysis, CACHE_TIMEOUT)
            logger.info(f"Message analysis cached with key {cache_key}")

            # Etapa 2: Inicialización del Contexto de Conversación
            logger.info("Stage 2: Initializing conversation context")
            logger.info(f"Initializing context for user_id {user_id}")
            event = await self.get_or_create_event(user_id, platform, business_unit)
            if not event:
                    logger.error(f"No se pudo crear el evento para el usuario {user_id}.")
                    await send_message(platform, user_id, "Error al inicializar el contexto. Inténtalo más tarde.", business_unit)
                    return
            logger.info(f"Event initialized: {event}")
            user, created = await self.get_or_create_user(user_id, event, {})
            logger.info(f"User fetched/created: {user}, Created: {created}")
            if not user:
                    logger.error(f"No se pudo crear o recuperar el usuario {user_id}.")
                    await send_message(platform, user_id, "Error al recuperar tu información. Inténtalo más tarde.", business_unit)
                    return
            context = self.build_context(user)
            logger.info(f"User context initialized: {context}")

            # Etapa 3: Manejo de Intents Conocidos
            logger.info("Stage 3: Handling known intents")
            if await self.handle_known_intents(intents, platform, user_id, event, business_unit):
                logger.info("Known intent handled, ending process_message")
                return

            # Etapa 4: Continuación del Flujo de Conversación
            logger.info("Stage 4: Continuing conversation flow")
            current_question = event.current_question
            if not current_question:
                first_question = await self.get_first_question(event.flow_model)
                if first_question:
                    event.current_question = first_question
                    await event.asave()
                    logger.info(f"Conversation started with the first question: {first_question.content}")
                    await send_message(platform, user_id, first_question.content, business_unit)
                else:
                    logger.error("No first question found in the flow model")
                    await send_message(platform, user_id, "Lo siento, no se pudo iniciar la conversación en este momento.", business_unit)
                return

            # Etapa 5: Procesamiento de la Respuesta del Usuario
            logger.info("Stage 5: Processing user's response")
            response, options = await self.determine_next_question(event, text, analysis, context)

            # Etapa 6: Guardar estado y enviar respuesta
            logger.info("Stage 6: Saving updated chat state and sending response")
            await event.asave()
            await self.send_response(platform, user_id, response, business_unit, options)
            logger.info(f"Response sent to user {user_id}")

            # Etapa 7: Manejo de Desviaciones en la Conversación
            logger.info("Stage 7: Handling conversation deviations")
            if await self.detect_and_handle_deviation(event, text, analysis):
                logger.info("Deviation handled, ending process_message")
                return

            # Etapa 8: Verificación del Perfil del Usuario
            logger.info("Stage 8: Verifying user profile")
            profile_check = await self.verify_user_profile(user)
            if profile_check:
                await send_message(platform, user_id, profile_check, business_unit)
                logger.info("User profile incomplete, notification sent")
                return

        except Exception as e:
            logger.error(f"Error processing message for {user_id}: {e}", exc_info=True)
            await send_message(platform, user_id, "Ha ocurrido un error. Por favor, inténtalo de nuevo más tarde.", business_unit)
# METODOS AUXILIARES
# Etapa 1: Preprocesamiento del Mensaje
# Etapa 2: Inicialización del Contexto de Conversación
# Etapa 3: Manejo de Intents Conocidos
# Etapa 4: Continuación del Flujo de Conversación
# Etapa 5: Procesamiento de la Respuesta del Usuario
# Etapa 6: Guardar estado y enviar respuesta
# Etapa 7: Manejo de Desviaciones en la Conversación
# Etapa 8: Verificación del Perfil del Usuario
# -------------------------------------------
# Etapa 1: Preprocesamiento del Mensaje
# -------------------------------------------
# Métodos auxiliares para esta etapa
# (No se requieren métodos adicionales aquí)
# -------------------------------------------
# Etapa 2: Inicialización del Contexto de Conversación
# -------------------------------------------
    async def get_or_create_event(self, user_id: str, platform: str, flow_model: FlowModel) -> ChatState:
        try:
            chat_state, created = await sync_to_async(ChatState.objects.get_or_create)(
                user_id=user_id,
                defaults={
                    'platform': platform,
#                    'business_unit': flow_model.unit if hasattr(flow_model, 'unit') else None,   #'business_unit': flow_model.business_unit if flow_model else None,
#                    'flow_model': flow_model,
                    'current_question': None
                }
            )
            if created:
                logger.debug(f"ChatState creado para usuario {user_id}")
            else:
                logger.debug(f"ChatState obtenido para usuario {user_id}")
            return chat_state
        except Exception as e:
            logger.error(f"Error en get_or_create_event para usuario {user_id}: {e}", exc_info=True)
            raise e

    async def get_or_create_user(self, user_id: str, event: ChatState, analysis: dict) -> Tuple[Person, bool]:
        try:
            entities = analysis.get('entities', {})
            name = entities.get('name') or event.platform or 'Usuario'

            user, created = await sync_to_async(Person.objects.get_or_create)(
                phone=user_id,
                defaults={'name': name}
            )
            if created:
                logger.debug(f"Persona creada: {user}")
            else:
                logger.debug(f"Persona obtenida: {user}")
            return user, created
        except Exception as e:
            logger.error(f"Error en get_or_create_user para usuario {user_id}: {e}", exc_info=True)
            raise e

    def build_context(self, user: Person) -> dict:
        """
        Construye el contexto de la conversación basado en la información del usuario.
        
        :param user: Instancia de Person.
        :return: Diccionario de contexto.
        """
        context = {
            'user_name': user.name,
            'user_phone': user.phone,
            # Agrega más campos según sea necesario
        }
        logger.debug(f"Contexto construido para usuario {user.phone}: {context}")
        return context
# -------------------------------------------
# Etapa 3: Manejo de Intents Conocidos
# -------------------------------------------
    async def handle_known_intents(
        self, intents: List[dict], platform: str, user_id: str, event: ChatState, business_unit
    ) -> bool:
        for intent in intents:
            intent_name = intent.get('name')
            confidence = intent.get('confidence', 0)
            logger.debug(f"Intent detectado: {intent_name} con confianza {confidence}")
            if confidence < 0.5:
                continue  # Ignorar intents con baja confianza

            if intent == "saludo":
                # Generar mensaje dinámico basado en la unidad de negocio
                greeting_message = f"Hola, buenos días. ¿Quieres conocer más acerca de {business_unit.name}?"
                
                # Enviar mensaje con botones de quick-reply
                quick_replies = [{"title": "Sí"}, {"title": "No"}]
                await send_whatsapp_decision_buttons(
                    user_id=user_id,
                    message=greeting_message,
                    decision_buttons=quick_replies,
                    api_token=business_unit.whatsapp_api_token,
                    phone_id=business_unit.phoneID,
                    v_api=business_unit.whatsapp_api_version
                )
                logger.info(f"Intent 'saludo' manejado para usuario {user_id}")
                return True
            elif intent_name == 'despedida':
                await send_message(platform, user_id, "¡Hasta luego! Si necesitas más ayuda, no dudes en contactarnos.", business_unit)
                logger.info(f"Intent 'despedida' manejado para usuario {user_id}")
                # Opcional: Resetear el estado del chat
                await self.reset_chat_state(user_id)
                return True
            elif intent_name == 'iniciar_conversacion':
                # Reiniciar el flujo de conversación
                event.current_question = None
                await event.asave()
                await send_message(platform, user_id, "¡Claro! Empecemos de nuevo. ¿En qué puedo ayudarte?", business_unit)
                logger.info(f"Intent 'iniciar_conversacion' manejado para usuario {user_id}")
                return True
            elif intent_name == 'menu':
                # Acceder al menú persistente
                await self.handle_persistent_menu(event)
                logger.info(f"Intent 'menu' manejado para usuario {user_id}")
                return True
            elif intent_name == 'solicitar_ayuda_postulacion':
                # Manejar la solicitud de ayuda para postulación
                ayuda_message = "Claro, puedo ayudarte con el proceso de postulación. ¿Qué necesitas saber específicamente?"
                await send_message(platform, user_id, ayuda_message, business_unit)
                logger.info(f"Intent 'solicitar_ayuda_postulacion' manejado para usuario {user_id}")
                return True
            elif intent_name == 'consultar_estatus':
                # Manejar la consulta de estatus de aplicación
                estatus_message = "Para consultar el estatus de tu aplicación, por favor proporciona tu número de aplicación o correo electrónico asociado."
                await send_message(platform, user_id, estatus_message, business_unit)
                logger.info(f"Intent 'consultar_estatus' manejado para usuario {user_id}")
                return True
            # Agrega más intents conocidos y sus manejadores aquí

        return False  # No se manejó ningún intent conocido

    async def process_decision_response(user_response, event, platform, user_id, business_unit): #Para iniciar la conversacion con un quick reply
        if user_response.lower() in ["sí", "si"]:
            # Obtener la primera pregunta del flujo
            first_question = await self.get_first_question(event.flow_model)
            if first_question:
                event.current_question = first_question
                await event.asave()

                # Enviar la primera pregunta
                await send_message(
                    platform=platform,
                    user_id=user_id,
                    message=first_question.content,
                    business_unit=business_unit
                )
            else:
                await send_message(
                    platform=platform,
                    user_id=user_id,
                    message="Lo siento, no puedo continuar en este momento. Intenta más tarde.",
                    business_unit=business_unit
                )
        elif user_response.lower() == "no":
            await send_message(
                platform=platform,
                user_id=user_id,
                message="Entendido, si necesitas más información, no dudes en escribirnos.",
                business_unit=business_unit
            )
            
    async def reset_chat_state(self, user_id: str):
        """
        Resetea el estado del chat para un usuario específico.
        
        :param user_id: Identificador único del usuario.
        """
        await reset_chat_state(user_id=user_id)
        logger.info(f"Chat state reset for user {user_id}")
# -------------------------------------------
# Etapa 4: Continuación del Flujo de Conversación
# -------------------------------------------
    async def get_first_question(self, flow_model: FlowModel) -> Optional[Pregunta]:
        """
        Obtiene la primera pregunta del FlowModel.
        
        :param flow_model: Instancia de FlowModel.
        :return: Instancia de Pregunta o None si no existe.
        """
        first_question = await sync_to_async(flow_model.preguntas.order_by('order').first)()
        if first_question:
            logger.debug(f"Primera pregunta obtenida: {first_question.content}")
        else:
            logger.debug("No se encontró la primera pregunta en el FlowModel.")
        return first_question

# -------------------------------------------
# Etapa 5: Procesamiento de la Respuesta del Usuario
# -------------------------------------------
    async def determine_next_question(self, event: ChatState, user_message: str, analysis: dict, context: dict) -> Tuple[Optional[str], List]:
        current_question = event.current_question
        logger.info(f"Procesando la pregunta actual: {current_question.content}")

        try:
            # 1. Manejar acciones basadas en action_type
            if current_question.action_type:
                response, options = await self._handle_action_type(event, current_question, context)
                return response, options

            # 2. Manejar respuestas de botones
            if current_question.botones_pregunta.exists():
                response, options = await self._handle_button_response(event, current_question, user_message, context)
                return response, options

            # 3. Manejar diferentes input_type
            input_type_handlers = {
                'skills': self._handle_skills_input,
                'select_job': self._handle_select_job_input,
                'schedule_interview': self._handle_schedule_interview_input,
                'confirm_interview_slot': self._handle_confirm_interview_slot_input,
                'finalizar_perfil': self._handle_finalize_profile_input,
                'confirm_recap': self._handle_confirm_recap_input,
                # Agrega más input_types si es necesario
            }

            handler = input_type_handlers.get(current_question.input_type)
            if handler:
                response, options = await handler(event, current_question, user_message, context)
                return response, options

            # 4. Flujo estándar: avanzar a la siguiente pregunta
            next_question = await self.get_next_question(current_question, user_message)
            if next_question:
                event.current_question = next_question
                await event.asave()
                response = render_dynamic_content(next_question.content, context)
                return response, []
            else:
                return "No hay más preguntas en este flujo.", []

        except Exception as e:
            logger.error(f"Error determinando la siguiente pregunta: {e}", exc_info=True)
            return "Ha ocurrido un error al procesar tu respuesta. Por favor, inténtalo de nuevo más tarde.", []
    # Métodos auxiliares para cada input_type
    async def _handle_skills_input(self, event, current_question, user_message, context):
        # Asignar habilidades al usuario
        user = context.get('user')
        if not user:
            user = await sync_to_async(Person.objects.get)(phone=event.user_id)
            context['user'] = user

        user.skills = user_message
        await sync_to_async(user.save)()

        vacante_manager = VacanteManager(context)
        recommended_jobs = await sync_to_async(vacante_manager.match_person_with_jobs)(user)

        if recommended_jobs:
            response = "Aquí tienes algunas vacantes que podrían interesarte:\n"
            for idx, (job, score) in enumerate(recommended_jobs[:5]):
                response += f"{idx + 1}. {job['title']} en {job['company']}\n"
            response += "Por favor, ingresa el número de la vacante que te interesa."
            event.context = {'recommended_jobs': recommended_jobs}
            await event.asave()
            return response, []
        else:
            response = "Lo siento, no encontré vacantes que coincidan con tu perfil."
            return response, []

    async def _handle_select_job_input(self, event, current_question, user_message, context):
        try:
            job_index = int(user_message.strip()) - 1
        except ValueError:
            return "Por favor, ingresa un número válido.", []

        recommended_jobs = event.context.get('recommended_jobs')
        if recommended_jobs and 0 <= job_index < len(recommended_jobs):
            selected_job = recommended_jobs[job_index]
            event.context['selected_job'] = selected_job
            # Obtener la pregunta 'schedule_interview' relacionada al flujo actual
            next_question = await self.get_question_by_option(event.flow_model, 'schedule_interview')
            if next_question:
                event.current_question = next_question
                await event.asave()
                return next_question.content, []
            else:
                logger.error("Pregunta 'schedule_interview' no encontrada.")
                return "No se pudo continuar con el proceso.", []
        else:
            return "Selección inválida.", []

    async def _handle_schedule_interview_input(self, event, current_question, user_message, context):
        selected_job = event.context.get('selected_job')
        if not selected_job:
            return "No se encontró la vacante seleccionada.", []

        vacante_manager = VacanteManager(context)
        available_slots = await sync_to_async(vacante_manager.get_available_slots)(selected_job)
        if available_slots:
            response = "Estos son los horarios disponibles para la entrevista:\n"
            for idx, slot in enumerate(available_slots):
                response += f"{idx + 1}. {slot}\n"
            response += "Por favor, selecciona el número del horario que prefieras."
            event.context['available_slots'] = available_slots
            await event.asave()
            return response, []
        else:
            return "No hay horarios disponibles.", []

    async def _handle_confirm_interview_slot_input(self, event, current_question, user_message, context):
        try:
            slot_index = int(user_message.strip()) - 1
        except ValueError:
            return "Por favor, ingresa un número válido.", []

        available_slots = event.context.get('available_slots')
        selected_job = event.context.get('selected_job')
        user = context.get('user')
        if available_slots and 0 <= slot_index < len(available_slots):
            selected_slot = available_slots[slot_index]
            vacante_manager = VacanteManager(context)
            success = await sync_to_async(vacante_manager.book_interview_slot)(selected_job, selected_slot, user)
            if success:
                response = f"Has reservado tu entrevista en el horario: {selected_slot}."
                await event.asave()
                return response, []
            else:
                return "No se pudo reservar el horario, por favor intenta nuevamente.", []
        else:
            return "Selección inválida. Por favor, intenta nuevamente.", []

    async def _handle_finalize_profile_input(self, event, current_question, user_message, context):
        user = context.get('user')
        if not user:
            user = await sync_to_async(Person.objects.get)(phone=event.user_id)
            context['user'] = user

        recap_message = await self.recap_information(user)
        await send_message(event.platform, event.user_id, recap_message, event.business_unit)
        # Obtener la pregunta 'confirm_recap' relacionada al flujo actual
        next_question = await self.get_question_by_option(event.flow_model, 'confirm_recap')
        if next_question:
            event.current_question = next_question
            await event.asave()
            return next_question.content, []
        else:
            logger.error("Pregunta 'confirm_recap' no encontrada.")
            return "No se pudo continuar con el proceso.", []

    async def _handle_confirm_recap_input(self, event, current_question, user_message, context):
        if user_message.strip().lower() in ['sí', 'si', 's']:
            response = "¡Perfecto! Continuemos."
            # Obtener la pregunta 'next_step' relacionada al flujo actual
            next_question = await self.get_question_by_option(event.flow_model, 'next_step')
            if next_question:
                event.current_question = next_question
                await event.asave()
                return response, []
            else:
                logger.error("Pregunta 'next_step' no encontrada.")
                return "No se pudo continuar con el proceso.", []
        else:
            await self.handle_correction_request(event, user_message)
            return None, []

    # Método auxiliar para obtener una pregunta por su opción
    async def get_question_by_option(self, flow_model, option):
        question = await sync_to_async(Pregunta.objects.filter(flow_model=flow_model, option=option).first)()
        return question

# -------------------------------------------
# Etapa 6: Guardar estado y enviar respuesta
# -------------------------------------------
    async def send_response(self, platform: str, user_id: str, response: str, business_unit, options: Optional[List] = None):
        """
        Envía una respuesta al usuario, incluyendo opciones si las hay.
        
        :param platform: Plataforma desde la cual se enviará el mensaje.
        :param user_id: Identificador único del usuario.
        :param response: Mensaje a enviar.
        :param business_unit: Instancia de BusinessUnit asociada.
        :param options: Lista de opciones para enviar junto al mensaje.
        """
        logger.debug(f"Preparando para enviar respuesta al usuario {user_id}: {response} con opciones: {options}")
        
        # Obtener el phone_id desde la configuración de la BusinessUnit
        whatsapp_api = await get_api_instance('whatsapp', business_unit)
        if not whatsapp_api:
            logger.error(f"No se encontró configuración de WhatsAppAPI para la unidad de negocio {business_unit}.")
            return
        
        phone_id = whatsapp_api.phoneID
        
        # Enviar el mensaje
        await send_whatsapp_message(user_id, response, phone_id, image_url=None, options=options)
        
        logger.info(f"Respuesta enviada al usuario {user_id}")

# -------------------------------------------
# Etapa 7: Manejo de Desviaciones en la Conversación
# -------------------------------------------
    async def detect_and_handle_deviation(self, event, text, analysis):
        # Define deviation thresholds and strategies
        if self.is_significant_deviation(event, text, analysis):
            await self.handle_user_deviation(event, text)
            return True
        return False

    def is_significant_deviation(self, event, text, analysis):
        # Implement deviation detection logic
        current_intent = event.current_question.intent if event.current_question else None
        detected_intents = analysis.get('intents', [])
        
        # Compare current context with detected intents
        deviation_score = self.calculate_deviation_score(current_intent, detected_intents)
        
        return deviation_score > DEVIATION_THRESHOLD

    def calculate_deviation_score(self, current_intent, detected_intents):
        # Custom scoring mechanism to assess conversation deviation
        pass

    async def handle_user_deviation(self, event, user_message):
        # Intelligent rerouting strategies
        strategies = [
            self.offer_menu_reset,
            self.provide_context_clarification,
            self.suggest_alternative_paths
        ]
        
        for strategy in strategies:
            if await strategy(event, user_message):
                break
    
    async def offer_menu_reset(self, event, user_message):
        # Offer to return to main menu or restart flow
        reset_options = [
            "Volver al menú principal",
            "Reiniciar conversación",
            "Continuar con el flujo actual"
        ]
        await send_options(event.platform, event.user_id, reset_options)
        return True

    async def provide_context_clarification(self, event, user_message):
        # Help user understand current conversation context
        context_message = (
            f"Estamos actualmente en: {event.current_question.content}\n"
            "¿Deseas continuar o necesitas ayuda?"
        )
        await send_message(event.platform, event.user_id, context_message)
        return True

    async def suggest_alternative_paths(self, event, user_message):
        # Suggest related conversation paths based on detected intent
        related_flows = self.find_related_flows(user_message)
        if related_flows:
            await send_options(event.platform, event.user_id, related_flows)
            return True
        return False
    
# -------------------------------------------
# Etapa 8: Verificación del Perfil del Usuario
# -------------------------------------------
    async def send_profile_completion_email(self, user_id: str, context: dict):
        """
        Envía un correo electrónico para completar el perfil del usuario.
        
        :param user_id: Identificador único del usuario.
        :param context: Contexto de la conversación.
        """
        # Implementa la lógica para enviar el correo electrónico
        # Esto podría incluir llamar a send_email desde services.py
        # Ejemplo:
        from app.integrations.services import send_email

        # Obtener el usuario para obtener su email
        try:
            user = await sync_to_async(Person.objects.get)(phone=user_id)
            email = user.email
            if email:
                subject = "Completa tu perfil en Amigro.org"
                body = f"Hola {user.name},\n\nPor favor completa tu perfil en Amigro.org para continuar."
                await send_email(
                    business_unit_name=user.business_unit.name,
                    subject=subject,
                    to_email=email,
                    body=body
                )
                logger.info(f"Correo de completación de perfil enviado a {email}")
            else:
                logger.warning(f"Usuario {user_id} no tiene email registrado.")
        except Person.DoesNotExist:
            logger.error(f"No se encontró usuario con phone {user_id} para enviar correo de completación de perfil.")
        except Exception as e:
            logger.error(f"Error enviando correo de completación de perfil a {user_id}: {e}", exc_info=True)

    async def verify_user_profile(self, user: Person) -> Optional[str]:
        """
        Verifica si el perfil del usuario está completo.
        
        :param user: Instancia de Person.
        :return: Mensaje de error si el perfil está incompleto, de lo contrario None.
        """
        required_fields = ['name', 'apellido_paterno', 'skills', 'ubicacion', 'email']
        missing_fields = [field for field in required_fields if not getattr(user, field, None)]
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            return f"Para continuar, completa estos datos: {fields_str}."
        logger.debug(f"Perfil completo para usuario {user.phone}.")
        return None
# -------------------------------------------
# Métodos Auxiliares
# -------------------------------------------
    async def get_next_question(self, current_question: Pregunta, user_message: str) -> Optional[Pregunta]:
        """
        Determina la siguiente pregunta basada en la respuesta del usuario.
        
        :param current_question: Pregunta actual en el flujo.
        :param user_message: Respuesta del usuario.
        :return: Siguiente Pregunta o None si el flujo termina.
        """
        # Lógica para determinar la siguiente pregunta
        # Puede ser basada en las opciones seleccionadas, entidades extraídas, etc.
        # Aquí un ejemplo simple basado en la respuesta "sí" o "no"

        response = user_message.strip().lower()
        if response in ['sí', 'si', 's']:
            next_question = current_question.next_si
        else:
            next_question = current_question.next_no

        if next_question:
            logger.debug(f"Siguiente pregunta basada en la respuesta '{response}': {next_question.content}")
        else:
            logger.debug("No hay siguiente pregunta definida en el flujo.")
        return next_question

    async def _handle_action_type(
            self, event: ChatState, current_question: Pregunta, context: dict
        ) -> Tuple[str, List]:
        """
        Maneja preguntas que requieren realizar una acción específica en lugar de continuar el flujo.
        
        :param event: Instancia de ChatState.
        :param current_question: Pregunta actual.
        :param context: Contexto de la conversación.
        :return: Respuesta y opciones.
        """
        # Implementa la lógica para manejar diferentes tipos de acciones
        # Por ejemplo, enviar un correo electrónico, iniciar un proceso, etc.
        # Este es un ejemplo genérico
        action = current_question.action_type
        logger.info(f"Handling action type '{action}' para pregunta {current_question.id}")
        
        if action == 'send_email':
            # Implementa la lógica para enviar un correo electrónico
            await self.send_profile_completion_email(event.user_id, context)
            response = "Te hemos enviado un correo electrónico con más información."
            return response, []
        elif action == 'start_process':
            # Implementa otra acción
            response = "Estamos iniciando el proceso solicitado."
            return response, []
        else:
            logger.warning(f"Tipo de acción desconocida: {action}")
            response = "Ha ocurrido un error al procesar tu solicitud."
            return response, []

    async def _handle_button_response(
            self, event: ChatState, current_question: Pregunta, user_message: str, context: dict
        ) -> Tuple[str, List]:
        """
        Maneja respuestas a preguntas con botones.
        
        :param event: Instancia de ChatState.
        :param current_question: Pregunta actual.
        :param user_message: Respuesta del usuario.
        :param context: Contexto de la conversación.
        :return: Respuesta y opciones.
        """
        # Suponiendo que los botones están definidos y se esperan respuestas específicas
        # Puedes mapear los títulos de los botones a acciones o siguientes preguntas
        logger.info(f"Manejando respuesta de botón: {user_message}")
        button = await sync_to_async(current_question.botones_pregunta.filter(name__iexact=user_message).first)()
        
        if button:
            next_question = button.next_question
            if next_question:
                event.current_question = next_question
                await event.asave()
                response = render_dynamic_content(next_question.content, context)
                return response, []
            else:
                # Si no hay siguiente pregunta, finalizar el flujo o realizar otra acción
                await send_message(event.platform, event.user_id, "Gracias por tu participación.", event.business_unit)
                event.current_question = None
                await event.asave()
                return "Gracias por tu participación.", []
        else:
            logger.warning(f"No se encontró botón correspondiente para la respuesta: {user_message}")
            response = "No entendí tu selección. Por favor, elige una opción válida."
            return response, []

    async def handle_persistent_menu(self, event):
        user = await sync_to_async(Person.objects.get)(phone=event.user_id)
        context = {
            'name': user.name or ''
        }
        response = f"Aquí tienes el menú principal, {context['name']}:"
        await send_menu(event.platform, event.user_id)
        return response, []
# -------------------------------------------
# Funciones bajo revisión en otros archivos para ver si se eliminan
# -------------------------------------------
# Estas funciones pueden ser eliminadas si no se utilizan en otros archivos.
# He revisado el archivo tasks.py que proporcionaste y encontré que la función
    async def notify_interviewer(self, interview):
        """
        Notifica al entrevistador que el candidato ha confirmado su asistencia.
        """
        job = interview.job
        interviewer = interview.interviewer  # Asegúrate de que este campo existe
        interviewer_phone = job.whatsapp or interviewer.phone  # WhatsApp del entrevistador
        interviewer_email = job.email or interviewer.email     # Email del entrevistador

        message = (
            f"El candidato {interview.person.name} ha confirmado su asistencia a la entrevista para la posición {job.title}.\n"
            f"Fecha de la entrevista: {interview.interview_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Tipo de entrevista: {'Presencial' if interview.interview_type == 'presencial' else 'Virtual'}"
        )
        try:
            # Enviar notificación por WhatsApp
            if interviewer_phone:
                await send_message('whatsapp', interviewer_phone, message)
                logger.info(f"Notificación enviada al entrevistador vía WhatsApp: {interviewer_phone}")

            # Enviar notificación por correo electrónico
            if interviewer_email:
                subject = f"Confirmación de asistencia para {job.title}"
                await send_email(
                    business_unit_name=job.business_unit.name,
                    subject=subject,
                    to_email=interviewer_email,  # Asegurado que el parámetro es 'to_email'
                    body=message
                )
                logger.info(f"Notificación enviada al entrevistador vía email: {interviewer_email}")

        except Exception as e:
            logger.error(f"Error enviando notificación al entrevistador: {e}")
# `notify_interviewer` es llamada desde tasks.py. Por lo tanto, esa función debe mantenerse.

    async def process_user_message(self, event, text, analysis, context):
        """
        Procesa el mensaje del usuario y determina la respuesta.

        :param event: Instancia de ChatState.
        :param text: Mensaje del usuario.
        :param analysis: Resultado del análisis NLP.
        :param context: Contexto de la conversación.
        :return: Respuesta y opciones.
        """
        try:
            current_question = event.current_question

            if not current_question:
                return "No hay una pregunta actual en el flujo.", []

            # Determine the next question or action
            response, options = await self.determine_next_question(
                event, text, analysis, context
            )
            return response, options
        except Exception as e:
            logger.error(f"Error processing user message in process_user_message: {e}", exc_info=True)
            return "Ha ocurrido un error al procesar tu mensaje. Por favor, intenta nuevamente.", []

    def get_flow_model(self, business_unit):
            """
            Obtiene el FlowModel asociado a la unidad de negocio.
            """
            try:
                return FlowModel.objects.filter(business_unit=business_unit).first()
            except Exception as e:
                logger.error(f"Error obteniendo FlowModel: {e}")
                return None
        
    async def recap_information(self, user):
        """
        Proporciona un resumen de la información del usuario y le permite hacer ajustes.

        :param user: Instancia de Person.
        :return: Mensaje de recapitulación.
        """
        recap_message = (
            f"Recapitulación de tu información:\n"
            f"Nombre: {user.name}\n"
            f"Apellido Paterno: {user.apellido_paterno}\n"
            f"Apellido Materno: {user.apellido_materno}\n"
            f"Fecha de Nacimiento: {user.fecha_nacimiento}\n"
            f"Sexo: {user.sexo}\n"
            f"Nacionalidad: {user.nationality}\n"
            f"Permiso de Trabajo: {user.permiso_trabajo}\n"
            f"CURP: {user.curp}\n"
            f"Ubicación: {user.ubicacion}\n"
            f"Experiencia Laboral: {user.work_experience}\n"
            f"Nivel Salarial Esperado: {user.nivel_salarial}\n\n"
            "¿Es correcta esta información? Responde 'Sí' o 'No'."
        )
        return recap_message

    async def handle_correction_request(self, event, user_response):
        """
        Permite que el usuario corrija su información tras la recapitulación.

        :param event: Instancia de ChatState.
        :param user_response: Respuesta del usuario.
        """
        correction_message = "Por favor, indica qué dato deseas corregir (e.g., 'nombre', 'email')."
        await self.send_response(event.platform, event.user_id, correction_message)
        event.awaiting_correction = True
        await event.asave()

    async def update_user_information(self, user, user_input):
        """
        Actualiza la información del usuario basada en la entrada de corrección.

        :param user: Instancia de Person.
        :param user_input: Entrada del usuario para actualizar datos.
        """
        field_mapping = {
            "nombre": "name",
            "apellido paterno": "apellido_paterno",
            "apellido materno": "apellido_materno",
            "nacionalidad": "nationality",
            "email": "email",
            "ubicación": "ubicacion",
            "experiencia laboral": "work_experience",
            "nivel salarial": "nivel_salarial",
        }
        try:
            field, new_value = user_input.split(':', 1)
            field = field_mapping.get(field.strip().lower())
            if field:
                setattr(user, field, new_value.strip())
                await user.asave()
            else:
                logger.info(f"Campo no encontrado para actualizar: {user_input}")
        except ValueError:
            logger.warning(f"Entrada de usuario inválida para actualización: {user_input}")

    async def invite_known_person(self, referrer, name, apellido, phone_number):
        """
        Invita a una persona conocida vía WhatsApp y crea un pre-registro.

        :param referrer: Usuario que refiere.
        :param name: Nombre del invitado.
        :param apellido: Apellido del invitado.
        :param phone_number: Número de teléfono del invitado.
        :return: Instancia de Person creada o existente.
        """
        invitado, created = await Person.objects.aget_or_create(
            phone=phone_number,
            defaults={'name': name, 'apellido_paterno': apellido},
        )

        await Invitacion.objects.acreate(referrer=referrer, invitado=invitado)

        if created:
            mensaje = (
                f"Hola {name}, has sido invitado por {referrer.name} a unirte a Amigro.org. "
                "¡Encuentra empleo en México de manera segura, gratuita e incluso podemos asesorarte en temas migrantes!"
            )
            await send_message("whatsapp", phone_number, mensaje)

        return invitado
# Métodos usados al momento de aplicar, agendar y enviar invitaciones
# Revisé el archivo tasks.py y encontré que `notify_interviewer` es utilizado en `notify_interviewer_task`
# Por lo tanto, la función `notify_interviewer` debe mantenerse.
    async def _get_next_main_question(self, event, current_question):
        return await sync_to_async(lambda: current_question.next_si)()

    async def _handle_whatsapp_template(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_message(
            event.platform, event.user_id, f"Enviando template: {current_question.option}"
        )
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_url(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_message(event.platform, event.user_id, "Aquí tienes el enlace:")
        await send_message(event.platform, event.user_id, current_question.content)
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_image(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_message(event.platform, event.user_id, "Aquí tienes la imagen:")
        await send_image(event.platform, event.user_id, current_question.content)
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_logo(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        await send_logo(event.platform, event.user_id)
        return await self._advance_to_next_question(event, current_question, context)

    async def _handle_yes_no_decision(
        self, event, current_question, context
    ) -> Tuple[None, List]:
        from app.integrations.whatsapp import send_whatsapp_decision_buttons

        decision_buttons = [{"title": "Sí"}, {"title": "No"}]
        whatsapp_api = await WhatsAppAPI.objects.afirst()
        await send_whatsapp_decision_buttons(
            event.user_id,
            current_question.content,
            decision_buttons,
            whatsapp_api.api_token,
            whatsapp_api.phoneID,
            whatsapp_api.v_api,
        )
        return None, []

    async def _handle_no_response_required(self, event, current_question, context) -> Tuple[Optional[str], List]:
        await self.send_response(event.platform, event.user_id, current_question.content)
        await asyncio.sleep(3)
        next_question = await sync_to_async(lambda: current_question.next_si)()
        if next_question:
            response = render_dynamic_content(next_question.content, context)
            return response, []
        else:
            return "No hay más preguntas en este flujo.", []
        
    async def _handle_multi_select(self, event, current_question, user_message: str, context) -> Tuple[Optional[str], List]:
        selected_options = [option.strip().lower() for option in user_message.split(',')]
        valid_options = []
        for option in selected_options:
            selected_button = await sync_to_async(
                lambda: current_question.botones_pregunta.filter(name__iexact=option).first()
            )()
            if selected_button:
                valid_options.append(selected_button.name)
            else:
                return "Opción no válida. Selecciona una opción válida.", []

        return await self._advance_to_next_question(event, current_question, context)

    async def _advance_to_next_question(
        self, event, current_question, context
    ) -> Tuple[str, List]:
        next_question = current_question.next_si
        if next_question:
            event.current_question = next_question
            await event.asave()
            response = render_dynamic_content(next_question.content, context)
            return response, []
        else:
            return "No hay más preguntas en este flujo.", []
# Metodos usados al momento de aplicar, agendar y enviar invitaciones
    async def handle_new_job_position(self, event):
        """
        Procesa la creación de una nueva posición laboral y envía la confirmación al usuario.

        :param event: Instancia de ChatState.
        """
        job_data = event.data  # Aquí recibimos los datos de la vacante recogidos en el flujo

        # Llamar a la función para procesar la vacante y crearla en WordPress
        result = await procesar_vacante(job_data)

        # Verificar el resultado y notificar al usuario
        if result["status"] == "success":
            await send_message(
                event.platform,
                event.user_id,
                "La vacante ha sido creada exitosamente en nuestro sistema.",
            )
        else:
            await send_message(
                event.platform,
                event.user_id,
                "Hubo un problema al crear la vacante. Por favor, inténtalo de nuevo.",
            )
            
    async def request_candidate_location(self, event, interview):
        """
        Solicita al candidato que comparta su ubicación antes de la entrevista, solo si es presencial.
        """
        if interview.interview_type != 'presencial':
            logger.info(f"No se solicita ubicación porque la entrevista es virtual para ID: {interview.id}")
            return

        message = (
            "Hola, para confirmar tu asistencia a la entrevista presencial, por favor comparte tu ubicación actual. "
            "Esto nos ayudará a verificar que estás en el lugar acordado."
        )
        await send_message(event.platform, event.user_id, message)

    async def handle_candidate_confirmation(self, platform, user_id, user_message):
        """
        Procesa la confirmación del candidato y guarda la información de ubicación si es presencial.
        Notifica al entrevistador sobre la confirmación del candidato.
        """
        person = await sync_to_async(Person.objects.get)(phone=user_id)
        interview = await sync_to_async(Interview.objects.filter)(person=person).first()

        if not interview or interview.candidate_confirmed:
            return

        if user_message.lower() in ['sí', 'si', 'yes']:
            interview.candidate_confirmed = True
            message = "¡Gracias por confirmar tu asistencia!"

            # Si es presencial, solicitar ubicación
            if interview.interview_type == 'presencial' and not interview.candidate_latitude:
                message += "\nPor favor, comparte tu ubicación actual para validar que estás en el lugar correcto."
            else:
                message += "\nTe deseamos mucho éxito en tu entrevista."

            await send_message(platform, user_id, message)
            await sync_to_async(interview.save)()

            # Notificar al entrevistador
            await self.notify_interviewer(interview)
        else:
            await send_message(platform, user_id, "Por favor, confirma tu asistencia respondiendo con 'Sí'.")
            
_____________________
# /home/amigro/app/integrations/services.py

import logging
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.cache import cache
from asgiref.sync import sync_to_async
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from langdetect import detect, DetectorFactory
from app.models import (
    WhatsAppAPI, TelegramAPI, InstagramAPI, MessengerAPI, MetaAPI, BusinessUnit, ConfiguracionBU,
    ChatState, Person, FlowModel, Pregunta
)
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 600  # 10 minutos
AMIGRO_VERIFY_TOKEN = "amigro_secret_token"
DetectorFactory.seed = 0  # Para resultados consistentes

# Dictionary mapping platforms to their respective send functions
platform_send_functions = {
    'telegram': 'send_telegram_message',
    'whatsapp': 'send_whatsapp_message',
    'messenger': 'send_messenger_message',
    'instagram': 'send_instagram_message',
}


async def send_message(platform: str, user_id: str, message: str, business_unit, options: Optional[List[Dict]] = None):
    """
    Envía un mensaje al usuario en la plataforma especificada, con opciones si las hay.
    
    :param platform: Plataforma desde la cual se enviará el mensaje.
    :param user_id: Identificador único del usuario.
    :param message: Mensaje a enviar.
    :param business_unit: Instancia de BusinessUnit asociada.
    :param options: Lista de opciones para enviar junto al mensaje.
    """
    try:
        send_function_name = platform_send_functions.get(platform)
        if not send_function_name:
            logger.error(f"Unknown platform: {platform}")
            return

        # Obtener configuración de API por unidad de negocio
        api_instance = await get_api_instance(platform, business_unit)
        if not api_instance:
            logger.error(f"No API configuration found for platform {platform} and business unit {business_unit}.")
            return

        # Importar dinámicamente la función de envío correspondiente
        send_module = __import__(f'app.integrations.{platform}', fromlist=[send_function_name])
        send_function = getattr(send_module, send_function_name)

        # Preparar argumentos según la plataforma
        if platform == 'whatsapp':
            if options:
                # Opcionalmente, manejar las opciones de otra manera o ignorarlas por ahora
                logger.warning("Opciones no manejadas actualmente para WhatsApp.")
                await send_function(user_id, message, api_instance.phoneID, image_url=None)
            else:
                await send_function(user_id, message, api_instance.phoneID, image_url=None)
        elif platform == 'telegram':
            if options:
                await send_function(user_id, message, api_instance.api_key, options=options)
            else:
                await send_function(user_id, message, api_instance.api_key)
        elif platform == 'messenger':
            if options:
                await send_function(user_id, message, api_instance.page_access_token, options=options)
            else:
                await send_function(user_id, message, api_instance.page_access_token)
        elif platform == 'instagram':
            if options:
                await send_function(user_id, message, api_instance.access_token, options=options)
            else:
                await send_function(user_id, message, api_instance.access_token)
        else:
            logger.error(f"Unsupported platform: {platform}")

        logger.info(f"Mensaje enviado a {user_id} en {platform}: {message}")

    except Exception as e:
        logger.error(f"Error sending message on {platform}: {e}", exc_info=True)

async def send_email(business_unit_name: str, subject: str, to_email: str, body: str, from_email: Optional[str] = None):
    """
    Envía un correo electrónico utilizando la configuración SMTP de la unidad de negocio.
    
    :param business_unit_name: Nombre de la unidad de negocio.
    :param subject: Asunto del correo.
    :param to_email: Destinatario del correo.
    :param body: Cuerpo del correo en HTML.
    :param from_email: Remitente del correo. Si no se proporciona, se usa el SMTP username.
    :return: Diccionario con el estado de la operación.
    """
    try:
        # Obtener configuración SMTP desde la caché
        cache_key = f"smtp_config:{business_unit_name}"
        config_bu = cache.get(cache_key)

        if not config_bu:
            config_bu = await ConfiguracionBU.objects.select_related('business_unit').aget(
                business_unit__name=business_unit_name
            )
            cache.set(cache_key, config_bu, CACHE_TIMEOUT)

        smtp_host = config_bu.smtp_host
        smtp_port = config_bu.smtp_port
        smtp_username = config_bu.smtp_username
        smtp_password = config_bu.smtp_password
        use_tls = config_bu.smtp_use_tls
        use_ssl = config_bu.smtp_use_ssl

        # Crear el mensaje de correo
        msg = MIMEMultipart()
        msg['From'] = from_email or smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Conectar al servidor SMTP
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)

        if use_tls and not use_ssl:
            server.starttls()

        # Autenticarse y enviar el correo
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()

        logger.info(f"Correo enviado a {to_email} desde {msg['From']}")
        return {"status": "success", "message": "Correo enviado correctamente."}

    except ObjectDoesNotExist:
        logger.error(f"Configuración SMTP no encontrada para la unidad de negocio: {business_unit_name}")
        return {"status": "error", "message": "Configuración SMTP no encontrada para la Business Unit."}
    except Exception as e:
        logger.error(f"Error enviando correo electrónico: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def reset_chat_state(user_id: Optional[str] = None):
    """
    Resetea el estado del chatbot para un usuario específico o para todos los usuarios.
    
    :param user_id: Si se proporciona, resetea el estado solo para este usuario.
                    Si es None, resetea el estado para todos los usuarios.
    """
    try:
        if user_id:
            chat_state = await ChatState.objects.aget(user_id=user_id)
            await chat_state.adelete()
            logger.info(f"Chatbot state reset for user {user_id}.")
        else:
            await ChatState.objects.all().adelete()
            logger.info("Chatbot state reset for all users.")
    except ChatState.DoesNotExist:
        logger.warning(f"No chatbot state found for user {user_id}.")
    except Exception as e:
        logger.error(f"Error resetting chatbot state: {e}", exc_info=True)

async def get_api_instance(platform: str, business_unit):
    """
    Recupera la instancia de API correspondiente a la plataforma y unidad de negocio, usando caché para minimizar consultas a la base de datos.
    
    :param platform: Plataforma de mensajería.
    :param business_unit: Instancia de BusinessUnit.
    :return: Instancia de API o None si no se encuentra.
    """
    cache_key = f"{platform}_api:{business_unit.id}"
    api_instance = cache.get(cache_key)

    if api_instance:
        return api_instance

    try:
        if platform == 'whatsapp':
            api_instance = await WhatsAppAPI.objects.filter(business_unit=business_unit).afirst()
        elif platform == 'telegram':
            api_instance = await TelegramAPI.objects.filter(business_unit=business_unit).afirst()
        elif platform == 'messenger':
            api_instance = await MessengerAPI.objects.filter(business_unit=business_unit).afirst()
        elif platform == 'instagram':
            api_instance = await InstagramAPI.objects.filter(business_unit=business_unit).afirst()
        else:
            logger.error(f"Unsupported platform: {platform}")
            return None

        if api_instance:
            cache.set(cache_key, api_instance, CACHE_TIMEOUT)
        return api_instance
    except Exception as e:
        logger.error(f"Error retrieving API instance for {platform} and business unit {business_unit}: {e}", exc_info=True)
        return None
# Mover importaciones dentro de las funciones para evitar referencias circulares
async def send_logo(platform, user_id, business_unit):
    try:
        configuracion = await ConfiguracionBU.objects.filter(business_unit=business_unit).afirst()
        image_url = configuracion.logo_url if configuracion else "https://amigro.org/logo.png"

        if platform == 'whatsapp':
            await send_message_with_image(platform, user_id, '', image_url, business_unit)
        elif platform == 'messenger':
            await send_message_with_image(platform, user_id, '', image_url, business_unit)
        else:
            logger.error(f"Image sending not supported for platform {platform}")

    except Exception as e:
        logger.error(f"Error sending image on {platform}: {e}", exc_info=True)

async def send_image(platform, user_id, message, image_url, business_unit):
    try:
        send_function_name = platform_send_functions.get(platform)
        if not send_function_name:
            logger.error(f"Unknown platform: {platform}")
            return

        api_instance = await get_api_instance(platform, business_unit)
        if not api_instance:
            logger.error(f"No API configuration found for platform {platform} and business unit {business_unit}.")
            return

        send_module = __import__(f'app.integrations.{platform}', fromlist=[send_function_name])
        send_function = getattr(send_module, send_function_name)

        if platform == 'whatsapp':
            await send_function(
                user_id, message, api_instance.api_token, api_instance.phoneID, api_instance.v_api, image_url=image_url
            )
        elif platform == 'messenger':
            await send_function(
                user_id, image_url, api_instance.page_access_token
            )
        else:
            logger.error(f"Image sending not supported for platform {platform}")

    except Exception as e:
        logger.error(f"Error sending message with image on {platform}: {e}", exc_info=True)

async def send_menu(platform, user_id, business_unit):
    menu_message = """
El Menú Principal de Amigro.org
1 - Bienvenida
2 - Registro
3 - Ver Oportunidades
4 - Actualizar Perfil
5 - Invitar Amigos
6 - Términos y Condiciones
7 - Contacto
8 - Solicitar Ayuda
"""
    await send_message(platform, user_id, menu_message, business_unit)

def render_dynamic_content(template_text, context):
    """
    Renders dynamic content in a message template using variables from the context.

    :param template_text: Template text containing variables to replace.
    :param context: Dictionary with variables to replace in the template.
    :return: Rendered text with dynamic content.
    """
    try:
        content = template_text.format(**context)
        return content
    except KeyError as e:
        logger.error(f"Error rendering dynamic content: Missing variable {e}")
        return template_text  # Return the original text in case of error

async def process_text_message(platform, sender_id, message_text, business_unit):
    from app.chatbot import ChatBotHandler  # Import within the function to avoid circular references
    chatbot_handler = ChatBotHandler()

    try:
        await chatbot_handler.process_message(
            platform, sender_id, message_text, business_unit
        )

    except Exception as e:
        logger.error(f"Error processing text message: {e}", exc_info=True)

async def send_options(platform, user_id, message, buttons=None):
    try:
        if platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api and buttons:
                from app.integrations.whatsapp import send_whatsapp_buttons
                button_options = [
                    {
                        'type': 'reply',
                        'reply': {'id': str(i), 'title': button.name},
                    }
                    for i, button in enumerate(buttons)
                ]
                await send_whatsapp_buttons(
                    user_id,
                    message,
                    button_options,
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api,
                )
            else:
                logger.error("No se encontró configuración de WhatsAppAPI o botones.")

        elif platform == 'telegram':
            telegram_api = await TelegramAPI.objects.afirst()
            if telegram_api and buttons:
                from app.integrations.telegram import send_telegram_buttons
                telegram_buttons = [
                    [{'text': button.name, 'callback_data': button.name}]
                    for button in buttons
                ]
                await send_telegram_buttons(
                    user_id, message, telegram_buttons, telegram_api.api_key
                )
            else:
                logger.error("No se encontró configuración de TelegramAPI o botones.")

        elif platform == 'messenger':
            messenger_api = await MessengerAPI.objects.afirst()
            if messenger_api and buttons:
                from app.integrations.messenger import send_messenger_quick_replies
                quick_reply_options = [
                    {'content_type': 'text', 'title': button.name, 'payload': button.name}
                for button in buttons
                ]
                await send_messenger_quick_replies(
                    user_id,
                    message,
                    quick_reply_options,
                    messenger_api.page_access_token,
                )
            else:
                logger.error("No se encontró configuración de MessengerAPI o botones.")

        elif platform == 'instagram':
            instagram_api = await InstagramAPI.objects.afirst()
            if instagram_api and buttons:
                from app.integrations.instagram import send_instagram_message
                options_text = "\n".join(
                    [f"{idx + 1}. {button.name}" for idx, button in enumerate(buttons)]
                )
                message_with_options = f"{message}\n\nOpciones:\n{options_text}"
                await send_instagram_message(
                    user_id, message_with_options, instagram_api.access_token
                )
            else:
                logger.error("No se encontró configuración de InstagramAPI o botones.")

        else:
            logger.error(f"Plataforma desconocida para envío de opciones: {platform}")

    except Exception as e:
        logger.error(f"Error enviando opciones a través de {platform}: {e}", exc_info=True)

def notify_employer(worker, message):
    try:
        if worker.whatsapp:
            whatsapp_api = WhatsAppAPI.objects.first()
            if whatsapp_api:
                from app.integrations.whatsapp import send_whatsapp_message
                send_whatsapp_message(
                    worker.whatsapp,
                    message,
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api,
                )
                logger.info(f"Notificación enviada al empleador {worker.name}.")
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")
        else:
            logger.warning(f"El empleador {worker.name} no tiene número de WhatsApp configurado.")

    except Exception as e:
        logger.error(f"Error enviando notificación al empleador {worker.name}: {e}", exc_info=True)

async def process_text_message(platform, sender_id, message_text):
    from app.chatbot import ChatBotHandler  # Mover importación dentro de la función
    chatbot_handler = ChatBotHandler()

    try:
        if platform == 'whatsapp':
            whatsapp_api = await WhatsAppAPI.objects.afirst()
            if whatsapp_api:
                business_unit = whatsapp_api.business_unit
                await chatbot_handler.process_message(
                    platform, sender_id, message_text, business_unit
                )
            else:
                logger.error("No se encontró configuración de WhatsAppAPI.")

        # Agregar lógica similar para otras plataformas si es necesario

    except Exception as e:
        logger.error(f"Error procesando mensaje de texto: {e}", exc_info=True)

async def send_message_with_image(platform: str, user_id: str, message: str, image_url: str, business_unit):
    """
    Envía un mensaje con una imagen a través de la plataforma especificada.
    
    :param platform: Plataforma desde la cual se enviará el mensaje.
    :param user_id: Identificador único del usuario.
    :param message: Mensaje a enviar.
    :param image_url: URL de la imagen a enviar.
    :param business_unit: Instancia de BusinessUnit asociada.
    """
    try:
        await send_message(platform, user_id, message, business_unit, options=[{'type': 'image', 'url': image_url}])
        logger.info(f"Mensaje con imagen enviado a {user_id} en {platform}")
    except Exception as e:
        logger.error(f"Error enviando mensaje con imagen en {platform} a {user_id}: {e}", exc_info=True)
___________________
# /home/amigro/app/integrations/whatsapp.py

import json
import httpx
import logging
from django.core.cache import cache
from asgiref.sync import sync_to_async
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from langdetect import detect, DetectorFactory
from app.models import WhatsAppAPI, MetaAPI, BusinessUnit, Configuracion, FlowModel, Person, ChatState
from app.integrations.services import send_message, get_api_instance
from typing import Optional, List, Dict

logger = logging.getLogger('whatsapp')
#Se crea un cache regenerativo para que no se hagan demasiadas llamadas al API
CACHE_TIMEOUT = 600  # 10 minutos
AMIGRO_VERIFY_TOKEN = "amigro_secret_token"
DetectorFactory.seed = 0  # Para resultados consistentes

@csrf_exempt
async def whatsapp_webhook(request):
    """
    Webhook de WhatsApp para manejar mensajes entrantes y verificación de token.
    """
    try:
        logger.info(f"Solicitud entrante: {request.method}, Headers: {dict(request.headers)}")

        # Manejo del método GET para verificación de token
        if request.method == 'GET':
            return await verify_whatsapp_token(request)

        # Manejo del método POST para mensajes entrantes
        elif request.method == 'POST':
            try:
                body = await sync_to_async(request.body.decode)('utf-8')
                payload = json.loads(body)
                logger.info(f"Payload recibido: {json.dumps(payload, indent=4)}")

                # Llamar a la función para manejar el mensaje entrante
                response = await handle_incoming_message(payload)
                logger.info(f"Respuesta generada: {response}")
                return response

            except json.JSONDecodeError as e:
                logger.error(f"Error al decodificar JSON: {str(e)}", exc_info=True)
                return JsonResponse({"error": "Error al decodificar el cuerpo de la solicitud"}, status=400)
            except Exception as e:
                logger.error(f"Error inesperado al manejar la solicitud POST: {str(e)}", exc_info=True)
                return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)

        # Manejar métodos no permitidos
        else:
            logger.warning(f"Método no permitido: {request.method}")
            return HttpResponse(status=405)

    except Exception as e:
        logger.error(f"Error crítico en el webhook de WhatsApp: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Error crítico: {str(e)}"}, status=500)
    
@csrf_exempt
async def verify_whatsapp_token(request):
    try:
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        phone_id = request.GET.get('phoneID')

        if not phone_id:
            logger.error("Falta el parámetro phoneID en la solicitud de verificación")
            return HttpResponse("Falta el parámetro phoneID", status=400)

        # Obtener WhatsAppAPI desde la caché
        cache_key_whatsapp = f"whatsappapi:{phone_id}"
        whatsapp_api = cache.get(cache_key_whatsapp)

        if not whatsapp_api:
            whatsapp_api = await sync_to_async(
                lambda: WhatsAppAPI.objects.filter(phoneID=phone_id).select_related('business_unit').first()
            )()
            if not whatsapp_api:
                logger.error(f"PhoneID no encontrado: {phone_id}")
                return HttpResponse('Configuración no encontrada', status=404)

            # Guardar en caché
            cache.set(cache_key_whatsapp, whatsapp_api, timeout=CACHE_TIMEOUT)

        # Obtener MetaAPI usando la unidad de negocio
        business_unit = whatsapp_api.business_unit
        cache_key_meta = f"metaapi:{business_unit.id}"
        meta_api = cache.get(cache_key_meta)

        if not meta_api:
            meta_api = await sync_to_async(
                lambda: MetaAPI.objects.filter(business_unit=business_unit).first()
            )()
            if not meta_api:
                logger.error(f"MetaAPI no encontrado para la unidad de negocio: {business_unit.name}")
                return HttpResponse('Configuración no encontrada', status=404)

            # Guardar en caché
            cache.set(cache_key_meta, meta_api, timeout=CACHE_TIMEOUT)

        # Validar el token de verificación
        if verify_token == meta_api.verify_token:
            logger.info(f"Token de verificación correcto para phoneID: {phone_id}")
            return HttpResponse(challenge)
        else:
            logger.warning(f"Token de verificación inválido: {verify_token}")
            return HttpResponse('Token de verificación inválido', status=403)

    except Exception as e:
        logger.exception(f"Error inesperado en verify_whatsapp_token: {str(e)}")
        return JsonResponse({"error": "Error inesperado en la verificación de token"}, status=500)

@csrf_exempt
async def handle_incoming_message(payload):
    """
    Manejo de mensajes entrantes de WhatsApp con conexión al chatbot.
    """
    try:
        from app.chatbot import ChatBotHandler
        chatbot_handler = ChatBotHandler()

        if 'entry' not in payload:
            logger.error("El payload no contiene la clave 'entry'")
            return JsonResponse({'error': "El payload no contiene la clave 'entry'"}, status=400)

        for entry in payload.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                messages = value.get('messages', [])
                if not messages:
                    logger.info("No se encontraron mensajes en el cambio")
                    continue
                for message in messages:
                    sender_id = message.get('from')
                    phone_id = value.get('metadata', {}).get('phone_number_id')
                    if not phone_id:
                        logger.error("No se encontró 'phone_number_id' en el metadata")
                        continue

                    # Obtener configuración de WhatsAppAPI y unidad de negocio
                    cache_key_whatsapp = f"whatsappapi:{phone_id}"
                    whatsapp_api = cache.get(cache_key_whatsapp)

                    if not whatsapp_api:
                        whatsapp_api = await sync_to_async(
                            lambda: WhatsAppAPI.objects.filter(phoneID=phone_id).select_related('business_unit').first()
                        )()
                        if not whatsapp_api:
                            logger.error(f"No se encontró WhatsAppAPI para phoneID: {phone_id}")
                            continue
                        cache.set(cache_key_whatsapp, whatsapp_api, timeout=CACHE_TIMEOUT)

                    business_unit = whatsapp_api.business_unit

                    # Obtener información del usuario y determinar idioma
                    name = value.get('contacts', [{}])[0].get('profile', {}).get('name', 'Usuario')
                    raw_text = message.get('text', {}).get('body', '')
                    language = value.get('contacts', [{}])[0].get('language', {}).get('code', 'es')
                    if not language and raw_text:
                        try:
                            language = detect(raw_text)
                        except Exception as e:
                            language = 'es_MX'
                            logger.warning(f"Error detectando idioma: {e}")

                    # Obtener o crear la instancia de Person
                    person, _ = await sync_to_async(Person.objects.get_or_create)(
                        phone=sender_id,
                        defaults={'name': name}
                    )

                    # Obtener o crear la instancia de ChatState
                    chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(
                        user_id=sender_id,
                        defaults={'platform': 'whatsapp', 'business_unit': business_unit}
                    )

                    # Process the message using a dictionary mapping
                    message_type = message.get('type', 'text')
                    message_handlers = {
                        'text': handle_text_message,
                        'image': handle_media_message,
                        'audio': handle_media_message,
                        'location': handle_location_message,
                        'interactive': handle_interactive_message,
                        # Add more message types and their handlers here
                    }

                    handler = message_handlers.get(message_type, handle_unknown_message)
                    await handler(message, sender_id, chatbot_handler, business_unit, person, chat_state)

        return JsonResponse({'status': 'success'}, status=200)

    except Exception as e:
        logger.error(f"Unexpected error handling the message: {e}", exc_info=True)
        return JsonResponse({'error': f"Unexpected error: {e}"}, status=500)
# Define handler functions for each message type
async def handle_text_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    text = message['text']['body']
    await chatbot_handler.process_message(
        platform='whatsapp',
        user_id=sender_id,
        text=text,
        business_unit=business_unit,
    )
async def handle_media_message(message, sender_id, *args, **kwargs):
    media_id = message.get('image', {}).get('id') or message.get('audio', {}).get('id')
    media_type = message['type']
    if media_id:
        await process_media_message('whatsapp', sender_id, media_id, media_type)
    else:
        logger.warning(f"Media message received without 'id' for type {media_type}")
async def handle_location_message(message, sender_id, *args, **kwargs):
    location = message.get('location')
    if location:
        await process_location_message('whatsapp', sender_id, location)
    else:
        logger.warning("Location message received without location data")
async def handle_interactive_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    interactive_type = message.get('interactive', {}).get('type')
    interactive_handlers = {
        'button_reply': handle_button_reply,
        'list_reply': handle_list_reply,
        'product': handle_product_message,
        'product_list': handle_product_list_message,
        'service': handle_service_message,
        'service_list': handle_service_list_message,
        # Add more interactive types and their handlers here
    }
    handler = interactive_handlers.get(interactive_type, handle_unknown_interactive)
    await handler(message, sender_id, chatbot_handler, business_unit, person, chat_state)
async def handle_button_reply(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    button_reply = message['interactive']['button_reply']
    payload = button_reply.get('payload') or button_reply.get('id')  # Adjust according to your payload structure
    logger.info(f"Button reply received: {payload}")
    await chatbot_handler.process_button_reply(
        platform='whatsapp',
        user_id=sender_id,
        payload=payload,
        business_unit=business_unit,
        person=person,
        chat_state=chat_state
    )
async def handle_list_reply(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    list_reply = message['interactive']['list_reply']
    payload = list_reply.get('payload') or list_reply.get('id')  # Adjust according to your payload structure
    logger.info(f"List reply received: {payload}")
    await chatbot_handler.process_list_reply(
        platform='whatsapp',
        user_id=sender_id,
        payload=payload,
        business_unit=business_unit,
        person=person,
        chat_state=chat_state
    )
async def handle_product_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    # Lógica para manejar mensajes de producto
    pass
async def handle_product_list_message(message, sender_id, chatbot_handler, business_unit, person, chat_state):
    # Lógica para manejar mensajes de lista de productos
    pass
async def send_service_list(user_id, platform, business_unit):
    api_instance = await get_api_instance(platform, business_unit)
    if not api_instance:
        logger.error(f"No se encontró configuración de API para {platform} y unidad de negocio {business_unit}.")
        return
    
    api_token = api_instance.api_token
    phone_id = api_instance.phoneID
    version_api = api_instance.v_api

    url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": user_id,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": "Selecciona una unidad de negocio para continuar:"},
            "footer": {"text": "Grupo huntRED®"},
            "action": {
                "button": "Ver Servicios",
                "sections": [
                    {
                        "title": "Unidades de Negocio",
                        "rows": [
                            {"id": "amigro", "title": "Amigro® - Plataforma de AI para Migrantes en México"},
                            {"id": "huntu", "title": "huntU® - Plataforma de AI para estudiantes y recién egresados a nivel licenciatura y Maestría"},
                            {"id": "huntred", "title": "huntRED® - Nuestro reconocido Headhunter de Gerencia Media a nivel Directivo."},
                            {"id": "huntred_executive", "title": "huntRED® Executive- Posiciones de Alta Dirección así como integración y participación en Consejos y Comités."},
                            {"id": "huntred_solutions", "title": "huntRED® Solutions- Consultora de Recursos Humanos, Desarrollo Organizacional y Cultura."},
                            {"id": "contacto", "title": "Contacta a nuestro Managing Partner - Pablo LLH."}
                        ]
                    }
                ]
            }
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"Lista de servicios enviada a {user_id}")
    except Exception as e:
        logger.error(f"Error enviando lista de servicios a {user_id}: {e}", exc_info=True)
async def process_service_selection(platform, user_id, selected_service, person, chat_state):
    # Mapear el servicio seleccionado a la unidad de negocio y plantilla correspondiente
    business_units = {
        'amigro': 'nueva_oportunidad_amigro',
        'huntu': 'nueva_oportunidad_huntu',
        'huntred': 'nueva_oportunidad_huntred',
        'huntred_executive': 'nueva_oportunidad_huntred_executive',
        'huntred_solutions': 'nueva_oportunidad_huntred_solutions',
    }

    if selected_service == 'contacto':
        # Lógica para enviar notificación al administrador
        await notify_admin_of_contact_request(person)
        
        # Enviar confirmación al usuario
        await send_message(platform, user_id, "Gracias por tu interés. Nuestro Managing Partner se pondrá en contacto contigo a la brevedad.", chat_state.business_unit)
        logger.info(f"Solicitud de contacto recibida de {person.name} ({person.phone})")
    elif selected_service in business_units:
        template_name = business_units[selected_service]
        # Actualizar el chat_state con la unidad de negocio seleccionada
        chat_state.business_unit = await BusinessUnit.objects.aget(name__iexact=selected_service)
        await chat_state.asave()
        
        # Enviar la plantilla correspondiente
        await send_whatsapp_template(user_id, template_name, chat_state.business_unit)
        logger.info(f"Plantilla {template_name} enviada a {user_id}")
    else:
        await send_message(platform, user_id, "Servicio no reconocido. Por favor, selecciona una opción válida.", chat_state.business_unit)
        logger.warning(f"Servicio no reconocido: {selected_service}")
async def notify_admin_of_contact_request(person):
    admin_phone_number = '525518490291'
    admin_email = 'pablo@huntred.com'
    message = f"Solicitud de contacto de:\nNombre: {person.name}\nTeléfono: {person.phone}\nEmail: {person.email or 'No proporcionado'}"

    # Enviar mensaje de WhatsApp al administrador si se dispone del número
    if admin_phone_number:
        try:
            # Obtener la instancia de WhatsAppAPI para enviar el mensaje
            whatsapp_api = await get_api_instance('whatsapp', person.business_unit)
            if whatsapp_api:
                await send_whatsapp_message(
                    admin_phone_number,
                    message,
                    whatsapp_api.api_token,
                    whatsapp_api.phoneID,
                    whatsapp_api.v_api
                )
                logger.info(f"Notificación de contacto enviada al administrador vía WhatsApp: {admin_phone_number}")
            else:
                logger.error("No se pudo obtener la configuración de WhatsAppAPI para enviar la notificación.")
        except Exception as e:
            logger.error(f"Error enviando notificación al administrador vía WhatsApp: {e}", exc_info=True)
    
    # Enviar correo electrónico al administrador si se dispone del email
    if admin_email:
        try:
            await send_email(
                business_unit_name=person.business_unit.name,
                subject='Solicitud de contacto de un usuario',
                to_email=admin_email,
                body=message
            )
            logger.info(f"Notificación de contacto enviada al administrador vía email: {admin_email}")
        except Exception as e:
            logger.error(f"Error enviando notificación al administrador vía email: {e}", exc_info=True)
async def handle_unknown_interactive(message, sender_id, *args, **kwargs):
    interactive_type = message.get('interactive', {}).get('type')
    logger.warning(f"Unsupported interactive type: {interactive_type}")
async def handle_unknown_message(message, sender_id, *args, **kwargs):
    message_type = message.get('type', 'unknown')
    logger.warning(f"Unsupported message type: {message_type}")
      
async def process_media_message(platform, sender_id, media_id, media_type):
    """
    Procesa mensajes de medios (imágenes, audio, etc.) entrantes.
    """
    try:
        whatsapp_api = await WhatsAppAPI.objects.afirst()
        if not whatsapp_api:
            logger.error("No se encontró configuración de WhatsAppAPI.")
            return

        # Obtener la URL de descarga del medio
        media_url = await get_media_url(media_id, whatsapp_api.api_token)
        if not media_url:
            logger.error(f"No se pudo obtener la URL del medio {media_id}")
            return

        # Descargar el archivo
        media_data = await download_media(media_url, whatsapp_api.api_token)
        if not media_data:
            logger.error(f"No se pudo descargar el medio {media_url}")
            return

        # Procesar el archivo según el tipo
        if media_type == 'image':
            await handle_image_message(platform, sender_id, media_data)
        elif media_type == 'audio':
            await handle_audio_message(platform, sender_id, media_data)
        else:
            logger.warning(f"Tipo de medio no soportado: {media_type}")

    except Exception as e:
        logger.error(f"Error procesando mensaje de medios: {e}", exc_info=True)

async def get_media_url(media_id, api_token):
    """
    Obtiene la URL de descarga para un medio específico.
    """
    url = f"https://graph.facebook.com/v17.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('url')
    except httpx.HTTPStatusError as e:
        logger.error(f"Error obteniendo la URL del medio: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error general obteniendo la URL del medio: {e}", exc_info=True)

    return None

async def download_media(media_url, api_token):
    """
    Descarga el contenido de un medio desde la URL proporcionada.
    """
    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, headers=headers)
            response.raise_for_status()
            return response.content
    except httpx.HTTPStatusError as e:
        logger.error(f"Error descargando el medio: {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error general descargando el medio: {e}", exc_info=True)

    return None

async def handle_image_message(platform, sender_id, image_data):
    """
    Procesa una imagen recibida.
    """
    # Aquí puedes guardar la imagen, procesarla o extraer información
    # Por ejemplo, podrías guardar la imagen en el sistema de archivos o en una base de datos

    logger.info(f"Imagen recibida de {sender_id}. Procesando imagen...")

    # Ejemplo: Guardar la imagen en el sistema de archivos
    image_path = f"/path/to/save/images/{sender_id}_{int(time.time())}.jpg"
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # Enviar una respuesta al usuario
    response_message = "Gracias por enviar la imagen. La hemos recibido correctamente."
    await send_message(platform, sender_id, response_message)

async def handle_audio_message(platform, sender_id, audio_data):
    """
    Procesa un archivo de audio recibido.
    """
    # Aquí puedes guardar el audio, procesarlo o extraer información
    # Por ejemplo, podrías transcribir el audio o guardarlo para análisis posterior

    logger.info(f"Audio recibido de {sender_id}. Procesando audio...")

    # Ejemplo: Guardar el audio en el sistema de archivos
    audio_path = f"/path/to/save/audio/{sender_id}_{int(time.time())}.ogg"
    with open(audio_path, 'wb') as f:
        f.write(audio_data)

    # Enviar una respuesta al usuario
    response_message = "Gracias por enviar el audio. Lo hemos recibido correctamente."
    await send_message(platform, sender_id, response_message)

async def process_location_message(platform, sender_id, location):
    latitude = location.get('latitude')
    longitude = location.get('longitude')
    logger.info(f"Ubicación recibida de {sender_id}: Latitud {latitude}, Longitud {longitude}")

    # Almacenar la ubicación en la base de datos
    person, created = await Person.objects.aupdate_or_create(
        phone=sender_id,
        defaults={'latitude': latitude, 'longitude': longitude}
    )

    # Buscar vacantes cercanas
    vacantes_cercanas = await obtener_vacantes_cercanas(latitude, longitude)
    # Verificar si el usuario tiene una entrevista programada
    interview = await Interview.objects.afilter(person__phone=sender_id, interview_date__gte=timezone.now()).afirst()
    if interview and interview.interview_type == 'presencial':
        distance = calcular_distancia(float(latitude), float(longitude), interview.job.latitude, interview.job.longitude)
        if distance <= 0.2:
            await send_message(platform, sender_id, "Has llegado al lugar de la entrevista. ¡Buena suerte!")
        else:
            await send_message(platform, sender_id, "Parece que aún no estás en el lugar de la entrevista. ¡Te esperamos!")

    # Formatear y enviar las vacantes al usuario
    if vacantes_cercanas:
        mensaje_vacantes = formatear_vacantes(vacantes_cercanas)
        await send_message(platform, sender_id, mensaje_vacantes)
    else:
        await send_message(platform, sender_id, "No se encontraron vacantes cercanas a tu ubicación.")

async def obtener_vacantes_cercanas(latitude, longitude):
    # Implementa la lógica para obtener vacantes cercanas basadas en la ubicación
    # Por ejemplo, podrías filtrar las vacantes en tu base de datos usando una consulta geoespacial
    pass

async def send_whatsapp_message(user_id, message, phone_id, image_url=None, options: Optional[List[Dict]] = None):
    """
    Envía un mensaje a través de WhatsApp usando la configuración de WhatsAppAPI.
    
    :param user_id: Número de WhatsApp del destinatario.
    :param message: Mensaje de texto a enviar.
    :param phone_id: Phone Number ID de WhatsApp.
    :param image_url: URL de la imagen a enviar (opcional).
    :param options: Lista de opciones para botones interactivos (opcional).
    """
    try:
        # Obtener la configuración de WhatsAppAPI para el phone_id proporcionado
        whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_id, is_active=True).first)()
        if not whatsapp_api:
            logger.error(f"No se encontró configuración activa para phoneID: {phone_id}")
            return

        token = whatsapp_api.api_token
        api_version = whatsapp_api.v_api

        url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Construir el payload de manera condicional
        payload = {
            "messaging_product": "whatsapp",
            "to": user_id,
            "type": "image" if image_url else "text",
        }

        if image_url:
            payload["image"] = {
                "link": image_url,
                # "caption": "Aquí va tu leyenda opcional"  # Opcional: Añadir caption si es necesario
            }
        else:
            payload["text"] = {
                "body": message
            }

        if options:
            # Añadir opciones como botones interactivos
            payload["interactive"] = {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": option["id"], "title": option["title"]}} for option in options
                    ]
                }
            }
            # Eliminar el campo 'text' si se usa 'interactive'
            del payload["text"]

        logger.debug(f"Enviando mensaje a WhatsApp con payload: {payload}")

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Mensaje enviado exitosamente a {user_id}: {message}")
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Error HTTP al enviar mensaje a {user_id}: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Error inesperado al enviar mensaje a {user_id}: {e}", exc_info=True)
    
async def send_whatsapp_decision_buttons(user_id, message, buttons, phone_id):
    """
    Envía botones interactivos de decisión (Sí/No) a través de WhatsApp usando MetaAPI.
    """
    # Obtener configuración de MetaAPI usando el phoneID
    whatsapp_api = await sync_to_async(WhatsAppAPI.objects.filter(phoneID=phone_id).first)()
    if not meta_api:
        logger.error(f"No se encontró configuración para phoneID: {phone_id}")
        return

    api_token = whatsapp_api.api_token
    version_api = meta_api.version_api

    url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Validación de botones para asegurarse de que sean sólo "Sí" y "No"
    if not isinstance(buttons, list) or len(buttons) != 2:
        raise ValueError("Se deben proporcionar exactamente 2 botones: Sí y No.")

    # Formatear los botones para WhatsApp
    formatted_buttons = []
    for idx, button in enumerate(buttons):
        formatted_button = {
            "type": "reply",
            "reply": {
                "id": f"btn_{idx}",  # ID único para cada botón
                "title": button['title'][:20]  # Límite de 20 caracteres
            }
        }
        formatted_buttons.append(formatted_button)

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": user_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message  # El mensaje que acompaña los botones
            },
            "action": {
                "buttons": formatted_buttons
            }
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Botones de Sí/No enviados a {user_id} correctamente.")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error enviando botones de decisión (Sí/No): {e.response.text}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"Error general enviando botones de decisión (Sí/No): {e}", exc_info=True)
        raise e

async def invite_known_person(referrer, name, apellido, phone_number):
    """
    Invita a una persona conocida vía WhatsApp y crea un pre-registro.
    """
    try:
        invitado, created = await sync_to_async(lambda: Person.objects.update_or_create(
            telefono=phone_number, defaults={'nombre': name, 'apellido_paterno': apellido}))()

        await sync_to_async(Invitacion.objects.create)(referrer=referrer, invitado=invitado)

        if created:
            mensaje = f"Hola {name}, has sido invitado por {referrer.nombre} a unirte a Amigro.org. ¡Únete a nuestra comunidad!"
            await send_whatsapp_message(phone_number, mensaje, referrer.api_token, referrer.phoneID, referrer.v_api)

        return invitado

    except Exception as e:
        logger.error(f"Error al invitar a {name}: {e}")
        raise

async def registro_amigro(recipient, access_token, phone_id, version_api, form_data):
    """
    Envía una plantilla de mensaje de registro personalizado a un nuevo usuario en WhatsApp.

    :param recipient: Número de teléfono del destinatario en formato internacional.
    :param access_token: Token de acceso para la API de WhatsApp.
    :param phone_id: ID del teléfono configurado para el envío de mensajes.
    :param version_api: Versión de la API de WhatsApp.
    :param form_data: Diccionario con datos del usuario para personalizar la plantilla.
    """
    try:
        url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": "registro_amigro",
                "language": {"code": "es_MX"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [{"type": "image", "image": {"link": "https://amigro.org/registro2.png"}}]
                    },
                    {"type": "body", "parameters": []},
                    {
                        "type": "button",
                        "sub_type": "FLOW",
                        "index": "0",
                        "parameters": [{"type": "text", "text": "https://amigro.org"}]
                    }
                ]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"Plantilla de registro enviada correctamente a {recipient}")
        return response.json()

    except Exception as e:
        logger.error(f"Error enviando plantilla de registro a {recipient}: {e}", exc_info=True)
        raise e

async def nueva_posicion_amigro(recipient, access_token, phone_id, version_api, form_data):
    """
    Envía una plantilla de mensaje para notificar al usuario de una nueva oportunidad laboral.

    :param recipient: Número de teléfono del destinatario en formato internacional.
    :param access_token: Token de acceso para la API de WhatsApp.
    :param phone_id: ID del teléfono configurado para el envío de mensajes.
    :param version_api: Versión de la API de WhatsApp.
    :param form_data: Diccionario con datos de la vacante para personalizar la plantilla.
    """
    try:
        url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": "nueva_posicion_amigro",
                "language": {"code": "es_MX"},
                "components": [
                    {
                        "type": "header",
                        "parameters": [{"type": "image", "image": {"link": "https://amigro.org/registro.png"}}]
                    },
                    {"type": "body", "parameters": [{"type": "text", "text": "Hola, bienvenido a Amigro!"}]},
                    {
                        "type": "button",
                        "sub_type": "FLOW",
                        "index": "0",
                        "parameters": [{"type": "text", "text": "https://amigro.org"}]
                    }
                ]
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"Plantilla de nueva posición enviada correctamente a {recipient}")
        return response.json()

    except Exception as e:
        logger.error(f"Error enviando plantilla de nueva posición a {recipient}: {e}", exc_info=True)
        raise e

async def send_whatsapp_template(user_id, template_name, business_unit):
    api_instance = await get_api_instance('whatsapp', business_unit)
    if not api_instance:
        logger.error(f"No se encontró configuración de WhatsAppAPI para la unidad de negocio {business_unit}.")
        return
    
    api_token = api_instance.api_token
    phone_id = api_instance.phoneID
    version_api = api_instance.v_api

    url = f"https://graph.facebook.com/{version_api}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": user_id,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "es_MX"}
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        logger.info(f"Plantilla {template_name} enviada correctamente a {user_id}")
    except Exception as e:
        logger.error(f"Error enviando plantilla {template_name} a {user_id}: {e}", exc_info=True)

def dividir_botones(botones, n):
    """
    Divide la lista de botones en grupos de tamaño `n`, útil para cuando una plataforma tiene límite en el número de botones.

    :param botones: Lista de botones para dividir.
    :param n: Tamaño del grupo de botones.
    :return: Generador que produce grupos de botones.
    """
    for i in range(0, len(botones), n):
        yield botones[i:i + n]

async def send_pregunta_with_buttons(user_id, pregunta, phone_id):
    """
    Envía una pregunta con botones de respuesta en WhatsApp.

    :param user_id: ID del usuario destinatario.
    :param pregunta: Objeto Pregunta con el contenido y los botones a enviar.
    :param phone_id: ID del teléfono de WhatsApp para obtener la configuración.
    """
    from app.integrations.whatsapp import send_whatsapp_buttons

    if pregunta.botones_pregunta.exists():
        botones = pregunta.botones_pregunta.all()
        whatsapp_api = await WhatsAppAPI.objects.afirst(phoneID__exact=phone_id)

        if not meta_api:
            logger.error(f"No se encontró configuración para phoneID: {phone_id}")
            return

        message = pregunta.content
        tasks = []

        # Dividir los botones en grupos de tres para WhatsApp
        for tercia in dividir_botones(list(botones), 3):
            buttons = [{"title": boton.name} for boton in tercia]
            logger.info(f"Enviando botones: {[boton['title'] for boton in buttons]} a {user_id}")
            tasks.append(send_whatsapp_buttons(
                user_id,
                message,
                buttons,
                meta_api.api_token,
                meta_api.phoneID,
                meta_api.version_api
            ))

        await asyncio.gather(*tasks)
    else:
        logger.warning(f"La pregunta {pregunta.id} no tiene botones asignados.")
    
async def send_test_notification(user_id):
    """
    Envía una notificación de prueba al número configurado.
    """
    from app.integrations.whatsapp import send_whatsapp_message
    config = await sync_to_async(lambda: Configuracion.objects.first())()
    message = "🔔 Notificación de prueba recibida. El sistema está operativo."
    
    await send_whatsapp_message(
        user_id,
        message,
        config.default_platform
    )
    logger.info(f"Notificación de prueba enviada a {user_id}.")


    _______
sudo nano app/chatbot.py && cd app/integrations && sudo nano services.py whatsapp.py instagram.py messenger.py telegram.py && sudo systemctl restart gunicorn && cd /home/amigro && python manage.py migrate
