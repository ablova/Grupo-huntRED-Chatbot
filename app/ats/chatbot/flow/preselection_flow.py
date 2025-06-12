# /home/pablo/app/ats/chatbot/flow/preselection_flow.py
from typing import Dict, Any, List, Optional
from django.utils import timezone
from datetime import timedelta
import logging
from collections import Counter

from app.models import Person, BusinessUnit, Vacante
from app.ats.chatbot.models.preselection import CandidatePreselection
from app.ats.chatbot.flow.conversational_flow import ConversationalFlowManager
from app.ats.notifications.specific_notifications import (
    process_notifier, event_notifier, alert_notifier, user_notifier,
    placement_notifier, payment_notifier, metrics_notifier
)
from app.ats.chatbot.notifications.telegram_notifications import TelegramNotifier

logger = logging.getLogger(__name__)

class PreselectionFlowManager(ConversationalFlowManager):
    """
    Gestor de flujo para la pre-selección de candidatos.
    Maneja la interacción con el Managing Partner para revisar y seleccionar candidatos.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        super().__init__(business_unit)
        
        # Inicializar notificadores específicos
        self.process_notifier = process_notifier(business_unit)
        self.event_notifier = event_notifier(business_unit)
        self.alert_notifier = alert_notifier(business_unit)
        self.user_notifier = user_notifier(business_unit)
        self.telegram_notifier = TelegramNotifier(business_unit.id)

    async def start_preselection(self, vacancy: Vacante, mp: Person) -> Dict[str, Any]:
        """
        Inicia el proceso de pre-selección para una vacante.
        """
        try:
            # Obtener candidatos pre-seleccionados
            preselection_data = await self.matchmaking_system.get_preselection_candidates(
                vacancy=vacancy,
                num_candidates=8  # Número inicial de candidatos
            )
            
            # Crear registro de pre-selección
            preselection = await CandidatePreselection.objects.acreate(
                vacancy=vacancy,
                business_unit=self.business_unit,
                preselection_data=preselection_data
            )
            
            # Notificar al MP vía Telegram
            await self.telegram_notifier.send_preselection_notification(
                mp.chat_id,
                {
                    'id': preselection.id,
                    'vacancy': vacancy.titulo,
                    'total_candidates': len(preselection_data['candidates']),
                    'created_at': preselection.created_at.strftime('%Y-%m-%d %H:%M')
                }
            )
            
            # Notificar evento del sistema
            await self.event_notifier.notify_system_event(
                recipient=mp,
                event_name='preselection_created',
                event_type='preselection_event',
                event_data={
                    'preselection_id': preselection.id,
                    'vacancy_id': vacancy.id,
                    'num_candidates': len(preselection_data['candidates'])
                }
            )
            
            return {
                'success': True,
                'preselection_id': preselection.id,
                'candidates': preselection_data['candidates']
            }
            
        except Exception as e:
            logger.error(f"Error iniciando pre-selección: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def process_mp_review(self, preselection_id: int, mp: Person, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la revisión del MP sobre los candidatos pre-seleccionados.
        """
        try:
            # Obtener pre-selección
            preselection = await CandidatePreselection.objects.aget(id=preselection_id)
            
            # Procesar feedback
            result = await self.matchmaking_system.process_mp_feedback(
                preselection_id=preselection_id,
                feedback=feedback
            )
            
            if result['success']:
                # Actualizar estado
                preselection.update_status('mp_reviewed')
                
                # Notificar resultado vía Telegram
                await self.telegram_notifier.send_review_completed(
                    mp.chat_id,
                    {
                        'vacancy': preselection.vacancy.titulo,
                        'selected_candidates': len(result['final_candidates']),
                        'review_time': (timezone.now() - preselection.created_at).total_seconds() / 3600
                    }
                )
                
                # Notificar evento del sistema
                await self.event_notifier.notify_system_event(
                    recipient=mp,
                    event_name='preselection_completed',
                    event_type='preselection_event',
                    event_data={
                        'preselection_id': preselection_id,
                        'selected_count': len(result['final_candidates'])
                    }
                )
                
                # Actualizar métricas
                await self.notify_metrics_update(
                    metrics_name="Pre-selección",
                    metrics_type="preselection_completion",
                    business_unit=self.business_unit,
                    metrics_data={
                        'total_candidates': len(preselection.preselection_data['candidates']),
                        'selected_candidates': len(result['final_candidates']),
                        'review_time': (timezone.now() - preselection.created_at).total_seconds() / 3600
                    }
                )
                
                # Notificar a candidatos rechazados
                await self.notify_rejected_candidates(preselection_id)
                
                return {
                    'success': True,
                    'final_candidates': result['final_candidates'],
                    'learning_points': result['learning_points']
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error procesando revisión del MP: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _notify_mp_preselection(self, preselection: CandidatePreselection, mp: Person):
        """
        Notifica al MP sobre una nueva pre-selección pendiente.
        """
        try:
            # Notificar inicio del proceso
            await self.process_notifier.notify_process_start(
                recipient=mp,
                process_type='candidate_preselection',
                process_id=str(preselection.id)
            )
            
            # Notificar evento
            await self.event_notifier.notify_system_event(
                recipient=mp,
                event_name='preselection_created',
                event_type='preselection_event',
                event_data={
                    'preselection_id': preselection.id,
                    'vacancy_id': preselection.vacancy.id,
                    'num_candidates': len(preselection.get_candidates())
                }
            )
            
            # Enviar alerta
            await self.alert_notifier.notify_system_alert(
                recipient=mp,
                alert_type='preselection_pending',
                alert_message=f"Nueva pre-selección pendiente para {preselection.vacancy.titulo}",
                severity='medium'
            )
            
        except Exception as e:
            logger.error(f"Error notificando pre-selección al MP: {str(e)}")

    async def _notify_preselection_completed(self, preselection: CandidatePreselection, mp: Person):
        """
        Notifica la finalización de una pre-selección.
        """
        try:
            # Notificar finalización del proceso
            await self.process_notifier.notify_process_start(
                recipient=mp,
                process_type='preselection_completed',
                process_id=str(preselection.id)
            )
            
            # Notificar evento
            await self.event_notifier.notify_system_event(
                recipient=mp,
                event_name='preselection_completed',
                event_type='preselection_event',
                event_data={
                    'preselection_id': preselection.id,
                    'vacancy_id': preselection.vacancy.id,
                    'selected_candidates': len(preselection.get_selected_candidates())
                }
            )
            
        except Exception as e:
            logger.error(f"Error notificando finalización de pre-selección: {str(e)}")

    async def get_preselection_summary(self, preselection_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen de la pre-selección.
        """
        try:
            preselection = await CandidatePreselection.objects.aget(id=preselection_id)
            
            return {
                'id': preselection.id,
                'vacancy': preselection.vacancy.titulo,
                'status': preselection.get_status_display(),
                'created_at': preselection.created_at,
                'reviewed_at': preselection.reviewed_at,
                'total_candidates': len(preselection.get_candidates()),
                'selected_candidates': len(preselection.get_selected_candidates()),
                'rejected_candidates': len(preselection.get_rejected_candidates()),
                'learning_points': preselection.get_learning_points()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de pre-selección: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def reprocess_candidates(self, preselection_id: int, mp: Person) -> Dict[str, Any]:
        """
        Reprocesa y obtiene nuevos candidatos para una pre-selección.
        """
        try:
            # Obtener pre-selección actual
            preselection = await CandidatePreselection.objects.aget(id=preselection_id)
            
            # Obtener nuevos candidatos
            new_preselection_data = await self.matchmaking_system.get_preselection_candidates(
                vacancy=preselection.vacancy,
                num_candidates=8,
                exclude_candidates=[c['id'] for c in preselection.get_candidates()]
            )
            
            # Actualizar datos de pre-selección
            preselection.preselection_data = new_preselection_data
            preselection.status = 'pending_review'
            preselection.reviewed_at = None
            preselection.mp_feedback = None
            preselection.mp_notes = None
            await preselection.asave()
            
            # Notificar al Managing Partner / Pablo vía Telegram
            await self.telegram_notifier.send_preselection_notification(
                mp.chat_id,
                {
                    'id': preselection.id,
                    'vacancy': preselection.vacancy.titulo,
                    'total_candidates': len(new_preselection_data['candidates']),
                    'created_at': preselection.created_at.strftime('%Y-%m-%d %H:%M')
                }
            )
            
            return {
                'success': True,
                'preselection_id': preselection.id,
                'candidates': new_preselection_data['candidates']
            }
            
        except Exception as e:
            logger.error(f"Error reprocesando candidatos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def notify_rejected_candidates(self, preselection_id: int) -> Dict[str, Any]:
        """
        Notifica a los candidatos rechazados sobre el resultado.
        """
        try:
            preselection = await CandidatePreselection.objects.aget(id=preselection_id)
            rejected_candidates = preselection.get_rejected_candidates()
            
            for candidate in rejected_candidates:
                # Obtener feedback específico si existe
                feedback = preselection.mp_feedback.get('feedback_notes', {}).get(str(candidate.id), '')
                
                # Preparar mensaje personalizado
                message = (
                    f"Estimado/a {candidate.nombre},\n\n"
                    f"Gracias por tu interés en la posición de {preselection.vacancy.titulo}.\n"
                    f"Hemos completado el proceso de selección y, aunque tu perfil es muy interesante, "
                    f"en esta oportunidad hemos decidido avanzar con otros candidatos.\n\n"
                )
                
                if feedback:
                    message += f"Feedback del proceso: {feedback}\n\n"
                
                message += (
                    "Te animamos a seguir revisando nuestras oportunidades, "
                    "ya que tu perfil podría ser ideal para otras posiciones.\n\n"
                    "Recuerdo que tenemos ya tu información y seguro encontramos una alternativa para tí muy pronto.\n\n"
                    "¡Te deseamos mucho éxito en tu búsqueda y seguimos en contacto!\n\n"
                    "Saludos cordiales,\n"
                    "El equipo de Grupo huntRED®"
                )
                
                # Enviar notificación
                await self.user_notifier.notify_user_event(
                    user_id=candidate.id,
                    user_name=candidate.nombre,
                    event_name='application_rejected',
                    event_type='application_status',
                    additional_details={
                        'vacancy_title': preselection.vacancy.titulo,
                        'message': message
                    }
                )
            
            return {
                'success': True,
                'notified_candidates': len(rejected_candidates)
            }
            
        except Exception as e:
            logger.error(f"Error notificando candidatos rechazados: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def process_mp_process_feedback(self, preselection_id: int, mp: Person, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa el feedback del MP sobre el proceso de pre-selección en sí.
        """
        try:
            preselection = await CandidatePreselection.objects.aget(id=preselection_id)
            
            # Guardar feedback del proceso
            process_feedback = {
                'mp_id': mp.id,
                'timestamp': timezone.now(),
                'feedback': feedback
            }
            
            preselection.learning_insights = {
                **preselection.learning_insights or {},
                'process_feedback': process_feedback
            }
            await preselection.asave()
            
            # Notificar al sistema sobre el feedback
            await self.event_notifier.notify_system_event(
                recipient=mp,
                event_name='preselection_process_feedback',
                event_type='feedback_event',
                event_data={
                    'preselection_id': preselection_id,
                    'feedback': feedback
                }
            )
            
            return {
                'success': True,
                'message': 'Feedback del proceso guardado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error procesando feedback del proceso: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_preselection_statistics(self, preselection_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas sobre la pre-selección.
        """
        try:
            preselection = await CandidatePreselection.objects.aget(id=preselection_id)
            
            # Calcular tiempos
            review_time = None
            if preselection.reviewed_at:
                review_time = preselection.reviewed_at - preselection.created_at
            
            # Obtener candidatos
            candidates = preselection.get_candidates()
            selected = preselection.get_selected_candidates()
            rejected = preselection.get_rejected_candidates()
            
            # Analizar razones de rechazo
            rejection_reasons = {}
            if preselection.mp_feedback and 'feedback_notes' in preselection.mp_feedback:
                for candidate_id, feedback in preselection.mp_feedback['feedback_notes'].items():
                    # Aquí podríamos implementar un análisis más sofisticado del feedback
                    # Por ahora, simplemente contamos las ocurrencias de palabras clave
                    for word in feedback.lower().split():
                        if word in ['experiencia', 'habilidades', 'perfil', 'cultural']:
                            rejection_reasons[word] = rejection_reasons.get(word, 0) + 1
            
            return {
                'preselection_id': preselection_id,
                'vacancy': preselection.vacancy.titulo,
                'created_at': preselection.created_at,
                'reviewed_at': preselection.reviewed_at,
                'review_time': str(review_time) if review_time else None,
                'total_candidates': len(candidates),
                'selected_candidates': len(selected),
                'rejected_candidates': len(rejected),
                'acceptance_rate': len(selected) / len(candidates) if candidates else 0,
                'rejection_reasons': rejection_reasons,
                'process_feedback': preselection.learning_insights.get('process_feedback', {}) if preselection.learning_insights else {}
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def check_pending_preselections(self) -> Dict[str, Any]:
        """
        Verifica pre-selecciones pendientes y envía recordatorios si es necesario.
        """
        try:
            now = timezone.now()
            pending_preselections = await CandidatePreselection.objects.filter(
                status='pending_review',
                created_at__lt=now - timedelta(hours=24)
            ).all()
            
            results = []
            for preselection in pending_preselections:
                hours_pending = (now - preselection.created_at).total_seconds() / 3600
                
                # Determinar severidad basada en tiempo pendiente
                if hours_pending >= 72:
                    severity = 'high'
                    message = f"⚠️ Pre-selección pendiente por más de 72 horas"
                elif hours_pending >= 48:
                    severity = 'medium'
                    message = f"⚠️ Pre-selección pendiente por más de 48 horas"
                else:
                    severity = 'low'
                    message = f"⏰ Pre-selección pendiente por más de 24 horas"
                
                # Enviar alerta al MP vía Telegram
                await self.telegram_notifier.send_review_reminder(
                    preselection.vacancy.business_unit.managing_partner.chat_id,
                    {
                        'id': preselection.id,
                        'vacancy': preselection.vacancy.titulo,
                        'total_candidates': len(preselection.preselection_data['candidates']),
                        'hours_pending': hours_pending
                    }
                )
                
                # Enviar alerta
                await self.alert_notifier.notify_system_alert(
                    recipient=preselection.vacancy.business_unit.managing_partner,
                    alert_type='preselection_pending_reminder',
                    alert_message=message,
                    severity=severity,
                    additional_details={
                        'preselection_id': preselection.id,
                        'vacancy_title': preselection.vacancy.titulo,
                        'hours_pending': hours_pending
                    }
                )
                
                results.append({
                    'preselection_id': preselection.id,
                    'hours_pending': hours_pending,
                    'severity': severity
                })
            
            return {
                'success': True,
                'pending_count': len(results),
                'details': results
            }
            
        except Exception as e:
            logger.error(f"Error verificando pre-selecciones pendientes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_prioritized_preselections(self, mp: Person) -> Dict[str, Any]:
        """
        Obtiene una lista priorizada de pre-selecciones pendientes.
        """
        try:
            # Obtener todas las pre-selecciones pendientes
            pending_preselections = await CandidatePreselection.objects.filter(
                status='pending_review',
                business_unit=self.business_unit
            ).all()
            
            prioritized = []
            for preselection in pending_preselections:
                # Calcular score de prioridad
                priority_score = await self._calculate_priority_score(preselection)
                
                prioritized.append({
                    'preselection_id': preselection.id,
                    'vacancy': preselection.vacancy.titulo,
                    'priority_score': priority_score,
                    'details': {
                        'created_at': preselection.created_at,
                        'num_candidates': len(preselection.get_candidates()),
                        'vacancy_urgency': preselection.vacancy.urgency_level,
                        'hours_pending': (timezone.now() - preselection.created_at).total_seconds() / 3600
                    }
                })
            
            # Ordenar por score de prioridad
            prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return {
                'success': True,
                'prioritized_list': prioritized
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo pre-selecciones priorizadas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _calculate_priority_score(self, preselection: CandidatePreselection) -> float:
        """
        Calcula el score de prioridad para una pre-selección.
        """
        try:
            # Factores de prioridad
            urgency_weight = 0.4
            time_weight = 0.3
            candidates_weight = 0.3
            
            # Urgencia de la vacante (1-5)
            urgency_score = preselection.vacancy.urgency_level / 5
            
            # Tiempo pendiente (normalizado a 0-1)
            hours_pending = (timezone.now() - preselection.created_at).total_seconds() / 3600
            time_score = min(hours_pending / 72, 1)  # Máximo 72 horas
            
            # Número de candidatos (normalizado)
            num_candidates = len(preselection.get_candidates())
            candidates_score = min(num_candidates / 10, 1)  # Máximo 10 candidatos
            
            # Calcular score final
            priority_score = (
                urgency_score * urgency_weight +
                time_score * time_weight +
                candidates_score * candidates_weight
            )
            
            return priority_score
            
        except Exception as e:
            logger.error(f"Error calculando score de prioridad: {str(e)}")
            return 0.0

    async def analyze_selection_trends(self, mp: Person, time_period: int = 30) -> Dict[str, Any]:
        """
        Analiza tendencias en las selecciones del MP.
        """
        try:
            # Obtener pre-selecciones completadas en el período
            start_date = timezone.now() - timedelta(days=time_period)
            completed_preselections = await CandidatePreselection.objects.filter(
                status='mp_reviewed',
                reviewed_at__gte=start_date,
                business_unit=self.business_unit
            ).all()
            
            # Analizar patrones
            rejection_patterns = Counter()
            selection_patterns = Counter()
            feedback_patterns = Counter()
            
            for preselection in completed_preselections:
                if preselection.mp_feedback:
                    # Analizar razones de rechazo
                    for candidate_id, feedback in preselection.mp_feedback.get('feedback_notes', {}).items():
                        words = feedback.lower().split()
                        rejection_patterns.update(words)
                    
                    # Analizar patrones de selección
                    for candidate in preselection.get_selected_candidates():
                        selection_patterns.update(candidate.skills)
                    
                    # Analizar feedback del proceso
                    if preselection.learning_insights and 'process_feedback' in preselection.learning_insights:
                        feedback = preselection.learning_insights['process_feedback']['feedback']
                        if 'suggestions' in feedback:
                            feedback_patterns.update(feedback['suggestions'].lower().split())
            
            return {
                'success': True,
                'analysis_period': f"Últimos {time_period} días",
                'total_preselections': len(completed_preselections),
                'rejection_patterns': dict(rejection_patterns.most_common(10)),
                'selection_patterns': dict(selection_patterns.most_common(10)),
                'feedback_patterns': dict(feedback_patterns.most_common(10))
            }
            
        except Exception as e:
            logger.error(f"Error analizando tendencias: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def notify_client_about_preselection(self, preselection_id: int) -> Dict[str, Any]:
        """
        Notifica al cliente sobre la pre-selección completada.
        """
        try:
            preselection = await CandidatePreselection.objects.aget(id=preselection_id)
            client = preselection.vacancy.client
            
            # Preparar resumen para el cliente
            summary = await self.get_preselection_summary(preselection_id)
            
            # Preparar mensaje
            message = (
                f"Estimado/a {client.name},\n\n"
                f"Hemos completado la pre-selección para la posición de {preselection.vacancy.titulo}.\n\n"
                f"Resumen de la pre-selección:\n"
                f"- Total de candidatos revisados: {summary['total_candidates']}\n"
                f"- Candidatos seleccionados: {summary['selected_candidates']}\n"
                f"- Tiempo de revisión: {summary['review_time']}\n\n"
            )
            
            if summary.get('rejection_reasons'):
                message += "Principales razones de selección:\n"
                for reason, count in summary['rejection_reasons'].items():
                    message += f"- {reason}: {count} menciones\n"
            
            message += (
                "\nLos candidatos seleccionados serán contactados para coordinar las siguientes etapas "
                "del proceso de selección.\n\n"
                "Saludos cordiales,\n"
                "El equipo de huntRED"
            )
            
            # Enviar notificación al cliente
            await self.user_notifier.notify_user_event(
                user_id=client.id,
                user_name=client.name,
                event_name='preselection_completed',
                event_type='client_notification',
                additional_details={
                    'vacancy_title': preselection.vacancy.titulo,
                    'message': message,
                    'summary': summary
                }
            )
            
            return {
                'success': True,
                'client_notified': True,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error notificando al cliente: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def notify_metrics_update(self, metrics_name: str, metrics_type: str, business_unit: BusinessUnit, metrics_data: Dict[str, Any]):
        """
        Notifica la actualización de métricas.
        """
        try:
            # Actualizar métricas
            await self.process_notifier.notify_process_start(
                recipient=business_unit.managing_partner,
                process_type='metrics_update',
                process_id=f"{metrics_name}_{metrics_type}"
            )
            
            # Notificar evento del sistema
            await self.event_notifier.notify_system_event(
                recipient=business_unit.managing_partner,
                event_name='metrics_update',
                event_type='metrics_event',
                event_data={
                    'metrics_name': metrics_name,
                    'metrics_type': metrics_type,
                    'business_unit_id': business_unit.id,
                    'metrics_data': metrics_data
                }
            )
            
            return {
                'success': True,
                'message': 'Métricas actualizadas exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error notificando actualización de métricas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 