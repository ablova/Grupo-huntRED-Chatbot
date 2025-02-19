# Ubicación: /home/pablo/app/chatbot/intents_handler.py
import logging
from typing import List
from asgiref.sync import sync_to_async

from app.models import ChatState, Person, BusinessUnit
from app.chatbot.integrations.services import  MessageService
from app.utilidades.vacantes import VacanteManager

logger = logging.getLogger("app.chatbot.intents_handler")


async def handle_known_intents(intents, platform, user_id, event, business_unit, user):
    """
    Maneja los intents conocidos del usuario.
    """
    chat_state, _ = await sync_to_async(ChatState.objects.get_or_create)(user_id=user_id, business_unit=business_unit)
    
    # Resto de la lógica para manejar los intents

    # 🔹 **Intentos con respuestas directas**
    INTENT_RESPONSES = {
        "saludo": "¡Hola! ¿En qué puedo ayudarte hoy?",
        "despedida": "¡Hasta luego! Si necesitas más ayuda, contáctame de nuevo.",
        "iniciar_conversacion": "¡Claro! Empecemos de nuevo. ¿En qué puedo ayudarte?",
        "solicitar_ayuda_postulacion": "Puedo guiarte en el proceso de postulación. ¿Qué necesitas saber?",
        "busqueda_impacto": "Entiendo que buscas un trabajo con impacto social. ¿Deseas ver vacantes con propósito?",
        "solicitar_informacion_empresa": "¿Sobre qué empresa necesitas información? Puedo contarte sobre sus valores, cultura o posiciones disponibles.",
        "solicitar_tips_entrevista": "Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas.",
        "consultar_sueldo_mercado": "¿Para qué posición o nivel buscas el rango salarial de mercado? Puedo darte una estimación.",
        "actualizar_perfil": "Claro, ¿qué dato de tu perfil deseas actualizar? (Ejemplo: nombre, email, experiencia, expectativas salariales)",
        "notificaciones": "Puedo enviarte notificaciones automáticas sobre cambios en tus procesos. ¿Quieres activarlas? Responde 'sí' para confirmar.",
        "agradecimiento": "¡De nada! ¿En qué más puedo ayudarte?",
    }

    for intent in intents:
        logger.debug(f"[handle_known_intents] Intent detectado: {intent}")

        # 🚀 **Mensajes Simples**
        if intent in INTENT_RESPONSES:
            response = INTENT_RESPONSES[intent]
            await send_message(platform, user_id, response, business_unit)
            return True

        # 🚀 **Menú Principal (con payloads)**
        elif intent == "menu":
            menu_options = [
                {"title": "🔍 Ver Vacantes", "payload": "ver_vacantes"},
                {"title": "📝 Actualizar Perfil", "payload": "actualizar_perfil"},
                {"title": "📖 Ayuda Postulación", "payload": "ayuda_postulacion"},
                {"title": "📊 Consultar Estatus", "payload": "consultar_estatus"}
            ]
            await send_message(platform, user_id, "Aquí tienes el menú principal:", business_unit, options=menu_options)
            return True

        # 🚀 **Estatus de Aplicación**
        elif intent == "consultar_estatus":
            response = "Por favor, proporciona tu correo electrónico asociado a la aplicación."
            await send_message(platform, user_id, response, business_unit)
            event.context['awaiting_status_email'] = True
            await sync_to_async(event.save)()
            return True

        # 🚀 **Viaje en Grupo / Con Familia**
        elif intent in ["travel_in_group", "travel_with_family"]:
            response = (
                "Entiendo, ¿te gustaría invitar a tus acompañantes para que también obtengan oportunidades laborales? "
                "Envíame su nombre completo y teléfono en el formato: 'Nombre Apellido +52XXXXXXXXXX'."
            )
            await send_message(platform, user_id, response, business_unit)
            event.context['awaiting_group_invitation'] = True
            await sync_to_async(event.save)()
            return True

        # 🚀 **Ver Vacantes**
        elif intent == "ver_vacantes":
            recommended_jobs = await sync_to_async(VacanteManager.match_person_with_jobs)(user)
            if recommended_jobs:
                event.context['recommended_jobs'] = recommended_jobs
                await sync_to_async(event.save)()
                await present_job_listings(platform, user_id, recommended_jobs, business_unit, event) # type: ignore
            else:
                await send_message(platform, user_id, "No encontré vacantes para tu perfil por ahora.", business_unit)
            return True

        # 🚀 **Términos y Condiciones (TOS)**
        elif intent in ["tos_accept", "tos_reject"]:
            if intent == "tos_accept":
                user.tos_accepted = True
                await sync_to_async(user.save)()
                response = "✅ Gracias por aceptar nuestros TOS. Ahora podemos continuar con el proceso."
            else:
                response = "⚠ No se puede continuar sin aceptar los TOS. Por favor, selecciona una opción:"
            
            tos_buttons = [
                {"title": "✅ Aceptar", "payload": "tos_accept"},
                {"title": "❌ Rechazar", "payload": "tos_reject"},
                {"title": "📜 Ver TOS", "url": "https://amigro.org/tos"}  # Para WhatsApp, el link se envía antes del mensaje
            ]

            if platform == "whatsapp":
                await send_message(platform, user_id, "📜 Puedes consultar nuestros términos aquí: https://amigro.org/tos", business_unit)
            
            await send_message(platform, user_id, response, business_unit, options=tos_buttons)
            return True

        # 🚀 **Ayuda con Entrevistas**
        elif intent == "preparacion_entrevista":
            response = (
                "Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables "
                "y prepara ejemplos de situaciones pasadas. ¿Necesitas más ayuda?"
            )
            await send_message(platform, user_id, response, business_unit)
            return True

        # 🚀 **Consulta de Beneficios**
        elif intent == "consultar_beneficios":
            response = "¿Qué tipo de beneficios te interesan?"
            benefit_buttons = [
                {"title": "🏥 Salud", "payload": "beneficio_salud"},
                {"title": "💰 Bonos", "payload": "beneficio_bonos"},
                {"title": "📆 Días libres", "payload": "beneficio_dias_libres"}
            ]
            await send_message(platform, user_id, response, business_unit, options=benefit_buttons)
            return True

        # 🚀 **Información de Empresas**
        elif intent == "empresa_info":
            response = "¿Sobre qué empresa necesitas información? Puedo contarte sobre sus valores, cultura o posiciones disponibles."
            await send_message(platform, user_id, response, business_unit)
            return True

        # 🚀 **Horario de Trabajo**
        elif intent == "consultar_horario":
            response = "¿Buscas un horario específico?"
            horario_buttons = [
                {"title": "⏳ Jornada Completa", "payload": "horario_completo"},
                {"title": "⏰ Medio Tiempo", "payload": "horario_medio_tiempo"},
                {"title": "🔄 Flexible", "payload": "horario_flexible"}
            ]
            await send_message(platform, user_id, response, business_unit, options=horario_buttons)
            return True


        # 🚀 **Tipo de Contrato**
        elif intent == "consultar_tipo_contrato":
            response = "¿Qué tipo de contrato buscas?"
            contrato_buttons = [
                {"title": "📄 Indefinido", "payload": "contrato_indefinido"},
                {"title": "📌 Por Proyecto", "payload": "contrato_proyecto"},
                {"title": "💼 Freelance", "payload": "contrato_freelance"}
            ]
            await send_message(platform, user_id, response, business_unit, options=contrato_buttons)
            return True

        # 🚀 **Reubicación**
        elif intent == "preguntar_reubicacion":
            response = "¿Estás dispuesto a reubicarte por una oportunidad laboral?"
            reubicacion_buttons = [
                {"title": "✅ Sí", "payload": "reubicacion_si"},
                {"title": "❌ No", "payload": "reubicacion_no"},
                {"title": "🤔 Depende (ubicación/posición)", "payload": "reubicacion_depende"}
            ]
            await send_message(platform, user_id, response, business_unit, options=reubicacion_buttons)
            return True
        
        elif intent == "agradecimiento":
            response = "¡De nada! ¿En qué más puedo ayudarte?"
            await send_message(platform, user_id, response, business_unit)
            return True

        elif intent == "busqueda_impacto":
            response = "Entiendo que buscas un trabajo con impacto social. Puedo mostrarte vacantes que destaquen proyectos con propósito. ¿Deseas verlas?"
            await send_message(platform, user_id, response, business_unit)
            return True

        elif intent == "solicitar_informacion_empresa":
            response = "¿Sobre qué empresa necesitas información? Puedo contarte sobre sus valores, cultura o posiciones disponibles."
            await send_message(platform, user_id, response, business_unit)
            return True

        elif intent == "solicitar_tips_entrevista":
            response = "Para entrevistas: investiga la empresa, sé puntual, muestra logros cuantificables y prepara ejemplos de situaciones pasadas."
            await send_message(platform, user_id, response, business_unit)
            return True

        elif intent == "consultar_sueldo_mercado":
            response = "¿Para qué posición o nivel buscas el rango salarial de mercado? Puedo darte una estimación."
            await send_message(platform, user_id, response, business_unit)
            return True

        elif intent == "actualizar_perfil":
            response = "Claro, ¿qué dato de tu perfil deseas actualizar? Ejemplo: nombre, email, experiencia, o expectativas salariales."
            await send_message(platform, user_id, response, business_unit)
            return True

        elif intent == "notificaciones":
            response = (
                "Puedo enviarte notificaciones automáticas sobre cambios en tus procesos. "
                "¿Quieres activarlas? Responde 'sí' para confirmar."
            )
            await send_message(platform, user_id, response, business_unit)
            await self.store_bot_message(event, response) # type: ignore
            return True

    return False  # Si no se manejó ningún intent

