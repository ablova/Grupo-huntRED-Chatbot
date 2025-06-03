"""
Signals relacionados con el sistema de notificaciones.
Este módulo centraliza todos los manejadores de señales para notificaciones
y eventos que requieren alertas en el sistema.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
import logging
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)

# Importar modelos necesarios
from app.models import Person, Vacante, Pago, BusinessUnit

# Importar servicio de notificaciones centralizado
from app.ats.notifications.manager import NotificationManager


@receiver(post_save, sender=Vacante)
def notify_vacancy_changes(sender, instance, created, **kwargs):
    """
    Envía notificaciones cuando una vacante es creada o actualizada.
    Notifica a los consultores asignados a la BU correspondiente.
    """
    try:
        bu_name = instance.bu.name if hasattr(instance, 'bu') and instance.bu else "Sin BU"
        
        # Determinar el tipo de evento
        event_type = "vacancy_created" if created else "vacancy_updated"
        
        # Datos para la notificación
        notification_data = {
            "vacancy_id": instance.id,
            "vacancy_title": instance.titulo if hasattr(instance, 'titulo') else "Sin título",
            "bu_name": bu_name,
            "action": "creada" if created else "actualizada",
            "timestamp": timezone.now().isoformat()
        }
        
        # Obtener IDs de usuarios a notificar (consultores de la BU)
        # Esta lógica debe adaptarse a tu modelo específico
        recipients = []
        if hasattr(instance, 'bu') and instance.bu:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Buscar consultores asignados a la BU
            # La implementación exacta depende de tu modelo de datos
            # Esto es un ejemplo que debe adaptarse
            consultants = User.objects.filter(
                profile__business_units=instance.bu, 
                is_active=True
            ).values_list('id', flat=True)
            
            recipients = list(consultants)
        
        # Si no hay destinatarios específicos, notificar a admin
        if not recipients:
            # Obtener admin de la BU como fallback
            admin_id = instance.bu.admin_id if hasattr(instance, 'bu') and hasattr(instance.bu, 'admin_id') else None
            if admin_id:
                recipients = [admin_id]
        
        # Enviar notificación a cada destinatario
        for user_id in recipients:
            async_to_sync(NotificationManager.notify)(
                event_type=event_type,
                user_id=user_id,
                data=notification_data,
                channels=["app", "email"]  # Notificar en app y email
            )
            
        logger.info(f"Sent {event_type} notifications for vacancy {instance.id} to {len(recipients)} recipients")
        
    except Exception as e:
        logger.error(f"Error sending vacancy notification: {str(e)}", exc_info=True)


@receiver(post_save, sender=Pago)
def notify_payment_status_change(sender, instance, created, **kwargs):
    """
    Envía notificaciones cuando cambia el estado de un pago.
    """
    try:
        # Verificar si estamos procesando un cambio de estado
        if not created and kwargs.get('update_fields') and 'estado' in kwargs.get('update_fields'):
            
            # Obtener el empleador asociado
            empleador = instance.empleador if hasattr(instance, 'empleador') else None
            
            if not empleador:
                logger.warning(f"No employer found for payment {instance.id}")
                return
                
            # Datos para la notificación
            notification_data = {
                "payment_id": instance.id,
                "employer_name": empleador.nombre if hasattr(empleador, 'nombre') else "Desconocido",
                "status": instance.estado,
                "amount": str(instance.monto) if hasattr(instance, 'monto') else "0",
                "timestamp": timezone.now().isoformat()
            }
            
            # Determinar canales y urgencia según el estado
            channels = ["app", "email"]
            
            if instance.estado == "aprobado":
                event_type = "payment_approved"
            elif instance.estado == "rechazado":
                event_type = "payment_rejected"
                channels.append("whatsapp")  # Añadir WhatsApp para notificaciones urgentes
            else:
                event_type = "payment_status_changed"
            
            # Notificar al empleador
            if hasattr(empleador, 'user_id') and empleador.user_id:
                async_to_sync(NotificationManager.notify)(
                    event_type=event_type,
                    user_id=empleador.user_id,
                    data=notification_data,
                    channels=channels
                )
            
            # Notificar al equipo financiero
            if hasattr(instance, 'bu') and instance.bu:
                # Obtener equipo financiero de la BU
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Esta consulta debe adaptarse a tu modelo exacto
                finance_team = User.objects.filter(
                    profile__role="finance",
                    profile__business_units=instance.bu,
                    is_active=True
                ).values_list('id', flat=True)
                
                for user_id in finance_team:
                    async_to_sync(NotificationManager.notify)(
                        event_type=event_type,
                        user_id=user_id,
                        data=notification_data,
                        channels=["app", "email"]
                    )
                
            logger.info(f"Sent {event_type} notification for payment {instance.id}")
            
    except Exception as e:
        logger.error(f"Error sending payment notification: {str(e)}", exc_info=True)


@receiver(post_save, sender=Person)
def notify_person_updates(sender, instance, created, **kwargs):
    """
    Envía notificaciones cuando se crea o actualiza un perfil de persona.
    Notifica sobre nuevos candidatos o actualizaciones importantes del perfil.
    """
    try:
        # Verificar si es nuevo o actualización
        if created:
            event_type = "new_person_created"
            
            # Determinar BU para notificaciones
            bu_id = None
            if hasattr(instance, 'business_unit') and instance.business_unit:
                bu_id = instance.business_unit.id
            
            # Datos para la notificación
            notification_data = {
                "person_id": instance.id,
                "person_name": f"{instance.nombre} {instance.apellido}" if hasattr(instance, 'nombre') and hasattr(instance, 'apellido') else "Sin nombre",
                "bu_id": bu_id,
                "timestamp": timezone.now().isoformat()
            }
            
            # Notificar a consultores de la BU
            if bu_id:
                # Obtener consultores de la BU
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                consultants = User.objects.filter(
                    profile__business_units__id=bu_id,
                    is_active=True
                ).values_list('id', flat=True)
                
                for user_id in consultants:
                    async_to_sync(NotificationManager.notify)(
                        event_type=event_type,
                        user_id=user_id,
                        data=notification_data,
                        channels=["app"]  # Notificar solo en app para evitar spam
                    )
                
                logger.info(f"Sent {event_type} notification for person {instance.id} to {len(consultants)} consultants")
        
        # Verificar si hay actualización de campos importantes
        elif kwargs.get('update_fields'):
            important_fields = {'cv', 'email', 'telefono', 'estado', 'skills'}
            updated_fields = set(kwargs.get('update_fields'))
            
            if important_fields.intersection(updated_fields):
                event_type = "person_important_update"
                
                # Datos para notificación
                notification_data = {
                    "person_id": instance.id,
                    "person_name": f"{instance.nombre} {instance.apellido}" if hasattr(instance, 'nombre') and hasattr(instance, 'apellido') else "Sin nombre",
                    "updated_fields": list(important_fields.intersection(updated_fields)),
                    "timestamp": timezone.now().isoformat()
                }
                
                # Notificar a usuarios siguiendo este perfil
                # Implementación según el modelo específico
                follower_ids = []  # Esta lista debe venir de la relación en el modelo
                
                for user_id in follower_ids:
                    async_to_sync(NotificationManager.notify)(
                        event_type=event_type,
                        user_id=user_id,
                        data=notification_data,
                        channels=["app"]  # Solo en app para evitar spam
                    )
                
    except Exception as e:
        logger.error(f"Error sending person notification: {str(e)}", exc_info=True)


@receiver(post_save, sender=BusinessUnit)
def notify_business_unit_changes(sender, instance, created, **kwargs):
    """
    Envía notificaciones cuando hay cambios en las Business Units.
    """
    try:
        if created:
            # Nueva BU creada
            event_type = "new_business_unit_created"
            
            # Datos para notificación
            notification_data = {
                "bu_id": instance.id,
                "bu_name": instance.name if hasattr(instance, 'name') else "Sin nombre",
                "timestamp": timezone.now().isoformat()
            }
            
            # Notificar a super admins
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            admins = User.objects.filter(is_superuser=True).values_list('id', flat=True)
            
            for user_id in admins:
                async_to_sync(NotificationManager.notify)(
                    event_type=event_type,
                    user_id=user_id,
                    data=notification_data,
                    channels=["app", "email"]
                )
                
            logger.info(f"Sent {event_type} notification for BU {instance.id} to {len(admins)} admins")
            
    except Exception as e:
        logger.error(f"Error sending BU notification: {str(e)}", exc_info=True)
