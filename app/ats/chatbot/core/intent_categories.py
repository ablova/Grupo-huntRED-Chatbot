"""
Categorización de intents para Meta Conversations 2025.

Este módulo define la clasificación de todos los intents del chatbot según
los criterios de Meta para optimización de costos (service, utility, marketing).

- SERVICE: Mensajes relacionados con la funcionalidad principal del servicio
  (perfil, aplicaciones, entrevistas, ofertas, etc.)
- UTILITY: Mensajes transaccionales o recordatorios
  (confirmaciones, verificaciones, alertas, etc.)
- MARKETING: Mensajes promocionales o de captación
  (ofertas, eventos, webinars, etc.)

Esta clasificación permite la optimización automática de costos de mensajería
y debe mantenerse actualizada con cualquier nuevo intent que se agregue al sistema.
"""

from typing import Dict, List, Set

# Intents que pertenecen a la categoría SERVICE (sin costo dentro de la ventana 24h)
# Relacionados con funcionalidad principal del negocio
SERVICE_INTENTS = {
    # Onboarding y creación de perfil
    "start_command", "saludo", "tos_accept", "presentacion_bu",
    "upload_cv", "crear_perfil", "actualizar_perfil", "modificar_perfil",
    "iniciar_perfil_conversacional",
    
    # Búsqueda y aplicación a vacantes
    "buscar_vacante", "aplicar_vacante", "buscar_trabajo", "consultar_vacantes",
    "solicitar_ayuda_postulacion", "status_postulacion", "estado_postulacion",
    "vacante_por_id", "seguir_vacante", "solicitar_mas_info_vacante",
    
    # Entrevistas y proceso
    "agendar_entrevista", "reagendar_entrevista", "cancelar_entrevista",
    "recordatorio_entrevista", "solicitar_feedback", "consultar_feedback",
    
    # Soporte y ayuda
    "ayuda", "soporte", "ayuda_perfil", "ayuda_postulacion", "ayuda_entrevista",
    "hablar_con_humano", "reportar_problema",
    
    # Assessment y evaluaciones
    "iniciar_assessment", "consultar_assessment", "status_assessment", "ayuda_assessment",
    
    # Consultas específicas del servicio
    "consultar_sueldo_mercado", "consultar_salario", "consultar_skill_gap",
    "salary_calculator", "consultar_skills",
    
    # Otros servicios principales
    "transition_to_higher_bu", "executive_roles", "internships",
    
    # Intents agregados por auditoría
    "busqueda_impacto", "calcular_salario", "cargar_cv", "compensacion",
    "consultar_estado_postulacion", "create_contract", "data", "migratory_status",
    "prueba_personalidad", "responses", "show_jobs", "solicitar_tips_entrevista",
}

# Intents que pertenecen a la categoría UTILITY (sin costo dentro de la ventana 24h)
# Mensajes transaccionales o recordatorios
UTILITY_INTENTS = {
    # Navegación y utilidades del bot
    "show_menu", "menu", "opciones", "inicio",
    "cambiar_idioma", "consultar_ayuda", 
    
    # Confirmaciones y verificaciones
    "confirmar_accion", "verificar_codigo", "confirmar_perfil",
    "verificar_identidad", "verificar_email", "verificar_telefono",
    
    # Recordatorios
    "recordatorio", "notificacion", "alerta",
    
    # Compartir y referenciar
    "referir_amigo", "travel_in_group", "compartir_vacante",
    "invitar_amigo", "compartir_perfil",
    
    # Feedback del sistema
    "agradecimiento", "despedida", "confirmacion",
    
    # Ajustes y preferencias
    "cambiar_notificaciones", "actualizar_preferencias",
    "opt_in", "opt_out", "toggle_notifications",
    
    # Intents agregados por auditoría
    "contacto", "retry_conversation", "solicitar_contacto_reclutador",
}

# Intents que pertenecen a la categoría MARKETING (potencialmente con costo)
# Mensajes promocionales o de captación
MARKETING_INTENTS = {
    # Promociones y eventos
    "promocion", "evento", "webinar", "curso", "taller",
    "descuento", "oferta_especial", "programa_especial",
    
    # Campañas y difusión
    "campana_reclutamiento", "campana_marketing", "newsletter",
    "programa_referidos", "promocionar_servicio",
    
    # Información sobre nuevas funciones
    "nueva_funcion", "nueva_caracteristica", "actualizacion_servicio",
    
    # Oportunidades premium
    "servicios_premium", "suscripcion_premium", "oferta_premium",
    
    # Engagement no esencial
    "encuesta_satisfaccion", "solicitar_rating", "solicitar_feedback_servicio",
    
    # Intents agregados por auditoría
    "internship_search",
}

def categorize_intent(intent_name: str) -> str:
    """
    Categoriza un intent según los criterios de Meta Conversations 2025.
    
    Args:
        intent_name: Nombre del intent a categorizar
        
    Returns:
        str: 'service', 'utility', o 'marketing'
    """
    if intent_name in SERVICE_INTENTS:
        return 'service'
    elif intent_name in UTILITY_INTENTS:
        return 'utility'
    elif intent_name in MARKETING_INTENTS:
        return 'marketing'
    else:
        # Por defecto, clasificar como servicio (más seguro para costos)
        return 'service'
        
def get_all_intents_by_category() -> Dict[str, List[str]]:
    """
    Obtiene todos los intents organizados por categoría.
    
    Returns:
        Dict con listas de intents por categoría
    """
    return {
        'service': sorted(list(SERVICE_INTENTS)),
        'utility': sorted(list(UTILITY_INTENTS)),
        'marketing': sorted(list(MARKETING_INTENTS))
    }
    
def validate_intent_classification(all_intents: Set[str]) -> Dict[str, List[str]]:
    """
    Valida que todos los intents del sistema estén clasificados.
    
    Args:
        all_intents: Conjunto con todos los nombres de intents en el sistema
        
    Returns:
        Dict con intents no clasificados y posibles duplicados
    """
    all_classified = SERVICE_INTENTS.union(UTILITY_INTENTS).union(MARKETING_INTENTS)
    
    unclassified = all_intents - all_classified
    duplicated = []
    
    # Verificar duplicados
    for intent in SERVICE_INTENTS:
        if intent in UTILITY_INTENTS or intent in MARKETING_INTENTS:
            duplicated.append(intent)
            
    for intent in UTILITY_INTENTS:
        if intent in MARKETING_INTENTS:
            duplicated.append(intent)
            
    return {
        'unclassified': sorted(list(unclassified)),
        'duplicated': sorted(list(set(duplicated)))
    }
