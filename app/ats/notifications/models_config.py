# /home/pablo/app/com/notifications/models_config.py
#
# Modelos para la configuración y personalización de notificaciones.
# Permite definir momentos de contacto específicos por BU y eventos personalizados.

import uuid
import json
from typing import Dict, Any, List, Optional
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder

from app.models import BusinessUnit, Vacante

class NotificationEvent(models.TextChoices):
    """Eventos estándar del sistema que pueden disparar notificaciones."""
    # Eventos de vacante
    PROCESO_CREADO = 'proceso_creado', 'Creación de proceso'
    BUSQUEDA_INICIADA = 'busqueda_iniciada', 'Búsqueda iniciada'
    ENTREVISTA_PROGRAMADA = 'entrevista_programada', 'Entrevista programada'
    VACANTE_CUBIERTA = 'vacante_cubierta', 'Vacante cubierta'
    VACANTE_CERRADA = 'vacante_cerrada', 'Vacante cerrada'
    
    # Eventos de candidato
    NUEVO_CANDIDATO = 'nuevo_candidato', 'Nuevo candidato'
    CANDIDATO_PRESELECCIONADO = 'candidato_preseleccionado', 'Candidato preseleccionado'
    CANDIDATO_CONTRATADO = 'candidato_contratado', 'Candidato contratado'
    CANDIDATO_RECHAZADO = 'candidato_rechazado', 'Candidato rechazado'
    
    # Eventos de oferta
    OFERTA_EMITIDA = 'oferta_emitida', 'Oferta emitida'
    OFERTA_ACEPTADA = 'oferta_aceptada', 'Oferta aceptada'
    OFERTA_RECHAZADA = 'oferta_rechazada', 'Oferta rechazada'
    
    # Eventos de facturación y pagos
    FACTURA_EMITIDA = 'factura_emitida', 'Factura emitida'
    FACTURA_PAGADA = 'factura_pagada', 'Factura pagada'
    FACTURA_VENCIDA = 'factura_vencida', 'Factura vencida'
    HITO_PAGO = 'hito_pago', 'Hito de pago'
    RECORDATORIO_PAGO = 'recordatorio_pago', 'Recordatorio de pago'
    
    # Eventos de propuesta y contrato
    PROPUESTA_EMITIDA = 'propuesta_emitida', 'Propuesta emitida'
    PROPUESTA_ACEPTADA = 'propuesta_aceptada', 'Propuesta aceptada'
    FIRMA_CONTRATO = 'firma_contrato', 'Firma de contrato'

class NotificationTargetRole(models.TextChoices):
    """Roles objetivo para las notificaciones."""
    RESPONSABLE_PROCESO = 'responsable_proceso', 'Responsable de proceso'
    CONSULTOR_ASIGNADO = 'consultor_asignado', 'Consultor asignado'
    CONTACTO_CLIENTE = 'contacto_cliente', 'Contacto en cliente'
    CONTACTO_FACTURACION = 'contacto_facturacion', 'Contacto de facturación'
    CANDIDATO = 'candidato', 'Candidato'
    EQUIPO_COMPLETO = 'equipo_completo', 'Equipo completo'

class ContactMoment(models.Model):
    """
    Define un momento de contacto específico con plantillas personalizadas.
    Permite configurar cuándo y cómo se envían notificaciones para cada evento y BU.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name=_('Nombre'))
    description = models.TextField(verbose_name=_('Descripción'), blank=True)
    
    # Asociación con BU y evento
    business_unit = models.ForeignKey(
        BusinessUnit, 
        on_delete=models.CASCADE, 
        related_name='contact_moments',
        verbose_name=_('Unidad de negocio')
    )
    event_type = models.CharField(
        max_length=50, 
        choices=NotificationEvent.choices,
        verbose_name=_('Tipo de evento')
    )
    
    # Configuración de destinatarios
    target_roles = models.JSONField(
        default=list,
        verbose_name=_('Roles destinatarios'),
        help_text=_('Roles a los que se enviará la notificación')
    )
    
    # Canales habilitados
    email_enabled = models.BooleanField(default=True, verbose_name=_('Email habilitado'))
    whatsapp_enabled = models.BooleanField(default=True, verbose_name=_('WhatsApp habilitado'))
    sms_enabled = models.BooleanField(default=False, verbose_name=_('SMS habilitado'))
    telegram_enabled = models.BooleanField(default=False, verbose_name=_('Telegram habilitado'))
    app_enabled = models.BooleanField(default=True, verbose_name=_('Notificación en app habilitada'))
    slack_enabled = models.BooleanField(default=False, verbose_name=_('Slack habilitado'))
    
    # Plantillas personalizadas
    email_subject_template = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name=_('Asunto del email'),
        help_text=_('Plantilla para el asunto del email. Usa {{ variable }} para datos dinámicos.')
    )
    email_body_template = models.TextField(
        blank=True,
        verbose_name=_('Cuerpo del email'),
        help_text=_('Plantilla HTML para el cuerpo del email. Usa {{ variable }} para datos dinámicos.')
    )
    whatsapp_template = models.TextField(
        blank=True,
        verbose_name=_('Mensaje de WhatsApp'),
        help_text=_('Plantilla para mensajes de WhatsApp. Usa {{ variable }} para datos dinámicos.')
    )
    
    # Configuración de tiempo
    send_immediately = models.BooleanField(
        default=True,
        verbose_name=_('Enviar inmediatamente'),
        help_text=_('Si está marcado, se envía inmediatamente cuando ocurre el evento')
    )
    delay_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Retraso (minutos)'),
        help_text=_('Minutos de retraso antes de enviar la notificación')
    )
    
    # Verificación y seguridad
    include_verification = models.BooleanField(
        default=False,
        verbose_name=_('Incluir código de verificación'),
        help_text=_('Si está marcado, incluye un código de verificación único en la notificación')
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Última actualización'))
    is_active = models.BooleanField(default=True, verbose_name=_('Activo'))
    
    # Condiciones adicionales
    conditions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Condiciones adicionales'),
        help_text=_('Condiciones específicas bajo las cuales se envía la notificación (formato JSON)')
    )
    
    class Meta:
        verbose_name = _('Momento de contacto')
        verbose_name_plural = _('Momentos de contacto')
        unique_together = ('business_unit', 'event_type', 'name')
        indexes = [
            models.Index(fields=['business_unit', 'event_type']),
            models.Index(fields=['event_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()} - {self.business_unit.name})"
    
    def get_enabled_channels(self) -> List[str]:
        """Devuelve una lista de canales habilitados para este momento de contacto."""
        channels = []
        if self.email_enabled:
            channels.append('email')
        if self.whatsapp_enabled:
            channels.append('whatsapp')
        if self.sms_enabled:
            channels.append('sms')
        if self.telegram_enabled:
            channels.append('telegram')
        if self.app_enabled:
            channels.append('app')
        if self.slack_enabled:
            channels.append('slack')
        return channels
    
    def should_send(self, context: Dict[str, Any]) -> bool:
        """
        Evalúa si la notificación debe enviarse según las condiciones configuradas.
        
        Args:
            context: Contexto con datos relevantes al evento
            
        Returns:
            True si debe enviarse, False en caso contrario
        """
        if not self.is_active:
            return False
            
        # Si no hay condiciones adicionales, siempre se envía
        if not self.conditions:
            return True
            
        # Evaluamos cada condición configurada
        try:
            for field, condition in self.conditions.items():
                # Obtenemos el valor del campo del contexto
                value = self._get_nested_value(context, field)
                
                # Si el campo no existe en el contexto, la condición no se cumple
                if value is None:
                    return False
                    
                # Operador de la condición
                operator = condition.get('operator', 'eq')
                target_value = condition.get('value')
                
                # Evaluamos según el operador
                if operator == 'eq' and value != target_value:
                    return False
                elif operator == 'neq' and value == target_value:
                    return False
                elif operator == 'gt' and not (value > target_value):
                    return False
                elif operator == 'lt' and not (value < target_value):
                    return False
                elif operator == 'contains' and target_value not in value:
                    return False
                elif operator == 'in' and value not in target_value:
                    return False
                    
            # Si todas las condiciones se cumplen
            return True
            
        except Exception as e:
            # Si hay algún error en la evaluación, registramos y permitimos el envío
            print(f"Error evaluando condiciones para {self}: {e}")
            return True
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """
        Obtiene un valor anidado de un diccionario usando una ruta de claves.
        
        Args:
            data: Diccionario de datos
            key_path: Ruta de claves separadas por puntos (e.g., "vacante.empresa.nombre")
            
        Returns:
            El valor encontrado o None si no existe
        """
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
                
        return value

class NotificationTemplate(models.Model):
    """
    Plantillas de notificación para diferentes tipos de eventos y canales.
    Permite personalizar los mensajes para cada unidad de negocio.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name=_('Nombre'))
    description = models.TextField(blank=True, verbose_name=_('Descripción'))
    
    # Asociación con BU y evento
    business_unit = models.ForeignKey(
        BusinessUnit, 
        on_delete=models.CASCADE, 
        related_name='notification_templates',
        verbose_name=_('Unidad de negocio')
    )
    event_type = models.CharField(
        max_length=50, 
        choices=NotificationEvent.choices,
        verbose_name=_('Tipo de evento')
    )
    
    # Contenido de las plantillas
    email_subject = models.CharField(
        max_length=255,
        verbose_name=_('Asunto del email')
    )
    email_body_html = models.TextField(
        verbose_name=_('Cuerpo HTML del email')
    )
    whatsapp_message = models.TextField(
        verbose_name=_('Mensaje de WhatsApp')
    )
    sms_message = models.TextField(
        blank=True,
        verbose_name=_('Mensaje SMS'),
        help_text=_('Limitado a 160 caracteres')
    )
    
    # Variables disponibles
    available_variables = models.JSONField(
        default=list,
        verbose_name=_('Variables disponibles'),
        help_text=_('Lista de variables que pueden usarse en las plantillas')
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Fecha de creación'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Última actualización'))
    is_default = models.BooleanField(
        default=False, 
        verbose_name=_('Es plantilla por defecto'),
        help_text=_('Si está marcado, esta plantilla se usa por defecto para este evento')
    )
    
    class Meta:
        verbose_name = _('Plantilla de notificación')
        verbose_name_plural = _('Plantillas de notificación')
        unique_together = ('business_unit', 'event_type', 'name')
        indexes = [
            models.Index(fields=['business_unit', 'event_type']),
            models.Index(fields=['event_type', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()} - {self.business_unit.name})"
