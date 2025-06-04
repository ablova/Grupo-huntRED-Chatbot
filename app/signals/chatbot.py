"""
Señales relacionadas con el módulo de chatbot en Grupo huntRED®.
Gestiona las señales para eventos de chatbot, mensajes y análisis de intención.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from app.models import Person, ChatSession, ChatMessage
from app.ats.chatbot.utils.chatbot_utils import ChatbotUtils
get_nlp_processor = ChatbotUtils.get_nlp_processor

logger = logging.getLogger(__name__)

# Señales personalizadas si son necesarias
# message_analyzed = Signal()
# chatbot_response_sent = Signal()

@receiver(post_save, sender=ChatMessage)
def process_chat_message(sender, instance, created, **kwargs):
    """
    Procesa un mensaje de chat cuando es creado.
    Analiza la intención y actualiza el estado de la sesión.
    """
    if created and instance.direction == 'in':  # Solo mensajes entrantes
        logger.info(f"Mensaje recibido de {instance.person.email if instance.person else 'desconocido'}")
        
        # Aquí podríamos lanzar una tarea async para procesar el mensaje
        # from app.ats.tasks.chatbot import process_message_task
        # process_message_task.delay(instance.id)


@receiver(post_save, sender=Person)
def initialize_chat_session(sender, instance, created, **kwargs):
    """
    Inicializa una sesión de chat para una persona nueva.
    """
    if created and instance.email:  # Solo si es una persona nueva con email
        logger.info(f"Inicializando sesión de chat para {instance.email}")
        
        # Verificar si ya tiene una sesión
        try:
            if not ChatSession.objects.filter(person=instance).exists():
                ChatSession.objects.create(
                    person=instance,
                    status='new',
                    channel=instance.preferred_channel or 'unknown'
                )
                logger.info(f"Sesión de chat creada para {instance.email}")
        except Exception as e:
            logger.error(f"Error creando sesión de chat: {str(e)}")
