from django.utils import timezone
from datetime import timedelta
from app.models import Proposal, Opportunity, Vacancy

class ProposalGenerator:
    def __init__(self, opportunity_id):
        """
        Inicializa el generador de propuestas.
        
        Args:
            opportunity_id: ID de la oportunidad
        """
        self.opportunity_id = opportunity_id
        self.opportunity = None
        self.vacancies = None
        
    def generate(self):
        """
        Genera una propuesta completa.
        
        Returns:
            dict: Datos de la propuesta generada
        """
        self._load_opportunity()
        pricing = self._calculate_pricing()
        proposal = self._create_proposal(pricing)
        
        return {
            'proposal': proposal,
            'pricing': pricing
        }
        
    def _load_opportunity(self):
        """
        Carga los datos de la oportunidad.
        """
        self.opportunity = Opportunity.objects.get(id=self.opportunity_id)
        self.vacancies = self.opportunity.vacancies.all()
        
    def _calculate_pricing(self):
        """
        Calcula el pricing para la propuesta.
        
        Returns:
            dict: Detalles del pricing
        """
        from app.ats.pricing.utils import calculate_pricing
        return calculate_pricing(self.opportunity_id)
        
    def _create_proposal(self, pricing):
        """
        Crea la propuesta en la base de datos.
        
        Args:
            pricing: Detalles del pricing
            
        Returns:
            Proposal: Instancia de la propuesta creada
        """
        proposal = Proposal.objects.create(
            company=self.opportunity.company,
            pricing_total=pricing['total'],
            pricing_details=pricing
        )
        
        # Asociar vacantes
        for vacancy in self.vacancies:
            proposal.vacancies.add(vacancy)
        
        return proposal

class ProposalAnalyzer:
    def __init__(self):
        """
        Inicializa el analizador de propuestas.
        """
        self._load_data()
        
    def _load_data(self):
        """
        Carga los datos necesarios para el análisis.
        """
        self.proposals = Proposal.objects.all().select_related('company')
        
    def get_conversion_rate(self):
        """
        Calcula la tasa de conversión de propuestas a contratos.
        
        Returns:
            float: Tasa de conversión
        """
        total_proposals = self.proposals.count()
        converted = self.proposals.filter(status='CONVERTED').count()
        
        if total_proposals == 0:
            return 0
            
        return (converted / total_proposals) * 100
        
    def get_average_pricing(self):
        """
        Calcula el precio promedio de las propuestas.
        
        Returns:
            float: Precio promedio
        """
        total = sum(proposal.pricing_total for proposal in self.proposals)
        count = self.proposals.count()
        
        if count == 0:
            return 0
            
        return total / count
        
    def get_industry_breakdown(self):
        """
        Obtiene el desglose de propuestas por industria.
        
        Returns:
            dict: Desglose por industria
        """
        breakdown = {}
        
        for proposal in self.proposals:
            industry = proposal.opportunity.industry
            breakdown[industry] = breakdown.get(industry, 0) + 1
            
        return breakdown
