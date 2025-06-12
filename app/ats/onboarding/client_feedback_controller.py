"""
Controlador para manejar encuestas de satisfacción de clientes.

Este módulo proporciona funcionalidades para:
1. Crear y programar encuestas de satisfacción para clientes
2. Procesar respuestas de encuestas
3. Generar reportes de satisfacción segmentados por Business Unit
4. Integrar con el sistema ML para análisis predictivo
"""

import json
import logging
import base64
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.signing import Signer, BadSignature
from django.conf import settings
from django.db import transaction
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

from app.models import Empresa, BusinessUnit, Person, ClientFeedback, ClientFeedbackSchedule, CLIENT_FEEDBACK_PERIODS
from app.ml.onboarding_processor import OnboardingMLProcessor

logger = logging.getLogger(__name__)

# Configuración para firma de tokens de seguridad
signer = Signer(salt='client-satisfaction')

class ClientFeedbackController:
    """
    Controlador principal para gestionar las encuestas de satisfacción de clientes.
    """
    
    @classmethod
    async def schedule_client_feedback(cls, empresa_id, business_unit_id, start_date=None, respondent_id=None, consultant_id=None):
        """
        Programa encuestas de satisfacción para un cliente.
        
        Args:
            empresa_id (int): ID de la empresa cliente
            business_unit_id (int): ID de la Business Unit asociada
            start_date (datetime, optional): Fecha de inicio de la relación. Si es None, usa la fecha actual.
            respondent_id (int, optional): ID de la persona que responderá la encuesta
            consultant_id (int, optional): ID del consultor responsable
            
        Returns:
            dict: Información sobre la programación creada
        """
        try:
            # Validar datos
            if not empresa_id or not business_unit_id:
                raise ValidationError("Se requieren empresa_id y business_unit_id")
                
            # Si no se proporciona fecha, usar la actual
            if not start_date:
                start_date = timezone.now()
            
            # Crear programación de forma asíncrona
            @sync_to_async
            def create_schedule():
                empresa = Empresa.objects.get(id=empresa_id)
                business_unit = BusinessUnit.objects.get(id=business_unit_id)
                
                # Verificar si ya existe una programación para esta empresa y BU
                existing = ClientFeedbackSchedule.objects.filter(
                    empresa_id=empresa_id,
                    business_unit_id=business_unit_id,
                    is_active=True
                ).first()
                
                if existing:
                    return existing, False
                
                # Crear nueva programación
                first_period = CLIENT_FEEDBACK_PERIODS[0]  # 30 días
                next_feedback_date = start_date + timedelta(days=first_period)
                
                schedule = ClientFeedbackSchedule.objects.create(
                    empresa_id=empresa_id,
                    business_unit_id=business_unit_id,
                    start_date=start_date,
                    next_feedback_date=next_feedback_date,
                    period_days=first_period
                )
                
                # Crear la primera encuesta programada
                feedback = ClientFeedback.objects.create(
                    empresa_id=empresa_id,
                    business_unit_id=business_unit_id,
                    respondent_id=respondent_id,
                    consultant_id=consultant_id,
                    period_days=first_period,
                    status='PENDING'
                )
                
                return schedule, True
            
            schedule, is_new = await create_schedule()
            
            return {
                'success': True,
                'schedule_id': schedule.id,
                'empresa_id': empresa_id,
                'business_unit_id': business_unit_id,
                'next_feedback_date': schedule.next_feedback_date.isoformat(),
                'is_new': is_new
            }
            
        except Exception as e:
            logger.error(f"Error programando feedback de cliente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    async def generate_feedback_link(cls, feedback_id):
        """
        Genera un enlace seguro para una encuesta de satisfacción de cliente.
        
        Args:
            feedback_id (int): ID de la encuesta
            
        Returns:
            str: URL firmada para la encuesta
        """
        try:
            @sync_to_async
            def get_feedback_data():
                feedback = get_object_or_404(ClientFeedback, id=feedback_id)
                
                # Verificar que la encuesta esté en estado pendiente
                if feedback.status != 'PENDING':
                    raise ValidationError(f"La encuesta no está en estado pendiente: {feedback.status}")
                
                # Generar token único
                token_data = {
                    'feedback_id': feedback_id,
                    'ts': timezone.now().timestamp(),
                    'uuid': str(uuid.uuid4())
                }
                
                # Firmar token y guardarlo en la encuesta
                signed_token = signer.sign(json.dumps(token_data))
                feedback.token = signed_token
                feedback.status = 'SENT'
                feedback.sent_date = timezone.now()
                feedback.save(update_fields=['token', 'status', 'sent_date'])
                
                return feedback, signed_token
            
            feedback, signed_token = await get_feedback_data()
            
            # Construir URL
            base_url = getattr(settings, 'SITE_URL', 'https://app.huntred.com')
            survey_url = f"{base_url}/onboarding/client-survey/?token={signed_token}"
            
            return survey_url
            
        except Exception as e:
            logger.error(f"Error generando enlace para encuesta de cliente: {str(e)}")
            return None
    
    @classmethod
    async def send_feedback_survey(cls, feedback_id):
        """
        Envía la encuesta de satisfacción al cliente.
        
        Args:
            feedback_id (int): ID de la encuesta
            
        Returns:
            dict: Resultado del envío
        """
        try:
            from app.ats.integrations.services import send_email, send_message
            
            # Generar enlace
            survey_url = await cls.generate_feedback_link(feedback_id)
            if not survey_url:
                raise ValueError(f"No se pudo generar el enlace para la encuesta ID: {feedback_id}")
            
            @sync_to_async
            def send_survey():
                feedback = get_object_or_404(ClientFeedback, id=feedback_id)
                empresa = feedback.empresa
                business_unit = feedback.business_unit
                respondent = feedback.respondent
                
                if not respondent:
                    raise ValueError("No hay destinatario definido para la encuesta")
                
                # Preparar mensaje
                message = f"👋 Hola {respondent.first_name},\n\n"
                message += f"En Grupo huntRED® valoramos su opinión sobre nuestros servicios.\n\n"
                message += f"Le invitamos a completar esta breve encuesta de satisfacción: {survey_url}\n\n"
                message += "Su feedback es fundamental para seguir mejorando nuestros servicios.\n\n"
                message += "Gracias,\nEquipo Grupo huntRED®"
                
                # Intentar enviar por email
                sent = False
                if respondent.email:
                    try:
                        email_subject = f"Encuesta de Satisfacción - {business_unit.name}"
                        send_email(respondent.email, email_subject, message)
                        sent = True
                        logger.info(f"Encuesta enviada por email a {respondent.email} para empresa {empresa.name}")
                    except Exception as e:
                        logger.warning(f"No se pudo enviar por email: {str(e)}")
                
                # Si no se envió por email, intentar por WhatsApp
                if not sent and respondent.whatsapp:
                    try:
                        send_message("whatsapp", respondent.whatsapp, message, business_unit_id=business_unit.id)
                        sent = True
                        logger.info(f"Encuesta enviada por WhatsApp a {respondent.whatsapp}")
                    except Exception as e:
                        logger.warning(f"No se pudo enviar por WhatsApp: {str(e)}")
                
                if not sent:
                    raise ValueError(f"No se pudo enviar la encuesta al cliente {empresa.name} por ningún canal")
                
                return feedback
            
            feedback = await send_survey()
            
            return {
                'success': True,
                'feedback_id': feedback_id,
                'message': 'Encuesta enviada correctamente'
            }
            
        except Exception as e:
            logger.error(f"Error enviando encuesta de satisfacción a cliente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    async def process_feedback_response(cls, token, data):
        """
        Procesa las respuestas de una encuesta de satisfacción de cliente.
        
        Args:
            token (str): Token firmado que contiene feedback_id
            data (dict): Datos de la encuesta
            
        Returns:
            dict: Resultado del procesamiento
        """
        try:
            # Validar y decodificar token
            try:
                token_data = json.loads(signer.unsign(token))
                feedback_id = token_data.get('feedback_id')
            except (BadSignature, json.JSONDecodeError) as e:
                logger.error(f"Token inválido: {str(e)}")
                return {'success': False, 'error': 'Token inválido'}
            
            if not feedback_id:
                return {'success': False, 'error': 'Token con datos incompletos'}
            
            # Guardar respuesta
            @sync_to_async
            def save_response():
                feedback = get_object_or_404(ClientFeedback, id=feedback_id)
                
                # Verificar que la encuesta esté en estado enviado y el token coincida
                if feedback.status != 'SENT':
                    if feedback.status == 'COMPLETED':
                        return feedback, True  # Ya fue respondida
                    else:
                        raise ValidationError(f"Estado de encuesta inválido: {feedback.status}")
                
                if feedback.token != token:
                    raise ValidationError("Token no coincide con el registrado")
                
                # Guardar respuestas
                feedback.record_responses(data)
                
                # Actualizar programación para próxima encuesta
                try:
                    schedule = ClientFeedbackSchedule.objects.get(
                        empresa=feedback.empresa,
                        business_unit=feedback.business_unit,
                        is_active=True
                    )
                    schedule.update_next_feedback_date()
                except ClientFeedbackSchedule.DoesNotExist:
                    pass
                
                # Si satisfacción es baja, crear alerta
                if feedback.is_low_satisfaction():
                    # TODO: Implementar sistema de alertas para satisfacción baja
                    logger.warning(f"Alerta: Baja satisfacción en cliente {feedback.empresa.name}, BU {feedback.business_unit.name}")
                
                return feedback, False
            
            feedback, already_completed = await save_response()
            
            if already_completed:
                return {
                    'success': True,
                    'already_completed': True,
                    'message': 'Esta encuesta ya había sido respondida'
                }
            
            # Procesar datos para ML
            ml_processor = OnboardingMLProcessor()
            await ml_processor.process_client_feedback(feedback.id)
            
            return {
                'success': True,
                'message': 'Respuesta procesada correctamente'
            }
            
        except Exception as e:
            logger.error(f"Error procesando respuesta de encuesta de cliente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    async def generate_bu_satisfaction_report(cls, business_unit_id, start_date=None, end_date=None):
        """
        Genera un reporte de satisfacción de clientes por Business Unit.
        
        Args:
            business_unit_id (int): ID de la Business Unit
            start_date (datetime, optional): Fecha de inicio del período
            end_date (datetime, optional): Fecha de fin del período
            
        Returns:
            dict: Datos del reporte
        """
        try:
            if not start_date:
                # Por defecto, reportes de los últimos 6 meses
                start_date = timezone.now() - timedelta(days=180)
                
            if not end_date:
                end_date = timezone.now()
            
            @sync_to_async
            def get_report_data():
                business_unit = get_object_or_404(BusinessUnit, id=business_unit_id)
                
                # Obtener encuestas completadas en el período
                feedback_list = ClientFeedback.objects.filter(
                    business_unit_id=business_unit_id,
                    status='COMPLETED',
                    completed_date__gte=start_date,
                    completed_date__lte=end_date
                ).select_related('empresa', 'respondent')
                
                # Calcular métricas
                total_count = feedback_list.count()
                
                if total_count == 0:
                    avg_satisfaction = None
                    satisfaction_trend = None
                    recommendation_rate = None
                    improvement_areas = []
                else:
                    # Satisfacción promedio
                    avg_satisfaction = feedback_list.filter(
                        satisfaction_score__isnull=False
                    ).values_list('satisfaction_score', flat=True)
                    
                    avg_satisfaction = sum(avg_satisfaction) / len(avg_satisfaction) if avg_satisfaction else 0
                    
                    # Tendencia (comparando primer y segundo trimestre)
                    mid_date = start_date + (end_date - start_date) / 2
                    first_half = feedback_list.filter(
                        completed_date__lt=mid_date,
                        satisfaction_score__isnull=False
                    ).values_list('satisfaction_score', flat=True)
                    
                    second_half = feedback_list.filter(
                        completed_date__gte=mid_date,
                        satisfaction_score__isnull=False
                    ).values_list('satisfaction_score', flat=True)
                    
                    first_avg = sum(first_half) / len(first_half) if first_half else 0
                    second_avg = sum(second_half) / len(second_half) if second_half else 0
                    
                    if first_avg > 0 and second_avg > 0:
                        change = ((second_avg - first_avg) / first_avg) * 100
                        satisfaction_trend = {
                            'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable',
                            'percentage': abs(change)
                        }
                    else:
                        satisfaction_trend = None
                    
                    # Tasa de recomendación
                    recommend_count = 0
                    for fb in feedback_list:
                        if fb.responses.get('would_recommend') == 'yes':
                            recommend_count += 1
                    
                    recommendation_rate = (recommend_count / total_count) * 100 if total_count > 0 else 0
                    
                    # Áreas de mejora
                    improvement_counts = {}
                    for fb in feedback_list:
                        areas = fb.get_improvement_areas()
                        for area in areas:
                            improvement_counts[area] = improvement_counts.get(area, 0) + 1
                    
                    improvement_areas = [
                        {'area': area, 'count': count}
                        for area, count in sorted(improvement_counts.items(), key=lambda x: x[1], reverse=True)
                    ]
                
                # Datos por empresa
                companies_data = []
                for empresa_id in feedback_list.values_list('empresa_id', flat=True).distinct():
                    empresa_feedback = feedback_list.filter(empresa_id=empresa_id)
                    empresa = empresa_feedback.first().empresa if empresa_feedback.exists() else None
                    
                    if not empresa:
                        continue
                        
                    scores = empresa_feedback.filter(
                        satisfaction_score__isnull=False
                    ).values_list('satisfaction_score', flat=True)
                    
                    avg_score = sum(scores) / len(scores) if scores else 0
                    
                    companies_data.append({
                        'id': empresa.id,
                        'name': empresa.name,
                        'count': empresa_feedback.count(),
                        'satisfaction_score': avg_score
                    })
                
                # Ordenar por satisfacción
                companies_data.sort(key=lambda x: x['satisfaction_score'], reverse=True)
                
                return {
                    'business_unit': {
                        'id': business_unit.id,
                        'name': business_unit.name,
                        'code': business_unit.code
                    },
                    'period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'metrics': {
                        'total_feedback_count': total_count,
                        'average_satisfaction': avg_satisfaction,
                        'satisfaction_trend': satisfaction_trend,
                        'recommendation_rate': recommendation_rate,
                        'improvement_areas': improvement_areas
                    },
                    'companies': companies_data
                }
            
            report_data = await get_report_data()
            return report_data
            
        except Exception as e:
            logger.error(f"Error generando reporte de satisfacción de BU: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    async def check_pending_feedback(cls):
        """
        Verifica las encuestas pendientes de envío según la programación.
        
        Returns:
            dict: Resultado de la verificación
        """
        try:
            @sync_to_async
            def get_pending_schedules():
                # Obtener programaciones con encuestas pendientes
                now = timezone.now()
                schedules = ClientFeedbackSchedule.objects.filter(
                    is_active=True,
                    next_feedback_date__lte=now
                ).select_related('empresa', 'business_unit')
                
                result = []
                for schedule in schedules:
                    # Verificar si ya existe una encuesta para este período
                    existing = ClientFeedback.objects.filter(
                        empresa=schedule.empresa,
                        business_unit=schedule.business_unit,
                        period_days=schedule.period_days,
                        status__in=['PENDING', 'SENT']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Obtener último respondent y consultant
                    last_feedback = ClientFeedback.objects.filter(
                        empresa=schedule.empresa,
                        business_unit=schedule.business_unit
                    ).order_by('-created_at').first()
                    
                    respondent_id = last_feedback.respondent_id if last_feedback else None
                    consultant_id = last_feedback.consultant_id if last_feedback else None
                    
                    # Crear nueva encuesta
                    feedback = ClientFeedback.objects.create(
                        empresa=schedule.empresa,
                        business_unit=schedule.business_unit,
                        respondent_id=respondent_id,
                        consultant_id=consultant_id,
                        period_days=schedule.period_days,
                        status='PENDING'
                    )
                    
                    result.append({
                        'feedback_id': feedback.id,
                        'empresa_id': schedule.empresa.id,
                        'empresa_name': schedule.empresa.name,
                        'business_unit_id': schedule.business_unit.id,
                        'business_unit_name': schedule.business_unit.name,
                        'period_days': schedule.period_days
                    })
                
                return result
            
            pending_feedback = await get_pending_schedules()
            
            return {
                'success': True,
                'pending_count': len(pending_feedback),
                'pending_feedback': pending_feedback
            }
            
        except Exception as e:
            logger.error(f"Error verificando encuestas pendientes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
