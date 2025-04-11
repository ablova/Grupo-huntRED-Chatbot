# /home/pablo/app/chatbot/workflow/common.py

import logging
import re
from forex_python.converter import CurrencyRates
from app.chatbot.workflow.profile_questions import get_questions
from django.core.files.storage import default_storage
from app.utilidades.signature.pdf_generator import (
    generate_cv_pdf, generate_contract_pdf, merge_signed_documents, generate_candidate_summary
)
from app.utilidades.signature.digital_sign import request_digital_signature
from app.utilidades.salario import (
    calcular_neto, calcular_bruto, calcular_isr_mensual, calcular_cuotas_imss, 
    obtener_tipo_cambio, DATOS_PPA, DATOS_COLI, DATOS_BIGMAC, UMA_DIARIA_2025
)
from app.chatbot.integrations.services import send_email, send_message, send_options, send_image, send_email, GamificationService
from app.utilidades.signature.pdf_generator import generate_personality_report #Para crear el PDF e integrarlo al CV
from app.models import BusinessUnit, ConfiguracionBU, Person, ChatState
from django.conf import settings
from urllib.parse import urlparse
from asgiref.sync import sync_to_async
from app.chatbot.workflow.personality import TEST_QUESTIONS, get_questions_personality, get_random_tipi_questions

logger = logging.getLogger(__name__)



# =========================================================
# Ejecución de Pruebas
# =========================================================

PRUEBAS_POR_UNIDAD = {
    'amigro': [
        {'nombre': 'huntTIPI', 'descripcion': 'Prueba breve para conocer tus rasgos de personalidad.'},
        {'nombre': 'huntDISC', 'descripcion': 'Evalúa cómo te comportas en el trabajo.'}
    ],
    'huntu': [
        {'nombre': 'huntBigFive', 'descripcion': 'Explora tu personalidad y potencial profesional.'},
        {'nombre': 'huntMBTI', 'descripcion': 'Descubre tus preferencias laborales.'}
    ],
    'huntred': [
        {'nombre': 'hunt16PF', 'descripcion': 'Análisis detallado de tu personalidad y liderazgo.'},
        {'nombre': 'huntNEO', 'descripcion': 'Evalúa rasgos clave para la gestión.'}
    ],
    'huntred_executive': [
        {'nombre': 'huntDISC', 'descripcion': 'Evalúa tu estilo de liderazgo y toma de decisiones.'},
        {'nombre': 'huntBigFive', 'descripcion': 'Analiza tu personalidad con enfoque en liderazgo estratégico.'}
    ]
}
# Funciones Genéricas para Pruebas

async def iniciar_prueba(plataforma: str, user_id: str, test_type: str, domain: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia una prueba de personalidad genérica."""
    if not questions:
        await send_message(plataforma, user_id, "Error: No hay preguntas disponibles para esta prueba.", bu_name)
        estado_chat.state = "idle"
        await sync_to_async(estado_chat.save)()
        return
    estado_chat.state = f'taking_{test_type}'
    estado_chat.context['test_type'] = test_type
    estado_chat.context['domain'] = domain
    estado_chat.context['current_step'] = 0
    estado_chat.context['answers'] = {}
    await sync_to_async(estado_chat.save)()

    questions = get_questions_personality(test_type, domain)
    if test_type == 'huntTIPI':
        questions = get_random_tipi_questions(domain)
    first_step = list(questions.keys())[0] if test_type in ['huntBigFive', 'hunt16PF', 'huntNEO'] else None
    estado_chat.context['current_step_key'] = first_step

    await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)

async def enviar_pregunta(plataforma: str, user_id: str, test_type: str, domain: str, estado_chat: ChatState, unidad_negocio: BusinessUnit):
    """Envía la siguiente pregunta según el tipo de prueba."""
    questions = get_questions_personalitys(test_type, domain)
    if test_type == 'huntTIPI':
        questions = get_random_tipi_questions(domain)
    step = estado_chat.context['current_step']
    step_key = estado_chat.context.get('current_step_key')

    if test_type in ['huntBigFive', 'hunt16PF', 'huntNEO']:
        trait_questions = questions[step_key]
        if step < len(trait_questions):
            question = trait_questions[step]['text']
            options = trait_questions[step]['options']
            await send_message(plataforma, user_id, f'{question}\nOpciones: {", ".join(options)}', unidad_negocio.name.lower())
    elif test_type == 'huntDISC':
        if step < len(questions):
            question = questions[step]['text']
            options = questions[step]['options']
            await send_message(plataforma, user_id, f'{question}\nOpciones: {", ".join(options)}', unidad_negocio.name.lower())
    elif test_type == 'huntMBTI':
        if step < len(questions):
            question = questions[step]['text']
            options = questions[step]['options']
            await send_message(plataforma, user_id, f'{question}\nOpciones: {", ".join(options)}', unidad_negocio.name.lower())
    elif test_type == 'huntTIPI':
        trait = list(questions.keys())[step // 2]
        q_idx = step % 2
        question = questions[trait][q_idx]['text']
        options = ['1 - Muy en desacuerdo', '2', '3', '4', '5', '6', '7 - Muy de acuerdo']
        await send_message(plataforma, user_id, f'{question}\nOpciones: {", ".join(options)}', unidad_negocio.name.lower())

async def manejar_respuesta_prueba(plataforma: str, user_id: str, texto: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Maneja las respuestas de cualquier prueba."""
    test_type = estado_chat.context.get('test_type')
    if not test_type or estado_chat.state != f'taking_{test_type}':
        return False

    domain = estado_chat.context['domain']
    questions = get_questions_personality(test_type, domain)
    if test_type == 'huntTIPI':
        questions = get_random_tipi_questions(domain)
    step = estado_chat.context['current_step']
    step_key = estado_chat.context.get('current_step_key')

    # Validar respuesta
    valid_range = range(1, 6) if test_type in ['huntBigFive', 'hunt16PF', 'huntNEO'] else range(1, 4) if test_type == 'huntMBTI' else range(1, 8) if test_type == 'huntTIPI' else None
    options = ['a', 'b', 'c', 'd'] if test_type == 'huntDISC' else None
    try:
        respuesta = texto.lower() if test_type == 'huntDISC' else int(texto)
        if (valid_range and respuesta not in valid_range) or (options and respuesta not in options):
            await send_message(plataforma, user_id, f'Por favor, responde con una opción válida.', unidad_negocio.name.lower())
            return True
    except ValueError:
        await send_message(plataforma, user_id, f'Por favor, responde con una opción válida.', unidad_negocio.name.lower())
        return True

    # Guardar respuesta
    if test_type in ['huntBigFive', 'hunt16PF', 'huntNEO']:
        if step_key not in estado_chat.context['answers']:
            estado_chat.context['answers'][step_key] = []
        estado_chat.context['answers'][step_key].append(respuesta)
    else:
        estado_chat.context['answers'][step] = respuesta

    # Avanzar
    estado_chat.context['current_step'] += 1
    if test_type in ['huntBigFive', 'hunt16PF', 'huntNEO']:
        trait_questions = questions[step_key]
        if estado_chat.context['current_step'] < len(trait_questions):
            await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)
        else:
            traits = list(questions.keys())
            current_idx = traits.index(step_key)
            if current_idx + 1 < len(traits):
                estado_chat.context['current_step'] = 0
                estado_chat.context['current_step_key'] = traits[current_idx + 1]
                await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)
            else:
                await finalizar_prueba(plataforma, user_id, test_type, estado_chat, persona, unidad_negocio)
    else:
        if estado_chat.context['current_step'] < (len(questions) if test_type in ['huntDISC', 'huntMBTI'] else len(questions) * 2):
            await enviar_pregunta(plataforma, user_id, test_type, domain, estado_chat, unidad_negocio)
        else:
            await finalizar_prueba(plataforma, user_id, test_type, estado_chat, persona, unidad_negocio)
    await sync_to_async(estado_chat.save)()
    return True

async def finalizar_prueba(plataforma: str, user_id: str, test_type: str, estado_chat: ChatState, persona: Person, unidad_negocio: BusinessUnit):
    """Calcula y guarda los resultados de la prueba."""
    answers = estado_chat.context.get('answers', {})
    if test_type == 'huntBigFive' or test_type == 'huntNEO':
        for trait, responses in answers.items():
            score = sum(responses) / len(responses)
            setattr(persona, {'apertura': 'openness', 'conciencia': 'conscientiousness', 'extraversion': 'extraversion', 'amabilidad': 'agreeableness', 'neuroticismo': 'neuroticism'}[trait], score)
    elif test_type == 'huntDISC':
        d, i, s, c = 0, 0, 0, 0
        for ans in answers.values():
            if ans == 'a': d += 1
            elif ans == 'b': i += 1
            elif ans == 'c': s += 1
            elif ans == 'd': c += 1
        persona.metadata['disc'] = f'D{d}I{i}S{s}C{c}'
    elif test_type == 'hunt16PF':
        for trait, responses in answers.items():
            score = sum(responses) / len(responses)
            persona.metadata[f'16pf_{trait}'] = score
    elif test_type == 'huntMBTI':
        ei = sum(answers[0:2]) / 2; sn = sum(answers[2:4]) / 2; tf = sum(answers[4:6]) / 2; jp = sum(answers[6:8]) / 2
        persona.mbti_type = ('E' if ei < 2 else 'I') + ('S' if sn < 2 else 'N') + ('T' if tf < 2 else 'F') + ('J' if jp < 2 else 'P')
    elif test_type == 'huntTIPI':
        for idx, trait in enumerate(['extraversion', 'agreeableness', 'conscientiousness', 'neuroticism', 'openness']):
            direct = answers[idx * 2]; reverse = 8 - answers[idx * 2 + 1]
            score = (direct + reverse) / 2
            setattr(persona, {'extraversion': 'extraversion', 'agreeableness': 'agreeableness', 'conscientiousness': 'conscientiousness', 'neuroticism': 'neuroticism', 'openness': 'openness'}[trait], score)
    await sync_to_async(persona.save)()
    await send_message(plataforma, user_id, f'¡Gracias por completar la prueba {test_type}! Tus resultados han sido guardados.', unidad_negocio.name.lower())
    
    # Generar y enviar reporte
    report_path = generate_personality_report(persona, unidad_negocio)
    await send_image(plataforma, user_id, "Aquí está tu reporte de personalidad", report_path, unidad_negocio.name)
    
    # Notificación por email con el reporte adjunto
    email_body = f"Hola {persona.nombre},<br>Has completado la prueba {test_type} con {unidad_negocio.name}. ¡Gracias por participar!<br>Adjunto encontrarás tu reporte de personalidad en PDF.<br>Saludos,<br>Equipo {unidad_negocio.name}"
    await send_email(
        subject=f"Prueba de Personalidad Completada - {unidad_negocio.name}",
        to_email=persona.email,
        body=email_body,
        business_unit_name=unidad_negocio.name,
        attachments=[report_path]
    )
    # Limpiar archivo temporal
    import os
    os.remove(report_path)

    # Gamificación: otorgar puntos
    gamification_service = GamificationService()
    await gamification_service.award_points(persona, f"prueba_{test_type}", points=100)
    
    # Actualizar estado y notificar
    estado_chat.state = 'idle'
    await sync_to_async(estado_chat.save)()
    
    # Manejo de respuestas durante una prueba de personalidad
    if await manejar_respuesta_prueba(plataforma, user_id, texto, unidad_negocio, estado_chat, persona):
        return True

    # Manejo de respuestas para campos específicos del perfil
    if estado_chat.state.startswith("waiting_for_"):
        field = estado_chat.state.replace("waiting_for_", "")
        if field in ['nombre', 'apellido_paterno', 'email', 'phone', 'nacionalidad']:
            # Validaciones específicas
            if field == 'email' and not re.match(r"[^@]+@[^@]+\.[^@]+", texto):
                await send_message(plataforma, user_id, "Por favor, ingresa un email válido.", bu_name)
                return True
            if field == 'phone' and not re.match(r"^\+\d{10,15}$", texto):
                await send_message(plataforma, user_id, "Por favor, usa el formato '+521234567890'.", bu_name)
                return True
            # Guardar el valor en el objeto persona
            setattr(persona, field, texto.capitalize() if field in ['nombre', 'apellido_paterno'] else texto)
            await sync_to_async(persona.save)()
            # Continuar según la unidad de negocio
            if bu_name == "amigro":
                from app.chatbot.workflow.amigro import continuar_perfil_amigro
                await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
            elif bu_name == "huntu":
                from app.chatbot.workflow.huntu import continuar_perfil_huntu
                await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
            else:
                await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)
        return True

    return False

async def ofrecer_prueba_personalidad(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, mensaje_base: str = ""):
    """Ofrece una prueba de personalidad al usuario."""
    bu_name = unidad_negocio.name.lower()
    pruebas = PRUEBAS_POR_UNIDAD.get(bu_name, [])
    if pruebas:
        mensaje = mensaje_base + f"Para {bu_name}, te recomendamos:\n" + "\n".join(
            [f"{i+1}. {p['nombre']} - {p['descripcion']}" for i, p in enumerate(pruebas)]
        ) + "\nResponde con el número de la prueba o 'No' para omitir."
    else:
        mensaje = "¡Perfil completo! 🎉\nPronto te contactaremos con oportunidades."
        estado_chat.state = "completed"
    await send_message(plataforma, user_id, mensaje, bu_name)
    if pruebas:
        estado_chat.state = "offering_personality_test"
    await sync_to_async(estado_chat.save)()
 


# =========================================================
# Creación de Perfil 
# =========================================================
# Diccionario de explicaciones para los métodos de creación de perfil
EXPLICACIONES_METODOS = {
    "default": {
        "dynamic": "Te haré preguntas una por una para completar tu perfil paso a paso.",
        "template": "Te enviaré un formulario inteligente para que llenes tus datos de una vez (solo en WhatsApp).",
        "cv": "Envía tu CV y extraeré automáticamente la información para tu perfil."
    },
    "amigro": {
        "dynamic": "Ideal si prefieres una conversación guiada sobre tu situación migratoria y experiencia.",
        "template": "Perfecto si quieres ingresar tus datos rápidamente en un solo paso (solo en WhatsApp).",
        "cv": "Si ya tienes un CV, puedo analizarlo para ahorrarte tiempo."
    },
    "huntu": {
        "dynamic": "Te guiaré para destacar tus habilidades como recién egresado.",
        "template": "Llena un formulario rápido para enfocarte en tus logros académicos (solo en WhatsApp).",
        "cv": "Envía tu CV y lo adaptaré a las oportunidades para jóvenes profesionales."
    },
    "huntred": {
        "dynamic": "Te ayudaré a detallar tu experiencia profesional paso a paso.",
        "template": "Ingresa tus datos clave en un formulario rápido (solo en WhatsApp).",
        "cv": "Sube tu CV y lo analizaré para encontrar las mejores vacantes ejecutivas."
    }
}

def obtener_explicaciones_metodos(bu_name: str) -> dict:
    """Devuelve las explicaciones de los métodos según la unidad de negocio."""
    return EXPLICACIONES_METODOS.get(bu_name.lower(), EXPLICACIONES_METODOS["default"])

async def iniciar_perfil_conversacional(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia o continúa el perfil conversacional (simplificado para este ejemplo)."""
    bu_name = unidad_negocio.name.lower()
    mensaje = "¡Perfil completo! 🎉\nRealizar una prueba de personalidad puede destacar tu perfil.\n"
    await ofrecer_prueba_personalidad(plataforma, user_id, unidad_negocio, estado_chat, persona, mensaje)

async def iniciar_creacion_perfil(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Inicia el proceso de creación de perfil, ofreciendo opciones según la unidad de negocio."""
    bu_name = unidad_negocio.name.lower()
    explicaciones = obtener_explicaciones_metodos(bu_name)
    
    # Opciones por unidad de negocio
    if bu_name in ["huntred", "huntred_executive", "huntu"]:
        opciones = [
            "1. Dinámico: " + explicaciones["dynamic"],
            "2. Template: " + explicaciones["template"] + " (solo WhatsApp)",
            "3. CV: " + explicaciones["cv"],
            "4. LinkedIn: Vincula tu perfil de LinkedIn para una creación rápida."
        ]
    elif bu_name == "amigro":
        opciones = [
            "1. Dinámico: " + explicaciones["dynamic"],
            "2. Template: " + explicaciones["template"] + " (solo WhatsApp)"
        ]
    else:
        opciones = [
            "1. Dinámico: " + explicaciones["dynamic"],
            "2. Template: " + explicaciones["template"] + " (solo WhatsApp)",
            "3. CV: " + explicaciones["cv"]
        ]
    
    mensaje = "Elige cómo crear tu perfil:\n" + "\n".join(opciones)
    await send_message(plataforma, user_id, mensaje, bu_name)
    estado_chat.state = "selecting_profile_method"
    await sync_to_async(estado_chat.save)()

async def manejar_respuesta_perfil(plataforma: str, user_id: str, texto: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, gpt_handler=None):
    """Maneja la respuesta del usuario según el estado del chat."""
    bu_name = unidad_negocio.name.lower()
    GPT_ENABLED = settings.GPT_ENABLED
    
    texto = texto.strip()
    texto_lower = texto.lower()
    
    # Manejo de estados de validación específicos de campo
    if estado_chat.state.startswith("waiting_for_"):
        field = estado_chat.state.replace("waiting_for_", "")
        
        if field == "phone":
            try:
                # Parsear y validar el número de teléfono
                parsed_phone = phonenumbers.parse(texto, "MX")  # Ajusta "MX" según el país
                if not phonenumbers.is_valid_number(parsed_phone):
                    raise ValueError("Número de teléfono no válido")
                # Formatear a E.164
                texto = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
                persona.phone = texto
                logger.info(f"Teléfono válido registrado para {user_id}: {texto}")
                
                # Continuar con el siguiente campo o estado
                await send_message(plataforma, user_id, f"¡Teléfono registrado correctamente!", bu_name)
                estado_chat.state = estado_chat.context.get('next_field', 'profile_in_progress')
                await sync_to_async(estado_chat.save)()
                return await continuar_registro(plataforma, user_id, unidad_negocio, estado_chat, persona)
            except Exception as e:
                logger.warning(f"Invalid phone number for {user_id}: {texto} - Error: {str(e)}")
                await send_message(plataforma, user_id, "El número de teléfono no es válido. Usa el formato internacional, como '+521234567890'.", bu_name)
                return True
        
        elif field == "email":
            if not re.match(r"[^@]+@[^@]+\.[^@]+", texto):
                logger.warning(f"Invalid email for {user_id}: {texto}")
                await send_message(plataforma, user_id, "Por favor, ingresa un email válido.", bu_name)
                return True
            persona.email = texto
            logger.info(f"Email válido registrado para {user_id}: {texto}")
            
            # Continuar con el siguiente campo o estado
            await send_message(plataforma, user_id, f"¡Email registrado correctamente!", bu_name)
            estado_chat.state = estado_chat.context.get('next_field', 'profile_in_progress')
            await sync_to_async(estado_chat.save)()
            return await continuar_registro(plataforma, user_id, unidad_negocio, estado_chat, persona)
        
        elif field == "name":
            if len(texto.split()) < 2:
                logger.warning(f"Invalid name for {user_id}: {texto} - Missing last name")
                await send_message(plataforma, user_id, "Por favor, ingresa tu nombre completo (nombre y apellido).", bu_name)
                return True
            persona.name = texto
            logger.info(f"Nombre registrado para {user_id}: {texto}")
            
            # Continuar con el siguiente campo
            await send_message(plataforma, user_id, f"¡Nombre registrado correctamente!", bu_name)
            estado_chat.state = estado_chat.context.get('next_field', 'profile_in_progress')
            await sync_to_async(estado_chat.save)()
            return await continuar_registro(plataforma, user_id, unidad_negocio, estado_chat, persona)
        
        elif field == "cv":
            # Procesar el CV adjunto
            parser = CVParser(unidad_negocio)
            try:
                from pathlib import Path
                file_path = Path(texto)  # En un caso real, esto vendría de un upload
                cv_text = parser.extract_text_from_file(file_path)
                if cv_text:
                    parsed_data = parser.parse(cv_text)
                    if parsed_data:
                        for key, value in parsed_data.items():
                            if key in ["email", "phone"] and value:
                                # Validar email y teléfono antes de guardarlos
                                if key == "email" and re.match(r"[^@]+@[^@]+\.[^@]+", value):
                                    setattr(persona, key, value)
                                elif key == "phone":
                                    try:
                                        parsed_phone = phonenumbers.parse(value, "MX")
                                        if phonenumbers.is_valid_number(parsed_phone):
                                            formatted_phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
                                            setattr(persona, key, formatted_phone)
                                    except:
                                        pass  # No guardamos números inválidos del CV
                            elif key == "skills":
                                persona.metadata["skills"] = value
                            elif key == "experience":
                                persona.metadata["experience"] = value
                            elif key == "education":
                                persona.metadata["education"] = value
                        persona.cv_file = str(file_path)
                        persona.cv_parsed = True
                        persona.cv_analysis = parsed_data
                        persona.metadata["last_cv_update"] = now().isoformat()
                        await sync_to_async(persona.save)()
                        await send_message(plataforma, user_id, "Tu CV ha sido procesado y tu perfil actualizado.", bu_name)
                        estado_chat.state = "offering_personality_test"
                        await sync_to_async(estado_chat.save)()
                        await ofrecer_prueba_personalidad(plataforma, user_id, unidad_negocio, estado_chat, persona)
                    else:
                        await send_message(plataforma, user_id, "No se pudo extraer información de tu CV. Intenta con otro método.", bu_name)
                        estado_chat.state = "selecting_profile_method"
                        await sync_to_async(estado_chat.save)()
                else:
                    await send_message(plataforma, user_id, "No se pudo leer tu CV. Asegúrate de enviar un PDF o Word válido.", bu_name)
            except Exception as e:
                logger.error(f"Error processing CV for {user_id}: {str(e)}")
                await send_message(plataforma, user_id, f"Error procesando tu CV: {str(e)}. Intenta de nuevo.", bu_name)
                estado_chat.state = "selecting_profile_method"
                await sync_to_async(estado_chat.save)()
            return True
        
        elif field == "linkedin":
            # Procesar la URL de LinkedIn
            linkedin_url = texto
            if not re.match(r"^https?://([a-z]{2,3}\.)?linkedin\.com/.*", linkedin_url, re.IGNORECASE):
                logger.warning(f"Invalid LinkedIn URL for {user_id}: {linkedin_url}")
                await send_message(plataforma, user_id, "Por favor, proporciona una URL válida de LinkedIn (ej: https://linkedin.com/in/tu-perfil).", bu_name)
                return True
                
            try:
                scraped_data = await scrape_linkedin_profile(linkedin_url, bu_name)
                if scraped_data:
                    # Validar datos obtenidos del scraping
                    if "email" in scraped_data and scraped_data["email"]:
                        if re.match(r"[^@]+@[^@]+\.[^@]+", scraped_data["email"]):
                            persona.email = scraped_data["email"]
                    if "phone" in scraped_data and scraped_data["phone"]:
                        try:
                            parsed_phone = phonenumbers.parse(scraped_data["phone"], "MX")
                            if phonenumbers.is_valid_number(parsed_phone):
                                persona.phone = phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
                        except:
                            pass  # Ignoramos números inválidos
                            
                    update_person_from_scrape(persona, scraped_data)
                    persona.metadata["linkedin_url"] = linkedin_url
                    await sync_to_async(persona.save)()
                    await send_message(plataforma, user_id, "Tu perfil de LinkedIn ha sido procesado y tu perfil actualizado.", bu_name)
                    estado_chat.state = "offering_personality_test"
                    await sync_to_async(estado_chat.save)()
                    await ofrecer_prueba_personalidad(plataforma, user_id, unidad_negocio, estado_chat, persona)
                else:
                    await send_message(plataforma, user_id, "No se pudo procesar tu perfil de LinkedIn. Intenta con otro método.", bu_name)
                    estado_chat.state = "selecting_profile_method"
                    await sync_to_async(estado_chat.save)()
            except Exception as e:
                logger.error(f"Error processing LinkedIn for {user_id}: {str(e)}")
                await send_message(plataforma, user_id, f"Error procesando LinkedIn: {str(e)}. Intenta de nuevo.", bu_name)
                estado_chat.state = "selecting_profile_method"
                await sync_to_async(estado_chat.save)()
            return True
        
        # Manejar otros campos específicos que requieran validación
        return True
    
    # Resto de la lógica original
    elif estado_chat.state == "selecting_profile_method":
        try:
            seleccion = int(texto)
            if seleccion == 1:  # Dinámico
                estado_chat.context['use_gpt'] = GPT_ENABLED and gpt_handler is not None
                await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)
            elif seleccion == 2 and plataforma == "whatsapp":  # Template
                template_name = f"registro_{bu_name}"
                await send_whatsapp_template(user_id, template_name, unidad_negocio)
                estado_chat.state = "waiting_for_template_response"
                await sync_to_async(estado_chat.save)()
            elif seleccion == 3 and bu_name != "amigro":  # CV
                await send_message(plataforma, user_id, "Por favor, envía tu CV como archivo adjunto (PDF o Word).", bu_name)
                estado_chat.state = "waiting_for_cv"
                await sync_to_async(estado_chat.save)()
            elif seleccion == 4 and bu_name in ["huntred", "huntred_executive", "huntu"]:  # LinkedIn
                await send_message(plataforma, user_id, "Proporciona la URL de tu perfil de LinkedIn.", bu_name)
                estado_chat.state = "waiting_for_linkedin"
                await sync_to_async(estado_chat.save)()
            else:
                await send_message(plataforma, user_id, "Selecciona una opción válida.", bu_name)
        except ValueError:
            await send_message(plataforma, user_id, "Por favor, responde con un número válido.", bu_name)
        return True
    
    elif estado_chat.state == "offering_personality_test":
        if texto_lower == "no":
            await send_message(plataforma, user_id, "¡Perfil completo! 🎉 Pronto te contactaremos con oportunidades.", bu_name)
            estado_chat.state = "completed"
            await sync_to_async(estado_chat.save)()
        else:
            try:
                seleccion = int(texto) - 1
                pruebas = PRUEBAS_POR_UNIDAD.get(bu_name, [])
                if 0 <= seleccion < len(pruebas):
                    prueba = pruebas[seleccion]["nombre"]
                    await send_message(plataforma, user_id, f"Has elegido {prueba}. Te enviaremos el enlace pronto.", bu_name)
                    estado_chat.state = "completed"
                    await sync_to_async(estado_chat.save)()
                else:
                    await send_message(plataforma, user_id, "Selecciona una opción válida o 'No' para omitir.", bu_name)
            except ValueError:
                await send_message(plataforma, user_id, "Responde con un número válido o 'No'.", bu_name)
        return True
    
    # Corrección de datos
    elif texto.startswith("corregir "):
        campo = texto.split(" ")[1]
        campos_validos = ["nombre", "apellido_paterno", "email", "phone"]
        if campo in campos_validos:
            estado_chat.state = f"waiting_for_{campo}"
            await sync_to_async(estado_chat.save)()
            await send_message(plataforma, user_id, f"Por favor, ingresa tu nuevo {campo}.", bu_name)
            return True
        else:
            await send_message(plataforma, user_id, "Campo no válido. Usa: nombre, apellido_paterno, email o phone.", bu_name)
            return True
    return False

async def continuar_registro(plataforma: str, user_id: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person):
    """Determina y ejecuta el siguiente paso en el proceso de registro."""
    bu_name = unidad_negocio.name.lower()
    
    # Verificar qué información falta
    campos_faltantes = []
    
    if not persona.email:
        campos_faltantes.append("email")
    if not persona.phone:
        campos_faltantes.append("phone")
    if not persona.name:
        campos_faltantes.append("name")
    
    if campos_faltantes:
        # Selecciona el primer campo faltante
        next_field = campos_faltantes[0]
        estado_chat.state = f"waiting_for_{next_field}"
        
        # Guarda el campo siguiente si hay más de uno
        if len(campos_faltantes) > 1:
            estado_chat.context['next_field'] = f"waiting_for_{campos_faltantes[1]}"
        else:
            estado_chat.context['next_field'] = "profile_completed"
        
        await sync_to_async(estado_chat.save)()
        
        # Solicita el siguiente campo
        messages = {
            "name": "Por favor, ingresa tu nombre completo (nombre y apellido).",
            "email": "Por favor, ingresa tu dirección de correo electrónico.",
            "phone": "Por favor, ingresa tu número de teléfono con formato internacional (ej: +521234567890)."
        }
        
        await send_message(plataforma, user_id, messages[next_field], bu_name)
        return True
    
    # Si ya están todos los campos básicos, ofrecer prueba de personalidad
    await send_message(plataforma, user_id, "¡Perfil básico completado! 🎉", bu_name)
    estado_chat.state = "offering_personality_test"
    await sync_to_async(estado_chat.save)()
    await ofrecer_prueba_personalidad(plataforma, user_id, unidad_negocio, estado_chat, persona)
    return True
  
async def procesar_respuesta_con_gpt(plataforma: str, user_id: str, texto: str, unidad_negocio: BusinessUnit, estado_chat: ChatState, persona: Person, gpt_handler):
    """Procesa respuestas en el flujo dinámico usando GPT."""
    bu_name = unidad_negocio.name.lower()
    field = estado_chat.state.replace("waiting_for_", "")
    prompt = (
        f"El usuario está proporcionando su {field} en un flujo conversacional. "
        f"Su respuesta fue: '{texto}'. Extrae el valor correspondiente para {field} de manera precisa. "
        f"Devuelve solo el valor extraído en texto plano, o 'NO_ENTENDIDO' si no se pudo interpretar."
    )
    respuesta_gpt = await gpt_handler.generate_response(prompt, unidad_negocio)

    if respuesta_gpt.strip() == "NO_ENTENDIDO":
        await send_message(plataforma, user_id, f"No entendí tu {field}. Por favor, intenta de nuevo.", bu_name)
        return

    if field == 'email' and not re.match(r"[^@]+@[^@]+\.[^@]+", respuesta_gpt):
        await send_message(plataforma, user_id, "Por favor, ingresa un email válido.", bu_name)
        return

    if field in ['nombre', 'apellido_paterno']:
        setattr(persona, field, respuesta_gpt.capitalize())
    else:
        setattr(persona, field, respuesta_gpt)
    await sync_to_async(persona.save)()

    if bu_name == "amigro":
        from app.chatbot.workflow.amigro import continuar_perfil_amigro
        await continuar_perfil_amigro(plataforma, user_id, unidad_negocio, estado_chat, persona)
    elif bu_name == "huntu":
        from app.chatbot.workflow.huntu import continuar_perfil_huntu
        await continuar_perfil_huntu(plataforma, user_id, unidad_negocio, estado_chat, persona)
    else:
        await iniciar_perfil_conversacional(plataforma, user_id, unidad_negocio, estado_chat, persona)

async def obtener_resumen_perfil(persona: Person) -> str:
    """Genera un resumen del perfil del usuario."""
    info_fields = {
        "Nombre": persona.nombre,
        "Apellido Paterno": persona.apellido_paterno,
        "Apellido Materno": persona.apellido_materno,
        "Email": persona.email,
        "Teléfono": persona.phone,
        "Nacionalidad": persona.nacionalidad,
        "Estatus Migratorio": persona.metadata.get('migratory_status') if 'migratory_status' in persona.metadata else None,
        "Experiencia Laboral": persona.work_experience
    }
    recap_lines = ["Recapitulación de tu información:"]
    faltante = []
    for etiqueta, valor in info_fields.items():
        if valor:
            recap_lines.append(f"{etiqueta}: {valor}")
        else:
            faltante.append(etiqueta)
    if faltante:
        recap_lines.append("\nInformación faltante: " + ", ".join(faltante))
    else:
        recap_lines.append("\nToda la información está completa.")
    recap_lines.append("\n¿Es correcta esta información? Responde 'Sí' o 'No'.")
    return "\n".join(recap_lines)

def send_welcome_message(user_id, platform, business_unit):
    """ Envía un mensaje de bienvenida, el logo de la unidad y el menú de servicios. """
    # Obtener el nombre de la unidad de negocio
    business_unit_name = business_unit.name.lower()

    # Definir el mensaje de bienvenida
    welcome_messages = {
        "huntred": "Bienvenido a huntRED® 🚀\nSomos expertos en encontrar el mejor talento para empresas líderes.",
        "huntred_executive": "Bienvenido a huntRED® Executive 🌟\nNos especializamos en colocación de altos ejecutivos.",
        "huntu": "Bienvenido a huntU® 🏆\nConectamos talento joven con oportunidades de alto impacto.",
        "amigro": "Bienvenido a Amigro® 🌍\nFacilitamos el acceso laboral a migrantes en Latinoamérica.",
        "sexsi": "Bienvenido a SEXSI 🔐\nAquí puedes gestionar acuerdos de consentimiento seguros y firmarlos digitalmente.",
    }

    # Obtener el logo de la unidad de negocio
    logo_urls = {
        "huntred": settings.MEDIA_URL + "huntred.png",
        "huntred_executive": settings.MEDIA_URL + "executive.png",
        "huntu": settings.MEDIA_URL + "huntu.png",
        "amigro": settings.MEDIA_URL + "amigro.png",
        "sexsi": settings.MEDIA_URL + "sexsi.png",
    }

    welcome_message = welcome_messages.get(business_unit_name, "Bienvenido a nuestra plataforma 🎉")
    logo_url = logo_urls.get(business_unit_name, settings.MEDIA_URL + "Grupo_huntRED.png")

    # Enviar mensaje de bienvenida
    send_message(platform, user_id, welcome_message, business_unit)

    # Enviar logo de la unidad de negocio
    send_image(platform, user_id, "Aquí tienes nuestro logo 📌", logo_url, business_unit)

    # Enviar menú de servicios
    send_menu(platform, user_id, business_unit)

    return "Mensaje de bienvenida enviado correctamente."

def generate_and_send_contract(candidate, client, job_position, business_unit):
    """
    Genera la Carta Propuesta para el candidato y la envía para su firma digital.
    En Huntu y HuntRED®, también se envía al cliente para su firma.
    """
    contract_path = generate_contract_pdf(candidate, client, job_position, business_unit)

    # Enviar contrato al candidato para firma digital
    request_digital_signature(
        user=candidate,
        document_path=contract_path,
        document_name=f"Carta Propuesta - {job_position.title}.pdf"
    )

    # Enviar al cliente en Huntu y HuntRED®
    if business_unit.name.lower() in ["huntu", "huntred"]:
        request_digital_signature(
            user=client,
            document_path=contract_path,
            document_name=f"Carta Propuesta - {job_position.title}.pdf"
        )

    return contract_path

def send_candidate_summary(candidate, client):
    """ Genera y envía el resumen del candidato al cliente """
    file_path = generate_candidate_summary(candidate)

    send_email(
        to=client.contact_email,
        subject=f"Resumen del candidato {candidate.full_name} - {candidate.position}",
        body="Adjunto encontrarás el resumen del candidato.",
        attachments=[file_path]
    )

    return f"Resumen de {candidate.full_name} enviado a {client.contact_email}"

def generate_final_signed_contract(candidate, business_unit):
    """
    Genera el reporte final consolidando el PDF con todas las firmas.
    """
    contract_path = f"{business_unit.name.lower()}/contracts/{candidate.id}.pdf"
    signed_path = f"{business_unit.name.lower()}/contracts/signed_{candidate.id}.pdf"

    try:
        # Unir documentos firmados
        merge_signed_documents(contract_path, signed_path)

        # Guardar archivo final
        default_storage.save(signed_path, open(signed_path, "rb"))

        return signed_path
    except Exception as e:
        return f"Error al generar documento firmado: {e}"


CURRENCY_MAP = {
    # Estados Unidos
    'usd': 'USD', 'dólar': 'USD', 'dolar': 'USD', 'dolares': 'USD', 'dólares': 'USD',
    # México
    'mxn': 'MXN', 'peso': 'MXN', 'pesos': 'MXN', 'peso mexicano': 'MXN', 'pesos mexicanos': 'MXN',
    # Nicaragua
    'nio': 'NIO', 'córdoba': 'NIO', 'cordoba': 'NIO', 'cordobas': 'NIO', 'córdobas': 'NIO',
    # Colombia
    'cop': 'COP', 'peso colombiano': 'COP', 'pesos colombianos': 'COP',
    # Argentina
    'ars': 'ARS', 'peso argentino': 'ARS', 'pesos argentinos': 'ARS',
    # Brasil
    'brl': 'BRL', 'real': 'BRL', 'reales': 'BRL',
    # Chile
    'clp': 'CLP', 'peso chileno': 'CLP', 'pesos chilenos': 'CLP',
    # Ecuador (actualmente usa USD, anteriormente Sucre - ECS)
    'ecs': 'ECS', 'sucre': 'ECS', 'sucres': 'ECS',
    # Perú
    'pen': 'PEN', 'sol': 'PEN', 'soles': 'PEN', 'sol peruano': 'PEN', 'soles peruanos': 'PEN',
    # Uruguay
    'uyu': 'UYU', 'peso uruguayo': 'UYU', 'pesos uruguayos': 'UYU',
    # Paraguay
    'pyg': 'PYG', 'guaraní': 'PYG', 'guarani': 'PYG', 'guaranies': 'PYG', 'guaraníes': 'PYG',
    # Panamá (oficial USD, también usa balboa - PAB)
    'pab': 'PAB', 'balboa': 'PAB', 'balboas': 'PAB',
    # República Dominicana
    'dop': 'DOP', 'peso dominicano': 'DOP', 'pesos dominicanos': 'DOP',
    # Bolivia
    'bob': 'BOB', 'boliviano': 'BOB', 'bolivianos': 'BOB',
    # Cuba
    'cup': 'CUP', 'peso cubano': 'CUP', 'pesos cubanos': 'CUP',
    # Costa Rica
    'crc': 'CRC', 'colón': 'CRC', 'colon': 'CRC', 'colones': 'CRC',
    # Guatemala
    'gtq': 'GTQ', 'quetzal': 'GTQ', 'quetzales': 'GTQ',
    # Haití
    'htg': 'HTG', 'gourde': 'HTG', 'gourdes': 'HTG',
    # Honduras
    'hnl': 'HNL', 'lempira': 'HNL', 'lempiras': 'HNL',
    # India (alta migración global hacia EE.UU.)
    'inr': 'INR', 'rupia': 'INR', 'rupias': 'INR', 'rupia india': 'INR',
    # China (ya incluida, pero relevante para migración)
    'cny': 'CNY', 'yuan': 'CNY', 'renminbi': 'CNY',
    # Filipinas (alta migración hacia EE.UU.)
    'php': 'PHP', 'peso filipino': 'PHP', 'pesos filipinos': 'PHP',
    # Principales monedas internacionales
    'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
    'gbp': 'GBP', 'libra esterlina': 'GBP', 'libras esterlinas': 'GBP', 'libra': 'GBP',
    'cad': 'CAD', 'dólar canadiense': 'CAD', 'dolar canadiense': 'CAD',
    'jpy': 'JPY', 'yen': 'JPY', 'yenes': 'JPY',
    'cny': 'CNY', 'yuan': 'CNY', 'renminbi': 'CNY',
    'chf': 'CHF', 'franco suizo': 'CHF', 'francos suizos': 'CHF',
    'aud': 'AUD', 'dólar australiano': 'AUD', 'dolar australiano': 'AUD',

    # Opcional: Criptomonedas principales
    'btc': 'BTC', 'bitcoin': 'BTC', 'bitcoins': 'BTC',
    'eth': 'ETH', 'ethereum': 'ETH',
    'usdt': 'USDT', 'tether': 'USDT',
}

def normalizar_numero(valor_str):
    """Convierte un string numérico (ej. '10k', '12,345.67') a float."""
    try:
        valor_str = valor_str.lower().replace(',', '')
        if 'k' in valor_str:
            return float(valor_str.replace('k', '')) * 1000
        return float(valor_str)
    except (ValueError, AttributeError):
        return 0.0  # Valor por defecto si falla la conversión

def extraer_moneda(mensaje):
    """Extrae la moneda del mensaje usando CURRENCY_MAP."""
    mensaje = mensaje.lower()
    for key, value in CURRENCY_MAP.items():
        if key in mensaje:
            return value
    return 'MXN'  # Por defecto

def parsear_mensaje(mensaje):
    """Parsea el mensaje para extraer datos de salario."""
    data = {}
    mensaje = mensaje.lower()

    # Buscar salario bruto
    match_bruto = re.search(r'salario[-\s]?bruto\s*=\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_bruto:
        data['salario_bruto'] = normalizar_numero(match_bruto.group(1))
        data['tipo'] = 'bruto'
    
    # Buscar salario neto
    match_neto = re.search(r'salario[-\s]?neto\s*=\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_neto:
        data['salario_neto'] = normalizar_numero(match_neto.group(1))
        data['tipo'] = 'neto'

    # Si no se especifica bruto o neto, buscar un valor genérico
    if 'salario_bruto' not in data and 'salario_neto' not in data:
        match_valor = re.search(r'(\d+(?:[,\.]\d+)?k?)', mensaje)
        if match_valor:
            data['salario_bruto'] = normalizar_numero(match_valor.group(1))
            data['tipo'] = 'bruto'  # Por defecto

    # Frecuencia
    if 'hora' in mensaje:
        data['frecuencia'] = 'hora'
    elif 'semanal' in mensaje:
        data['frecuencia'] = 'semanal'
    elif 'quincenal' in mensaje:
        data['frecuencia'] = 'quincenal'
    elif 'mensual' in mensaje:
        data['frecuencia'] = 'mensual'
    elif 'anual' in mensaje:
        data['frecuencia'] = 'anual'
    else:
        data['frecuencia'] = 'mensual'  # Por defecto

    # Moneda
    data['moneda'] = extraer_moneda(mensaje)

    # Bono
    match_bono = re.search(r'(\d+)\s*mes(?:es)?\s*de\s*bono', mensaje, re.IGNORECASE)
    if match_bono:
        data['bono'] = int(match_bono.group(1))
    else:
        data['bono'] = 0

    # Prestaciones adicionales
    if re.search(r'sin prestaciones adicionales', mensaje, re.IGNORECASE):
        data['prestaciones_adicionales'] = False
    else:
        data['prestaciones_adicionales'] = True

    # Prestaciones específicas
    match_vales = re.search(r'vales\s*(?:de)?\s*([\d,\.]+k?)', mensaje, re.IGNORECASE)
    if match_vales:
        data['monto_vales'] = normalizar_numero(match_vales.group(1))
    else:
        data['monto_vales'] = 0.0

    data['fondo_ahorro'] = 'fondo de ahorro' in mensaje.lower()

    return data

def get_business_unit_domain(business_unit):
    domains = {
        "huntred": "huntred.com",
        "huntred_executive": "executive.huntred.com",
        "huntu": "huntu.com",
        "amigro": "amigro.com",
        "sexsi": "sexsi.com"
    }
    return domains.get(business_unit.name.lower() if hasattr(business_unit, 'name') else business_unit, "huntred.com")

async def calcular_salario_chatbot(platform, user_id, mensaje, business_unit_name):
    data = parsear_mensaje(mensaje)
    if 'salario_bruto' not in data and 'salario_neto' not in data:
        response = "Por favor, proporciona un salario válido (ej. 'salario bruto = 20k MXN mensual')."
        await send_message(platform, user_id, response, business_unit_name)
        return response

    # Obtener tipo de cambio
    tipo_cambio = obtener_tipo_cambio(data['moneda'])
    tipo_cambio_inverso = 1 / tipo_cambio if tipo_cambio != 1.0 else 1.0

    # Estandarizar a mensual en moneda original y MXN
    valor = data['salario_bruto'] if data['tipo'] == 'bruto' else data['salario_neto']
    if data['frecuencia'] == 'hora':
        valor_mensual_orig = valor * 40 * 4
    elif data['frecuencia'] == 'semanal':
        valor_mensual_orig = valor * 4
    elif data['frecuencia'] == 'quincenal':
        valor_mensual_orig = valor * 2
    elif data['frecuencia'] == 'anual':
        valor_mensual_orig = valor / 12
    else:  # mensual
        valor_mensual_orig = valor
    valor_mensual_mxn = valor_mensual_orig * tipo_cambio

    # Ajustar bono
    bono_mensual_mxn = 0.0
    bono_mensual_orig = 0.0
    if data['bono'] > 0:
        bono_anual_mxn = data['bono'] * valor_mensual_mxn
        bono_mensual_mxn = bono_anual_mxn / 12
        valor_mensual_mxn += bono_mensual_mxn
        bono_mensual_orig = bono_mensual_mxn * tipo_cambio_inverso
        valor_mensual_orig += bono_mensual_orig

    # Parámetros adicionales para cálculos detallados
    incluye_prestaciones = data.get('prestaciones_adicionales', False)
    monto_vales = data.get('monto_vales', 0.0)
    fondo_ahorro = data.get('fondo_ahorro', False)
    porcentaje_fondo = data.get('porcentaje_fondo', 0.13)
    credito_infonavit = data.get('credito_infonavit', 0.0)
    pension_alimenticia = data.get('pension_alimenticia', 0.0)
    aplicar_subsidio = data.get('aplicar_subsidio', True)

    # Calcular bruto y neto en MXN con todos los detalles
    if data['tipo'] == 'bruto':
        salario_bruto_mxn = valor_mensual_mxn
        salario_neto_mxn = calcular_neto(
            salario_bruto_mxn,
            incluye_prestaciones=incluye_prestaciones,
            monto_vales=monto_vales,
            fondo_ahorro=fondo_ahorro,
            porcentaje_fondo=porcentaje_fondo,
            credito_infonavit=credito_infonavit,
            pension_alimenticia=pension_alimenticia,
            aplicar_subsidio=aplicar_subsidio
        )
    else:  # neto
        salario_neto_mxn = valor_mensual_mxn
        salario_bruto_mxn = calcular_bruto(
            salario_neto_mxn,
            incluye_prestaciones=incluye_prestaciones,
            monto_vales=monto_vales,
            fondo_ahorro=fondo_ahorro,
            porcentaje_fondo=porcentaje_fondo,
            credito_infonavit=credito_infonavit,
            pension_alimenticia=pension_alimenticia,
            aplicar_subsidio=aplicar_subsidio
        )

    # Conversión a moneda original
    salario_bruto_orig = salario_bruto_mxn * tipo_cambio_inverso
    salario_neto_orig = salario_neto_mxn * tipo_cambio_inverso

    # Cálculos detallados para mostrar en el mensaje
    base_gravable = salario_bruto_mxn - (monto_vales if incluye_prestaciones else 0.0)
    isr = calcular_isr_mensual(base_gravable)
    imss = calcular_cuotas_imss(salario_bruto_mxn)
    infonavit_descuento = credito_infonavit if credito_infonavit >= 1 else salario_bruto_mxn * credito_infonavit if credito_infonavit > 0 else 0.0
    pension_desc = pension_alimenticia if pension_alimenticia >= 1 else salario_bruto_mxn * pension_alimenticia if pension_alimenticia > 0 else 0.0
    ahorro_desc = salario_bruto_mxn * porcentaje_fondo if fondo_ahorro else 0.0
    subsidio = 0.0  # Pendiente de implementar si deseas lógica específica

    # Construir mensaje con formato mejorado
    msg = f"🤔 *Con base en el salario:* `{mensaje}`\n\n"
    msg += "```\n"
    msg += f"💰 Bruto Mensual : {salario_bruto_orig:>10,.2f} {data['moneda']} ({salario_bruto_mxn:,.2f} MXN)\n"
    msg += f"🏠 Neto Mensual  : {salario_neto_orig:>10,.2f} {data['moneda']} ({salario_neto_mxn:,.2f} MXN)\n"
    msg += "```\n"
    msg += "📊 *Detalles del cálculo:*\n"
    msg += "```\n"
    msg += f"🏛️ ISR            : {isr:>10,.2f} MXN\n"
    msg += f"🏥 IMSS           : {imss:>10,.2f} MXN\n"
    msg += f"🏡 Infonavit      : {infonavit_descuento:>10,.2f} MXN\n"
    msg += f"🏦 Fondo Ahorro   : {ahorro_desc:>10,.2f} MXN\n"
    msg += f"🍽️ Pensión Alim. : {pension_desc:>10,.2f} MXN\n"
    msg += f"💸 Subsidio Emp.  : {subsidio:>10,.2f} MXN\n"
    if incluye_prestaciones and monto_vales > 0:
        msg += f"🎟️ Vales (exento): {monto_vales:>10,.2f} MXN\n"
    if data['bono'] > 0:
        msg += f"🎁 Bono Mensual  : {bono_mensual_orig:>10,.2f} {data['moneda']} ({bono_mensual_mxn:,.2f} MXN)\n"
    msg += "```\n"

    # Leyenda si hay valores asumidos en 0
    campos_no_provistos = []
    if not incluye_prestaciones or monto_vales == 0: campos_no_provistos.append("Vales")
    if not fondo_ahorro: campos_no_provistos.append("Fondo de Ahorro")
    if credito_infonavit == 0: campos_no_provistos.append("Infonavit")
    if pension_alimenticia == 0: campos_no_provistos.append("Pensión Alimenticia")
    if not aplicar_subsidio or subsidio == 0: campos_no_provistos.append("Subsidio al Empleo")
    
    if campos_no_provistos:
        msg += f"📝 *Nota:* Basado en los datos provistos, los valores de {', '.join(campos_no_provistos)} se calculan en 0.\n"

    # Comparativa bidireccional
    pais_origen = {'MXN': 'México', 'USD': 'USA', 'NIO': 'Nicaragua', 'COP': 'Colombia', 'ARS': 'Argentina', 'BRL': 'Brasil'}.get(data['moneda'], 'Otro')
    ciudad_origen = {'México': 'Ciudad de México', 'USA': 'Nueva York', 'Nicaragua': 'Managua', 'Colombia': 'Bogotá', 'Argentina': 'Buenos Aires', 'Brasil': 'São Paulo'}.get(pais_origen, 'Otra ciudad')

    # Calcular ajustes para México
    adjustment_coli_mx = DATOS_COLI['Ciudad de México'] / DATOS_COLI.get(ciudad_origen, 50.0)
    adjustment_ppa_mx = DATOS_PPA['México'] / DATOS_PPA.get(pais_origen, 1.0)
    adjustment_bigmac_mx = DATOS_BIGMAC['México'] / DATOS_BIGMAC.get(pais_origen, 5.0)

    # Calcular ajustes para el país de origen
    adjustment_coli_orig = DATOS_COLI.get(ciudad_origen, 50.0) / DATOS_COLI['Ciudad de México']
    adjustment_ppa_orig = DATOS_PPA.get(pais_origen, 1.0) / DATOS_PPA['México']
    adjustment_bigmac_orig = DATOS_BIGMAC.get(pais_origen, 5.0) / DATOS_BIGMAC['México']

    # Construir tabla comparativa dinámica
    msg += "\n🌍 *Comparativa Salario Neto:*\n"
    msg += "```\n"
    msg += f"{'':<15} {'🇲🇽 México':<15} {(f'🌎 {pais_origen}' if data['moneda'] != 'MXN' else ''):<15}\n"
    msg += f"{'-' * 15} {'-' * 15} {'-' * 15 if data['moneda'] != 'MXN' else ''}\n"
    msg += f"📊 COLI         {salario_neto_mxn * adjustment_coli_mx:>10,.2f} MXN {(f'{salario_neto_orig * adjustment_coli_orig:>10,.2f} {data['moneda']}' if data['moneda'] != 'MXN' else '')}\n"
    msg += f"⚖️ PPA          {salario_neto_mxn * adjustment_ppa_mx:>10,.2f} MXN {(f'{salario_neto_orig * adjustment_ppa_orig:>10,.2f} {data['moneda']}' if data['moneda'] != 'MXN' else '')}\n"
    msg += f"🍔 BigMac Index {salario_neto_mxn * adjustment_bigmac_mx:>10,.2f} MXN {(f'{salario_neto_orig * adjustment_bigmac_orig:>10,.2f} {data['moneda']}' if data['moneda'] != 'MXN' else '')}\n"
    msg += "```\n"

    # Obtener el dominio desde ConfiguracionBU de manera asíncrona
    try:
        business_unit = await sync_to_async(BusinessUnit.objects.get)(name=business_unit_name)
        config = await sync_to_async(lambda: business_unit.configuracionbu)()
        if config and config.dominio_bu:
            parsed_url = urlparse(config.dominio_bu)
            domain = parsed_url.netloc or parsed_url.path  # Extrae el dominio limpio
            domain = domain.replace('www.', '')  # Elimina 'www.' si existe
        else:
            domain = "huntred.com"  # Dominio por defecto si no hay configuración
    except BusinessUnit.DoesNotExist:
        domain = "huntred.com"  # Dominio por defecto si la unidad no existe
    except ConfiguracionBU.DoesNotExist:
        domain = "huntred.com"  # Dominio por defecto si no hay ConfiguracionBU
    except Exception as e:
        logger.error(f"Error al obtener dominio para {business_unit_name}: {e}")
        domain = "huntred.com"  # Fallback en caso de error inesperado

    # Añadir referencia dinámica
    msg += f"\n📚 *Referencia:* https://{domain}/salario/"

    await send_message(platform, user_id, msg, business_unit_name)
    return msg