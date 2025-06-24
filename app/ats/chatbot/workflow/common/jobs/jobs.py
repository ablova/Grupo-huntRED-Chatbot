# /home/pablo/app/com/chatbot/workflow/jobs.py
import logging
from asgiref.sync import sync_to_async
from app.models import Person, ChatState, BusinessUnit, Application, EnhancedNetworkGamificationProfile, NotificationPreference, Vacante
from app.ats.integrations.services import send_message, send_options, send_menu
from django.utils import timezone
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.ats.utils.vacantes import VacanteManager
from app.ats.services.interview_service import InterviewService
from app.ats.utils.google_calendar import notify_no_slots_available

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
    """
    Maneja las acciones relacionadas con trabajos en el chatbot.
    Mejorado para incluir slots grupales y mejor experiencia.
    """
    try:
        bu_name = unidad_negocio.name
        recommended_jobs = estado_chat.context.get('recommended_jobs', [])
        
        if texto.startswith("apply_"):
            job_index = int(texto.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                selected_job = recommended_jobs[job_index]
                # Lógica de aplicación
                resp = f"¡Excelente elección! Has aplicado para {selected_job['title']}. Te contactaremos pronto."
                await send_message(plataforma, user_id, resp, bu_name)
            else:
                resp = "No encuentro esa vacante."
                await send_message(plataforma, user_id, resp, bu_name)

        elif texto.startswith("schedule_"):
            job_index = int(texto.split('_')[1])
            if 0 <= job_index < len(recommended_jobs):
                selected_job = recommended_jobs[job_index]
                
                # Obtener la vacante
                try:
                    vacancy = await sync_to_async(Vacante.objects.get)(id=selected_job['id'])
                except Vacante.DoesNotExist:
                    resp = "Lo sentimos, esa vacante ya no está disponible."
                    await send_message(plataforma, user_id, resp, bu_name)
                    return
                
                # Obtener slots disponibles
                slots = await get_interview_slots(selected_job)
                
                if not slots:
                    # Obtener mensaje de alternativas
                    message = await notify_no_slots_available(selected_job['title'], persona, unidad_negocio)
                    
                    # Crear botones para las opciones
                    buttons = [
                        {'title': 'Dejar horarios preferidos', 'payload': 'set_preferred_times'},
                        {'title': 'Llamada informativa', 'payload': 'schedule_info_call'},
                        {'title': 'Recibir información por email', 'payload': 'get_email_info'}
                    ]
                    
                    await send_message(plataforma, user_id, message, bu_name, options=buttons)
                    estado_chat.state = "waiting_slot_preference"
                    estado_chat.context['selected_job'] = selected_job
                    await sync_to_async(estado_chat.save)()
                    return
                
                # Crear botones para los slots
                buttons = []
                for idx, slot in enumerate(slots):
                    # Crear etiqueta más descriptiva
                    if slot['session_type'] == 'grupal':
                        button_text = f"{slot['label']} (Grupal)"
                    else:
                        button_text = f"{slot['label']} (Individual)"
                    
                    buttons.append({
                        'title': button_text,
                        'payload': f"book_slot_{idx}"
                    })
                
                # Añadir opción para más horarios
                buttons.append({
                    'title': 'Ver más horarios disponibles',
                    'payload': 'show_more_slots'
                })
                
                estado_chat.context['available_slots'] = slots
                estado_chat.context['selected_job'] = selected_job
                await sync_to_async(estado_chat.save)()
                
                # Mensaje mejorado
                resp = f"🎯 Perfecto para {selected_job['title']}! Aquí tienes los horarios disponibles:\n\n"
                resp += "📅 Selecciona el horario que mejor te convenga:\n\n"
                
                await send_message(plataforma, user_id, resp, bu_name, options=buttons)
            else:
                resp = "No encuentro esa vacante."
                await send_message(plataforma, user_id, resp, bu_name)

        elif texto.startswith("book_slot_"):
            slot_index = int(texto.split('_')[2])
            available_slots = estado_chat.context.get('available_slots', [])
            selected_job = estado_chat.context.get('selected_job')
            
            if not selected_job:
                resp = "No se encontró la vacante seleccionada."
                await send_message(plataforma, user_id, resp, bu_name)
                return
            
            if 0 <= slot_index < len(available_slots):
                selected_slot = available_slots[slot_index]
                
                # Obtener la vacante
                try:
                    vacancy = await sync_to_async(Vacante.objects.get)(id=selected_job['id'])
                except Vacante.DoesNotExist:
                    resp = "Lo sentimos, esa vacante ya no está disponible."
                    await send_message(plataforma, user_id, resp, bu_name)
                    return
                
                # Reservar el slot
                result = await book_interview_slot(persona, vacancy, selected_slot, unidad_negocio)
                
                if result['success']:
                    await send_message(plataforma, user_id, result['message'], bu_name)
                    
                    # Limpiar contexto
                    estado_chat.context.pop('available_slots', None)
                    estado_chat.context.pop('selected_job', None)
                    estado_chat.state = "idle"
                    await sync_to_async(estado_chat.save)()
                else:
                    await send_message(plataforma, user_id, result['message'], bu_name)
            else:
                resp = "No encuentro ese horario."
                await send_message(plataforma, user_id, resp, bu_name)

        elif texto == "show_more_slots":
            selected_job = estado_chat.context.get('selected_job')
            if selected_job:
                # Generar más slots automáticamente
                try:
                    vacancy = await sync_to_async(Vacante.objects.get)(id=selected_job['id'])
                    interview_service = InterviewService(unidad_negocio)
                    
                    # Generar slots para los próximos 14 días
                    start_date = timezone.now() + timedelta(days=7)
                    end_date = start_date + timedelta(days=14)
                    
                    await interview_service.generate_interview_slots(
                        vacancy=vacancy,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # Obtener slots actualizados
                    new_slots = await get_interview_slots(selected_job)
                    
                    if new_slots:
                        buttons = []
                        for idx, slot in enumerate(new_slots):
                            if slot['session_type'] == 'grupal':
                                button_text = f"{slot['label']} (Grupal)"
                            else:
                                button_text = f"{slot['label']} (Individual)"
                            
                            buttons.append({
                                'title': button_text,
                                'payload': f"book_slot_{idx}"
                            })
                        
                        estado_chat.context['available_slots'] = new_slots
                        await sync_to_async(estado_chat.save)()
                        
                        resp = "🎯 Aquí tienes más horarios disponibles:\n\n"
                        await send_message(plataforma, user_id, resp, bu_name, options=buttons)
                    else:
                        resp = "No hay más horarios disponibles en este momento. Te notificaremos cuando se liberen nuevos slots."
                        await send_message(plataforma, user_id, resp, bu_name)
                        
                except Exception as e:
                    logger.error(f"Error generando más slots: {str(e)}")
                    resp = "No se pudieron generar más horarios en este momento."
                    await send_message(plataforma, user_id, resp, bu_name)
            else:
                resp = "No se encontró la vacante seleccionada."
                await send_message(plataforma, user_id, resp, bu_name)

        elif texto == "set_preferred_times":
            resp = "📅 Por favor, indícame tus horarios preferidos:\n\n"
            resp += "• ¿Qué días de la semana prefieres? (Lunes-Viernes)\n"
            resp += "• ¿Qué horarios te funcionan mejor? (Mañana/Tarde)\n"
            resp += "• ¿Prefieres entrevistas individuales o grupales?\n\n"
            resp += "Ejemplo: 'Prefiero lunes y miércoles por la mañana, entrevistas individuales'"
            
            estado_chat.state = "waiting_time_preferences"
            await sync_to_async(estado_chat.save)()
            
            await send_message(plataforma, user_id, resp, bu_name)

        elif texto == "schedule_info_call":
            resp = "📞 Perfecto! Te programaremos una llamada informativa.\n\n"
            resp += "Un reclutador te contactará en las próximas 24 horas para:\n"
            resp += "• Explicarte más sobre el puesto\n"
            resp += "• Resolver tus dudas\n"
            resp += "• Coordinar una entrevista formal\n\n"
            resp += "¿En qué horario prefieres que te llamen?"
            
            estado_chat.state = "waiting_call_preference"
            await sync_to_async(estado_chat.save)()
            
            await send_message(plataforma, user_id, resp, bu_name)

        elif texto == "get_email_info":
            resp = "📧 Te enviaremos información detallada por email.\n\n"
            resp += "Recibirás:\n"
            resp += "• Descripción completa del puesto\n"
            resp += "• Requisitos y beneficios\n"
            resp += "• Proceso de aplicación\n"
            resp += "• Enlaces para agendar entrevista\n\n"
            resp += "Revisa tu email en los próximos minutos."
            
            # Aquí se enviaría el email
            # await send_job_info_email(persona, selected_job)
            
            await send_message(plataforma, user_id, resp, bu_name)

    except Exception as e:
        logger.error(f"Error en handle_job_action: {str(e)}")
        resp = "Lo sentimos, hubo un error. Por favor, intenta nuevamente."
        await send_message(plataforma, user_id, resp, bu_name)

async def get_interview_slots(job: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Obtiene slots de entrevista disponibles para una vacante.
    Ahora incluye soporte para slots grupales y mejor información.
    """
    try:
        # Obtener la vacante
        vacancy = await sync_to_async(Vacante.objects.get)(id=job['id'])
        
        # Crear servicio de entrevistas
        interview_service = InterviewService(vacancy.business_unit)
        
        # Obtener slots disponibles
        available_slots = await interview_service.get_available_slots_for_vacancy(vacancy)
        
        if not available_slots:
            return []
        
        # Formatear slots para el chatbot
        formatted_slots = []
        for slot in available_slots:
            # Crear etiqueta descriptiva
            if slot['session_type'] == 'grupal':
                label = f"{slot['label']} (Grupal - {slot['available_spots']}/{slot['total_spots']} cupos)"
            else:
                label = f"{slot['label']} (Individual)"
            
            formatted_slots.append({
                'id': slot['id'],
                'label': label,
                'datetime': slot['datetime'],
                'session_type': slot['session_type'],
                'available_spots': slot['available_spots'],
                'total_spots': slot['total_spots'],
                'mode': slot['mode'],
                'location': slot['location']
            })
        
        return formatted_slots
        
    except Exception as e:
        logger.error(f"Error obteniendo slots de entrevista: {str(e)}")
        return []

async def book_interview_slot(
    person: Person,
    vacancy: Vacante,
    slot_data: Dict[str, Any],
    business_unit: BusinessUnit
) -> Dict[str, Any]:
    """
    Reserva un slot de entrevista para un candidato.
    Ahora maneja slots grupales e individuales.
    """
    try:
        # Crear servicio de entrevistas
        interview_service = InterviewService(business_unit)
        
        # Reservar el slot
        result = await interview_service.book_slot_for_candidate(
            person=person,
            vacancy=vacancy,
            slot_id=slot_data['id'],
            interview_type='video'  # Por defecto video
        )
        
        if result['success']:
            # Preparar mensaje de confirmación
            if result.get('session_type') == 'grupal':
                message = f"¡Perfecto! Te has registrado en una entrevista grupal para {vacancy.titulo}.\n\n"
                message += f"📅 Fecha: {datetime.fromisoformat(result['datetime']).strftime('%A %d/%m/%Y a las %H:%M')}\n"
                message += "👥 Tipo: Entrevista grupal\n"
                message += "🔗 Recibirás el enlace de la videollamada 30 minutos antes.\n\n"
                message += "💡 Consejos para entrevistas grupales:\n"
                message += "• Llega 5 minutos antes\n"
                message += "• Ten tu cámara y micrófono listos\n"
                message += "• Participa activamente en la conversación\n"
                message += "• Ten preguntas preparadas sobre el puesto"
            else:
                message = f"¡Excelente! Tu entrevista individual para {vacancy.titulo} ha sido confirmada.\n\n"
                message += f"📅 Fecha: {datetime.fromisoformat(result['datetime']).strftime('%A %d/%m/%Y a las %H:%M')}\n"
                message += "👤 Tipo: Entrevista individual\n"
                message += "🔗 Recibirás el enlace de la videollamada 30 minutos antes.\n\n"
                message += "💡 Consejos para tu entrevista:\n"
                message += "• Llega 5 minutos antes\n"
                message += "• Ten tu cámara y micrófono listos\n"
                message += "• Revisa tu CV y prepárate para preguntas\n"
                message += "• Ten preguntas preparadas sobre el puesto"
            
            return {
                'success': True,
                'message': message,
                'interview_id': result['interview_id']
            }
        else:
            return {
                'success': False,
                'message': f"No se pudo reservar el horario: {result.get('error', 'Error desconocido')}"
            }
            
    except Exception as e:
        logger.error(f"Error reservando slot: {str(e)}")
        return {
            'success': False,
            'message': "Hubo un error al reservar tu entrevista. Por favor, intenta nuevamente."
        }

async def handle_time_preferences(plataforma: str, user_id: str, texto: str, estado_chat: ChatState, unidad_negocio: BusinessUnit, persona: Person):
    """
    Maneja las preferencias de horarios del candidato.
    """
    try:
        bu_name = unidad_negocio.name
        selected_job = estado_chat.context.get('selected_job')
        
        if not selected_job:
            resp = "No se encontró la vacante seleccionada."
            await send_message(plataforma, user_id, resp, bu_name)
            return
        
        # Guardar preferencias en el perfil del usuario
        if not persona.metadata:
            persona.metadata = {}
        
        persona.metadata['preferred_time_slots'] = texto
        await sync_to_async(persona.save)()
        
        resp = "✅ Perfecto! He guardado tus preferencias de horarios.\n\n"
        resp += "Te notificaremos cuando haya slots disponibles que coincidan con tus preferencias.\n\n"
        resp += "Mientras tanto, ¿te gustaría:\n"
        resp += "• Ver otras vacantes disponibles\n"
        resp += "• Recibir información por email\n"
        resp += "• Programar una llamada informativa"
        
        # Crear botones
        buttons = [
            {'title': 'Ver otras vacantes', 'payload': 'show_more_jobs'},
            {'title': 'Recibir información por email', 'payload': 'get_email_info'},
            {'title': 'Llamada informativa', 'payload': 'schedule_info_call'}
        ]
        
        estado_chat.state = "idle"
        await sync_to_async(estado_chat.save)()
        
        await send_message(plataforma, user_id, resp, bu_name, options=buttons)
        
    except Exception as e:
        logger.error(f"Error manejando preferencias de horarios: {str(e)}")
        resp = "Lo sentimos, hubo un error guardando tus preferencias."
        await send_message(plataforma, user_id, resp, bu_name)

async def notify_no_slots_available(job_title: str, persona: Person, unidad_negocio: BusinessUnit) -> str:
    """
    Genera un mensaje personalizado cuando no hay slots disponibles.
    """
    message = f"📅 Actualmente no hay horarios disponibles para {job_title}.\n\n"
    message += "Pero no te preocupes, tenemos estas opciones para ti:\n\n"
    message += "🕐 **Dejar horarios preferidos**: Te notificaremos cuando haya disponibilidad\n"
    message += "📞 **Llamada informativa**: Un reclutador te contactará para coordinar\n"
    message += "📧 **Información por email**: Recibe detalles completos del puesto\n\n"
    message += "¿Qué opción prefieres?"
    
    return message

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