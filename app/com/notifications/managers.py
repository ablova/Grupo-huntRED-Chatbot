"""
Gestores de notificaciones para diferentes flujos y roles del sistema.

Implementa clases para gestionar las notificaciones según los diferentes
roles y fases del proceso de reclutamiento.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from app.models import Person, BusinessUnit, Vacante, User, Company, Notification, NotificationType, NotificationStatus
from app.com.notifications.corecore import send_notification, schedule_notification

logger = logging.getLogger('notifications')

class NotificationManager:
    """
    Clase base para todos los gestores de notificaciones.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
    
    async def send_notification(
        self, 
        notification_type: str,
        recipient: Person,
        title: str = None,
        content: str = None,
        context: Dict[str, Any] = None,
        sender: User = None,
        vacante: Vacante = None,
        channels: List[str] = None,
        include_verification: bool = False,
        template_name: str = None,
    ) -> Notification:
        """
        Envía una notificación utilizando el core del sistema.
        """
        return await send_notification(
            notification_type=notification_type,
            recipient=recipient,
            business_unit=self.business_unit,
            title=title,
            content=content,
            context=context,
            sender=sender,
            vacante=vacante,
            channels=channels,
            include_verification=include_verification,
            template_name=template_name,
        )
    
    def schedule_notification(
        self,
        notification_type: str,
        recipient: Person,
        scheduled_time: datetime,
        title: str = None,
        content: str = None,
        context: Dict[str, Any] = None,
        sender: User = None,
        vacante: Vacante = None,
        channels: List[str] = None,
        include_verification: bool = False,
        template_name: str = None,
    ) -> Notification:
        """
        Programa una notificación para envío futuro.
        """
        return schedule_notification(
            notification_type=notification_type,
            recipient=recipient,
            business_unit=self.business_unit,
            scheduled_time=scheduled_time,
            title=title,
            content=content,
            context=context,
            sender=sender,
            vacante=vacante,
            channels=channels,
            include_verification=include_verification,
            template_name=template_name,
        )
    
    def get_pending_notifications(self, recipient: Optional[Person] = None) -> List[Notification]:
        """
        Obtiene las notificaciones pendientes para un destinatario o todas.
        """
        query = Q(
            business_unit=self.business_unit,
            status=NotificationStatus.PENDING,
        )
        
        if recipient:
            query &= Q(recipient=recipient)
            
        return Notification.objects.filter(query).order_by('created_at')


class ProcesoNotificationManager(NotificationManager):
    """
    Gestor especializado para notificaciones de responsables de proceso.
    """
    
    async def notificar_proceso_creado(self, responsable: Person, vacante: Vacante, sender: User = None) -> Notification:
        """
        Notifica al responsable de proceso sobre la creación de un nuevo proceso.
        """
        return await self.send_notification(
            notification_type=NotificationType.PROCESO_CREADO,
            recipient=responsable,
            vacante=vacante,
            sender=sender,
            template_name='proceso_creado'
        )
    
    async def solicitar_feedback(
        self, 
        responsable: Person, 
        candidato: Person, 
        vacante: Vacante, 
        entrevista_fecha: datetime,
        feedback_url: str,
        sender: User = None
    ) -> Notification:
        """
        Solicita feedback al responsable sobre una entrevista.
        """
        context = {
            'candidato': candidato,
            'entrevista_fecha': entrevista_fecha,
            'feedback_url': feedback_url
        }
        
        return await self.send_notification(
            notification_type=NotificationType.FEEDBACK_REQUERIDO,
            recipient=responsable,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='feedback_requerido'
        )
    
    async def confirmar_entrevista(
        self,
        responsable: Person,
        candidato: Person,
        vacante: Vacante,
        entrevista_fecha: datetime,
        entrevista_virtual: bool = True,
        entrevista_link: str = None,
        entrevista_lugar: str = None,
        sender: User = None
    ) -> Notification:
        """
        Confirma una entrevista al responsable del proceso.
        """
        context = {
            'candidato': candidato,
            'entrevista_fecha': entrevista_fecha,
            'entrevista_virtual': entrevista_virtual,
            'entrevista_link': entrevista_link,
            'entrevista_lugar': entrevista_lugar
        }
        
        return await self.send_notification(
            notification_type=NotificationType.CONFIRMACION_ENTREVISTA,
            recipient=responsable,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='confirmacion_entrevista'
        )
    
    async def felicitar_contratacion(
        self,
        responsable: Person,
        candidato: Person,
        vacante: Vacante,
        fecha_incorporacion: datetime,
        paquete_salarial: str,
        comision: str,
        sender: User = None
    ) -> Notification:
        """
        Felicita al responsable por una contratación exitosa.
        """
        context = {
            'candidato': candidato,
            'fecha_incorporacion': fecha_incorporacion,
            'paquete_salarial': paquete_salarial,
            'comision': comision
        }
        
        return await self.send_notification(
            notification_type=NotificationType.FELICITACION_CONTRATACION,
            recipient=responsable,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='felicitacion_contratacion'
        )


class ClienteNotificationManager(NotificationManager):
    """
    Gestor especializado para notificaciones a contactos en cliente.
    """
    
    async def solicitar_firma_contrato(
        self,
        contacto: Person,
        vacante: Vacante,
        firma_url: str,
        sender: User = None
    ) -> Notification:
        """
        Solicita la firma de contrato al contacto del cliente.
        """
        context = {
            'firma_url': firma_url
        }
        
        return await self.send_notification(
            notification_type=NotificationType.FIRMA_CONTRATO,
            recipient=contacto,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='firma_contrato'
        )
    
    async def enviar_propuesta(
        self,
        contacto: Person,
        vacante: Vacante,
        propuesta_url: str,
        sender: User = None
    ) -> Notification:
        """
        Envía una propuesta de servicio al contacto del cliente.
        """
        context = {
            'propuesta_url': propuesta_url
        }
        
        return await self.send_notification(
            notification_type=NotificationType.EMISION_PROPUESTA,
            recipient=contacto,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='emision_propuesta'
        )
    
    async def presentar_candidatos(
        self,
        contacto: Person,
        vacante: Vacante,
        candidatos: List[Person],
        dashboard_url: str,
        sender: User = None
    ) -> Notification:
        """
        Presenta candidatos disponibles al contacto del cliente.
        """
        context = {
            'candidatos': candidatos,
            'num_candidatos': len(candidatos),
            'dashboard_url': dashboard_url
        }
        
        return await self.send_notification(
            notification_type=NotificationType.CANDIDATOS_DISPONIBLES,
            recipient=contacto,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='candidatos_disponibles'
        )
    
    async def presentar_candidatos_blind(
        self,
        contacto: Person,
        vacante: Vacante,
        num_candidatos: int,
        blind_profiles_url: str,
        sender: User = None
    ) -> Notification:
        """
        Presenta perfiles anónimos al contacto del cliente.
        """
        context = {
            'num_candidatos': num_candidatos,
            'blind_profiles_url': blind_profiles_url
        }
        
        return await self.send_notification(
            notification_type=NotificationType.CANDIDATOS_BLIND,
            recipient=contacto,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='candidatos_blind'
        )


class ConsultorNotificationManager(NotificationManager):
    """
    Gestor especializado para notificaciones a consultores asignados.
    """
    
    async def enviar_estatus_diario(
        self,
        consultor: Person,
        vacante: Vacante,
        stats: Dict[str, int],
        actividades_recientes: List[Dict],
        proximos_pasos: List[Dict],
        dashboard_url: str,
        sender: User = None
    ) -> Notification:
        """
        Envía un estatus diario del proceso al consultor.
        """
        context = {
            'stats': stats,
            'actividades_recientes': actividades_recientes,
            'proximos_pasos': proximos_pasos,
            'dashboard_url': dashboard_url
        }
        
        return await self.send_notification(
            notification_type=NotificationType.ESTATUS_DIARIO,
            recipient=consultor,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name='estatus_diario'
        )


class PagosNotificationManager(NotificationManager):
    """
    Gestor especializado para notificaciones de pagos y facturación.
    """
    
    async def enviar_recordatorio_pago(
        self,
        contacto: Person,
        vacante: Vacante,
        factura: Dict,
        datos_bancarios: Dict,
        sender: User = None
    ) -> Notification:
        """
        Envía un recordatorio de pago con verificación.
        """
        context = {
            'factura': factura,
            'datos_bancarios': datos_bancarios
        }
        
        return await self.send_notification(
            notification_type=NotificationType.RECORDATORIO_PAGO,
            recipient=contacto,
            vacante=vacante,
            sender=sender,
            context=context,
            include_verification=True,
            template_name='recordatorio_pago'
        )


class CandidatoNotificationManager(NotificationManager):
    """
    Gestor especializado para notificaciones a candidatos.
    """
    
    async def invitar_entrevista(
        self,
        candidato: Person,
        vacante: Vacante,
        entrevista_fecha: datetime,
        entrevista_virtual: bool = True,
        entrevista_link: str = None,
        entrevista_lugar: str = None,
        sender: User = None
    ) -> Notification:
        """
        Invita a un candidato a una entrevista.
        """
        context = {
            'entrevista_fecha': entrevista_fecha,
            'entrevista_virtual': entrevista_virtual,
            'entrevista_link': entrevista_link,
            'entrevista_lugar': entrevista_lugar,
            'empresa': vacante.empresa.nombre if hasattr(vacante, 'empresa') else None
        }
        
        # Personalizar para cada BU
        if self.business_unit.name.lower() == 'huntred':
            template_name = 'invitacion_entrevista_huntred'
        elif self.business_unit.name.lower() == 'huntu':
            template_name = 'invitacion_entrevista_huntu'
        elif self.business_unit.name.lower() == 'amigro':
            template_name = 'invitacion_entrevista_amigro'
        elif self.business_unit.name.lower() == 'huntred_executive':
            template_name = 'invitacion_entrevista_huntred_executive'
        else:
            template_name = 'invitacion_entrevista'
        
        return await self.send_notification(
            notification_type=NotificationType.INVITACION_ENTREVISTA,
            recipient=candidato,
            vacante=vacante,
            sender=sender,
            context=context,
            template_name=template_name
        )


class VacanteManager:
    """
    Gestor para manejar todas las notificaciones relacionadas con una vacante específica.
    """
    
    def __init__(self, vacante: Vacante):
        self.vacante = vacante
        self.business_unit = self._get_business_unit()
        
        # Inicializamos todos los gestores especializados
        self.proceso_manager = ProcesoNotificationManager(self.business_unit)
        self.cliente_manager = ClienteNotificationManager(self.business_unit)
        self.consultor_manager = ConsultorNotificationManager(self.business_unit)
        self.pagos_manager = PagosNotificationManager(self.business_unit)
        self.candidato_manager = CandidatoNotificationManager(self.business_unit)
    
    def _get_business_unit(self) -> BusinessUnit:
        """
        Obtiene la unidad de negocio asociada a la vacante.
        """
        if hasattr(self.vacante, 'business_unit') and self.vacante.business_unit:
            return self.vacante.business_unit
        
        # Si no tiene BU directamente, intentamos inferirla
        try:
            from app.com.utils.vacantes import get_business_unit_for_vacante
            return get_business_unit_for_vacante(self.vacante)
        except ImportError:
            # Si no se puede importar, intentamos con el nombre
            try:
                return BusinessUnit.objects.get(name='huntRED')  # Default a huntRED
            except BusinessUnit.DoesNotExist:
                # Crear una BU temporal para no fallar
                logger.error(f"No se pudo determinar la BU para la vacante {self.vacante.id}")
                return BusinessUnit(name='huntRED', id=1)
    
    async def notify_all_stakeholders(self, event_type: str, context: Dict[str, Any] = None, sender: User = None) -> List[Notification]:
        """
        Notifica a todos los interesados sobre un evento en la vacante.
        """
        notifications = []
        context = context or {}
        
        # Añadimos datos comunes al contexto
        context.update({
            'vacante': self.vacante,
            'business_unit': self.business_unit,
        })
        
        # Determinamos qué notificaciones enviar según el tipo de evento
        if event_type == 'proceso_creado':
            # Notificar al responsable del proceso
            if hasattr(self.vacante, 'responsable') and self.vacante.responsable:
                notification = await self.proceso_manager.notificar_proceso_creado(
                    self.vacante.responsable, self.vacante, sender
                )
                notifications.append(notification)
                
        elif event_type == 'entrevista_programada':
            # Notificar al responsable y al candidato
            candidato = context.get('candidato')
            if candidato and hasattr(self.vacante, 'responsable') and self.vacante.responsable:
                # Notificar al responsable
                notification = await self.proceso_manager.confirmar_entrevista(
                    self.vacante.responsable,
                    candidato,
                    self.vacante,
                    context.get('entrevista_fecha'),
                    context.get('entrevista_virtual', True),
                    context.get('entrevista_link'),
                    context.get('entrevista_lugar'),
                    sender
                )
                notifications.append(notification)
                
                # Notificar al candidato
                notification = await self.candidato_manager.invitar_entrevista(
                    candidato,
                    self.vacante,
                    context.get('entrevista_fecha'),
                    context.get('entrevista_virtual', True),
                    context.get('entrevista_link'),
                    context.get('entrevista_lugar'),
                    sender
                )
                notifications.append(notification)
                
        elif event_type == 'propuesta_emitida':
            # Notificar al contacto del cliente
            if hasattr(self.vacante, 'empresa') and hasattr(self.vacante.empresa, 'contacto_principal'):
                notification = await self.cliente_manager.enviar_propuesta(
                    self.vacante.empresa.contacto_principal,
                    self.vacante,
                    context.get('propuesta_url'),
                    sender
                )
                notifications.append(notification)
                
        elif event_type == 'candidatos_disponibles':
            # Notificar al contacto del cliente
            if hasattr(self.vacante, 'empresa') and hasattr(self.vacante.empresa, 'contacto_principal'):
                notification = await self.cliente_manager.presentar_candidatos(
                    self.vacante.empresa.contacto_principal,
                    self.vacante,
                    context.get('candidatos', []),
                    context.get('dashboard_url'),
                    sender
                )
                notifications.append(notification)
                
        elif event_type == 'recordatorio_pago':
            # Notificar al contacto fiscal del cliente
            if hasattr(self.vacante, 'empresa') and hasattr(self.vacante.empresa, 'contacto_facturacion'):
                notification = await self.pagos_manager.enviar_recordatorio_pago(
                    self.vacante.empresa.contacto_facturacion,
                    self.vacante,
                    context.get('factura', {}),
                    context.get('datos_bancarios', {}),
                    sender
                )
                notifications.append(notification)
        
        # Agregar más tipos de eventos según sea necesario
        
        return notifications
