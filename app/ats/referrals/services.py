from django.utils import timezone
from django.db.models import Q
from decimal import Decimal

from app.models import Person, Company, Proposal
from .models import ReferralProgram

class ReferralService:
    """
    Servicio para manejar la lógica de negocio del programa de referidos.
    """
    
    @staticmethod
    def create_referral(referrer: Person, company_name: str, commission_percentage: Decimal = Decimal('10.00')) -> ReferralProgram:
        """
        Crea una nueva referencia.
        
        Args:
            referrer: Persona que hace la referencia
            company_name: Nombre de la empresa referida
            commission_percentage: Porcentaje de comisión (8-15%)
            
        Returns:
            ReferralProgram: Instancia creada
        """
        # Verificar si la empresa ya existe
        if Company.objects.filter(name__iexact=company_name).exists():
            raise ValueError("La empresa ya existe en el sistema")
            
        # Verificar límite de referidos activos
        active_referrals = ReferralProgram.objects.filter(
            referrer=referrer,
            status__in=['pending', 'validated']
        ).count()
        
        if active_referrals >= 5:  # Límite de 5 referidos activos
            raise ValueError("Has alcanzado el límite de referidos activos")
            
        # Crear la referencia
        referral = ReferralProgram.objects.create(
            referrer=referrer,
            referred_company=company_name,
            commission_percentage=commission_percentage
        )
        
        return referral
    
    @staticmethod
    def validate_referral(referral: ReferralProgram) -> bool:
        """
        Valida una referencia.
        
        Args:
            referral: Instancia de ReferralProgram
            
        Returns:
            bool: True si se validó correctamente
        """
        if referral.status != 'pending':
            return False
            
        referral.validate_referral()
        return True
    
    @staticmethod
    def complete_referral(referral: ReferralProgram, proposal: Proposal) -> bool:
        """
        Completa una referencia cuando se genera una propuesta.
        
        Args:
            referral: Instancia de ReferralProgram
            proposal: Propuesta generada
            
        Returns:
            bool: True si se completó correctamente
        """
        if referral.status != 'validated':
            return False
            
        referral.proposal = proposal
        referral.complete_referral()
        return True
    
    @staticmethod
    def calculate_commission(referral: ReferralProgram, amount: Decimal) -> Decimal:
        """
        Calcula la comisión para una referencia.
        
        Args:
            referral: Instancia de ReferralProgram
            amount: Monto de la propuesta
            
        Returns:
            Decimal: Monto de la comisión
        """
        return referral.calculate_commission(amount)
    
    @staticmethod
    def get_referrer_stats(referrer: Person) -> dict:
        """
        Obtiene estadísticas de referidos para una persona.
        
        Args:
            referrer: Persona que hace las referencias
            
        Returns:
            dict: Estadísticas de referidos
        """
        referrals = ReferralProgram.objects.filter(referrer=referrer)
        
        return {
            'total_referrals': referrals.count(),
            'pending_referrals': referrals.filter(status='pending').count(),
            'validated_referrals': referrals.filter(status='validated').count(),
            'completed_referrals': referrals.filter(status='completed').count(),
            'rejected_referrals': referrals.filter(status='rejected').count(),
            'total_commission': sum(
                referral.calculate_commission(referral.proposal.pricing_total)
                for referral in referrals.filter(status='completed')
                if referral.proposal and referral.proposal.pricing_total
            )
        }
    
    @staticmethod
    def search_referrals(query: str = None, status: str = None, referrer: Person = None) -> list:
        """
        Busca referidos según criterios.
        
        Args:
            query: Término de búsqueda
            status: Estado de las referencias
            referrer: Persona que hace las referencias
            
        Returns:
            list: Lista de referidos que coinciden con los criterios
        """
        filters = Q()
        
        if query:
            filters &= Q(referred_company__icontains=query)
            
        if status:
            filters &= Q(status=status)
            
        if referrer:
            filters &= Q(referrer=referrer)
            
        return ReferralProgram.objects.filter(filters).order_by('-created_at') 