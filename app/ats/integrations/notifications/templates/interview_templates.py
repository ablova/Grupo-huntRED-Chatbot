"""
Templates para notificaciones de entrevistas.
"""

def get_interview_scheduled_candidate_template() -> str:
    """
    Template para notificar al candidato sobre una entrevista programada.
    """
    return """
    🎯 Entrevista Programada
    
    Hola {candidate_name},
    
    Te confirmamos que has sido seleccionado para una entrevista para el puesto de {position} en {company}.
    
    📅 Fecha: {interview_date}
    📍 Lugar: {location}
    📝 Tipo: {interview_type}
    
    {additional_notes}
    
    ¡Te deseamos mucho éxito!
    """

def get_interview_scheduled_client_template() -> str:
    """
    Template para notificar al cliente sobre una entrevista programada.
    """
    return """
    🎯 Nueva Entrevista Programada
    
    Hola,
    
    Se ha programado una entrevista para el puesto de {position}.
    
    👤 Candidato: {candidate_name}
    📅 Fecha: {interview_date}
    📍 Lugar: {location}
    📝 Tipo: {interview_type}
    
    {additional_notes}
    """

def get_interview_cancelled_candidate_template() -> str:
    """
    Template para notificar al candidato sobre una entrevista cancelada.
    """
    return """
    ❌ Entrevista Cancelada
    
    Hola {candidate_name},
    
    Lamentamos informarte que la entrevista programada para el puesto de {position} en {company} ha sido cancelada.
    
    📅 Fecha original: {interview_date}
    📝 Razón: {reason}
    
    Nos pondremos en contacto contigo pronto para reprogramar la entrevista.
    """

def get_interview_cancelled_client_template() -> str:
    """
    Template para notificar al cliente sobre una entrevista cancelada.
    """
    return """
    ❌ Entrevista Cancelada
    
    Hola,
    
    La entrevista programada para el puesto de {position} ha sido cancelada.
    
    👤 Candidato: {candidate_name}
    📅 Fecha original: {interview_date}
    📝 Razón: {reason}
    👤 Cancelada por: {cancelled_by}
    """

def get_candidate_location_update_template() -> str:
    """
    Template para notificar sobre actualización de ubicación del candidato.
    """
    return """
    📍 Actualización de Ubicación
    
    El candidato {candidate_name} para el puesto de {position} está:
    
    🚶 Estado: {status}
    📍 Ubicación actual: {current_location}
    📏 Distancia: {distance}
    ⏰ Llegada estimada: {estimated_arrival}
    
    Entrevista programada para: {interview_date}
    """

def get_interview_delay_template() -> str:
    """
    Template para notificar sobre retraso en la entrevista.
    """
    return """
    ⚠️ Retraso en Entrevista
    
    El candidato {candidate_name} para el puesto de {position} llegará con retraso.
    
    ⏰ Retraso: {delay_minutes} minutos
    📝 Razón: {reason}
    
    Entrevista programada para: {interview_date}
    """ 