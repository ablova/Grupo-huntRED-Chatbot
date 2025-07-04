from django.utils import timezone
from django.db import transaction
from app.ats.core.offlimits.models import OffLimitsRestriction, CandidateInitiatedContact, OffLimitsAudit, get_offlimits_period


class OffLimitsService:
    """
    Servicio principal para manejar la lógica de negocio relacionada con 
    restricciones OffLimits/Cooling Period.
    """
    
    @staticmethod
    def check_offlimits(candidate, client, business_unit, service_type):
        """
        Verifica si un candidato está en período OffLimits para un cliente específico.
        
        Args:
            candidate: Objeto Candidate
            client: Objeto Client
            business_unit: Objeto BusinessUnit
            service_type: String (humano, hibrido, ai)
            
        Returns:
            bool: True si el candidato está en OffLimits, False si no lo está
        """
        # Verificar que el candidato trabaja actualmente en la empresa cliente
        if not hasattr(candidate, 'current_company') or not candidate.current_company:
            return False
            
        if candidate.current_company != client.company:
            return False
        
        # Buscar restricciones activas
        restrictions = OffLimitsRestriction.objects.filter(
            client=client,
            business_unit=business_unit,
            service_type=service_type,
            is_active=True,
            end_date__gte=timezone.now().date()
        )
        
        if not restrictions.exists():
            return False
            
        # Verificar si hay una excepción registrada (el candidato inició contacto)
        exceptions = CandidateInitiatedContact.objects.filter(
            candidate=candidate,
            client=client,
            verification_date__isnull=False  # Solo excepciones verificadas
        )
        
        # Registrar auditoría de la verificación
        OffLimitsAudit.objects.create(
            candidate=candidate,
            client=client,
            business_unit=business_unit,
            action_type='check',
            details=f"Verificación de OffLimits para {service_type}"
        )
        
        # Si hay excepciones verificadas, el candidato no está en OffLimits
        return not exceptions.exists()
    
    @staticmethod
    def filter_offlimits_candidates(candidates, client, business_unit, service_type):
        """
        Filtra una lista de candidatos, excluyendo aquellos en OffLimits.
        
        Args:
            candidates: QuerySet de Candidate
            client: Objeto Client
            business_unit: Objeto BusinessUnit
            service_type: String (humano, hibrido, ai)
            
        Returns:
            QuerySet: Candidatos filtrados
        """
        offlimits_candidates = []
        for candidate in candidates:
            if OffLimitsService.check_offlimits(candidate, client, business_unit, service_type):
                offlimits_candidates.append(candidate.id)
        
        return candidates.exclude(id__in=offlimits_candidates)
    
    @staticmethod
    @transaction.atomic
    def create_restriction(client, process, business_unit, service_type, created_by):
        """
        Crea una nueva restricción OffLimits al finalizar un proceso de reclutamiento.
        
        Args:
            client: Objeto Client
            process: Objeto RecruitmentProcess
            business_unit: Objeto BusinessUnit
            service_type: String (humano, hibrido, ai)
            created_by: Objeto User
            
        Returns:
            OffLimitsRestriction: Objeto creado
        """
        # Verificar si el proceso califica para OffLimits
        if not process.is_full_recruitment or not process.is_paid or process.is_assessment_only:
            return None
            
        # Calcular el período de OffLimits
        months = get_offlimits_period(business_unit.code, service_type)
        if months <= 0:
            return None
            
        # Calcular la fecha de finalización
        end_date = timezone.now().date() + timezone.timedelta(days=30*months)
        
        # Crear la restricción
        restriction = OffLimitsRestriction.objects.create(
            client=client,
            business_unit=business_unit,
            service_type=service_type,
            process=process,
            end_date=end_date,
            is_active=True,
            created_by=created_by
        )
        
        # Registrar auditoría
        OffLimitsAudit.objects.create(
            user=created_by,
            candidate=process.candidate,
            client=client,
            business_unit=business_unit,
            action_type='create_restriction',
            restriction=restriction,
            details=f"Restricción creada para {client} - {business_unit.name} - {service_type}"
        )
        
        return restriction
    
    @staticmethod
    @transaction.atomic
    def register_candidate_initiated_contact(candidate, client, evidence_type, evidence_reference, notes, registered_by):
        """
        Registra cuando un candidato inicia contacto (excepción a OffLimits).
        
        Args:
            candidate: Objeto Candidate
            client: Objeto Client
            evidence_type: String (tipo de evidencia)
            evidence_reference: String (referencia o URL a la evidencia)
            notes: String (notas adicionales)
            registered_by: Objeto User
            
        Returns:
            CandidateInitiatedContact: Objeto creado
        """
        contact = CandidateInitiatedContact.objects.create(
            candidate=candidate,
            client=client,
            evidence_type=evidence_type,
            evidence_reference=evidence_reference,
            notes=notes,
            verified_by=registered_by,
            verification_date=timezone.now()
        )
        
        # Registrar auditoría
        OffLimitsAudit.objects.create(
            user=registered_by,
            candidate=candidate,
            client=client,
            business_unit=None,  # No aplica para el registro inicial
            action_type='approve_exception',
            details=f"Excepción aprobada: {evidence_type} - {notes}"
        )
        
        return contact
    
    @staticmethod
    def get_active_restrictions_for_client(client):
        """
        Obtiene todas las restricciones activas para un cliente.
        
        Args:
            client: Objeto Client
            
        Returns:
            QuerySet: Restricciones activas
        """
        return OffLimitsRestriction.objects.filter(
            client=client,
            is_active=True,
            end_date__gte=timezone.now().date()
        )
    
    @staticmethod
    def get_all_active_restrictions():
        """
        Obtiene todas las restricciones activas en el sistema.
        
        Returns:
            QuerySet: Restricciones activas
        """
        return OffLimitsRestriction.objects.filter(
            is_active=True,
            end_date__gte=timezone.now().date()
        )
