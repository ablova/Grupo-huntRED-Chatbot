"""
Módulo principal para el manejo de referencias.
"""

from typing import Dict, List, Optional, Union
from django.utils import timezone
from app.models import Person, Reference, BusinessUnit
from .notifications import ReferenceNotificationManager
from .utils import ReferenceUtils
from app.ats.chatbot.workflow.business_units.reference_config import get_reference_config

class ReferenceManager:
    """Clase principal para gestionar referencias."""
    
    def __init__(self, business_unit: BusinessUnit):
        self.business_unit = business_unit
        self.notification_manager = ReferenceNotificationManager(business_unit)
        self.utils = ReferenceUtils()
        self.config = get_reference_config(business_unit.code)
    
    def capture_references(self, candidate: Person, references_data: List[Dict]) -> List[Reference]:
        """
        Captura las referencias proporcionadas por el candidato.
        
        Args:
            candidate: Person - Candidato que proporciona las referencias
            references_data: List[Dict] - Lista de datos de referencias
            
        Returns:
            List[Reference] - Lista de referencias creadas
        """
        # Validar número de referencias
        if len(references_data) < self.config['min_references']:
            raise ValueError(f"Se requieren al menos {self.config['min_references']} referencias")
        if len(references_data) > self.config['max_references']:
            raise ValueError(f"No se pueden agregar más de {self.config['max_references']} referencias")
        
        created_references = []
        
        for ref_data in references_data:
            # Validar datos de referencia
            errors = self.utils.validate_reference_data(ref_data)
            if errors:
                raise ValueError(f"Error en datos de referencia: {', '.join(errors)}")
            
            reference = Reference.objects.create(
                candidate=candidate,
                name=ref_data['name'],
                relationship=ref_data['relationship'],
                company=ref_data['company'],
                title=ref_data['title'],
                email=ref_data['email'],
                phone=ref_data.get('phone'),
                status='pending',
                metadata={
                    'questions': self.config['questions'],
                    'response_days': self.config['response_days']
                }
            )
            created_references.append(reference)
            
            # Enviar solicitud de referencia
            self.notification_manager.send_reference_request(reference)
        
        return created_references
    
    def process_reference_response(self, reference: Reference, feedback: Dict) -> bool:
        """
        Procesa la respuesta de una referencia.
        
        Args:
            reference: Reference - Referencia que responde
            feedback: Dict - Feedback proporcionado
            
        Returns:
            bool - True si se procesó correctamente
        """
        try:
            # Validar que el feedback incluya todas las preguntas requeridas
            required_questions = {q['id'] for q in self.config['questions']}
            provided_questions = set(feedback.keys())
            
            if not required_questions.issubset(provided_questions):
                missing = required_questions - provided_questions
                raise ValueError(f"Faltan respuestas para: {', '.join(missing)}")
            
            reference.feedback = feedback
            reference.status = 'responded'
            reference.response_date = timezone.now()
            reference.score = self.utils.calculate_reference_score(feedback)
            reference.save()
            
            # Actualizar CV del candidato con el feedback
            self.utils.update_candidate_cv_with_feedback(reference)
            
            # Intentar conversión si hay consentimiento
            if reference.consent:
                self.convert_reference_to_candidate(reference)
            
            return True
            
        except Exception as e:
            print(f"Error procesando respuesta de referencia: {e}")
            return False
    
    def convert_reference_to_candidate(self, reference: Reference) -> Optional[Person]:
        """
        Convierte una referencia en candidato.
        
        Args:
            reference: Reference - Referencia a convertir
            
        Returns:
            Optional[Person] - Candidato creado o None si falla
        """
        try:
            if reference.convert_to_candidate():
                # Enviar notificación de bienvenida
                self.notification_manager.send_welcome_to_candidate(reference.converted_to)
                return reference.converted_to
            return None
            
        except Exception as e:
            print(f"Error convirtiendo referencia a candidato: {e}")
            return None
    
    def get_references_for_candidate(self, candidate: Person) -> List[Reference]:
        """
        Obtiene todas las referencias de un candidato.
        
        Args:
            candidate: Person - Candidato
            
        Returns:
            List[Reference] - Lista de referencias
        """
        return Reference.objects.filter(candidate=candidate).order_by('-created_at')
    
    def get_pending_references(self) -> List[Reference]:
        """
        Obtiene todas las referencias pendientes.
        
        Returns:
            List[Reference] - Lista de referencias pendientes
        """
        return Reference.objects.filter(
            status='pending',
            created_at__gte=timezone.now() - timezone.timedelta(days=self.config['response_days'])
        ).order_by('created_at')
    
    def send_reminders(self) -> int:
        """
        Envía recordatorios a referencias pendientes.
        
        Returns:
            int - Número de recordatorios enviados
        """
        pending_refs = self.get_pending_references()
        sent_count = 0
        
        for ref in pending_refs:
            days_passed = (timezone.now() - ref.created_at).days
            
            # Verificar si es momento de enviar recordatorio
            if days_passed in self.config['reminder_days']:
                if self.notification_manager.send_reminder(ref):
                    sent_count += 1
                    ref.last_contacted = timezone.now()
                    ref.save()
        
        return sent_count 