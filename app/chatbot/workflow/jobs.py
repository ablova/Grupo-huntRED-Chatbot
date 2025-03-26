# /home/pablo/app/chatbot/workflow/jobs.py
import logging
from asgiref.sync import sync_to_async
from app.models import Person, ChatState, BusinessUnit, Application, EnhancedNetworkGamificationProfile
from app.chatbot.integrations.services import send_message, send_options, send_menu

logger = logging.getLogger(__name__)

async def handle_job_selection(plataforma: str, user_id: str, texto: str, estado_chat: ChatState, unidad_negocio: BusinessUnit, persona: Person):
    """Maneja la selección de una vacante por parte del usuario."""
    recommended_jobs = estado_chat.context.get('recommended_jobs', [])
    if not recommended_jobs:
        resp = "No hay vacantes recomendadas disponibles actualmente."
        await send_message(plataforma, user_id, resp, unidad_negocio.name.lower())
        return
    try:
        job_index = int(texto.strip()) - 1
    except ValueError:
        resp = "Por favor, ingresa un número válido."
        await send_message(plataforma, user_id, resp, unidad_negocio.name.lower())
        return

    if 0 <= job_index < len(recommended_jobs):
        selected_job = recommended_jobs[job_index]
        buttons = [
            {'title': 'Aplicar', 'payload': f"apply_{job_index}"},
            {'title': 'Ver Detalles', 'payload': f"details_{job_index}"},
            {'title': 'Agendar Entrevista', 'payload': f"schedule_{job_index}"},
            {'title': 'Tips Entrevista', 'payload': f"tips_{job_index}"}
        ]
        resp = f"Has seleccionado: {selected_job['title']}. ¿Qué deseas hacer?"
        await send_message(plataforma, user_id, resp, unidad_negocio.name.lower(), options=buttons)
        estado_chat.context['selected_job'] = selected_job
        await sync_to_async(estado_chat.save)()
    else:
        resp = "Selección inválida."
        await send_message(plataforma, user_id, resp, unidad_negocio.name.lower())

async def handle_job_action(plataforma: str, user_id: str, texto: str, estado_chat: ChatState, unidad_negocio: BusinessUnit, persona: Person):
    recommended_jobs = estado_chat.context.get('recommended_jobs', [])
    bu_name = unidad_negocio.name.lower()

    if texto.startswith("apply_"):
        job_index = int(texto.split('_')[1])
        if 0 <= job_index < len(recommended_jobs):
            job = recommended_jobs[job_index]
            await sync_to_async(Application.objects.create)(user=persona, vacancy_id=job['id'], status='applied')
            estado_chat.state = "applied"  # Transición a estado 'applied'
            await sync_to_async(estado_chat.save)()
            resp = "¡Has aplicado a la vacante con éxito!"
            await send_message(plataforma, user_id, resp, bu_name)
            await award_gamification_points(persona, "job_application", plataforma, unidad_negocio)
            await send_menu(plataforma, user_id, unidad_negocio)  # Enviar menú dinámico
        else:
            resp = "No encuentro esa vacante."
            await send_message(plataforma, user_id, resp, bu_name)

    elif texto.startswith("details_"):
        job_index = int(texto.split('_')[1])
        if 0 <= job_index < len(recommended_jobs):
            job = recommended_jobs[job_index]
            details = job.get('description', 'No hay descripción disponible.')
            resp = f"Detalles de la posición:\n{details}"
            await send_message(plataforma, user_id, resp, bu_name)
        else:
            resp = "No encuentro esa vacante."
            await send_message(plataforma, user_id, resp, bu_name)

    elif texto.startswith("schedule_"):
        job_index = int(texto.split('_')[1])
        if 0 <= job_index < len(recommended_jobs):
            selected_job = recommended_jobs[job_index]
            slots = await get_interview_slots(selected_job)
            if not slots:
                resp = "No hay horarios disponibles por el momento."
                await send_message(plataforma, user_id, resp, bu_name)
                return
            buttons = [{'title': slot['label'], 'payload': f"book_slot_{idx}"} for idx, slot in enumerate(slots)]
            estado_chat.context['available_slots'] = slots
            estado_chat.context['selected_job'] = selected_job
            await sync_to_async(estado_chat.save)()
            resp = "Elige un horario para la entrevista:"
            await send_message(plataforma, user_id, resp, bu_name, options=buttons)
        else:
            resp = "No encuentro esa vacante."
            await send_message(plataforma, user_id, resp, bu_name)

    elif texto.startswith("tips_"):
        job_index = int(texto.split('_')[1])
        resp = "Prepárate, investiga la empresa, sé puntual y comunica tus logros con seguridad."
        await send_message(plataforma, user_id, resp, bu_name)

    elif texto.startswith("book_slot_"):
        slot_index = int(texto.split('_')[2])
        available_slots = estado_chat.context.get('available_slots', [])
        if 0 <= slot_index < len(available_slots):
            selected_slot = available_slots[slot_index]
            resp = f"Entrevista agendada para {selected_slot['label']} ¡Éxito!"
            await send_message(plataforma, user_id, resp, bu_name)
            estado_chat.state = "scheduled"  # Movido aquí
            await sync_to_async(estado_chat.save)()
            await send_menu(plataforma, user_id, unidad_negocio)
        else:
            resp = "No encuentro ese horario."
            await send_message(plataforma, user_id, resp, bu_name)

    else:
        resp = "Opción no reconocida."
        await send_message(plataforma, user_id, resp, bu_name)

async def get_interview_slots(job: Dict[str, Any]) -> List[Dict[str, str]]:
    """Devuelve horarios disponibles para entrevistas."""
    return [
        {'label': 'Mañana 10:00 AM', 'datetime': '2025-03-22T10:00:00'},
        {'label': 'Mañana 11:00 AM', 'datetime': '2025-03-22T11:00:00'}
    ]

async def award_gamification_points(persona: Person, activity_type: str, plataforma: str, unidad_negocio: BusinessUnit):
    profile, created = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get_or_create)(
        user=persona, defaults={'points': 0, 'level': 1}
    )
    points_awarded = {"job_application": 20, "tos_accepted": 10}.get(activity_type, 5)
    profile.points += points_awarded
    if profile.points >= 300 and profile.level < 4:
        profile.level = 4
        await send_message(plataforma, persona.phone, "¡Subiste al nivel 4! Eres un candidato estrella.", unidad_negocio.name.lower())
    elif profile.points >= 200 and profile.level < 3:
        profile.level = 3
        await send_message(plataforma, persona.phone, "¡Subiste al nivel 3! Eres un candidato destacado.", unidad_negocio.name.lower())
    elif profile.points >= 100 and profile.level < 2:
        profile.level = 2
        await send_message(plataforma, persona.phone, "¡Subiste al nivel 2! Más beneficios desbloqueados.", unidad_negocio.name.lower())
    await sync_to_async(profile.save)()
    await notify_user_gamification_update(persona, activity_type, plataforma, unidad_negocio)

async def notify_user_gamification_update(persona: Person, activity_type: str, plataforma: str, unidad_negocio: BusinessUnit):
    """Notifica al usuario sobre la actualización de puntos de gamificación."""
    try:
        profile = await sync_to_async(EnhancedNetworkGamificationProfile.objects.get)(user=persona)
        message = f"¡Has ganado puntos por {activity_type}! Ahora tienes {profile.points} puntos (Nivel {profile.level})."
        await send_message(plataforma, persona.phone, message, unidad_negocio.name.lower())
    except EnhancedNetworkGamificationProfile.DoesNotExist:
        logger.warning(f"No se encontró perfil de gamificación para {persona.nombre}")
    except Exception as e:
        logger.error(f"Error notificando gamificación a {persona.nombre}: {e}", exc_info=True)