"""
Módulo de notificaciones específicas para el proceso de ofertas.
Maneja todas las notificaciones relacionadas con ofertas laborales y contrataciones.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.models import Person, Vacante, BusinessUnit
from app.ats.integrations.notifications.core.base_service import BaseNotificationService
from app.ats.integrations.notifications.core.config import (
    NotificationType,
    NotificationSeverity
)

logger = logging.getLogger(__name__)

class OfferNotificationService(BaseNotificationService):
    """
    Servicio de notificaciones para el proceso de ofertas.
    Extiende el servicio base con funcionalidad específica para ofertas.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        """
        Inicializa el servicio de notificaciones de ofertas.
        
        Args:
            business_unit: Unidad de negocio requerida para las notificaciones
        """
        if not business_unit:
            raise ValueError("Se requiere especificar una unidad de negocio")
            
        super().__init__(business_unit)
        
    async def notify_offer_made(
        self,
        person: Person,
        vacancy: Vacante,
        offer_details: Dict[str, Any],
        deadline: datetime
    ) -> bool:
        """
        Notifica sobre una oferta laboral realizada.
        
        Args:
            person: Candidato que recibe la oferta
            vacancy: Vacante relacionada
            offer_details: Detalles de la oferta
            deadline: Fecha límite para aceptar la oferta
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            # Preparar contexto
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'salary': offer_details.get('salary', ''),
                'benefits': offer_details.get('benefits', []),
                'start_date': offer_details.get('start_date', ''),
                'deadline': deadline.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name
            }
            
            # Notificar al candidato
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_offer_made_template('candidate'),
                context=context,
                channels=['email', 'whatsapp']
            )
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_offer_made_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando oferta realizada: {str(e)}", exc_info=True)
            return False
            
    async def notify_offer_accepted(
        self,
        person: Person,
        vacancy: Vacante,
        acceptance_date: datetime
    ) -> bool:
        """
        Notifica sobre la aceptación de una oferta.
        
        Args:
            person: Candidato que aceptó la oferta
            vacancy: Vacante relacionada
            acceptance_date: Fecha de aceptación
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'acceptance_date': acceptance_date.strftime('%d/%m/%Y %H:%M'),
                'business_unit': self.business_unit.name
            }
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_offer_accepted_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            # Notificar al cliente
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_offer_accepted_template('client'),
                context=context,
                channels=['email']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando aceptación de oferta: {str(e)}", exc_info=True)
            return False
            
    async def notify_offer_declined(
        self,
        person: Person,
        vacancy: Vacante,
        reason: str
    ) -> bool:
        """
        Notifica sobre el rechazo de una oferta.
        
        Args:
            person: Candidato que rechazó la oferta
            vacancy: Vacante relacionada
            reason: Razón del rechazo
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': person.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'reason': reason,
                'business_unit': self.business_unit.name
            }
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_offer_declined_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            # Notificar al cliente
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_offer_declined_template('client'),
                context=context,
                channels=['email']
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando rechazo de oferta: {str(e)}", exc_info=True)
            return False
            
    async def notify_ideal_candidate_selected(
        self,
        selected_candidate: Person,
        vacancy: Vacante,
        other_candidates: List[Person],
        selection_reason: str = None
    ) -> bool:
        """
        Notifica cuando se identifica el candidato ideal y agradece a los demás.
        
        Args:
            selected_candidate: Candidato seleccionado
            vacancy: Vacante relacionada
            other_candidates: Lista de candidatos descartados
            selection_reason: Razón de la selección
            
        Returns:
            bool: True si las notificaciones se enviaron correctamente
        """
        try:
            success_count = 0
            
            # 1. Notificar al candidato seleccionado
            selected_context = {
                'candidate_name': selected_candidate.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'business_unit': self.business_unit.name,
                'selection_reason': selection_reason or "Tu perfil se alinea perfectamente con los requerimientos del puesto.",
                'next_steps': "Nos pondremos en contacto contigo en las próximas 24 horas para coordinar los siguientes pasos."
            }
            
            selected_success = await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_candidate_selected_template('selected'),
                context=selected_context,
                channels=['email', 'whatsapp']
            )
            
            if selected_success:
                success_count += 1
            
            # 2. Notificar y agradecer a los candidatos descartados
            for candidate in other_candidates:
                rejected_context = {
                    'candidate_name': candidate.full_name,
                    'position': vacancy.title,
                    'company': vacancy.company_name,
                    'business_unit': self.business_unit.name,
                    'feedback': "Aunque tu perfil es muy interesante, hemos decidido avanzar con otro candidato.",
                    'future_opportunities': "Te mantendremos en nuestra base de datos para futuras oportunidades."
                }
                
                rejected_success = await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_candidate_selected_template('rejected'),
                    context=rejected_context,
                    channels=['email', 'whatsapp']
                )
                
                if rejected_success:
                    success_count += 1
            
            # 3. Notificar al consultor sobre la selección
            if vacancy.assigned_consultant:
                consultant_context = {
                    'selected_candidate_name': selected_candidate.full_name,
                    'position': vacancy.title,
                    'company': vacancy.company_name,
                    'total_candidates': len(other_candidates) + 1,
                    'selection_reason': selection_reason,
                    'business_unit': self.business_unit.name
                }
                
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_candidate_selected_template('consultant'),
                    context=consultant_context,
                    channels=['email', 'telegram']
                )
            
            # 4. Notificar al cliente
            client_context = {
                'selected_candidate_name': selected_candidate.full_name,
                'position': vacancy.title,
                'selection_reason': selection_reason,
                'next_steps': "Procederemos con la preparación de la oferta formal."
            }
            
            await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_candidate_selected_template('client'),
                context=client_context,
                channels=['email']
            )
            
            logger.info(f"Notificaciones de candidato ideal enviadas: {success_count} exitosas")
            return True
            
        except Exception as e:
            logger.error(f"Error notificando candidato ideal: {str(e)}", exc_info=True)
            return False

    async def notify_candidate_rejected_from_admin(
        self,
        candidate: Person,
        vacancy: Vacante,
        rejection_reason: str,
        admin_user: str = None
    ) -> bool:
        """
        Notifica a un candidato que ha sido rechazado desde el admin.
        
        Args:
            candidate: Candidato rechazado
            vacancy: Vacante relacionada
            rejection_reason: Razón del rechazo
            admin_user: Usuario del admin que realizó el rechazo
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'candidate_name': candidate.full_name,
                'position': vacancy.title,
                'company': vacancy.company_name,
                'business_unit': self.business_unit.name,
                'rejection_reason': rejection_reason,
                'admin_user': admin_user or "el equipo de selección",
                'future_opportunities': "Te mantendremos en nuestra base de datos para futuras oportunidades que se ajusten mejor a tu perfil."
            }
            
            # Notificar al candidato
            candidate_success = await self.send_notification(
                notification_type=NotificationType.PROCESS_EVENT.value,
                message=self._get_admin_rejection_template('candidate'),
                context=context,
                channels=['email', 'whatsapp']
            )
            
            # Notificar al consultor si existe
            if vacancy.assigned_consultant:
                consultant_context = {
                    'candidate_name': candidate.full_name,
                    'position': vacancy.title,
                    'company': vacancy.company_name,
                    'rejection_reason': rejection_reason,
                    'admin_user': admin_user,
                    'business_unit': self.business_unit.name
                }
                
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_admin_rejection_template('consultant'),
                    context=consultant_context,
                    channels=['email', 'telegram']
                )
            
            return candidate_success
            
        except Exception as e:
            logger.error(f"Error notificando rechazo desde admin: {str(e)}", exc_info=True)
            return False

    async def notify_bulk_candidates_rejected(
        self,
        candidates: List[Person],
        vacancy: Vacante,
        rejection_reason: str,
        admin_user: str = None
    ) -> Dict[str, int]:
        """
        Notifica a múltiples candidatos rechazados desde el admin.
        
        Args:
            candidates: Lista de candidatos rechazados
            vacancy: Vacante relacionada
            rejection_reason: Razón del rechazo
            admin_user: Usuario del admin que realizó el rechazo
            
        Returns:
            Dict con conteo de notificaciones exitosas y fallidas
        """
        try:
            success_count = 0
            failed_count = 0
            
            for candidate in candidates:
                success = await self.notify_candidate_rejected_from_admin(
                    candidate=candidate,
                    vacancy=vacancy,
                    rejection_reason=rejection_reason,
                    admin_user=admin_user
                )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"Notificaciones masivas de rechazo: {success_count} exitosas, {failed_count} fallidas")
            
            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'total_candidates': len(candidates)
            }
            
        except Exception as e:
            logger.error(f"Error en notificaciones masivas de rechazo: {str(e)}", exc_info=True)
            return {
                'success_count': 0,
                'failed_count': len(candidates),
                'total_candidates': len(candidates),
                'error': str(e)
            }

    async def notify_candidate_comparison_completed(
        self,
        vacancy: Vacante,
        comparison_results: Dict[str, Any],
        selected_candidate: Person = None
    ) -> bool:
        """
        Notifica cuando se completa una comparación de candidatos.
        
        Args:
            vacancy: Vacante relacionada
            comparison_results: Resultados de la comparación
            selected_candidate: Candidato seleccionado (opcional)
            
        Returns:
            bool: True si la notificación se envió correctamente
        """
        try:
            context = {
                'position': vacancy.title,
                'company': vacancy.company_name,
                'total_candidates': comparison_results.get('total_candidates', 0),
                'top_candidate': comparison_results.get('top_candidate', {}),
                'score_distribution': comparison_results.get('score_distribution', {}),
                'recommendations': comparison_results.get('recommendations', []),
                'business_unit': self.business_unit.name
            }
            
            if selected_candidate:
                context['selected_candidate_name'] = selected_candidate.full_name
                context['selection_made'] = True
            else:
                context['selection_made'] = False
            
            # Notificar al consultor
            if vacancy.assigned_consultant:
                await self.send_notification(
                    notification_type=NotificationType.PROCESS_EVENT.value,
                    message=self._get_comparison_completed_template('consultant'),
                    context=context,
                    channels=['email', 'telegram']
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error notificando comparación completada: {str(e)}", exc_info=True)
            return False

    def _get_offer_made_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'candidate': (
                "🎉 *¡Oferta Laboral!*\n\n"
                "👋 *{candidate_name}*\n\n"
                "¡Felicitaciones! Has recibido una oferta para la posición de {position} en {company}.\n\n"
                "💰 *Salario:* {salary}\n"
                "🎁 *Beneficios:*\n{benefits}\n"
                "📅 *Fecha de inicio:* {start_date}\n"
                "⏰ *Fecha límite para aceptar:* {deadline}\n\n"
                "Por favor, revisa los detalles y comunica tu decisión antes de la fecha límite."
            ),
            'consultant': (
                "🎉 *Nueva Oferta Realizada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "💰 *Salario:* {salary}\n"
                "🎁 *Beneficios:*\n{benefits}\n"
                "📅 *Fecha de inicio:* {start_date}\n"
                "⏰ *Fecha límite:* {deadline}"
            )
        }
        return templates.get(recipient_type, templates['candidate'])
        
    def _get_offer_accepted_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'consultant': (
                "✅ *Oferta Aceptada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📅 *Fecha de aceptación:* {acceptance_date}"
            ),
            'client': (
                "✅ *Oferta Aceptada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "📅 *Fecha de aceptación:* {acceptance_date}\n\n"
                "¡Felicitaciones! El candidato ha aceptado la oferta."
            )
        }
        return templates.get(recipient_type, templates['consultant'])
        
    def _get_offer_declined_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'consultant': (
                "❌ *Oferta Rechazada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📝 *Razón:* {reason}"
            ),
            'client': (
                "❌ *Oferta Rechazada*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "📝 *Razón:* {reason}\n\n"
                "El candidato ha declinado la oferta. Por favor, revisa los detalles para futuras referencias."
            )
        }
        return templates.get(recipient_type, templates['consultant'])

    def _get_candidate_selected_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla según el tipo de destinatario."""
        templates = {
            'selected': (
                "🎉 *¡Felicidades! Has sido seleccionado*\n\n"
                "👋 *{candidate_name}*\n\n"
                "¡Excelentes noticias! Has sido seleccionado como el candidato ideal "
                "para la posición de {position} en {company}.\n\n"
                "📝 *Razón de selección:* {selection_reason}\n\n"
                "🔄 *Próximos pasos:* {next_steps}\n\n"
                "¡Te deseamos mucho éxito en esta nueva etapa!"
            ),
            'rejected': (
                "🙏 *Gracias por tu interés*\n\n"
                "👋 *{candidate_name}*\n\n"
                "Gracias por tu interés en la posición de {position} en {company}.\n\n"
                "📝 *Feedback:* {feedback}\n\n"
                "🔮 *Futuras oportunidades:* {future_opportunities}\n\n"
                "¡Te deseamos mucho éxito en tu búsqueda profesional!"
            ),
            'consultant': (
                "🎯 *Candidato Ideal Identificado*\n\n"
                "👤 *Candidato seleccionado:* {selected_candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📊 *Total de candidatos evaluados:* {total_candidates}\n"
                "📝 *Razón de selección:* {selection_reason}\n\n"
                "Proceder con la preparación de la oferta formal."
            ),
            'client': (
                "🎯 *Candidato Seleccionado*\n\n"
                "👤 *Candidato:* {selected_candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "📝 *Razón:* {selection_reason}\n\n"
                "🔄 *Próximos pasos:* {next_steps}"
            )
        }
        return templates.get(recipient_type, templates['selected'])

    def _get_comparison_completed_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla para comparación completada."""
        templates = {
            'consultant': (
                "📊 *Comparación de Candidatos Completada*\n\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "👥 *Total de candidatos:* {total_candidates}\n\n"
                "🏆 *Mejor candidato:* {top_candidate[name]}\n"
                "📈 *Score:* {top_candidate[score]:.1%}\n\n"
                "📊 *Distribución de scores:*\n"
                "• Mínimo: {score_distribution[min]:.1%}\n"
                "• Máximo: {score_distribution[max]:.1%}\n"
                "• Promedio: {score_distribution[avg]:.1%}\n\n"
                "🎯 *Recomendaciones:*\n"
                "{recommendations}\n\n"
                "{'✅ Selección realizada' if selection_made else '⏳ Pendiente de selección'}"
            )
        }
        return templates.get(recipient_type, templates['consultant'])

    def _get_admin_rejection_template(self, recipient_type: str) -> str:
        """Obtiene la plantilla para rechazos desde admin."""
        templates = {
            'candidate': (
                "🙏 *Actualización de tu Aplicación*\n\n"
                "👋 *{candidate_name}*\n\n"
                "Gracias por tu interés en la posición de {position} en {company}.\n\n"
                "📝 *Decisión:* Después de una cuidadosa evaluación, hemos decidido no continuar con tu aplicación en esta oportunidad.\n\n"
                "💡 *Feedback:* {rejection_reason}\n\n"
                "🔮 *Futuras oportunidades:* {future_opportunities}\n\n"
                "¡Te deseamos mucho éxito en tu búsqueda profesional!\n\n"
                "Saludos cordiales,\n"
                "El equipo de {business_unit}"
            ),
            'consultant': (
                "❌ *Candidato Rechazado desde Admin*\n\n"
                "👤 *Candidato:* {candidate_name}\n"
                "💼 *Posición:* {position}\n"
                "🏢 *Empresa:* {company}\n"
                "📝 *Razón:* {rejection_reason}\n"
                "👤 *Rechazado por:* {admin_user}\n\n"
                "El candidato ha sido notificado automáticamente."
            )
        }
        return templates.get(recipient_type, templates['candidate'])
