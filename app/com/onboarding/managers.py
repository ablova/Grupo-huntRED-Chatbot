from typing import Dict, Any, Optional, List
from django.utils import timezone
from datetime import timedelta
import logging

from app.models import Person, BusinessUnit, Vacante, OnboardingProcess
from app.com.notifications.managers import NotificationManager

logger = logging.getLogger(__name__)

class OnboardingManager:
    """
    Gestor de procesos de onboarding y seguimiento post-contratación.
    """
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.notification_manager = NotificationManager(business_unit)
    
    async def start_onboarding(self, person: Person) -> Dict[str, Any]:
        """
        Inicia el proceso de onboarding para una persona.
        """
        try:
            # Crear proceso de onboarding
            onboarding = await OnboardingProcess.objects.acreate(
                person=person,
                business_unit=self.business_unit,
                start_date=timezone.now(),
                status='in_progress'
            )
            
            # Programar check-ins
            await self._schedule_check_ins(onboarding)
            
            # Enviar notificación inicial
            await self.notification_manager.send_notification(
                notification_type='ONBOARDING_STARTED',
                recipient=person,
                context={
                    'onboarding_id': onboarding.id,
                    'next_steps': await self._get_next_steps(onboarding)
                }
            )
            
            return {
                'success': True,
                'onboarding_id': onboarding.id
            }
            
        except Exception as e:
            logger.error(f"Error starting onboarding: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def check_status(self, person: Person) -> Dict[str, Any]:
        """
        Verifica el estado del proceso de onboarding.
        """
        try:
            onboarding = await self.get_onboarding_for_person(person)
            
            if not onboarding:
                return {
                    'success': False,
                    'error': 'No se encontró un proceso de onboarding'
                }
            
            return {
                'success': True,
                'status': onboarding.status,
                'completed_steps': await self._get_completed_steps(onboarding),
                'pending_steps': await self._get_pending_steps(onboarding),
                'next_check_in': await self._get_next_check_in(onboarding)
            }
            
        except Exception as e:
            logger.error(f"Error checking onboarding status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def complete_step(self, person: Person, step: str) -> Dict[str, Any]:
        """
        Marca un paso del onboarding como completado.
        """
        try:
            onboarding = await self.get_onboarding_for_person(person)
            
            if not onboarding:
                return {
                    'success': False,
                    'error': 'No se encontró un proceso de onboarding'
                }
            
            # Marcar paso como completado
            await onboarding.complete_step(step)
            
            # Verificar si se completó todo el proceso
            if await self._is_onboarding_complete(onboarding):
                await self._complete_onboarding(onboarding)
            
            return {
                'success': True,
                'step_completed': step,
                'is_complete': onboarding.status == 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error completing onboarding step: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_feedback_survey(self, person: Person, survey_type: str, **kwargs) -> Dict[str, Any]:
        """
        Envía una encuesta de feedback post-contratación.
        """
        try:
            if survey_type == 'candidato':
                onboarding = kwargs.get('onboarding')
                if not onboarding:
                    return {
                        'success': False,
                        'error': 'Se requiere el proceso de onboarding'
                    }
                
                # Enviar encuesta al candidato
                await self.notification_manager.send_notification(
                    notification_type='CANDIDATO_FEEDBACK_SURVEY',
                    recipient=person,
                    context={
                        'onboarding_id': onboarding.id,
                        'survey_url': f"/onboarding/feedback/candidato/{onboarding.id}/"
                    }
                )
                
            elif survey_type == 'cliente':
                empresa = kwargs.get('empresa')
                if not empresa:
                    return {
                        'success': False,
                        'error': 'Se requiere la empresa'
                    }
                
                # Enviar encuesta al cliente
                await self.notification_manager.send_notification(
                    notification_type='CLIENTE_FEEDBACK_SURVEY',
                    recipient=person,
                    context={
                        'empresa_id': empresa.id,
                        'survey_url': f"/onboarding/feedback/cliente/{empresa.id}/"
                    }
                )
            
            return {
                'success': True,
                'survey_type': survey_type,
                'sent_to': person.nombre
            }
            
        except Exception as e:
            logger.error(f"Error sending feedback survey: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def perform_check_in(self, person: Person, onboarding: OnboardingProcess) -> Dict[str, Any]:
        """
        Realiza un check-in del proceso de onboarding.
        """
        try:
            # Registrar check-in
            await onboarding.register_check_in()
            
            # Enviar notificación de check-in
            await self.notification_manager.send_notification(
                notification_type='ONBOARDING_CHECK_IN',
                recipient=person,
                context={
                    'onboarding_id': onboarding.id,
                    'check_in_number': await onboarding.get_check_in_count(),
                    'next_check_in': await self._get_next_check_in(onboarding)
                }
            )
            
            return {
                'success': True,
                'check_in_registered': True
            }
            
        except Exception as e:
            logger.error(f"Error performing check-in: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_onboarding_for_person(self, person: Person) -> Optional[OnboardingProcess]:
        """
        Obtiene el proceso de onboarding activo para una persona.
        """
        try:
            return await OnboardingProcess.objects.filter(
                person=person,
                business_unit=self.business_unit,
                status__in=['in_progress', 'pending']
            ).afirst()
        except Exception as e:
            logger.error(f"Error getting onboarding for person: {str(e)}")
            return None
    
    async def _schedule_check_ins(self, onboarding: OnboardingProcess):
        """
        Programa los check-ins del proceso de onboarding.
        """
        check_in_dates = [
            timezone.now() + timedelta(days=7),   # 1 semana
            timezone.now() + timedelta(days=30),  # 1 mes
            timezone.now() + timedelta(days=90)   # 3 meses
        ]
        
        for check_in_date in check_in_dates:
            try:
                await self.notification_manager.schedule_notification(
                    notification_type='ONBOARDING_CHECK_IN_REMINDER',
                    recipient=onboarding.person,
                    scheduled_time=check_in_date,
                    context={
                        'onboarding_id': onboarding.id,
                        'check_in_date': check_in_date
                    }
                )
            except Exception as e:
                logger.error(f"Error scheduling check-in: {str(e)}")
    
    async def _get_next_steps(self, onboarding: OnboardingProcess) -> List[str]:
        """
        Obtiene los siguientes pasos del proceso de onboarding.
        """
        # Implementar lógica para obtener los siguientes pasos
        return []
    
    async def _get_completed_steps(self, onboarding: OnboardingProcess) -> List[str]:
        """
        Obtiene los pasos completados del proceso de onboarding.
        """
        # Implementar lógica para obtener los pasos completados
        return []
    
    async def _get_pending_steps(self, onboarding: OnboardingProcess) -> List[str]:
        """
        Obtiene los pasos pendientes del proceso de onboarding.
        """
        # Implementar lógica para obtener los pasos pendientes
        return []
    
    async def _get_next_check_in(self, onboarding: OnboardingProcess) -> Optional[timezone.datetime]:
        """
        Obtiene la fecha del próximo check-in.
        """
        # Implementar lógica para obtener el próximo check-in
        return None
    
    async def _is_onboarding_complete(self, onboarding: OnboardingProcess) -> bool:
        """
        Verifica si el proceso de onboarding está completo.
        """
        # Implementar lógica para verificar si está completo
        return False
    
    async def _complete_onboarding(self, onboarding: OnboardingProcess):
        """
        Marca el proceso de onboarding como completado.
        """
        try:
            onboarding.status = 'completed'
            onboarding.completion_date = timezone.now()
            await onboarding.asave()
            
            # Enviar notificación de completado
            await self.notification_manager.send_notification(
                notification_type='ONBOARDING_COMPLETED',
                recipient=onboarding.person,
                context={
                    'onboarding_id': onboarding.id,
                    'completion_date': onboarding.completion_date
                }
            )
            
        except Exception as e:
            logger.error(f"Error completing onboarding: {str(e)}") 