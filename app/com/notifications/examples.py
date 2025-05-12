"""
Ejemplos de uso del sistema de notificaciones.

Este módulo proporciona ejemplos concretos de cómo utilizar el sistema 
de notificaciones para diferentes roles y escenarios del proceso de reclutamiento.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from django.utils import timezone
from asgiref.sync import async_to_sync

from app.models import Person, BusinessUnit, Vacante, User, Company, Notification, NotificationType, NotificationStatus
from .core import send_notification, schedule_notification
from .managers import (
    ProcesoNotificationManager, 
    ClienteNotificationManager,
    ConsultorNotificationManager,
    PagosNotificationManager,
    CandidatoNotificationManager,
    VacanteManager
)

logger = logging.getLogger('notifications')

# ============================================================
# EJEMPLOS PARA RESPONSABLE DE PROCESO
# ============================================================

def ejemplo_notificacion_proceso_creado():
    """
    Ejemplo de notificación de proceso creado para el responsable.
    """
    # Obtenemos los objetos necesarios
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='active').first()
        responsable = vacante.responsable
        
        if not responsable:
            logger.error("La vacante no tiene responsable asignado")
            return
            
        # Creamos el gestor de notificaciones
        manager = ProcesoNotificationManager(business_unit)
        
        # Enviamos la notificación
        notification = async_to_sync(manager.notificar_proceso_creado)(
            responsable=responsable,
            vacante=vacante
        )
        
        logger.info(f"Notificación de proceso creado enviada: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_notificacion_proceso_creado: {e}")

def ejemplo_solicitar_feedback():
    """
    Ejemplo de solicitud de feedback al responsable tras una entrevista.
    """
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='active').first()
        
        if not vacante.responsable:
            logger.error("La vacante no tiene responsable asignado")
            return
            
        # Obtenemos un candidato para el ejemplo
        candidato = Person.objects.filter(
            role='candidate', 
            state='active'
        ).first()
        
        if not candidato:
            logger.error("No se encontraron candidatos activos")
            return
            
        # Datos de ejemplo para la entrevista
        entrevista_fecha = timezone.now() - timedelta(days=1)
        feedback_url = f"https://dashboard.huntred.com/feedback/{vacante.id}/{candidato.id}"
        
        # Creamos el gestor y enviamos la notificación
        manager = ProcesoNotificationManager(business_unit)
        notification = async_to_sync(manager.solicitar_feedback)(
            responsable=vacante.responsable,
            candidato=candidato,
            vacante=vacante,
            entrevista_fecha=entrevista_fecha,
            feedback_url=feedback_url
        )
        
        logger.info(f"Solicitud de feedback enviada: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_solicitar_feedback: {e}")

def ejemplo_felicitacion_contratacion():
    """
    Ejemplo de felicitación por contratación exitosa.
    """
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='filled').first()
        
        if not vacante or not vacante.responsable:
            logger.error("No se encontró vacante cubierta con responsable")
            return
            
        # Obtenemos el candidato contratado
        candidato = Person.objects.filter(
            role='hired',
            vacante=vacante
        ).first()
        
        if not candidato:
            logger.error("No se encontró candidato contratado para la vacante")
            return
            
        # Datos de ejemplo para la contratación
        fecha_incorporacion = timezone.now() + timedelta(days=15)
        paquete_salarial = f"${vacante.salary:,.2f} MXN brutos mensuales"
        comision = f"${vacante.salary * 0.15:,.2f} MXN"
        
        # Enviamos la notificación
        manager = ProcesoNotificationManager(business_unit)
        notification = async_to_sync(manager.felicitar_contratacion)(
            responsable=vacante.responsable,
            candidato=candidato,
            vacante=vacante,
            fecha_incorporacion=fecha_incorporacion,
            paquete_salarial=paquete_salarial,
            comision=comision
        )
        
        logger.info(f"Felicitación por contratación enviada: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_felicitacion_contratacion: {e}")

# ============================================================
# EJEMPLOS PARA CONTACTO EN CLIENTE
# ============================================================

def ejemplo_solicitar_firma_contrato():
    """
    Ejemplo de solicitud de firma de contrato al cliente.
    """
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='active').first()
        
        if not vacante or not hasattr(vacante, 'empresa') or not vacante.empresa:
            logger.error("La vacante no tiene empresa asociada")
            return
            
        contacto = getattr(vacante.empresa, 'contacto_principal', None)
        if not contacto:
            logger.error("La empresa no tiene contacto principal")
            return
            
        # URL de ejemplo para la firma
        firma_url = f"https://firmas.huntred.com/contrato/{vacante.id}"
        
        # Enviamos la notificación
        manager = ClienteNotificationManager(business_unit)
        notification = async_to_sync(manager.solicitar_firma_contrato)(
            contacto=contacto,
            vacante=vacante,
            firma_url=firma_url
        )
        
        logger.info(f"Solicitud de firma de contrato enviada: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_solicitar_firma_contrato: {e}")

def ejemplo_presentar_candidatos():
    """
    Ejemplo de presentación de candidatos al cliente.
    """
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='active').first()
        
        if not vacante or not hasattr(vacante, 'empresa') or not vacante.empresa:
            logger.error("La vacante no tiene empresa asociada")
            return
            
        contacto = getattr(vacante.empresa, 'contacto_principal', None)
        if not contacto:
            logger.error("La empresa no tiene contacto principal")
            return
            
        # Obtenemos algunos candidatos de ejemplo
        candidatos = Person.objects.filter(
            role='candidate', 
            state='active'
        )[:3]
        
        if not candidatos:
            logger.error("No se encontraron candidatos activos")
            return
            
        # Dashboard URL de ejemplo
        dashboard_url = f"https://dashboard.huntred.com/vacantes/{vacante.id}/candidatos"
        
        # Enviamos la notificación
        manager = ClienteNotificationManager(business_unit)
        notification = async_to_sync(manager.presentar_candidatos)(
            contacto=contacto,
            vacante=vacante,
            candidatos=list(candidatos),
            dashboard_url=dashboard_url
        )
        
        logger.info(f"Presentación de candidatos enviada: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_presentar_candidatos: {e}")

def ejemplo_presentar_candidatos_blind():
    """
    Ejemplo de presentación de perfiles anónimos al cliente.
    """
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='active').first()
        
        if not vacante or not hasattr(vacante, 'empresa') or not vacante.empresa:
            logger.error("La vacante no tiene empresa asociada")
            return
            
        contacto = getattr(vacante.empresa, 'contacto_principal', None)
        if not contacto:
            logger.error("La empresa no tiene contacto principal")
            return
            
        # Dashboard URL de ejemplo
        blind_profiles_url = f"https://dashboard.huntred.com/vacantes/{vacante.id}/candidatos-blind"
        
        # Enviamos la notificación
        manager = ClienteNotificationManager(business_unit)
        notification = async_to_sync(manager.presentar_candidatos_blind)(
            contacto=contacto,
            vacante=vacante,
            num_candidatos=5,
            blind_profiles_url=blind_profiles_url
        )
        
        logger.info(f"Presentación de perfiles anónimos enviada: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_presentar_candidatos_blind: {e}")

# ============================================================
# EJEMPLOS PARA CONSULTOR ASIGNADO
# ============================================================

def ejemplo_estatus_diario():
    """
    Ejemplo de envío de estatus diario al consultor.
    """
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='active').first()
        
        if not vacante:
            logger.error("No se encontró vacante activa")
            return
            
        consultor = getattr(vacante, 'consultor', None)
        if not consultor:
            logger.error("La vacante no tiene consultor asignado")
            return
            
        # Datos de ejemplo para el estatus
        stats = {
            'contactados': 45,
            'cv_revisados': 32,
            'entrevistas_iniciales': 18,
            'entrevistas_cliente': 5,
            'proceso_final': 2
        }
        
        actividades_recientes = [
            {'fecha': timezone.now() - timedelta(days=1), 'descripcion': 'Entrevista con candidato Juan Pérez'},
            {'fecha': timezone.now() - timedelta(days=2), 'descripcion': 'Envío de CV a cliente'},
            {'fecha': timezone.now() - timedelta(days=3), 'descripcion': 'Contacto con 10 nuevos candidatos'}
        ]
        
        proximos_pasos = [
            {'fecha': timezone.now() + timedelta(days=1), 'descripcion': 'Feedback del cliente sobre perfiles enviados'},
            {'fecha': timezone.now() + timedelta(days=2), 'descripcion': 'Entrevista técnica con candidato finalista'}
        ]
        
        dashboard_url = f"https://dashboard.huntred.com/vacantes/{vacante.id}"
        
        # Enviamos la notificación
        manager = ConsultorNotificationManager(business_unit)
        notification = async_to_sync(manager.enviar_estatus_diario)(
            consultor=consultor,
            vacante=vacante,
            stats=stats,
            actividades_recientes=actividades_recientes,
            proximos_pasos=proximos_pasos,
            dashboard_url=dashboard_url
        )
        
        logger.info(f"Estatus diario enviado: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_estatus_diario: {e}")

# ============================================================
# EJEMPLOS PARA RECORDATORIOS DE PAGO
# ============================================================

def ejemplo_recordatorio_pago():
    """
    Ejemplo de recordatorio de pago con verificación.
    """
    try:
        business_unit = BusinessUnit.objects.get(name='huntRED')
        vacante = Vacante.objects.filter(status='filled').first()
        
        if not vacante or not hasattr(vacante, 'empresa') or not vacante.empresa:
            logger.error("La vacante no tiene empresa asociada")
            return
            
        contacto = getattr(vacante.empresa, 'contacto_facturacion', None)
        if not contacto:
            contacto = getattr(vacante.empresa, 'contacto_principal', None)
            
        if not contacto:
            logger.error("La empresa no tiene contacto para facturación")
            return
            
        # Datos de ejemplo para la factura
        factura = {
            'numero': f"HUNT-{vacante.id}-2025",
            'fecha_emision': timezone.now() - timedelta(days=25),
            'fecha_vencimiento': timezone.now() + timedelta(days=5),
            'monto_total': f"${vacante.salary * 1.5:,.2f} MXN",
            'concepto': f"Servicio de reclutamiento para posición {vacante.title}"
        }
        
        # Datos bancarios de ejemplo
        datos_bancarios = {
            'banco': 'BBVA',
            'titular': 'Grupo huntRED, S.A. de C.V.',
            'cuenta': '012345678901234567',
            'clabe': '012180001234567890'
        }
        
        # Enviamos la notificación
        manager = PagosNotificationManager(business_unit)
        notification = async_to_sync(manager.enviar_recordatorio_pago)(
            contacto=contacto,
            vacante=vacante,
            factura=factura,
            datos_bancarios=datos_bancarios
        )
        
        logger.info(f"Recordatorio de pago enviado: {notification.id}")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_recordatorio_pago: {e}")

# ============================================================
# EJEMPLO DE NOTIFICACIÓN A TODOS LOS STAKEHOLDERS
# ============================================================

def ejemplo_notificar_stakeholders():
    """
    Ejemplo de notificación a todos los interesados en una vacante.
    """
    try:
        vacante = Vacante.objects.filter(status='active').first()
        
        if not vacante:
            logger.error("No se encontró vacante activa")
            return
            
        # Creamos el gestor de vacante
        manager = VacanteManager(vacante)
        
        # Ejemplo: Notificar sobre entrevista programada
        candidato = Person.objects.filter(
            role='candidate', 
            state='active'
        ).first()
        
        if not candidato:
            logger.error("No se encontró candidato activo")
            return
            
        context = {
            'candidato': candidato,
            'entrevista_fecha': timezone.now() + timedelta(days=2, hours=3),
            'entrevista_virtual': True,
            'entrevista_link': 'https://teams.microsoft.com/l/meetup-join/abc123'
        }
        
        # Enviamos las notificaciones
        notifications = async_to_sync(manager.notify_all_stakeholders)(
            event_type='entrevista_programada',
            context=context
        )
        
        logger.info(f"Se enviaron {len(notifications)} notificaciones a los stakeholders")
        
    except Exception as e:
        logger.error(f"Error en ejemplo_notificar_stakeholders: {e}")

# Función para ejecutar todos los ejemplos
def ejecutar_todos_ejemplos():
    """
    Ejecuta todos los ejemplos de notificaciones.
    """
    logger.info("Iniciando ejemplos de notificaciones...")
    
    # Responsable de proceso
    ejemplo_notificacion_proceso_creado()
    ejemplo_solicitar_feedback()
    ejemplo_felicitacion_contratacion()
    
    # Contacto en cliente
    ejemplo_solicitar_firma_contrato()
    ejemplo_presentar_candidatos()
    ejemplo_presentar_candidatos_blind()
    
    # Consultor asignado
    ejemplo_estatus_diario()
    
    # Pagos
    ejemplo_recordatorio_pago()
    
    # Stakeholders
    ejemplo_notificar_stakeholders()
    
    logger.info("Ejemplos de notificaciones completados")
